import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# Konfigurasi
UBIDOTS_TOKEN = "BBUS-A1uMgpxyOyNqmTZ7tHrWvhI8pos3wk"
DEVICE_LABEL = "bebas"
REFRESH_INTERVAL = 5  # Detik

@st.cache_data(ttl=REFRESH_INTERVAL)
def get_ubidots_data():
    try:
        url = f"https://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_LABEL}"
        headers = {"X-Auth-Token": UBIDOTS_TOKEN}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        
        data = r.json()
        return {
            "motion": data.get("motion_detected", {}).get("last_value", {}).get("value", 0),
            "ldr": data.get("ldr_value", {}).get("last_value", {}).get("value", 0),
            "led": data.get("led_state", {}).get("last_value", {}).get("value", 0),
            "timestamp": data.get("motion_detected", {}).get("last_value", {}).get("timestamp", 0)
        }
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def main():
    st.set_page_config(page_title="IoT Monitoring", layout="wide")
    
    st.title("📡 Monitoring Lampu Otomatis")
    st.markdown("""
    **Logika Sistem**:
    - 🟢 **Gerakan Terdeteksi**: LED Menyala
    - 🔵 **Cahaya Terang + Tidak Ada Gerakan**: LED Mati
    - 🌙 **Gelap + Tidak Ada Gerakan**: Pertahankan Status
    """)
    
    placeholder = st.empty()
    
    while True:
        data = get_ubidots_data()
        
        with placeholder.container():
            if not data:
                st.warning("Menunggu data...")
                time.sleep(REFRESH_INTERVAL)
                continue
            
            # Tampilan Real-time
            cols = st.columns(3)
            with cols[0]:
                st.metric("Gerakan", "DETECTED" if data["motion"] else "TIDAK ADA", 
                         help="1 = Ada gerakan")
            with cols[1]:
                st.metric("Intensitas Cahaya", data["ldr"])
            with cols[2]:
                st.metric("Status LED", "ON 🔆" if data["led"] else "OFF ⚫")
            
            # Grafik
            chart_data = pd.DataFrame({
                "Parameter": ["Gerakan", "Cahaya", "Lampu"],
                "Nilai": [data["motion"]*1000, data["ldr"], data["led"]*500]
            })
            st.bar_chart(chart_data.set_index("Parameter"))
            
            # Waktu Real-time
            current_time = datetime.now()
            st.caption(f"🕒 Waktu Saat Ini: {current_time.strftime('%d/%m/%Y %H:%M:%S')}")
            
            # Last Updated
            last_update = datetime.fromtimestamp(data["timestamp"]/1000)
            st.caption(f"🕒 Terakhir Update: {last_update.strftime('%d/%m/%Y %H:%M:%S')}")
        
        time.sleep(REFRESH_INTERVAL)

if __name__ == "__main__":
    main()
