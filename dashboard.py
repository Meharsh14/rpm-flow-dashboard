import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import time

# =========================
# 🔧 Replace with your Firebase details
# =========================
database_url = "https://rpm-flow-dashboard-default-rtdb.firebaseio.com/"
cred = credentials.Certificate("serviceAccountKey.json")  # Download JSON key from Firebase Console
firebase_admin.initialize_app(cred, {"databaseURL": database_url})

st.set_page_config(page_title="ESP32 RPM & Flow Dashboard", layout="centered")

st.title("🌀 ESP32 RPM & Flow Rate Dashboard")

rpm_placeholder = st.empty()
flow_placeholder = st.empty()

st.markdown("---")

st.info("Fetching live data from Firebase...")

while True:
    rpm = db.reference("/sensorData/RPM").get()
    flow = db.reference("/sensorData/FlowRate").get()

    rpm_placeholder.metric("RPM", rpm)
    flow_placeholder.metric("Flow Rate (L/min)", flow)

    time.sleep(2)
