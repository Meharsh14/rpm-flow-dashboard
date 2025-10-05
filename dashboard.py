import streamlit as st
import pandas as pd
import time
import requests

# Firebase Realtime Database URL
FIREBASE_URL = "https://console.firebase.google.com/project/rpm-flow-dashboard/database/rpm-flow-dashboard-default-rtdb/data/~2F"

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Timestamp", "RPM", "Flow"])

st.title("RPM & Flow Dashboard (Firebase)")

start = st.button("▶️ Start Simulation")
stop = st.button("⏹ Stop Simulation")

running = True if start else False

while running:
    try:
        rpm = requests.get(FIREBASE_URL + "rpm.json").json()
        flow = requests.get(FIREBASE_URL + "flow.json").json()
        
        new_row = {
            "Timestamp": pd.Timestamp.now(),
            "RPM": rpm,
            "Flow": flow,
        }
        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)

        st.line_chart(st.session_state.data.set_index("Timestamp")[["RPM", "Flow"]].tail(50))
        st.write(st.session_state.data.tail(5))
        
    except Exception as e:
        st.error(f"Error fetching data: {e}")

    time.sleep(1)
    
    if stop:
        running = False
