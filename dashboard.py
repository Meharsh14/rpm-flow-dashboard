import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="RPM & Flow Dashboard", layout="wide")

st.title("🌀 Real-Time RPM & Flow Dashboard")

FIREBASE_URL = "https://your-project-id.firebaseio.com/machine_data.json"

placeholder = st.empty()
data_log = []

start = st.button("▶️ Start Simulation")
stop = st.button("⏹️ Stop Simulation")

running = False

if start:
    running = True

if stop:
    running = False

while running:
    try:
        response = requests.get(FIREBASE_URL)
        if response.status_code == 200:
            data = response.json()
            rpm = data.get("rpm", 0)
            flow = data.get("flow", 0.0)
            timestamp = datetime.now().strftime("%H:%M:%S")
            data_log.append({"Time": timestamp, "RPM": rpm, "Flow": flow})

            df = pd.DataFrame(data_log)
            placeholder.line_chart(df.set_index("Time"))

            st.metric("RPM", rpm)
            st.metric("Flow (L/min)", flow)

            time.sleep(2)
        else:
            st.error("Error fetching data from Firebase")
    except Exception as e:
        st.error(f"Exception: {e}")
        time.sleep(2)
