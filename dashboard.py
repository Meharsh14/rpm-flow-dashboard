import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json, os

# --- Firebase Initialization ---
def init_firebase():
    if not firebase_admin._apps:
        cred = None
        # 1️⃣ Check Streamlit secrets (for Streamlit Cloud)
        if "FIREBASE_SERVICE_ACCOUNT" in st.secrets:
            st.write("🔐 Loading Firebase credentials from Streamlit secrets...")
            firebase_config = json.loads(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
            cred = credentials.Certificate(firebase_config)

        # 2️⃣ Else check local JSON file (for local dev)
        elif os.path.exists("serviceAccountKey.json"):
            st.write("📁 Loading Firebase credentials from local file...")
            cred = credentials.Certificate("serviceAccountKey.json")

        # 3️⃣ Else check environment variable (for servers)
        elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            st.write("🌍 Loading Firebase credentials from environment variable...")
            cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

        else:
            st.error(
                "❌ Firebase initialization failed: No credentials found.\n"
                "Provide one of:\n"
                "- Place `serviceAccountKey.json` next to dashboard.py, OR\n"
                "- Add FIREBASE_SERVICE_ACCOUNT to Streamlit secrets, OR\n"
                "- Set GOOGLE_APPLICATION_CREDENTIALS env var."
            )
            st.stop()

        firebase_admin.initialize_app(cred)
        st.success("✅ Firebase initialized successfully!")

# --- Initialize Firebase ---
init_firebase()

# Example Firestore usage
db = firestore.client()

# Streamlit UI
st.title("RPM & Flow Dashboard")
st.write("Firebase connection is working!")

# Test button
if st.button("Add Test Data to Firestore"):
    db.collection("test_data").add({"status": "ok"})
    st.success("✅ Data written to Firestore successfully!")
