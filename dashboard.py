import streamlit as st
import paho.mqtt.client as mqtt
import pandas as pd
import time
from io import BytesIO
import matplotlib.pyplot as plt

st.set_page_config(page_title="Live RPM Dashboard", layout="wide")

st.title("🚀 Live Washing Machine RPM Monitor")

mqtt_status = st.empty()
rpm_display = st.empty()
chart_area = st.empty()
placeholder = st.empty()

start_btn = st.button("Start Simulation")
stop_btn = st.button("Stop Simulation")

data = []
is_running = False

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        mqtt_status.success("✅ Connected to MQTT Broker")
        client.subscribe("washingmachine/rpm")
    else:
        mqtt_status.error("❌ Failed to connect, return code %d" % rc)

def on_message(client, userdata, msg):
    global data, is_running
    if is_running:
        try:
            rpm = float(msg.payload.decode())
            data.append({"Time": time.strftime("%H:%M:%S"), "RPM": rpm})
            rpm_display.metric("Current RPM", f"{rpm:.2f}")
            df = pd.DataFrame(data)
            chart_area.line_chart(df.set_index("Time"))
        except:
            pass

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect("10.217.118.7", 1883, 60)
    mqtt_status.info("🔄 Connecting to MQTT broker...")
except:
    mqtt_status.error("⚠️ Unable to connect to MQTT broker.")

if start_btn:
    is_running = True
    st.toast("Started fetching live data!")
if stop_btn:
    is_running = False
    st.toast("Stopped fetching data!")

client.loop_start()

if not is_running:
    if len(data) > 0:
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button(
            label="📊 Download Data as Excel",
            data=output.getvalue(),
            file_name="rpm_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        placeholder.warning("No data to save yet.")
