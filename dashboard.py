import streamlit as st
import pandas as pd
import time
import paho.mqtt.client as mqtt
from io import BytesIO

# --- Config ---
st.set_page_config(page_title="RPM & Flow Meter Dashboard", layout="wide")

MQTT_BROKER = "10.0.5.121"   # same as your ESP32 broker
MQTT_PORT = 1883
MQTT_TOPIC = "ifb/rpmData"

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
        client.subscribe(MQTT_TOPIC)
    else:
        st.session_state.mqtt_status = f"❌ Failed (rc={rc})"

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        # Expected: "RPM,Flow" or just "RPM"
        parts = payload.split(",")
        rpm = int(parts[0])
        flow = float(parts[1]) if len(parts) > 1 else 0.0

        # Calculate volume (simple integration per sec)
        st.session_state.last_volume += (flow / 60.0)  # L/s

        new_row = {
            "Timestamp": pd.Timestamp.now(),
            "RPM": rpm,
            "Flow": flow,
            "Volume": st.session_state.last_volume,
        }
        st.session_state.data = pd.concat(
            [st.session_state.data, pd.DataFrame([new_row])], ignore_index=True
        )
    except Exception as e:
        print("Error parsing MQTT:", e)

# --- Start/Stop functions ---
def start_stream():
    st.session_state.run = True
    client.loop_start()

def stop_stream():
    st.session_state.run = False
    client.loop_stop()

# --- MQTT Setup ---
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    st.session_state.mqtt_status = "🔄 Connecting..."
except Exception as e:
    st.session_state.mqtt_status = f"⚠️ MQTT Error: {e}"

# --- UI ---
st.title("⚙️ RPM, Flow & Volume Dashboard")
st.markdown(f"**MQTT Status:** {st.session_state.mqtt_status}")

col1, col2 = st.columns(2)
col1.button("▶️ Start Stream", on_click=start_stream)
col2.button("⏹️ Stop Stream", on_click=stop_stream)

metric_container = st.empty()
chart_container = st.empty()

# --- Live update loop ---
if st.session_state.run:
    while st.session_state.run:
        if not st.session_state.data.empty:
            latest = st.session_state.data.iloc[-1]
            with metric_container.container():
                c1, c2, c3 = st.columns(3)
                c1.metric("💧 Flow Rate (L/min)", latest["Flow"])
                c2.metric("🔄 RPM", latest["RPM"])
                c3.metric("🧪 Total Volume (L)", round(latest["Volume"], 2))

            chart_container.line_chart(
                st.session_state.data.set_index("Timestamp")[["RPM", "Flow"]].tail(50)
            )
        time.sleep(1)

# --- Download Excel after stop ---
if not st.session_state.run and not st.session_state.data.empty:
    st.markdown("### 📥 Download Recorded Data")
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        st.session_state.data.to_excel(writer, index=False, sheet_name="Data")
    st.download_button(
        label="Download Excel",
        data=buffer,
        file_name="rpm_flow_volume_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
