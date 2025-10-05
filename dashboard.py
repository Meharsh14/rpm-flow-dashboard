import streamlit as st
import pandas as pd
import time
import paho.mqtt.client as mqtt
from io import BytesIO

st.set_page_config(page_title="RPM & Flow Meter Dashboard", layout="wide")

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "esp32/rpmFlow"

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Timestamp", "RPM", "Flow", "Volume"])
if "run" not in st.session_state:
    st.session_state.run = False
if "volume" not in st.session_state:
    st.session_state.volume = 0.0

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        st.session_state.mqtt_status = "✅ Connected"
        client.subscribe(MQTT_TOPIC)
    else:
        st.session_state.mqtt_status = f"❌ Failed (rc={rc})"

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        data = payload.replace('{"data":"', '').replace('"}', '')
        rpm, flow = map(float, data.split(","))
        st.session_state.volume += (flow / 60.0)

        new_row = {"Timestamp": pd.Timestamp.now(), "RPM": rpm, "Flow": flow, "Volume": st.session_state.volume}
        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
    except Exception as e:
        print("Parse error:", e)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)

st.title("🔄 RPM & Flow Live Dashboard")
st.write(f"**MQTT Status:** {st.session_state.get('mqtt_status', '🔄 Connecting...')}")

col1, col2 = st.columns(2)
col1.button("▶️ Start", on_click=lambda: client.loop_start() or setattr(st.session_state, "run", True))
col2.button("⏹ Stop", on_click=lambda: client.loop_stop() or setattr(st.session_state, "run", False))

metric = st.empty()
chart = st.empty()

if st.session_state.run:
    while st.session_state.run:
        if not st.session_state.data.empty:
            latest = st.session_state.data.iloc[-1]
            with metric.container():
                c1, c2, c3 = st.columns(3)
                c1.metric("RPM", int(latest["RPM"]))
                c2.metric("Flow (L/min)", latest["Flow"])
                c3.metric("Total Volume (L)", round(latest["Volume"], 2))

            chart.line_chart(st.session_state.data.set_index("Timestamp")[["RPM", "Flow"]].tail(50))
        time.sleep(1)

if not st.session_state.data.empty:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        st.session_state.data.to_excel(writer, index=False, sheet_name="Data")
    st.download_button(
        label="📥 Download Excel",
        data=buffer,
        file_name="rpm_flow_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
