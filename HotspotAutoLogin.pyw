import logging, sys, traceback

# Log all errors to a log.txt file
def log_exception(exctype, value, tb):
    logging.exception("Uncaught exception: {0}".format(str(value)))
    logging.exception("Traceback: {0}".format(''.join(traceback.format_tb(tb))))
    logging.shutdown()
    sys.exit(1)

sys.excepthook = log_exception

# Log all messages except DEBUG to a log.txt file
logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

# Load configuration from file
with open("config.json", "r") as f:
    config = json.load(f)

# Your payload
payload = config["payload"]
url = config["url"]
if (config["ssid"]):
    expected_ssid = config["ssid"]
    expected_ssid_lower = config["ssid"].lower()
else:
    config["ssid"] = "Wi-Fi"
    expected_ssid = config["ssid"]
    expected_ssid_lower = None

def is_internet_available():
    try:
        # Try to send a simple HTTP GET request to a known website
        response = requests.get("https://www.google.com", timeout=10)
        # If the request was successful, it means the internet is available
        return True
    except (requests.ConnectionError, requests.RequestException):
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
                        return "Ethernet"
        else:
            return False
    except subprocess.CalledProcessError:
        return False

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
log_dialog_open = False
def show_log_dialog():
    global log_dialog, log_text, log_dialog_open
    if log_dialog_open == False:
        log_dialog_open = True
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
    else:
        hide_log_dialog()

# Function to hide the log dialog
def hide_log_dialog():
    global log_dialog, log_dialog_open
    log_dialog_open = False
    if log_dialog:
        log_dialog.withdraw()
        log_dialog = None

# Create the system tray icon
def create_system_tray_icon():
    image = Image.open("icon.png")

    menu = pystray.Menu(
        pystray.MenuItem('Show Log', show_log_dialog, default=True),
        pystray.MenuItem('Exit', exit_application)
    )
    icon = pystray.Icon("my_icon", image, "HotspotAutoLogin", menu)
    icon.run()

# Function to check network status
running = True
errorcount = 0
sleepcount = config["check_every_second"]
connected_ssid_lower = None
def check_network_status():
    global running, errorcount, sleepcount, connected_ssid_lower
    while running and errorcount < 10:
        connected_ssid = get_connected_network()
        if (connected_ssid):
            connected_ssid_lower = connected_ssid.lower()
        if (connected_ssid) and ((connected_ssid_lower == expected_ssid_lower) or (connected_ssid == "Ethernet")):
            if (is_internet_available()):
                sleepcount = config["check_every_second"]
                message = "Connected to {} and internet connection is available. Checking again in {} seconds...".format(connected_ssid, str(sleepcount))
                errorcount = 0
                add_to_log(message)
            else:
                sleepcount = 3
                time.sleep(sleepcount)
                message = "Connected to {} but internet is down. Sending the request in {} seconds...".format(connected_ssid, str(sleepcount))
                add_to_log(message)
                save_to_file(message)
                # Send the request and handle potential errors
                try:
                    # Update SSL cipher list
                    try:
                        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'
                    except AttributeError as e:
                        # no pyopenssl support used / needed / available
                        add_to_log("Error when adding to DEFAULT_CIPHERS: {}".format(e))
                        save_to_file("Error when adding to DEFAULT_CIPHERS: {}".format(e))
                        pass
                    time.sleep(1)
                    response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False, timeout=10)
                    message = "Request sent."
                    add_to_log(message)
                    save_to_file(message)
                    # Check the response status code
                    if response.ok:
                        # Success!
                        errorcount = 0
                        sleepcount = 10
                        message = "Request was successful. Connection established! Checking the internet connection in " + str(sleepcount) + " seconds..."
                        add_to_log(message)
                        save_to_file(message)
                    else:
                        errorcount += 1
                        sleepcount = 10  # Sleep ... seconds before trying again
                        message = "Request failed with status code: {}. Trying again in {} seconds... (Errors: {}/10)".format(response.status_code, str(sleepcount), errorcount)
                        add_to_log(message)
                        save_to_file(message)
                except requests.exceptions.RequestException as e:
                    # Catch the exception and add a delay before trying again
                    errorcount += 1
                    sleepcount = 10
                    message = "Failed to send request: {}. Trying again in {} seconds... (Errors: {}/10)".format(e, str(sleepcount), str(errorcount))
                    add_to_log(message)
                    save_to_file(message)
                    time.sleep(sleepcount)
                    continue
        else:
            sleepcount = 10  # Sleep ... seconds before trying again
            message = "Not connected to target {} or any Ethernet. Checking again in {} seconds...".format(expected_ssid, str(sleepcount))
            add_to_log(message)
            save_to_file(message)

        time.sleep(sleepcount)  # Sleep ... seconds before trying again

    message = "Maximum error count reached. Exiting in 5 seconds..."
    add_to_log(message)
    save_to_file(message)
    time.sleep(5)
    running = False
    os._exit(0)

def open_log_dialog_thread():
    log_thread = threading.Thread(target=show_log_dialog)
    log_thread.start()

if __name__ == '__main__':
    
    # Create a Tkinter window to run the main loop
    root = tk.Tk()

    # Create a thread for the system tray icon
    tray_thread = threading.Thread(target=create_system_tray_icon)
    tray_thread.daemon = True
    tray_thread.start()

    # Open Log Messages at startup
    open_log_dialog_thread()

    # Start the network status checking in the main thread
    check_network_status()

    # Start the Tkinter main loop
    root.mainloop()

    # Wait for all threads to finish
    tray_thread.join()
