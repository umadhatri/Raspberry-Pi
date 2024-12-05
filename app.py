import streamlit as st
import pandas as pd
import time
import threading
import subprocess
from twilio.rest import Client
import numpy as np

# Twilio credentials
account_sid = "Twilio_account_sid"
auth_token = "auth_token_here"
twilio_phone_number = "twilio_number_here"
recipient_phone_number = "your_number_here"

# Twilio client for sending SMS
def send_sms_alert(message):
    client = Client(account_sid, auth_token)
    client.messages.create(
        body=message,
        from_=twilio_phone_number,
        to=recipient_phone_number,
    )

# Function to load the CSV data
def load_data():
    try:
        data = pd.read_csv('network_log.csv')
        data['Timestamp'] = pd.to_datetime(data['Timestamp'])  # Ensure datetime format
        data['Timestamp'] = data['Timestamp'].dt.strftime('%H:%M:%S')  # Format as HH:MM:SS
        return data
    except FileNotFoundError:
        st.error("The network_log.csv file does not exist!")
        return pd.DataFrame(columns=['Timestamp', 'Download', 'Upload', 'Ping', 'Jitter', 'Packet Loss'])

# Function to run the speed test in the background
def run_speed_test():
    subprocess.Popen(['python', 'network_test.py'])

# Run the speed test in a separate thread
speed_test_thread = threading.Thread(target=run_speed_test)
speed_test_thread.daemon = True  # Allow thread to exit when the main program exits
speed_test_thread.start()

# Streamlit app
st.title("Real-Time Network Speed Monitor with Advanced Metrics")

# Placeholder for the chart
chart_placeholder = st.empty()

# User selection for chart type
chart_type = st.selectbox("Select Chart Type", ["Line", "Bar", "Area"])

# Display summary metrics
st.subheader("Metrics Summary")
average_download = st.empty()
max_download = st.empty()
min_upload = st.empty()

# Advanced metrics placeholders
st.subheader("Advanced Metrics")
avg_latency = st.empty()
avg_jitter = st.empty()
avg_packet_loss = st.empty()
stability_index = st.empty()

# Load initial data to define default values for time input
data = load_data()
if not data.empty:
    data['Timestamp'] = pd.to_datetime(data['Timestamp'], format='%H:%M:%S')
    default_start_time = data['Timestamp'].iloc[0].time()
    default_end_time = data['Timestamp'].iloc[-1].time()
else:
    default_start_time = time.localtime().tm_hour, time.localtime().tm_min, 0  # Defaults to current time
    default_end_time = time.localtime().tm_hour, time.localtime().tm_min, 59

# Time filtering controls
st.subheader("Filter Data by Time Range")
start_time_value = st.time_input("Start Time", value=default_start_time, key="start_time_input")
end_time_value = st.time_input("End Time", value=default_end_time, key="end_time_input")

# Add threshold inputs for alerts
st.subheader("Threshold Alerts")
download_threshold = st.number_input("Download Speed Threshold (Mbps)", value=10.0, min_value=0.0)
upload_threshold = st.number_input("Upload Speed Threshold (Mbps)", value=5.0, min_value=0.0)

# Real-time update loop
while True:
    data = load_data()  # Load the latest data
    download_alert_triggered = False
    upload_alert_triggered = False
    if not data.empty:
        # Update metrics
        average_download.metric("Average Download Speed", f"{data['Download'].mean():.2f} Mbps")
        max_download.metric("Max Download Speed", f"{data['Download'].max():.2f} Mbps")
        min_upload.metric("Min Upload Speed", f"{data['Upload'].min():.2f} Mbps")

        # Check if the latest download/upload speed exceeds the thresholds
        latest_download_speed = data['Download'].iloc[-1]
        latest_upload_speed = data['Upload'].iloc[-1]

        if latest_download_speed < download_threshold and not download_alert_triggered:
            send_sms_alert(f"Low Download Speed: {latest_download_speed:.2f} Mbps")
            download_alert_triggered = True
        elif latest_download_speed >= download_threshold:
            download_alert_triggered = False
            
        if latest_upload_speed < upload_threshold and not upload_alert_triggered:
            send_sms_alert(f"Low Upload Speed: {latest_upload_speed:.2f} Mbps")
            upload_alert_triggered = True
        elif latest_upload_speed >= upload_threshold:
            upload_alert_triggered = False

        # Calculate advanced metrics
        avg_latency_value = data['Ping'].mean() if 'Ping' in data.columns else np.nan
        avg_jitter_value = data['Jitter'].mean() if 'Jitter' in data.columns else np.nan
        avg_packet_loss_value = data['Packet Loss'].mean() if 'Packet Loss' in data.columns else np.nan
        stability_index_value = (data['Download'].std() + data['Upload'].std()) / 2 if not data.empty else np.nan

        # Update advanced metrics
        avg_latency.metric("Average Latency", f"{avg_latency_value:.2f} ms")
        avg_jitter.metric("Average Jitter", f"{avg_jitter_value:.2f} ms")
        avg_packet_loss.metric("Average Packet Loss", f"{avg_packet_loss_value:.2f}%")
        stability_index.metric("Connection Stability Index", f"{stability_index_value:.2f}")

        # Apply filter based on selected time range
        data['Timestamp'] = pd.to_datetime(data['Timestamp'], format='%H:%M:%S')
        filtered_data = data[
            (data['Timestamp'].dt.time >= start_time_value) & 
            (data['Timestamp'].dt.time <= end_time_value)
        ]

        # Render the chart based on selected type
        if chart_type == "Line":
            chart_placeholder.line_chart(filtered_data[['Download', 'Upload']])
        elif chart_type == "Bar":
            chart_placeholder.bar_chart(filtered_data[['Download', 'Upload']])
        elif chart_type == "Area":
            chart_placeholder.area_chart(filtered_data[['Download', 'Upload']])

    else:
        st.info("Waiting for network speed data...")
    time.sleep(5)  # Refresh every 5 seconds
