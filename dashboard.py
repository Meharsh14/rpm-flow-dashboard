import streamlit as st
import time, io, re
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import serial
from streamlit_autorefresh import st_autorefresh

# ------------------------------
# SERIAL CONFIG (EDIT COM PORT)
# ------------------------------
SERIAL_PORT = "COM5"   # e.g. COM3 / COM5
BAUD_RATE = 9600

# ------------------------------
# Streamlit Setup
# ------------------------------
st.set_page_config(page_title="RPM & Flow Dashboard", layout="wide")
st.title("📊 Washing Machine RPM, Flow & Volume Dashboard")
st.caption("Live data directly from Arduino UNO (USB)")

# ------------------------------
# Serial Connection (Cached)
# ------------------------------
@st.cache_resource
def init_serial():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        return ser
    except Exception as e:
        st.error(f"❌ Serial connection failed: {e}")
        return None

ser = init_serial()

# ------------------------------
# Utility
# ------------------------------
def safe_float(value):
    try:
        return float(value)
    except:
        return 0.0

def read_serial():
    if ser and ser.in_waiting:
        line = ser.readline().decode(errors="ignore").strip()
        return line
    return None

# ------------------------------
# Session State
# ------------------------------
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(
        columns=["Time", "RPM", "FlowRate", "TotalVolume"]
    )

if "running" not in st.session_state:
    st.session_state.running = True

# ------------------------------
# Controls
# ------------------------------
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("▶️ Start"):
        st.session_state.running = True

with col2:
    if st.button("⏹ Stop"):
        st.session_state.running = False

with col3:
    if not st.session_state.history.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            st.session_state.history.to_excel(writer, index=False)
        output.seek(0)

        st.download_button(
            "💾 Download Excel",
            data=output,
            file_name="washing_machine_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# ------------------------------
# Auto Refresh
# ------------------------------
st_autorefresh(interval=1500, key="refresh")

# ------------------------------
# Read & Process Data
# ------------------------------
line = read_serial()

if line:
    parts = line.split(",")

    if len(parts) == 3:
        rpm = safe_float(parts[0])
        flow = safe_float(parts[1])
        volume = safe_float(parts[2])

        new_row = {
            "Time": pd.Timestamp.now(),
            "RPM": rpm,
            "FlowRate": flow,
            "TotalVolume": volume,
        }

        st.session_state.history = pd.concat(
            [st.session_state.history, pd.DataFrame([new_row])],
            ignore_index=True,
        )

        if len(st.session_state.history) > 500:
            st.session_state.history = st.session_state.history.tail(500)

# ------------------------------
# Display Gauges
# ------------------------------
if not st.session_state.history.empty:
    latest = st.session_state.history.iloc[-1]

    c1, c2, c3 = st.columns(3)

    with c1:
        st.plotly_chart(
            go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=latest["RPM"],
                    title={"text": "RPM"},
                    gauge={"axis": {"range": [0, 2000]}},
                )
            ),
            use_container_width=True,
        )

    with c2:
        st.plotly_chart(
            go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=latest["FlowRate"],
                    title={"text": "Flow Rate (L/min)"},
                    gauge={"axis": {"range": [0, 20]}},
                )
            ),
            use_container_width=True,
        )

    with c3:
        st.plotly_chart(
            go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=latest["TotalVolume"],
                    title={"text": "Total Volume (L)"},
                    gauge={"axis": {"range": [0, max(10, latest["TotalVolume"] + 1)]}},
                )
            ),
            use_container_width=True,
        )

    # ------------------------------
    # Live Graph
    # ------------------------------
    with st.expander("📈 Live Graph", expanded=True):
        fig = px.line(
            st.session_state.history,
            x="Time",
            y=["RPM", "FlowRate"],
            title="Live RPM & Flow Rate",
        )
        st.plotly_chart(fig, use_container_width=True)
