from machine import Pin, ADC, reset
import network
import utime as time
import urequests as requests
import ujson
import sys

# Konfigurasi Hardware
PIR = Pin(15, Pin.IN)      # GPIO15 untuk PIR
LDR = ADC(Pin(34))         # GPIO34 (ADC) untuk LDR 
LED = Pin(19, Pin.OUT)     # GPIO19 untuk LED

# Kalibrasi ADC
LDR.atten(ADC.ATTN_11DB)  # Rentang penuh 0-3.3V
LDR.width(ADC.WIDTH_12BIT)  # Resolusi 12-bit

# Konfigurasi Jaringan
WIFI_SSID = "DIAS MOTOR"
WIFI_PASS = "budiono1977"
UBIDOTS_TOKEN = "BBUS-A1uMgpxyOyNqmTZ7tHrWvhI8pos3wk"
DEVICE_LABEL = "bebas"

# Parameter Sistem
SEND_INTERVAL = 10  # Detik
MAX_RETRIES = 3
LDR_THRESHOLD = 200  # Nilai threshold cahaya

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(pm=0xa11140)  # Nonaktifkan power save mode
    
    if not wlan.isconnected():
        print("Menghubungkan WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        
        for _ in range(30):  # Timeout 15 detik
            if wlan.isconnected():
                break
            time.sleep(0.5)
            print(".", end='')
    
    if wlan.isconnected():
        print("\nWiFi OK:", wlan.ifconfig())
        return True
    print("\nGagal koneksi WiFi")
    return False

def send_to_ubidots(motion, ldr, led_state):
    url = f"https://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_LABEL}"
    headers = {
        "X-Auth-Token": UBIDOTS_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "motion_detected": motion,
        "ldr_value": ldr,
        "led_state": led_state
    }
    
    print("Payload:", payload)  # Debug
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                url,
                data=ujson.dumps(payload),
                headers=headers,
                timeout=10
            )
            
            print(f"Attempt {attempt+1} Status: {response.status_code}")
            print("Response:", response.text)
            
            if response.status_code in [200, 201]:
                print("Data terkirim sukses")
                response.close()
                return True
                
            response.close()
            time.sleep(2)
            
        except Exception as e:
            print(f"Error attempt {attempt+1}: {str(e)}")
            if attempt == MAX_RETRIES-1:
                return False
            time.sleep(2)
    
    return False

def main():
    if not connect_wifi():
        print("WiFi gagal, reset dalam 30s...")
        time.sleep(30)
        reset()
    
    last_sent = 0
    print("Sistem mulai monitoring...")
    
    while True:
        try:
            current_time = time.time()
            
            if current_time - last_sent >= SEND_INTERVAL:
                motion = PIR.value()
                ldr_val = LDR.read()
                
                # Logika kontrol LED: 
                # - Nyala jika ada gerakan ATAU cahaya rendah
                # - Tetap mati jika cahaya cukup
                led_state = 1 if (motion or ldr_val < LDR_THRESHOLD) else 0
                LED.value(led_state)
                
                if send_to_ubidots(motion, ldr_val, led_state):
                    last_sent = current_time
                    print(f"Data Terkirim | Motion: {motion}, LDR: {ldr_val}, LED: {led_state}")
                else:
                    print("Gagal mengirim data")
                
            time.sleep(1)
            
        except OSError as e:
            print("OSError:", e)
            time.sleep(10)
        except Exception as e:
            print("Error kritis:", e)
            time.sleep(30)
            reset()

if __name__ == "__main__":
    main()