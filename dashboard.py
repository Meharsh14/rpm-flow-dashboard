import streamlit as st
import time
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import serial
from streamlit_autorefresh import st_autorefresh

# ---------------- SERIAL CONFIG ----------------
SERIAL_PORT = "COM23"
BAUD_RATE = 9600

st.set_page_config(page_title="RPM & Flow Dashboard", layout="wide")
st.title("📊 Washing Machine RPM, Flow & Volume Dashboard")

# ---------------- SERIAL INIT ----------------
@st.cache_resource
def init_serial():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    return ser

try:
    ser = init_serial()
except Exception as e:
    st.error(f"❌ Serial error: {e}")
    st.stop()

# ---------------- SESSION STATE ----------------
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(
        columns=["Time", "RPM", "FlowRate", "TotalVolume"]
    )

# ---------------- AUTO REFRESH ----------------
st_autorefresh(interval=1000, key="refresh")

# ---------------- READ SERIAL (ALWAYS) ----------------
try:
    line = ser.readline().decode(errors="ignore").strip()
except:
    line = ""

st.write("📡 RAW SERIAL:", line)  # DEBUG LINE (IMPORTANT)

if line:
    parts = line.split(",")

    if len(parts) == 3:
        try:
            rpm = float(parts[0])
            flow = float(parts[1])
            volume = float(parts[2])

            st.session_state.history.loc[len(st.session_state.history)] = [
                pd.Timestamp.now(),
                rpm,
                flow,
                volume
            ]

            if len(st.session_state.history) > 300:
                st.session_state.history = st.session_state.history.tail(300)

        except ValueError:
            st.warning("⚠ Parsing error")

# ---------------- DISPLAY ----------------
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
            use_container_width=True
        )

    with c2:
        st.plotly_chart(
            go.Figure(go.Indicator(
                mode="gauge+number",
                value=latest["FlowRate"],
                title={"text": "Flow Rate (L/min)"},
                gauge={"axis": {"range": [0, 20]}},
            )),
            use_container_width=True
        )

    with c3:
        st.plotly_chart(
            go.Figure(go.Indicator(
                mode="gauge+number",
                value=latest["TotalVolume"],
                title={"text": "Total Volume (L)"},
            )),
            use_container_width=True
        )

    fig = px.line(
        st.session_state.history,
        x="Time",
        y=["RPM", "FlowRate"],
        title="Live RPM & Flow Rate"
    )
    st.plotly_chart(fig, use_container_width=True)
