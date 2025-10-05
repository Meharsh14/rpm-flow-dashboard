import streamlit as st
import pandas as pd
import time
from io import BytesIO
from flask import Flask, request, jsonify
from threading import Thread
import requests

# ---------------- Flask Setup ----------------
app = Flask(__name__)
data_store = []  # Store RPM/Flow data

@app.route("/update_rpm_flow", methods=["POST"])
def update():
    data = request.form.get("data")  # Expected format: "RPM,Flow"
    try:
        rpm, flow = map(float, data.split(","))
        data_store.append({"RPM": int(rpm), "Flow": flow})
        return "OK"
    except:
        return "Invalid data", 400

@app.route("/get_rpm_flow", methods=["GET"])
def get_data():
    return jsonify(data_store[-50:])  # Return last 50 readings

def run_flask():
    app.run(host="0.0.0.0", port=8502)

# Start Flask in background thread
flask_thread = Thread(target=run_flask, daemon=True)
flask_thread.start()
time.sleep(1)  # Give Flask time to start

# ---------------- Streamlit Dashboard ----------------
st.set_page_config(page_title="RPM & Flow Meter Dashboard", layout="wide")

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Timestamp", "RPM", "Flow", "Volume"])
if "last_volume" not in st.session_state:
    st.session_state.last_volume = 0.0

st.title("⚙️ RPM, Flow & Volume Dashboard")
status_text = st.empty()
metric_container = st.empty()
chart_container = st.empty()

FLASK_SERVER_URL = "http://10.217.118.7:8502"  # Replace with your PC IP

def fetch_data():
    try:
        response = requests.get(f"{FLASK_SERVER_URL}/get_rpm_flow", timeout=1)
        if response.status_code == 200:
            data_list = response.json()
            # Add only new data
            for entry in data_list[len(st.session_state.data):]:
                rpm = entry.get("RPM", 0)
                flow = entry.get("Flow", 0.0)
                st.session_state.last_volume += (flow / 60.0)  # L/min -> L/sec
                new_row = {
                    "Timestamp": pd.Timestamp.now(),
                    "RPM": rpm,
                    "Flow": flow,
                    "Volume": st.session_state.last_volume,
                }
                st.session_state.data = pd.concat(
                    [st.session_state.data, pd.DataFrame([new_row])], ignore_index=True
                )
            status_text.markdown("✅ Live data fetching successful")
        else:
            status_text.markdown(f"⚠️ HTTP Response code: {response.status_code}")
    except Exception as e:
        status_text.markdown(f"❌ Error fetching data: {e}")

# ---------------- Streamlit Loop ----------------
run_loop = True
while run_loop:
    fetch_data()
    if not st.session_state.data.empty:
        latest = st.session_state.data.iloc[-1]
        with metric_container.container():
            c1, c2, c3 = st.columns(3)
            c1.metric("💧 Flow Rate (L/min)", latest["Flow"])
            c2.metric("🔄 RPM", latest["RPM"])
            c3.metric("🧪 Total Volume (L)", round(latest["Volume"], 2))

        chart_container.line_chart(
            st.session_state.data.set_index("Timestamp")[["RPM", "Flow"]].tail(50)
        )
    time.sleep(1)

# ---------------- Excel Download ----------------
st.markdown("### 📥 Download Recorded Data")
buffer = BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    st.session_state.data.to_excel(writer, index=False, sheet_name="Data")
st.download_button(
    label="Download Excel",
    data=buffer,
    file_name="rpm_flow_volume_data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
