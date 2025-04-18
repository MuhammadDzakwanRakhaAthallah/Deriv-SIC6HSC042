import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Konfigurasi (tidak diubah)
UBIDOTS_TOKEN = "BBUS-A1uMgpxyOyNqmTZ7tHrWvhI8pos3wk"
DEVICE_LABEL = "bebas"

def get_data():
    url = f"https://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_LABEL}"
    headers = {"X-Auth-Token": UBIDOTS_TOKEN}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('variables', {}).values()
        st.error(f"Error: {response.status_code}")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def main():
    st.title("Real-time ESP32 Data Monitoring")
    
    # Container untuk data terbaru
    latest_data = st.container()
    
    # Ambil data saat pertama kali load
    data = get_data()
    
    if data:
        with latest_data:
            st.header("🔄 Latest Sensor Readings")
            cols = st.columns(3)
            
            # Ekstrak nilai terbaru
            sensor_values = {
                'motion_detected': {'value': None, 'timestamp': None},
                'ldr_value': {'value': None, 'timestamp': None},
                'led_state': {'value': None, 'timestamp': None}
            }
            
            for var in data:
                var_name = var.get('name')
                last_value = var.get('last_value')
                
                if var_name in sensor_values:
                    sensor_values[var_name]['value'] = last_value.get('value')
                    sensor_values[var_name]['timestamp'] = datetime.fromtimestamp(
                        last_value.get('timestamp')/1000
                    ).strftime('%Y-%m-%d %H:%M:%S')

            # Tampilkan dalam kolom
            with cols[0]:
                st.metric(
                    label="Motion Detected",
                    value="YES" if sensor_values['motion_detected']['value'] else "NO",
                    help=f"Last update: {sensor_values['motion_detected']['timestamp']}"
                )
                
            with cols[1]:
                st.metric(
                    label="LDR Value",
                    value=sensor_values['ldr_value']['value'],
                    help=f"Last update: {sensor_values['ldr_value']['timestamp']}"
                )
                
            with cols[2]:
                st.metric(
                    label="LED State",
                    value="ON" if sensor_values['led_state']['value'] else "OFF",
                    help=f"Last update: {sensor_values['led_state']['timestamp']}"
                )

        # Grafik historis LDR
        st.header("📈 LDR Value History")
        ldr_history_url = f"https://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_LABEL}"
        ldr_response = requests.get(ldr_history_url, headers=headers)
        
        if ldr_response.status_code == 200:
            ldr_data = ldr_response.json().get('results', [])
            if ldr_data:
                df = pd.DataFrame([{
                    'timestamp': datetime.fromtimestamp(d['timestamp']/1000),
                    'value': d['value']
                } for d in ldr_data])
                
                df.set_index('timestamp', inplace=True)
                st.line_chart(df, use_container_width=True)
            else:
                st.warning("No historical LDR data available")
                
    else:
        st.warning("Tidak ada data yang diterima dari perangkat")

    # Auto-refresh setiap 5 detik
    st.rerun()

if __name__ == "__main__":
    st.set_page_config(page_title="ESP32 Monitor", page_icon="🌐")
    main()