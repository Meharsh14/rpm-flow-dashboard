import streamlit as st
import pandas as pd
from flask import Flask, request
import threading
from io import BytesIO
import matplotlib.pyplot as plt
import time

st.set_page_config(page_title="RPM & Flow Dashboard", layout="wide")

# --- Shared Data ---
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Timestamp", "RPM", "Flow", "Volume"])
if "run" not in st.session_state:
    st.session_state.run = False

# --- Flask App ---
app = Flask(__name__)

@app.route("/update_rpm_flow", methods=["POST"])
def update_rpm_flow():
    try:
        data_str = request.form.get("data", "0,0,0")
        parts = data_str.split(",")
        rpm = int(parts[0])
        flow = float(parts[1])
        volume = float(parts[2])
        new_row = {"Timestamp": pd.Timestamp.now(), "RPM": rpm, "Flow": flow, "Volume": volume}
        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
        return "OK"
    except Exception as e:
        return f"Error: {e}"

def run_flask():
    app.run(host="0.0.0.0", port=8502, debug=False, use_reloader=False)

# Start Flask in background
if "flask_started" not in st.session_state:
    threading.Thread(target=run_flask, daemon=True).start()
    st.session_state.flask_started = True
    time.sleep(1)

# --- Start / Stop ---
def start_stream():
    st.session_state.run = True
def stop_stream():
    st.session_state.run = False

st.title("⚙️ Real-Time RPM, Flow & Volume Dashboard")
col1, col2 = st.columns(2)
col1.button("▶️ Start Stream", on_click=start_stream)
col2.button("⏹️ Stop Stream", on_click=stop_stream)

metric_container = st.empty()
plot_container = st.empty()

# --- Live update ---
while st.session_state.run:
    if not st.session_state.data.empty:
        latest = st.session_state.data.iloc[-1]
        with metric_container.container():
            c1, c2, c3 = st.columns(3)
            c1.metric("🔄 RPM", latest["RPM"])
            c2.metric("💧 Flow (L/min)", latest["Flow"])
            c3.metric("🧪 Total Volume (L)", latest["Volume"])

        with plot_container.container():
            plt.figure(figsize=(8,4))
            plt.plot(st.session_state.data["Timestamp"], st.session_state.data["RPM"], label="RPM")
            plt.plot(st.session_state.data["Timestamp"], st.session_state.data["Flow"], label="Flow")
            plt.plot(st.session_state.data["Timestamp"], st.session_state.data["Volume"], label="Volume")
            plt.xlabel("Time")
            plt.legend()
            st.pyplot(plt)
    time.sleep(0.5)

# --- Download Excel after stop ---
if not st.session_state.run and not st.session_state.data.empty:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        st.session_state.data.to_excel(writer, index=False, sheet_name="RPM_Flow_Volume")
    st.download_button(
        label="📥 Download Excel",
        data=buffer,
        file_name="rpm_flow_volume.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
