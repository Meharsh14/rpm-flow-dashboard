import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import json, os, time
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
import io

# ------------------------------
# Firebase Initialization
# ------------------------------
@st.cache_resource
def init_firebase():
    db_url = "https://rpm-flow-dashboard-default-rtdb.firebaseio.com/"
    cred = None

    # Streamlit secrets (cloud)
    if "FIREBASE_SERVICE_ACCOUNT" in st.secrets:
        firebase_config = json.loads(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
        cred = credentials.Certificate(firebase_config)
    # Local JSON file
    elif os.path.exists("serviceAccountKey.json"):
        cred = credentials.Certificate("serviceAccountKey.json")
    # Environment variable
    elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
    else:
        st.error("❌ No Firebase credentials found. Upload `serviceAccountKey.json` or set secrets.")
        st.stop()

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {"databaseURL": db_url})

    return db

# ------------------------------
# Initialize Firebase
# ------------------------------
db = init_firebase()

# ------------------------------
# Streamlit UI
# ------------------------------
st.title("📊 RPM & Flow Rate Dashboard")
st.caption("Live data fetched from Firebase Realtime Database")

# ------------------------------
# Session state initialization
# ------------------------------
if "total_volume" not in st.session_state:
    st.session_state.total_volume = 0.0
    st.session_state.prev_time = time.time()

if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["Time", "RPM", "FlowRate", "TotalVolume"])

if "running" not in st.session_state:
    st.session_state.running = True

# ------------------------------
# Control buttons
# ------------------------------
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("▶️ Start"):
        st.session_state.running = True
with col2:
    if st.button("⏹ Stop"):
        st.session_state.running = False
with col3:
    # Download Excel button
    if st.button("💾 Download Excel"):
        # Create in-memory Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            st.session_state.history.to_excel(writer, index=False, sheet_name="SensorData")
            writer.save()
        output.seek(0)
        st.download_button(
            label="Download Data",
            data=output,
            file_name="sensor_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ------------------------------
# Placeholders for metrics
# ------------------------------
rpm_placeholder = st.empty()
flow_placeholder = st.empty()
volume_placeholder = st.empty()

# ------------------------------
# Expander for chart
# ------------------------------
with st.expander("📈 Live Chart", expanded=True):
    chart_placeholder = st.empty()

# ------------------------------
# Auto-refresh every 2 seconds
# ------------------------------
st_autorefresh(interval=2000, key="datarefresh")

# ------------------------------
# Fetch & display data
# ------------------------------
try:
    if st.session_state.running:
        ref = db.reference("sensorData")
        data = ref.get()

        if data:
            rpm = data.get("RPM", 0)
            flow = data.get("FlowRate", 0)

            # Calculate total volume
            current_time = time.time()
            elapsed = current_time - st.session_state.prev_time
            st.session_state.total_volume += (flow / 60) * elapsed  # L/min -> L/s
            st.session_state.prev_time = current_time

            # Update metrics
            rpm_placeholder.metric("Current RPM", f"{rpm} RPM")
            flow_placeholder.metric("Flow Rate", f"{flow:.2f} L/min")
            volume_placeholder.metric("Total Volume", f"{st.session_state.total_volume:.2f} L")

            # Append to history
            st.session_state.history = pd.concat([
                st.session_state.history,
                pd.DataFrame([{
                    "Time": pd.Timestamp.now(),
                    "RPM": rpm,
                    "FlowRate": flow,
                    "TotalVolume": st.session_state.total_volume
                }])
            ], ignore_index=True)

            # Update chart
            fig = px.line(
                st.session_state.history,
                x="Time",
                y=["RPM", "FlowRate"],
                labels={"value": "Value", "variable": "Parameter"},
                title="Live RPM & Flow Rate"
            )
            chart_placeholder.plotly_chart(fig, use_container_width=True)

        else:
            st.warning("No data received yet from ESP32.")

except Exception as e:
    st.error(f"Error fetching data: {e}")
