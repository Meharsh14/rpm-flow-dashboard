import streamlit as st
import requests
import time, io, re
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# ------------------------------
# Firebase Realtime Database URLs
# ------------------------------
BASE_URL = "https://rpm-flow-volume-default-rtdb.asia-southeast1.firebasedatabase.app/WashingMachine"
URL_RPM = f"{BASE_URL}/RPM.json"
URL_FLOW = f"{BASE_URL}/FlowRate.json"
URL_VOLUME = f"{BASE_URL}/TotalVolume.json"

# ------------------------------
# Streamlit Setup
# ------------------------------
st.set_page_config(page_title="RPM & Flow Dashboard", layout="wide")
st.title("📊 Washing Machine RPM & Flow Dashboard")
st.caption("Live data fetched from Firebase Realtime Database")

# ------------------------------
# Utility
# ------------------------------
def safe_float(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"[-+]?\d*\.?\d+", value)
        return float(match.group()) if match else 0.0
    return 0.0

# ------------------------------
# Session State
# ------------------------------
if "running" not in st.session_state:
    st.session_state.running = False

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "elapsed_sec" not in st.session_state:
    st.session_state.elapsed_sec = 0

if "prev_time" not in st.session_state:
    st.session_state.prev_time = time.time()

if "total_volume" not in st.session_state:
    st.session_state.total_volume = 0.0

if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(
        columns=[
            "Timestamp",
            "Elapsed_Time_sec",
            "RPM",
            "FlowRate",
            "TotalVolume",
        ]
    )

# ------------------------------
# Buttons
# ------------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button("▶️ Start"):
        st.session_state.running = True
        st.session_state.start_time = time.time()
        st.session_state.prev_time = time.time()

with col2:
    stop_clicked = st.button("⏹ Stop")
    if stop_clicked:
        st.session_state.running = False

# ------------------------------
# Auto Refresh (1 sec)
# ------------------------------
st_autorefresh(interval=1000, key="refresh")

# ------------------------------
# Fetch Firebase Data
# ------------------------------
try:
    rpm_resp = requests.get(URL_RPM, timeout=5)
    flow_resp = requests.get(URL_FLOW, timeout=5)
    vol_resp = requests.get(URL_VOLUME, timeout=5)

    if all(r.status_code == 200 for r in [rpm_resp, flow_resp, vol_resp]):

        rpm = safe_float(rpm_resp.json())
        flow = safe_float(flow_resp.json())

        now = time.time()
        delta = now - st.session_state.prev_time

        # ---------------- TIMER ----------------
        if st.session_state.running:
            st.session_state.elapsed_sec = int(now - st.session_state.start_time)
            st.session_state.total_volume += (flow / 60) * delta

        st.session_state.prev_time = now

        # ---------------- SAVE DATA ----------------
        if st.session_state.running:
            st.session_state.history = pd.concat(
                [
                    st.session_state.history,
                    pd.DataFrame(
                        [
                            {
                                "Timestamp": pd.Timestamp.now(),
                                "Elapsed_Time_sec": st.session_state.elapsed_sec,
                                "RPM": rpm,
                                "FlowRate": flow,
                                "TotalVolume": st.session_state.total_volume,
                            }
                        ]
                    ),
                ],
                ignore_index=True,
            )

        if len(st.session_state.history) > 1000:
            st.session_state.history = st.session_state.history.tail(1000)

        # ---------------- DISPLAY TIMER ----------------
        st.metric("⏱ Timer (sec)", st.session_state.elapsed_sec)

        # ---------------- GAUGES ----------------
        c1, c2, c3 = st.columns(3)

        with c1:
            st.plotly_chart(
                go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=rpm,
                    title={"text": "RPM"},
                    gauge={"axis": {"range": [0, 2000]}}
                )),
                use_container_width=True,
            )

        with c2:
            st.plotly_chart(
                go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=flow,
                    title={"text": "Flow Rate (L/min)"},
                    gauge={"axis": {"range": [0, 20]}}
                )),
                use_container_width=True,
            )

        with c3:
            st.plotly_chart(
                go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=st.session_state.total_volume,
                    title={"text": "Total Volume (L)"},
                    gauge={"axis": {"range": [0, max(10, st.session_state.total_volume + 1)]}}
                )),
                use_container_width=True,
            )

        # ---------------- GRAPH ----------------
        with st.expander("📈 Live Graph", expanded=True):
            fig = px.line(
                st.session_state.history,
                x="Elapsed_Time_sec",
                y=["RPM", "FlowRate"],
                title="RPM & Flow Rate vs Time",
            )
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("❌ Firebase fetch failed")

except Exception as e:
    st.error(f"⚠️ Error: {e}")

# ------------------------------
# AUTO DOWNLOAD ON STOP
# ------------------------------
if stop_clicked and not st.session_state.history.empty:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        st.session_state.history.to_excel(
            writer, index=False, sheet_name="CapturedData"
        )
    output.seek(0)

    st.download_button(
        label="⬇️ Download Captured Data",
        data=output,
        file_name="washing_machine_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
