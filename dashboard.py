import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import json, os, time, io
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# ------------------------------
# Firebase Initialization
# ------------------------------
@st.cache_resource
def init_firebase():
    db_url = "https://rpm-flow-dashboard-default-rtdb.firebaseio.com/"
    cred = None

    # --- Streamlit secrets (for Streamlit Cloud) ---
    if "FIREBASE_SERVICE_ACCOUNT" in st.secrets:
        firebase_config = json.loads(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
        cred = credentials.Certificate(firebase_config)

    # --- Local JSON file (for local testing) ---
    elif os.path.exists("serviceAccountKey.json"):
        cred = credentials.Certificate("serviceAccountKey.json")

    elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

    else:
        st.error("❌ No Firebase credentials found. Upload `serviceAccountKey.json` or add secrets.")
        st.stop()

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {"databaseURL": db_url})

    return db


# ------------------------------
# Initialize Firebase
# ------------------------------
db = init_firebase()

# ------------------------------
# Streamlit UI Setup
# ------------------------------
st.set_page_config(page_title="RPM & Flow Dashboard", layout="wide")
st.title("📊 RPM & Flow Rate Dashboard")
st.caption("Live data fetched from Firebase Realtime Database")

# ------------------------------
# Session State
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
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            st.session_state.history.to_excel(writer, index=False, sheet_name="SensorData")
        output.seek(0)

        st.download_button(
            label="💾 Download Excel File",
            data=output,
            file_name="sensor_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# ------------------------------
# Auto-refresh every 2 seconds (no scroll jump)
# ------------------------------
st_autorefresh(interval=2000, key="data_refresh")

# ------------------------------
# Fetch & Display Live Data
# ------------------------------
try:
    if st.session_state.running:
        ref = db.reference("sensorData")
        data = ref.get()

        if data:
            rpm = data.get("RPM", 0)
            flow = data.get("FlowRate", 0)

            # --- Volume calculation (L/min -> L/s) ---
            current_time = time.time()
            elapsed = current_time - st.session_state.prev_time
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

            if len(st.session_state.history) > 200:
                st.session_state.history = st.session_state.history.tail(200)

            # ------------------------------
            # Display Gauges
            # ------------------------------
            c1, c2, c3 = st.columns(3)

            with c1:
                fig_rpm = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=rpm,
                    title={"text": "RPM"},
                    gauge={"axis": {"range": [0, 2000]}, "bar": {"color": "blue"}},
                ))
                st.plotly_chart(fig_rpm, use_container_width=True)

            with c2:
                fig_flow = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=flow,
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
            st.warning("No data received yet from ESP32.")

except Exception as e:
    st.error(f"Error fetching data: {e}")
