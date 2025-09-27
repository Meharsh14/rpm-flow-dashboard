import streamlit as st
import pandas as pd
import numpy as np
import time
import random

# --- Page Config ---
st.set_page_config(page_title="RPM & Flow Meter Dashboard", layout="wide")

st.title("⚙️ RPM & Flow Meter Test Dashboard")
st.markdown("Simulated live data (random values for testing without ESP32)")

# --- Placeholders ---
flow_placeholder = st.empty()
rpm_placeholder = st.empty()
chart_placeholder = st.empty()

# --- DataFrame to store readings ---
data = pd.DataFrame(columns=["Timestamp", "RPM", "Flow"])

# --- Simulation loop ---
if "run" not in st.session_state:
    st.session_state.run = False

def start_stream():
    st.session_state.run = True

def stop_stream():
    st.session_state.run = False

# Buttons
col1, col2 = st.columns(2)
col1.button("▶️ Start Simulation", on_click=start_stream)
col2.button("⏹️ Stop Simulation", on_click=stop_stream)

# Simulation
while st.session_state.run:
    # Generate random data
    rpm = random.randint(500, 1500)      # fake RPM
    flow = round(random.uniform(1.0, 10.0), 2)  # fake L/min

    # Update dataframe
    new_row = {"Timestamp": pd.Timestamp.now(), "RPM": rpm, "Flow": flow}
    data = pd.concat([data, pd.DataFrame([new_row])], ignore_index=True)

    # Display values
    flow_placeholder.metric("💧 Flow Rate (L/min)", flow)
    rpm_placeholder.metric("🔄 RPM", rpm)

    # Show chart (last 50 points)
    chart_placeholder.line_chart(data.set_index("Timestamp").tail(50))

    # Wait
    time.sleep(1)
