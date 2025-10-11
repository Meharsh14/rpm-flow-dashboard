import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
from firebase_admin import credentials, initialize_app, db
import io
from datetime import datetime

# --- Firebase Configuration ---
if not st.session_state.get("firebase_initialized", False):
    cred = credentials.Certificate("serviceAccountKey.json")
    initialize_app(cred, {"databaseURL": "https://your-database-url.firebaseio.com/"})
    st.session_state.firebase_initialized = True

# --- Streamlit Page Config ---
st.set_page_config(page_title="RPM & Flow Dashboard", layout="wide")
st.title("🔄 Real-Time RPM & Flow Monitoring Dashboard")

# --- Initialize session states ---
if "running" not in st.session_state:
    st.session_state.running = False
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Timestamp", "RPM", "FlowRate", "Volume"])

# --- Control Buttons ---
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("▶️ Start"):
        st.session_state.running = True
with col2:
    if st.button("⏹ Stop"):
        st.session_state.running = False
with col3:
    if st.button("📥 Download Excel"):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            st.session_state.data.to_excel(writer, index=False, sheet_name="SensorData")
        st.download_button(
            label="Click to Download Excel File",
            data=output.getvalue(),
            file_name=f"sensor_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

st.divider()

# --- Layout for Gauges and Graphs ---
g1, g2, g3 = st.columns(3)

# --- Main Data Loop ---
placeholder = st.empty()

while st.session_state.running:
    try:
        ref = db.reference("sensorData")
        data = ref.get()
        if data:
            rpm = float(data.get("rpm", 0))
            flow = float(data.get("flowRate", 0))
            volume = float(data.get("volume", 0))
            timestamp = datetime.now().strftime("%H:%M:%S")

            new_row = pd.DataFrame([[timestamp, rpm, flow, volume]], columns=["Timestamp", "RPM", "FlowRate", "Volume"])
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)

            # --- Speedometers ---
            with g1:
                fig_rpm = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=rpm,
                    title={'text': "RPM"},
                    gauge={'axis': {'range': [0, 2000]}}
                ))
                st.plotly_chart(fig_rpm, use_container_width=True)

            with g2:
                fig_flow = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=flow,
                    title={'text': "Flow Rate (L/min)"},
                    gauge={'axis': {'range': [0, 30]}}
                ))
                st.plotly_chart(fig_flow, use_container_width=True)

            with g3:
                fig_vol = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=volume,
                    title={'text': "Volume (L)"},
                    gauge={'axis': {'range': [0, 100]}}
                ))
                st.plotly_chart(fig_vol, use_container_width=True)

            # --- Line Graphs ---
            with placeholder.container():
                st.subheader("📈 Live Graphs")
                col_graph1, col_graph2 = st.columns(2)

                with col_graph1:
                    st.line_chart(st.session_state.data[["Timestamp", "RPM"]].set_index("Timestamp"))
                with col_graph2:
                    st.line_chart(st.session_state.data[["Timestamp", "FlowRate"]].set_index("Timestamp"))

                st.metric("💧 Total Volume", f"{volume:.2f} L")

        time.sleep(2)  # Refresh interval

    except Exception as e:
        st.error(f"Error fetching data: {e}")
        time.sleep(5)

# --- When stopped, show final graph ---
if not st.session_state.running and not st.session_state.data.empty:
    st.subheader("📊 Final Data Overview")
    st.line_chart(st.session_state.data.set_index("Timestamp"))
