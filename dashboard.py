import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="RPM & Flow Dashboard", layout="wide")

if "run" not in st.session_state:
    st.session_state.run = False
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Timestamp", "RPM", "Flow"])

st.title("⚙️ RPM & Flow Dashboard")

col1, col2 = st.columns(2)
col1.button("▶️ Start Stream", on_click=lambda: st.session_state.update(run=True))
col2.button("⏹️ Stop Stream", on_click=lambda: st.session_state.update(run=False))

chart_container = st.empty()
metric_container = st.empty()

def fetch_data():
    try:
        resp = requests.get("http://10.217.118.7:8502/get_rpm_flow")  # Flask server IP
        if resp.status_code == 200:
            df = pd.DataFrame(resp.json())
            return df
    except:
        return pd.DataFrame(columns=["Timestamp", "RPM", "Flow"])
    return pd.DataFrame(columns=["Timestamp", "RPM", "Flow"])

while st.session_state.run:
    df = fetch_data()
    if not df.empty:
        st.session_state.data = df
        latest = df.iloc[-1]

        with metric_container.container():
            c1, c2 = st.columns(2)
            c1.metric("🔄 RPM", latest["RPM"])
            c2.metric("💧 Flow (L/min)", latest["Flow"])

        chart_container.line_chart(df.set_index("Timestamp")[["RPM", "Flow"]])
    time.sleep(1)
