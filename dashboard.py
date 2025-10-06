import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import time
import json

# =========================
# 🔧 Replace with your Firebase details
# =========================
database_url = "https://rpm-flow-dashboard-default-rtdb.firebaseio.com/"

# 🎯 FIX: Use st.secrets to securely load credentials (removes the FileNotFoundError)
# The st.secrets["firebase"] dictionary contains all the key-value pairs
# from your service account JSON file (stored in secrets.toml or Streamlit Cloud Secrets).
try:
    # credentials.Certificate can accept a dict containing the service account info
    cred = credentials.Certificate(st.secrets["firebase"])
except FileNotFoundError:
    # This block is unlikely to run if secrets are set up, but is good practice
    st.error("Credential file 'serviceAccountKey.json' not found. Please ensure it is in the correct path or use Streamlit secrets.")
    st.stop()
except KeyError:
    st.error("Firebase secrets not found! Please configure your credentials in `secrets.toml` or Streamlit Cloud secrets under the key `firebase`.")
    st.stop()


# Initialize Firebase App
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {"databaseURL": database_url})

# --- Streamlit Dashboard Layout ---

st.set_page_config(page_title="ESP32 RPM & Flow Dashboard", layout="centered")

st.title("🌀 ESP32 RPM & Flow Rate Dashboard")

# Create placeholders for metrics to update them dynamically
rpm_placeholder = st.empty()
flow_placeholder = st.empty()

st.markdown("---")

st.info("Fetching live data from Firebase...")

# Main update loop
while True:
    try:
        # Fetch data from the Realtime Database
        rpm = db.reference("/sensorData/RPM").get()
        flow = db.reference("/sensorData/FlowRate").get()

        # Update the metrics using the placeholders
        rpm_placeholder.metric("RPM", f"{rpm:.0f}" if isinstance(rpm, (int, float)) else "N/A")
        flow_placeholder.metric("Flow Rate (L/min)", f"{flow:.2f}" if isinstance(flow, (int, float)) else "N/A")

    except Exception as e:
        # Handle cases where data retrieval fails
        st.warning(f"Error fetching data: {e}")
        rpm_placeholder.metric("RPM", "ERROR")
        flow_placeholder.metric("Flow Rate (L/min)", "ERROR")

    # Wait for 2 seconds before the next update
    time.sleep(2)
