# dashboard.py
import os
import json
from pathlib import Path

import streamlit as st

# Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, firestore

st.set_page_config(page_title="RPM & Flow Dashboard", layout="wide")


def load_firebase_credentials():
    """
    Resolve Firebase credentials in the following order:
      1) GOOGLE_APPLICATION_CREDENTIALS env var (path to JSON)
      2) local file serviceAccountKey.json next to this script
      3) Streamlit secrets: st.secrets["FIREBASE_SERVICE_ACCOUNT"] or st.secrets["firebase"]
      4) Environment variable FIREBASE_SERVICE_ACCOUNT (JSON string)
    Returns: firebase_admin.credentials.Certificate(...) or raises FileNotFoundError/ValueError
    """
    base = Path(__file__).resolve().parent

    # 1) GOOGLE_APPLICATION_CREDENTIALS path
    gac = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if gac:
        p = Path(gac)
        if p.exists():
            return credentials.Certificate(str(p))

    # 2) local file serviceAccountKey.json (project root)
    local = base / "serviceAccountKey.json"
    if local.exists():
        return credentials.Certificate(str(local))

    # 3) Streamlit secrets (preferred for Streamlit Cloud)
    try:
        # st.secrets may be a dict or have nested structure
        sa = st.secrets.get("FIREBASE_SERVICE_ACCOUNT") if isinstance(st.secrets, dict) else None
        if not sa:
            # Check common alternative key
            sa = st.secrets.get("firebase") if isinstance(st.secrets, dict) else None
    except Exception:
        sa = None

    if sa:
        # st.secrets may already be a dict (if you added keys individually) or a JSON string
        if isinstance(sa, dict):
            return credentials.Certificate(sa)
        else:
            # parse JSON string
            try:
                cfg = json.loads(sa)
                return credentials.Certificate(cfg)
            except json.JSONDecodeError as ex:
                raise ValueError(f"Could not parse JSON from st.secrets['FIREBASE_SERVICE_ACCOUNT']: {ex}")

    # 4) Environment variable with JSON string
    env_sa = os.environ.get("FIREBASE_SERVICE_ACCOUNT") or os.environ.get("FIREBASE")
    if env_sa:
        try:
            cfg = json.loads(env_sa)
            return credentials.Certificate(cfg)
        except json.JSONDecodeError as ex:
            raise ValueError(f"Could not parse JSON from FIREBASE_SERVICE_ACCOUNT env var: {ex}")

    # Nothing found
    raise FileNotFoundError(
        "No Firebase credentials found. Provide one of:\n"
        " - set GOOGLE_APPLICATION_CREDENTIALS to the path of serviceAccountKey.json,\n"
        " - place serviceAccountKey.json next to dashboard.py,\n"
        " - add FIREBASE_SERVICE_ACCOUNT (full JSON) to Streamlit secrets or env var."
    )


def init_firebase():
    """Initialize Firebase Admin SDK if not already initialized."""
    try:
        # If already initialized, get_app() will succeed
        firebase_admin.get_app()
        return True
    except ValueError:
        # not initialized yet -> load creds and initialize
        cred = load_firebase_credentials()
        firebase_admin.initialize_app(cred)
        return True


# Try to initialize Firebase and create a Firestore client
db = None
try:
    init_firebase()
    db = firestore.client()
    st.success("✅ Firebase initialized.")
except Exception as e:
    st.error(f"Firebase initialization failed: {e}")

# --- Simple demo UI to test Firestore reads/writes ---
st.title("RPM & Flow Dashboard — Firebase test")

st.markdown(
    """
This example demonstrates safe Firebase Admin initialization.
Use the buttons below to test writing/reading a small document to Firestore (collection: `rpm_flow_demo`).
"""
)

if db:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Write test document to Firestore"):
            try:
                doc_ref = db.collection("rpm_flow_demo").document()
                doc_ref.set({
                    "rpm": 1200,
                    "flow_lpm": 3.5,
                    "note": "test write from Streamlit",
                })
                st.success("Wrote test document to collection 'rpm_flow_demo'.")
            except Exception as ex:
                st.error(f"Write failed: {ex}")

    with col2:
        if st.button("Read last 5 docs (ordered by rpm desc)"):
            try:
                query = db.collection("rpm_flow_demo").order_by("rpm", direction=firestore.Query.DESCENDING).limit(5)
                docs = query.stream()
                rows = []
                for d in docs:
                    item = d.to_dict()
                    item["_id"] = d.id
                    rows.append(item)
                if rows:
                    st.table(rows)
                else:
                    st.info("No documents found.")
            except Exception as ex:
                st.error(f"Read failed: {ex}")
else:
    st.info("Firestore client is not available. Follow the setup steps below to add credentials.")
