import streamlit as st
import time
import threading
import serial
import pandas as pd
import plotly.express as px

SERIAL_PORT = "COM23"
BAUD_RATE = 9600

# ---------------- SHARED DATA ----------------
latest_data = {
    "rpm": 0,
    "flow": 0.0,
    "volume": 0.0
}

# ---------------- SERIAL THREAD ----------------
def serial_reader():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
    except Exception as e:
        print("Serial error:", e)
        return

    while True:
        try:
            line = ser.readline().decode(errors="ignore").strip()
            if not line:
                continue

            parts = line.split(",")
            if len(parts) == 3:
                latest_data["rpm"] = float(parts[0])
                latest_data["flow"] = float(parts[1])
                latest_data["volume"] = float(parts[2])

        except:
            pass

# Start thread ONCE
if "serial_thread_started" not in st.session_state:
    threading.Thread(target=serial_reader, daemon=True).start()
    st.session_state.serial_thread_started = True

# ---------------- STREAMLIT UI ----------------
st.set_page_config(layout="wide")
st.title("📊 Washing Machine Live Dashboard")

st_autorefresh = st.experimental_rerun
time.sleep(1)

df = pd.DataFrame([{
    "RPM": latest_data["rpm"],
    "FlowRate": latest_data["flow"],
    "TotalVolume": latest_data["volume"]
}])

st.metric("RPM", latest_data["rpm"])
st.metric("Flow Rate (L/min)", latest_data["flow"])
st.metric("Total Volume (L)", latest_data["volume"])

fig = px.bar(
    df,
    y=["RPM", "FlowRate", "TotalVolume"],
    title="Live Values"
)
st.plotly_chart(fig, use_container_width=True)

