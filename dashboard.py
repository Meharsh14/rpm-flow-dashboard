import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import json, os, time

# --- Firebase Initialization ---
def init_firebase():
    if not firebase_admin._apps:
        cred = None
        db_url = "https://rpm-flow-dashboard-default-rtdb.firebaseio.com"

        if "FIREBASE_SERVICE_ACCOUNT" in st.secrets:
            st.write("🔐 Loading Firebase credentials from Streamlit secrets...")
            firebase_config = json.loads(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
            cred = credentials.Certificate(firebase_config)

        elif os.path.exists("serviceAccountKey.json"):
            st.write("📁 Loading Firebase credentials from local file...")
            cred = credentials.Certificate("serviceAccountKey.json")

        elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            st.write("🌍 Loading Firebase credentials from environment variable...")
            cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

        else:
            st.error("❌ No Firebase credentials found. Upload `serviceAccountKey.json` or add secrets.")
            st.stop()

        firebase_admin.initialize_app(cred, {"databaseURL": db_url})
        st.success("✅ Connected to Firebase Realtime Database!")

# --- Initialize Firebase ---
init_firebase()

# --- Streamlit UI ---
st.title("📊 RPM & Flow Rate Dashboard")
st.write("Fetching live data from Firebase Realtime Database...")

rpm_placeholder = st.empty()
flow_placeholder = st.empty()
volume_placeholder = st.empty()

# --- Live update loop ---
total_volume = 0
prev_time = time.time()

while True:
    try:
        ref = db.reference("sensorData")
        data = ref.get()

        if data:
            rpm = data.get("RPM", 0)
            flow = data.get("FlowRate", 0)

            # Calculate water volume (approximate)
            current_time = time.time()
            elapsed = current_time - prev_time
            total_volume += (flow / 60) * elapsed  # convert L/min to L/s
            prev_time = current_time

            rpm_placeholder.metric("Current RPM", f"{rpm} RPM")
            flow_placeholder.metric("Flow Rate", f"{flow:.2f} L/min")
            volume_placeholder.metric("Total Volume", f"{total_volume:.2f} L")

        time.sleep(2)

    except Exception as e:
        st.error(f"Error fetching data: {e}")
        time.sleep(5)

