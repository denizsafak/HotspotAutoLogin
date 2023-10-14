import json
import os
import requests
import time
import subprocess
import pystray
import threading
import tkinter as tk
from PIL import Image
from collections import deque
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'

try:
    requests.packages.urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST += 'HIGH:!DH:!aNULL'
except AttributeError:
    # no pyopenssl support used / needed / available
    pass

# Load configuration from file
with open("config.json", "r") as f:
    config = json.load(f)

# Your authentication payload and URL
payload = config["payload"]
url = config["url"]

# Convert the expected SSID to lowercase (or uppercase)
expected_ssid = config["ssid"].lower()

def is_internet_available():
    try:
        # Try to send a simple HTTP GET request to a known website
        response = requests.get("https://www.google.com")
        # If the request was successful, it means the internet is available
        return response.status_code == 200
    except requests.ConnectionError:
        # If an exception is raised, there's no internet connectivity
        return False

# Function to get the currently connected SSID using system commands (for Windows)
def get_connected_network():
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # Get Wi-Fi SSID
        wifi_output = subprocess.check_output(["netsh", "wlan", "show", "interfaces"], startupinfo=startupinfo).decode("utf-8")
        wifi_lines = wifi_output.split("\n")
        wifi_ssid = None
        for line in wifi_lines:
            if "SSID" in line:
                wifi_ssid = line.strip().split(": ")[1]
                break

        if wifi_ssid is not None:
            return wifi_ssid
        elif wifi_ssid is None:
            # Check if connected to Ethernet
            ethernet_output = subprocess.check_output(["netsh", "interface", "show", "interface"], startupinfo=startupinfo).decode("utf-8")
            ethernet_lines = ethernet_output.split("\n")
            for line in ethernet_lines:
                if "Connected" in line:
                    if "Ethernet" in line:
                        return "Ethernet Network"
        else:
            return None
    except subprocess.CalledProcessError:
        return None

headers = {
    "Content-Type": "application/json;charset=UTF-8",
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

# Function to add a message to the log file (txt)
def save_to_file(message):
    # Get the current date and time
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    # Format the message with the timestamp
    formatted_message = f"({timestamp}) {message}\n"

    # Open the file in append mode and write the formatted message
    with open("log.txt", "a") as f:
        f.write(formatted_message)

# Flag to control the main loop
running = True

# Function to gracefully exit the application
def exit_application(icon, item):
    icon.stop()
    os._exit(0)

# Queue to store log messages
log_messages = deque(maxlen=20)
log_dialog = None
log_text = None

# Function to exit the application
def exit_application(icon, item):
    if log_dialog:
        log_dialog.destroy()
    icon.stop()
    os._exit(0)

# Function to update the log
def update_log():
    if log_text:
        log_text.delete(1.0, tk.END)
        for message in get_last_log_messages():
            log_text.insert(tk.END, message + "\n")

# Function to add a message to the log
def add_to_log(message):
    global log_messages
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    log_messages.append(f"({timestamp}) {message}")
    update_log()

# Function to get the last log messages
def get_last_log_messages():
    global log_messages
    return list(log_messages)

# Function to show the log dialog
def show_log_dialog(icon, item):
    global log_dialog, log_text
    if log_dialog:
        log_dialog.deiconify()
        update_log()
    else:
        log_dialog = tk.Tk()
        log_dialog.title("Log Messages")
        log_text = tk.Text(log_dialog)
        log_dialog.geometry("1024x500")
        log_frame = tk.Frame(log_dialog)
        log_frame.pack(fill=tk.BOTH, expand=True)
        log_text = tk.Text(log_frame, wrap=tk.WORD)
        log_text.pack(fill=tk.BOTH, expand=True)
        update_log()
        log_dialog.protocol("WM_DELETE_WINDOW", hide_log_dialog)
        log_dialog.mainloop()

# Function to hide the log dialog
def hide_log_dialog():
    global log_dialog
    if log_dialog:
        log_dialog.withdraw()

# Create the system tray icon
def create_system_tray_icon():
    image = Image.open("icon.png")

    menu = pystray.Menu(
        pystray.MenuItem('Show Log', show_log_dialog),
        pystray.MenuItem('Exit', exit_application)
    )
    icon = pystray.Icon("my_icon", image, "HotspotAutoLogin", menu)
    icon.run()

# Function to check network status
def check_network_status():
    errorcount = 0
    sleepcount = config["check_every_second"]
    while running and errorcount < 10:
        connected_ssid = get_connected_network()
        if connected_ssid.lower() == expected_ssid or connected_ssid == "Ethernet Network":
            if is_internet_available():
                errorcount = 0
                sleepcount = config["check_every_second"]
                message = "Connected to " + config["ssid"] + " and internet connection is available. Checking again in " + str(sleepcount) + " seconds..."
                add_to_log(message)
            else:
                message = "Connected to " + config["ssid"] + ", but internet connection is down. Running the script..."
                add_to_log(message)
                save_to_file(message)

                # Send the request and handle potential errors
                try:
                    response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False, timeout=10, allow_redirects=True)

                    # Check the response status code
                    if response.status_code == 200:
                        # Success!
                        errorcount = 0
                        sleepcount = 10
                        message = "Request was successful. Connection established! Checking the internet connection in " + str(sleepcount) + " seconds..."
                        add_to_log(message)
                        save_to_file(message)
                    else:
                        errorcount += 1
                        sleepcount = 10  # Sleep ... seconds before trying again
                        message = "Request failed with status code: {}. Trying again in {} seconds... (Errors: {}/10)".format(response.status_code, sleepcount, errorcount)
                        add_to_log(message)
                        save_to_file(message)
                except requests.exceptions.RequestException as e:
                    # Catch the exception and add a delay before trying again
                    errorcount += 1
                    sleepcount = 10
                    message = "Failed to send request: {}. Trying again in {} seconds... (Errors: {}/10)".format(e, sleepcount, errorcount)
                    add_to_log(message)
                    save_to_file(message)
                    time.sleep(sleepcount)
                    continue
        else:
            sleepcount = 10  # Sleep ... seconds before trying again
            message = "Not connected to {}. Checking again in {} seconds...".format(config["ssid"], sleepcount)
            add_to_log(message)
            save_to_file(message)
            time.sleep(sleepcount)

        time.sleep(sleepcount)  # Sleep ... seconds before trying again

    message = "Maximum error count reached. Exiting in 5 seconds..."
    add_to_log(message)
    save_to_file(message)
    time.sleep(5)
    os._exit(0)

if __name__ == '__main__':
    
    # Create a thread for the system tray icon
    tray_thread = threading.Thread(target=create_system_tray_icon)
    tray_thread.daemon = True  # Set as a daemon thread so it exits when the main program exits
    tray_thread.start()

    # Start the network status checking in the main thread
    check_network_status()
