import streamlit as st
import requests
import time, io, re
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# ------------------------------
# Firebase Realtime Database URLs (UPDATED)
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
# Utility Function
# ------------------------------
def safe_float(value):
    """Convert mixed data (string/int/float) safely to float."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"[-+]?\d*\.?\d+", value)
        return float(match.group()) if match else 0.0
    return 0.0

# ------------------------------
# Session State Initialization
# ------------------------------
if "total_volume" not in st.session_state:
    st.session_state.total_volume = 0.0
    st.session_state.prev_time = time.time()

if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(
        columns=["Time", "RPM", "FlowRate", "TotalVolume"]
    )

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
            st.session_state.history.to_excel(
                writer, index=False, sheet_name="SensorData"
            )
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
    rpm_resp = requests.get(URL_RPM, timeout=5)
    flow_resp = requests.get(URL_FLOW, timeout=5)
    vol_resp = requests.get(URL_VOLUME, timeout=5)

    if all(r.status_code == 200 for r in [rpm_resp, flow_resp, vol_resp]):
        rpm = safe_float(rpm_resp.json())
        flow = safe_float(flow_resp.json())
        firebase_volume = safe_float(vol_resp.json())

        # --- Volume calculation ---
        current_time = time.time()
        elapsed = current_time - st.session_state.prev_time

        if st.session_state.running:
            st.session_state.total_volume += (flow / 60) * elapsed

        st.session_state.prev_time = current_time

        # --- Append history ---
        new_row = {
            "Time": pd.Timestamp.now(),
            "RPM": rpm,
            "FlowRate": flow,
            "TotalVolume": st.session_state.total_volume,
        }

        st.session_state.history = pd.concat(
            [st.session_state.history, pd.DataFrame([new_row])],
            ignore_index=True,
        )

        if len(st.session_state.history) > 500:
            st.session_state.history = st.session_state.history.tail(500)

        # ------------------------------
        # Gauges
        # ------------------------------
        c1, c2, c3 = st.columns(3)

        with c1:
            st.plotly_chart(
                go.Figure(
                    go.Indicator(
                        mode="gauge+number",
                        value=rpm,
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
                        value=flow,
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
                        value=st.session_state.total_volume,
                        title={"text": "Total Volume (L)"},
                        gauge={
                            "axis": {
                                "range": [
                                    0,
                                    max(10, st.session_state.total_volume + 1),
                                ]
                            }
                        },
                    )
                ),
                use_container_width=True,
            )

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
        st.error("❌ Firebase fetch failed — check DB rules or URL")

except Exception as e:
    st.error(f"⚠️ Error fetching data: {e}")
