import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import json, os, time
from streamlit_autorefresh import st_autorefresh  # new library for auto-refresh

# --- Firebase Initialization ---
@st.cache_resource
def init_firebase():
    db_url = "https://rpm-flow-dashboard-default-rtdb.firebaseio.com/"
    cred = None

    if "FIREBASE_SERVICE_ACCOUNT" in st.secrets:
        firebase_config = json.loads(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
        cred = credentials.Certificate(firebase_config)
    elif os.path.exists("serviceAccountKey.json"):
        cred = credentials.Certificate("serviceAccountKey.json")
    elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
    else:
        st.error("❌ No Firebase credentials found.")
        st.stop()

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {"databaseURL": db_url})

    return db

# --- Initialize Firebase ---
db = init_firebase()

# --- Streamlit UI ---
st.title("📊 RPM & Flow Rate Dashboard")
st.caption("Live data fetched from Firebase Realtime Database")

# --- Auto-refresh every 2 seconds ---
st_autorefresh(interval=2000, key="data_refresh")  # refresh dashboard every 2 sec

# --- Display placeholders ---
rpm_placeholder = st.empty()
flow_placeholder = st.empty()
volume_placeholder = st.empty()

# --- Session state for volume tracking ---
if "total_volume" not in st.session_state:
    st.session_state.total_volume = 0.0
    st.session_state.prev_time = time.time()

# --- Fetch data from Firebase ---
try:
    ref = db.reference("sensorData")
    data = ref.get()

    if data:
        rpm = data.get("RPM", 0)
        flow = data.get("FlowRate", 0)

        # Calculate total volume
        current_time = time.time()
        elapsed = current_time - st.session_state.prev_time
        st.session_state.total_volume += (flow / 60) * elapsed  # L/min → L/s
        st.session_state.prev_time = current_time

        rpm_placeholder.metric("Current RPM", f"{rpm} RPM")
        flow_placeholder.metric("Flow Rate", f"{flow:.2f} L/min")
        volume_placeholder.metric("Total Volume", f"{st.session_state.total_volume:.2f} L")
    else:
        st.warning("No data received yet from ESP32.")

except Exception as e:
    st.error(f"Error fetching data: {e}")
