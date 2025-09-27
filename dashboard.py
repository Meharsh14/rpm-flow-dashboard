import streamlit as st
import pandas as pd
import random
import time
from io import BytesIO

# --- Page Config ---
st.set_page_config(page_title="RPM & Flow Meter Dashboard", layout="wide")

st.title("⚙️ RPM & Flow & Volume Dashboard")
st.markdown("Simulated live data (random values for testing without ESP32)")

# --- Placeholders ---
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Timestamp", "RPM", "Flow", "Volume"])

if "run" not in st.session_state:
    st.session_state.run = False

def start_stream():
    st.session_state.run = True

def stop_stream():
    st.session_state.run = False

# --- Control Buttons ---
col1, col2 = st.columns(2)
col1.button("▶️ Start Simulation", on_click=start_stream)
col2.button("⏹️ Stop Simulation", on_click=stop_stream)

# --- Tabs ---
tab1, tab2 = st.tabs(["📊 Live Data", "💧 Water Volume"])

# Simulation loop
while st.session_state.run:
    rpm = random.randint(500, 1500)  # fake RPM
    flow = round(random.uniform(1.0, 10.0), 2)  # fake L/min
    volume = 0

    if not st.session_state.data.empty:
        # assume 1 second interval => convert flow L/min → L/sec
        last_volume = st.session_state.data["Volume"].iloc[-1]
        volume = last_volume + (flow / 60.0)  # add litres per second
    else:
        volume = flow / 60.0

    # Add to DataFrame
    new_row = {"Timestamp": pd.Timestamp.now(), "RPM": rpm, "Flow": flow, "Volume": volume}
    st.session_state.data = pd.concat(
        [st.session_state.data, pd.DataFrame([new_row])], ignore_index=True
    )

    # --- Tab 1: Live Flow & RPM ---
    with tab1:
        colA, colB = st.columns(2)
        colA.metric("💧 Flow Rate (L/min)", flow)
        colB.metric("🔄 RPM", rpm)

        st.line_chart(st.session_state.data.set_index("Timestamp")[["RPM", "Flow"]].tail(50))

    # --- Tab 2: Water Volume ---
    with tab2:
        total_volume = round(st.session_state.data["Volume"].iloc[-1], 2)
        st.metric("Total Water Consumed (L)", total_volume)
        st.area_chart(st.session_state.data.set_index("Timestamp")[["Volume"]])

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
