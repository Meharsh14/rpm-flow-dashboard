import streamlit as st
import paho.mqtt.client as mqtt
import json

st.set_page_config(page_title="ESP32 Live Dashboard", layout="wide")
st.title("📊 ESP32 Live Data Dashboard")

# Display placeholders
rpm_display = st.empty()
flow_display = st.empty()

# MQTT Broker & Topic
broker = "broker.hivemq.com"
topic = "esp32/demo/data"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker")
        client.subscribe(topic)
    else:
        print("❌ Failed to connect, return code %d\n", rc)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        rpm_display.metric("RPM", data["rpm"])
        flow_display.metric("Flow Rate", f"{data['flow']} L/min")
    except:
        pass

# Setup MQTT Client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker, 1883, 60)
client.loop_start()
