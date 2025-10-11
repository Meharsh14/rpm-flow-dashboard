import streamlit as st
import pandas as pd
import random
import time
from io import BytesIO
import plotly.graph_objects as go

# --- Streamlit Page Setup ---
st.set_page_config(page_title="RPM & Flow Meter Dashboard", layout="wide")

st.title("🌀 Real-Time RPM & Flow Rate Dashboard")

# --- Initialize Session State ---
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Timestamp", "RPM", "Flow Rate (L/min)", "Volume (L)"])
if "total_volume" not in st.session_state:
    st.session_state.total_volume = 0
if "running" not in st.session_state:
    st.session_state.running = False

# --- Function to Generate Random Data ---
def generate_data():
    rpm = random.randint(400, 1200)
    flow_rate = round(random.uniform(1.0, 10.0), 2)
    volume_increment = flow_rate / 30  # simulate per 2-second update
    st.session_state.total_volume += volume_increment
    return rpm, flow_rate, st.session_state.total_volume

# --- Control Buttons ---
col_btn1, col_btn2, col_btn3 = st.columns(3)
with col_btn1:
    if st.button("▶️ Start"):
        st.session_state.running = True
with col_btn2:
    if st.button("⏸️ Stop"):
        st.session_state.running = False
with col_btn3:
    st.write("")  # spacing

# --- Only Update if Running ---
if st.session_state.running:
    rpm, flow_rate, total_volume = generate_data()

    new_row = pd.DataFrame(
        [[time.strftime("%H:%M:%S"), rpm, flow_rate, round(total_volume, 2)]],
        columns=["Timestamp", "RPM", "Flow Rate (L/min)", "Volume (L)"]
    )
    st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
    time.sleep(2)
    st.rerun()
else:
    # Display last values if available
    if not st.session_state.data.empty:
        last_row = st.session_state.data.iloc[-1]
        rpm = last_row["RPM"]
        flow_rate = last_row["Flow Rate (L/min)"]
        total_volume = last_row["Volume (L)"]
    else:
        rpm, flow_rate, total_volume = 0, 0, 0

# --- Gauges Layout ---
col1, col2, col3 = st.columns(3)

with col1:
    fig_rpm = go.Figure(go.Indicator(
        mode="gauge+number",
        value=rpm,
        title={'text': "RPM"},
        gauge={'axis': {'range': [0, 1500]},
               'bar': {'color': "blue"},
               'steps': [
                   {'range': [0, 800], 'color': "lightgray"},
                   {'range': [800, 1200], 'color': "lightgreen"},
                   {'range': [1200, 1500], 'color': "orange"}]}
    ))
    st.plotly_chart(fig_rpm, use_container_width=True)

with col2:
    fig_flow = go.Figure(go.Indicator(
        mode="gauge+number",
        value=flow_rate,
        title={'text': "Flow Rate (L/min)"},
        gauge={'axis': {'range': [0, 15]},
               'bar': {'color': "green"},
               'steps': [
                   {'range': [0, 5], 'color': "lightgray"},
                   {'range': [5, 10], 'color': "lightblue"},
                   {'range': [10, 15], 'color': "orange"}]}
    ))
    st.plotly_chart(fig_flow, use_container_width=True)

with col3:
    fig_vol = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(total_volume, 2),
        title={'text': "Total Volume (L)"},
        gauge={'axis': {'range': [0, 100]},
               'bar': {'color': "purple"},
               'steps': [
                   {'range': [0, 25], 'color': "lightgray"},
                   {'range': [25, 50], 'color': "lightgreen"},
                   {'range': [50, 100], 'color': "lightblue"}]}
    ))
    st.plotly_chart(fig_vol, use_container_width=True)

# --- Graph Section ---
st.subheader("📈 Live RPM & Flow Rate Graph")
if not st.session_state.data.empty:
    chart_data = st.session_state.data.set_index("Timestamp")
    st.line_chart(chart_data[["RPM", "Flow Rate (L/min)"]])

# --- Display Total Volume ---
st.metric("💧 Total Volume (L)", round(total_volume, 2))

# --- Download Excel ---
excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
    st.session_state.data.to_excel(writer, index=False, sheet_name="Sensor Data")

excel_data = excel_buffer.getvalue()

st.download_button(
    label="📥 Download Data as Excel",
    data=excel_data,
    file_name="rpm_flow_data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
