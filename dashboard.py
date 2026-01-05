import streamlit as st
import time, io
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import serial
from streamlit_autorefresh import st_autorefresh

# ------------------------------
# SERIAL CONFIG
# ------------------------------
SERIAL_PORT = "COM23"
BAUD_RATE = 9600

# ------------------------------
# Streamlit Setup
# ------------------------------
st.set_page_config(page_title="RPM & Flow Dashboard", layout="wide")
st.title("📊 Washing Machine RPM, Flow & Volume Dashboard")
st.caption("Live data directly from Arduino UNO (USB)")

# ------------------------------
# Serial Connection (ONE TIME)
# ------------------------------
@st.cache_resource
def init_serial():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    return ser

try:
    ser = init_serial()
except Exception as e:
    st.error(f"❌ Serial connection failed: {e}")
    st.stop()

# ------------------------------
# Session State
# ------------------------------
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(
        columns=["Time", "RPM", "FlowRate", "TotalVolume"]
    )

# ------------------------------
# Auto Refresh
# ------------------------------
st_autorefresh(interval=1000, key="refresh")

# ------------------------------
# Read Serial
# ------------------------------
if ser.in_waiting:
    line = ser.readline().decode(errors="ignore").strip()

    parts = line.split(",")
    if len(parts) == 3:
        try:
            rpm = float(parts[0])
            flow = float(parts[1])
            volume = float(parts[2])

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

        except:
            pass

# ------------------------------
# Display
# ------------------------------
if not st.session_state.history.empty:
    latest = st.session_state.history.iloc[-1]

    c1, c2, c3 = st.columns(3)

    with c1:
        st.plotly_chart(
            go.Figure(go.Indicator(
                mode="gauge+number",
                value=latest["RPM"],
                title={"text": "RPM"},
                gauge={"axis": {"range": [0, 2000]}},
            )),
            use_container_width=True,
        )

    with c2:
        st.plotly_chart(
            go.Figure(go.Indicator(
                mode="gauge+number",
                value=latest["FlowRate"],
                title={"text": "Flow Rate (L/min)"},
                gauge={"axis": {"range": [0, 20]}},
            )),
            use_container_width=True,
        )

    with c3:
        st.plotly_chart(
            go.Figure(go.Indicator(
                mode="gauge+number",
                value=latest["TotalVolume"],
                title={"text": "Total Volume (L)"},
                gauge={"axis": {"range": [0, max(10, latest["TotalVolume"] + 1)]}},
            )),
            use_container_width=True,
        )

    with st.expander("📈 Live Graph", expanded=True):
        fig = px.line(
            st.session_state.history,
            x="Time",
            y=["RPM", "FlowRate"],
            title="Live RPM & Flow Rate",
        )
        st.plotly_chart(fig, use_container_width=True)
