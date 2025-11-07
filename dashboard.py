import streamlit as st
import requests
import time, io
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# ------------------------------
# Firebase Realtime Database URLs
# ------------------------------
BASE_URL = "https://rpm-flow-dashboard-default-rtdb.firebaseio.com/WashingMachine"
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
# Session State Initialization
# ------------------------------
if "total_volume" not in st.session_state:
    st.session_state.total_volume = 0.0
    st.session_state.prev_time = time.time()

if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["Time", "RPM", "FlowRate", "TotalVolume"])

if "running" not in st.session_state:
    st.session_state.running = True

# ------------------------------
# Control Buttons
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
            st.session_state.history.to_excel(writer, index=False, sheet_name="SensorData")
        output.seek(0)

        st.download_button(
            label="💾 Download Excel File",
            data=output,
            file_name="washing_machine_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# ------------------------------
# Auto-refresh every 1.5 seconds
# ------------------------------
st_autorefresh(interval=1500, key="data_refresh")

# ------------------------------
# Fetch & Display Live Data
# ------------------------------
try:
    # Always fetch Firebase data, even when stopped
    rpm_resp = requests.get(URL_RPM)
    flow_resp = requests.get(URL_FLOW)
    vol_resp = requests.get(URL_VOLUME)

    if all(r.status_code == 200 for r in [rpm_resp, flow_resp, vol_resp]):
        rpm = rpm_resp.json() or 0
        flow = flow_resp.json() or 0
        total_volume = vol_resp.json() or 0

        # If running, compute new total volume
        if st.session_state.running:
            current_time = time.time()
            elapsed = current_time - st.session_state.prev_time
            st.session_state.total_volume += (float(flow) / 60) * elapsed
            st.session_state.prev_time = current_time
        else:
            # When stopped, just freeze total volume
            current_time = time.time()
            st.session_state.prev_time = current_time

        # --- Append to history (even if stopped) ---
        new_row = {
            "Time": pd.Timestamp.now(),
            "RPM": float(rpm),
            "FlowRate": float(flow),
            "TotalVolume": st.session_state.total_volume,
        }
        st.session_state.history = pd.concat(
            [st.session_state.history, pd.DataFrame([new_row])],
            ignore_index=True,
        )

        # Keep only last 500 records for performance
        if len(st.session_state.history) > 500:
            st.session_state.history = st.session_state.history.tail(500)

        # ------------------------------
        # Display Gauges
        # ------------------------------
        c1, c2, c3 = st.columns(3)

        with c1:
            fig_rpm = go.Figure(go.Indicator(
                mode="gauge+number",
                value=float(rpm),
                title={"text": "RPM"},
                gauge={"axis": {"range": [0, 2000]}, "bar": {"color": "blue"}},
            ))
            st.plotly_chart(fig_rpm, use_container_width=True)

        with c2:
            fig_flow = go.Figure(go.Indicator(
                mode="gauge+number",
                value=float(flow),
                title={"text": "Flow Rate (L/min)"},
                gauge={"axis": {"range": [0, 20]}, "bar": {"color": "green"}},
            ))
            st.plotly_chart(fig_flow, use_container_width=True)

        with c3:
            fig_vol = go.Figure(go.Indicator(
                mode="gauge+number",
                value=st.session_state.total_volume,
                title={"text": "Total Volume (L)"},
                gauge={"axis": {"range": [0, max(10, st.session_state.total_volume + 1)]},
                       "bar": {"color": "orange"}},
            ))
            st.plotly_chart(fig_vol, use_container_width=True)

        # ------------------------------
        # Line Chart
        # ------------------------------
        with st.expander("📈 Live Graph", expanded=True):
            fig = px.line(
                st.session_state.history,
                x="Time",
                y=["RPM", "FlowRate"],
                labels={"value": "Value", "variable": "Parameter"},
                title="Live RPM & Flow Rate",
            )
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("❌ Firebase data fetch failed — check database URL or network.")

except Exception as e:
    st.error(f"⚠️ Error fetching data: {e}")
