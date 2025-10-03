import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import time
from io import BytesIO

# --- Config ---
st.set_page_config(page_title="ESP32 RPM & Flow Dashboard", layout="wide")
st.title("⚙️ ESP32 RPM, Flow & Volume Dashboard")

BROKER = "broker.hivemq.com"   # Public broker (or your broker IP)
TOPIC = "esp32/demo/data"

# --- Session State ---
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Timestamp", "RPM", "Flow", "Volume"])

if "run" not in st.session_state:
    st.session_state.run = False

if "last_volume" not in st.session_state:
    st.session_state.last_volume = 0.0

# --- MQTT Handlers ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        st.session_state.mqtt_status = "✅ Connected"
        client.subscribe(TOPIC)
    else:
        st.session_state.mqtt_status = f"❌ Failed (rc={rc})"

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        rpm = data.get("rpm", 0)
        flow = data.get("flow", 0.0)

        # integrate volume (flow in L/min → L/s)
        st.session_state.last_volume += (flow / 60.0)

        new_row = {
            "Timestamp": pd.Timestamp.now(),
            "RPM": rpm,
            "Flow": flow,
            "Volume": st.session_state.last_volume
        }
        st.session_state.data = pd.concat(
            [st.session_state.data, pd.DataFrame([new_row])],
            ignore_index=True
        )
    except Exception as e:
        print("Error parsing:", e)

# --- MQTT Setup ---
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
try:
    client.connect(BROKER, 1883, 60)
    st.session_state.mqtt_status = "🔄 Connecting..."
except Exception as e:
    st.session_state.mqtt_status = f"⚠️ MQTT Error: {e}"

# --- UI ---
st.markdown(f"**MQTT Status:** {st.session_state.mqtt_status}")

col1, col2 = st.columns(2)
if col1.button("▶️ Start Simulation"):
    st.session_state.run = True
    client.loop_start()

if col2.button("⏹️ Stop Simulation"):
    st.session_state.run = False
    client.loop_stop()

placeholder = st.empty()

# --- Live Update ---
if st.session_state.run:
    while st.session_state.run:
        with placeholder.container():
            if not st.session_state.data.empty:
                latest = st.session_state.data.iloc[-1]

                c1, c2, c3 = st.columns(3)
                c1.metric("🔄 RPM", latest["RPM"])
                c2.metric("💧 Flow Rate (L/min)", latest["Flow"])
                c3.metric("🧪 Total Volume (L)", round(latest["Volume"], 2))

                st.line_chart(
                    st.session_state.data.set_index("Timestamp")[["RPM", "Flow"]].tail(50)
                )
            else:
                st.info("Waiting for data from ESP32...")

        time.sleep(1)

# --- Excel Export ---
if not st.session_state.run and not st.session_state.data.empty:
    st.markdown("### 📥 Download Recorded Data")
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        st.session_state.data.to_excel(writer, index=False, sheet_name="Data")
    st.download_button(
        label="Download Excel",
        data=buffer,
        file_name="esp32_rpm_flow_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
