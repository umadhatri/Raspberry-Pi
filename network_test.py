from speedtest import Speedtest
import csv
from datetime import datetime
import time

# Define a function to calculate jitter
def calculate_jitter(ping_times):
    if len(ping_times) < 2:
        return 0  # Not enough data to calculate jitter
    diffs = [abs(ping_times[i] - ping_times[i - 1]) for i in range(1, len(ping_times))]
    return sum(diffs) / len(diffs)

# Initialize variables
ping_times = []  # To store ping values for jitter calculation

# Run the speed test
def run_speed_test():
    s = Speedtest()
    s.get_best_server()
    download_speed = s.download() / 1_000_000  # Convert to Mbps
    upload_speed = s.upload() / 1_000_000  # Convert to Mbps
    ping = s.results.ping  # Ping in milliseconds

    # Add the ping to the list for jitter calculation
    ping_times.append(ping)
    jitter = calculate_jitter(ping_times)

    # Get the current timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Write the results to a CSV file
    file_exists = False
    try:
        with open('network_log.csv', 'r') as f:
            file_exists = True
    except FileNotFoundError:
        pass

    with open('network_log.csv', 'a', newline='') as csvfile:
        fieldnames = ['Timestamp', 'Download', 'Upload', 'Ping', 'Jitter']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()  # Write headers if the file doesn't exist
        writer.writerow({
            'Timestamp': timestamp,
            'Download': download_speed,
            'Upload': upload_speed,
            'Ping': ping,
            'Jitter': jitter
        })

# Run the speed test periodically
while True:
    run_speed_test()
    time.sleep(30)  # Run every 30 seconds