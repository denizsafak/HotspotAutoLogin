import json
import requests
import time
import subprocess
import pystray
from PIL import Image
import threading
import tkinter as tk
from collections import deque
from datetime import datetime
import os
import socket

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
        # Attempt to resolve a common internet domain (e.g., google.com)
        host = socket.gethostbyname("www.google.com")
        # If successful, it means the internet is available
        return True
    except socket.error:
        # If an exception is raised, there's no internet connectivity
        return False

# Function to get the currently connected WiFi SSID using system commands (for Windows)
def get_connected_wifi_ssid():
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        output = subprocess.check_output(["netsh", "wlan", "show", "interfaces"], startupinfo=startupinfo).decode("utf-8")
        lines = output.split("\n")
        for line in lines:
            if "SSID" in line:
                ssid = line.strip().split(": ")[1]
                return ssid
        return None
    except subprocess.CalledProcessError:
        return None

headers = {
    "Content-Type": "application/json"
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
log_messages = deque(maxlen=10)

# Function to add a message to the log
def add_to_log(message):
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    log_messages.append(f"({timestamp}) {message}")
    update_log()  # Update the log after adding a message

# Function to update the log
def update_log():
    if 'log_text' in globals():  # Check if the log dialog is open
        log_text.delete(1.0, tk.END)  # Clear the existing log
        for message in get_last_log_messages():
            log_text.insert(tk.END, message + "\n")

# Function to get the last log messages
def get_last_log_messages():
    return list(log_messages)

# Create the system tray icon
def create_system_tray_icon():
    image = Image.open("icon.png")  # Replace "icon.png" with your own icon image

    def show_log_dialog(icon, item):
        global log_dialog, log_text  # Make these variables global so they can be accessed in update_log
        log_dialog = tk.Tk()
        log_dialog.title("Log Messages")
        log_text = tk.Text(log_dialog)
        log_text.pack()

        update_log()  # Update the log when the dialog is shown
        log_dialog.mainloop()

    menu = pystray.Menu(pystray.MenuItem('Show Log', show_log_dialog), pystray.MenuItem('Exit', exit_application))
    icon = pystray.Icon("my_icon", image, "WIFI Autologin", menu)
    icon.run()

# Function to check network status
def check_network_status():
    errorcount = 0
    sleepcount = config["check_every_second"]
    while running and errorcount < 10:
        connected_ssid = get_connected_wifi_ssid()
        if connected_ssid and connected_ssid.lower() == expected_ssid:
            if is_internet_available():
                errorcount = 0
                sleepcount = config["check_every_second"]
                message = "Connected to "+config["ssid"]+" and internet connection is available. Checking again in "+str(sleepcount)+" seconds..."
                add_to_log(message)
            else:
                message = "Connected to "+config["ssid"]+", but internet connection is down. Running the script..."
                add_to_log(message)
                save_to_file(message)

                # Semd the request and ignore SSL errors
                response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)

                # Check the response status code
                if response.status_code == 200:
                    # Success!
                    errorcount = 0
                    sleepcount = config["check_every_second"]
                    message = "Request was successful. Connection established! Checking again in "+str(sleepcount)+" seconds..."
                    add_to_log(message)
                    save_to_file(message)
                else:
                    errorcount += 1
                    sleepcount = 10  # Sleep ... seconds before trying again
                    message = "Request failed with status code: {}".format(response.status_code)+" Trying again in "+str(sleepcount)+" seconds... (Errors: "+str(errorcount)+"/10)"
                    add_to_log(message)
                    save_to_file(message)
        else:
            errorcount += 1
            sleepcount = 10  # Sleep ... seconds before trying again
            message = "Not connected to "+config["ssid"]+" Checking again in "+str(sleepcount)+" seconds... (Errors: "+str(errorcount)+"/10)"
            add_to_log(message)
            save_to_file(message)

        time.sleep(sleepcount)  # Sleep ... seconds before trying again

    message = "Maximum error count reached. Exiting in 5 seconds..."
    add_to_log(message)
    save_to_file(message)
    time.sleep(5)
    os._exit(0)

if __name__ == '__main__':
    # Create a thread for the system tray icon
    tray_thread = threading.Thread(target=create_system_tray_icon)
    tray_thread.start()

    # Start the network status checking in the main thread
    check_network_status()