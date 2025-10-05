import streamlit as st
import pandas as pd
import requests
import time
from io import BytesIO

st.set_page_config(page_title="RPM & Flow Dashboard", layout="wide")

if "run" not in st.session_state:
    st.session_state.run = False
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Timestamp","RPM","Flow","Volume"])

st.title("⚙️ RPM, Flow & Volume Dashboard")

col1, col2 = st.columns(2)
col1.button("▶️ Start Stream", on_click=lambda: st.session_state.update(run=True))
col2.button("⏹️ Stop Stream", on_click=lambda: st.session_state.update(run=False))

metric_container = st.empty()
chart_container = st.empty()

def fetch_data():
    try:
        resp = requests.get("http://10.217.118.7:8502/get_rpm_flow")
        if resp.status_code == 200:
            return pd.DataFrame(resp.json())
    except:
        return pd.DataFrame(columns=["Timestamp","RPM","Flow","Volume"])
    return pd.DataFrame(columns=["Timestamp","RPM","Flow","Volume"])

while st.session_state.run:
    df = fetch_data()
    if not df.empty:
        st.session_state.data = df
        latest = df.iloc[-1]

        with metric_container.container():
            c1,c2,c3 = st.columns(3)
            c1.metric("🔄 RPM", latest["RPM"])
            c2.metric("💧 Flow (L/min)", latest["Flow"])
            c3.metric("🧪 Volume (L)", round(latest["Volume"],2))

        chart_container.line_chart(df.set_index("Timestamp")[["RPM","Flow","Volume"]])
    time.sleep(1)

# Download Excel after stop
if not st.session_state.run and not st.session_state.data.empty:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        st.session_state.data.to_excel(writer, index=False, sheet_name="Data")
    st.download_button(
        label="📥 Download Excel",
        data=buffer,
        file_name="rpm_flow_volume.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
