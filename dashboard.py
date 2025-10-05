import streamlit as st
import pandas as pd
import time
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
from io import BytesIO

# --- Config ---
st.set_page_config(page_title="RPM Dashboard", layout="wide")

MQTT_BROKER = "10.217.118.7"  # 🧠 Replace with your PC IP
MQTT_PORT = 1883
MQTT_TOPIC = "ifb/rpmData"

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Timestamp", "RPM"])
if "run" not in st.session_state:
    st.session_state.run = False

# --- MQTT Handlers ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        st.session_state.mqtt_status = "✅ Connected"
        client.subscribe(MQTT_TOPIC)
    else:
        st.session_state.mqtt_status = f"❌ Failed (rc={rc})"

def on_message(client, userdata, msg):
    try:
        rpm = int(msg.payload.decode().strip())
        new_row = {"Timestamp": pd.Timestamp.now(), "RPM": rpm}
        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
    except Exception as e:
        print("Error parsing MQTT:", e)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    st.session_state.mqtt_status = "🔄 Connecting..."
except Exception as e:
    st.session_state.mqtt_status = f"⚠️ MQTT Error: {e}"

def start_stream():
    st.session_state.run = True
    client.loop_start()

def stop_stream():
    st.session_state.run = False
    client.loop_stop()

st.title("⚙️ Real-Time RPM Dashboard")
st.markdown(f"**MQTT Status:** {st.session_state.mqtt_status}")

col1, col2 = st.columns(2)
col1.button("▶️ Start Stream", on_click=start_stream)
col2.button("⏹️ Stop Stream", on_click=stop_stream)

plot_container = st.empty()
metric_container = st.empty()

if st.session_state.run:
    while st.session_state.run:
        if not st.session_state.data.empty:
            latest = st.session_state.data.iloc[-1]
            with metric_container.container():
                st.metric("🔄 Current RPM", latest["RPM"])
            with plot_container.container():
                plt.figure(figsize=(8, 4))
                plt.plot(st.session_state.data["Timestamp"], st.session_state.data["RPM"], label="RPM", linewidth=2)
                plt.xlabel("Time")
                plt.ylabel("RPM")
                plt.legend()
                st.pyplot(plt)
        time.sleep(1)

if not st.session_state.run and not st.session_state.data.empty:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        st.session_state.data.to_excel(writer, index=False, sheet_name="Data")
    st.download_button(
        label="📥 Download Excel",
        data=buffer,
        file_name="rpm_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

