import json
import os
import requests
import time
import subprocess
import pystray
import threading
import tkinter as tk
from tkinter import Text, Scrollbar
from PIL import Image
from collections import deque
from datetime import datetime
import dns.resolver
dns.resolver.override_system_resolver(dns.resolver.Resolver())
dns.resolver.default_resolver = dns.resolver.Resolver()
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# Function to center a window on the screen
def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

def select_profile():
    global selected_profile
    selected_index = listbox.curselection()
    
    if selected_index:
        selected_index = int(selected_index[0])
        selected_profile = profiles[selected_index]
        root.destroy()

# Define a function to update the profile details
def update_profile_details(event):
    selected_index = listbox.curselection()
    if selected_index:
        selected_index = int(selected_index[0])
        selected_profile = profiles[selected_index]
        profile_name.config(text=f"Selected Profile: {selected_profile['name']}")
        profile_details.config(state=tk.NORMAL)
        profile_details.delete(1.0, tk.END)
        
        # Insert profile details with all variables except "name"WWWW
        profile_details.tag_configure("bold", font=("Courier New", 10, "bold"), foreground="#08872a")
        for key, value in selected_profile.items():
            if key != 'name':  # Skip displaying the "name" variable
                profile_details.insert(tk.END, f"{key}: ", "bold")
                profile_details.insert(tk.END, f"{value}\n")
        
        profile_details.config(state=tk.DISABLED)
    else:
        reset_profile_details()

def reset_profile_details():
    profile_name.config(text="Selected Profile: ")
    profile_details.config(state=tk.NORMAL)
    profile_details.delete(1.0, tk.END)
    profile_details.config(state=tk.DISABLED)

# Load configuration from file
with open("config.json", "r") as f:
    config = json.load(f)

# Get the list of profiles
profiles = config.get("profiles", [])

# Create the main window
root = tk.Tk()
root.title("Profile Selection")

# Set a maximum size for the window
width = 850
height = 300
root.minsize(width, height)  # Adjust the values as needed
center_window(root, width, height)

# Create a frame for listing profiles
profiles_frame = tk.Frame(root)
profiles_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

# Create a listbox to display available profiles
listbox = tk.Listbox(profiles_frame, selectmode=tk.SINGLE)
listbox.pack(side=tk.LEFT, fill=tk.Y)

for profile in profiles:
    listbox.insert(tk.END, profile['name'])

# Create a vertical scrollbar for the listbox
scrollbar = tk.Scrollbar(profiles_frame, orient=tk.VERTICAL)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Link the listbox and scrollbar
listbox.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=listbox.yview)

# Bind the listbox selection event to update the profile details
listbox.bind('<<ListboxSelect>>', update_profile_details)

# Create a frame for displaying profile details
details_frame = tk.Frame(root)
details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

# Create a label for the selected profile name
profile_name = tk.Label(details_frame, text="Selected Profile: ", anchor="w")
profile_name.pack(fill="x", pady=(0, 5))

# Create a Text widget for displaying profile details with a fixed height and scrollbars
profile_details = Text(details_frame, wrap=tk.WORD, height=10, state=tk.DISABLED, exportselection=False)
profile_details.pack(fill="both", expand=True)

# Create a vertical scrollbar for the profile details Text widget
profile_scrollbar = Scrollbar(profile_details, command=profile_details.yview)
profile_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Link the profile details Text widget and scrollbar
profile_details.config(yscrollcommand=profile_scrollbar.set)

# Function to exit the application
def on_closing():
    root.destroy()
    os._exit(0)

root.protocol("WM_DELETE_WINDOW", on_closing)

# Create the "Select" button
select_button = tk.Button(
    details_frame,
    text="Run",
    command=select_profile,
    padx=10,
    pady=10,
    fg="white",
    bg="#08872a",
    activebackground="#076921",
    activeforeground="white",
    relief=tk.RAISED,
    borderwidth=2,
)
select_button.pack(fill="x", pady=(10, 0))

# Start with no profile selected
selected_profile = None

# Select the first profile by default
if profiles:
    selected_profile = profiles[0]
    listbox.select_set(0)  # Highlight the first item in the list
    update_profile_details(None)  # Update the profile details

root.mainloop()

# Access the selected profile's data after the window closes
if selected_profile:
    payload = selected_profile.get('payload')
    url = selected_profile.get('url', "")
    ssid = selected_profile.get('ssid', "")
    check_every_second = selected_profile.get('check_every_second', "")
    dialog_geometry = selected_profile.get('dialog_geometry', "")
    headers = selected_profile.get('headers', "")
    if ssid:
        expected_ssid = ssid
        expected_ssid_lower = expected_ssid.lower()
    else:
        ssid = "Ethernet"
        expected_ssid = ssid
        expected_ssid_lower = None


# Function to send the request
def send_request():
    session = requests.Session()
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'
    response = session.post(url, json.dumps(payload), headers=headers, allow_redirects=True, verify=False, timeout=3)
    response.raise_for_status()  # Check for HTTP errors
    return response

# Function to check if internet is available
def is_internet_available():
    try:
        # -n is the number of pings
        # -l is the size of the packet
        # -w is the timeout in seconds
        subprocess.run(['ping', '8.8.8.8', '-n', '3', '-l', '32', '-w', '3'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except subprocess.CalledProcessError:
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
    
# Function to exit the application
def exit_application(icon, item):
    icon.stop()
    os._exit(0)

# Queue to store log messages
log_messages = deque(maxlen=20)
log_dialog = None
log_text = None
log_dialog_open = False

# Get the dialog geometry from the config file
width = dialog_geometry["width"]
height = dialog_geometry["height"]
x = 0
y = 0

# Function to update the window's position and size variables
def update_window_geometry(event):
    global x, y, width, height
    x, y = event.x, event.y
    width, height = event.width, event.height

# Function to show the log dialog
def show_log_dialog():
    global log_dialog, log_text, log_dialog_open
    if not log_dialog_open:
        log_dialog_open = True
        if log_dialog:
            log_dialog.deiconify()
            update_log()
        else:
            log_dialog = tk.Tk()
            log_dialog.title("Log Messages")
            log_text = tk.Text(log_dialog)
            log_frame = tk.Frame(log_dialog)
            log_frame.pack(fill=tk.BOTH, expand=True)
            log_text = tk.Text(log_frame, wrap=tk.WORD)
            log_text.pack(fill=tk.BOTH, expand=True)
            update_log()
            log_dialog.protocol("WM_DELETE_WINDOW", hide_log_dialog)
            center_window(log_dialog, width, height)
            log_dialog.bind("<Configure>", update_window_geometry)
            log_dialog.mainloop()
    else:
        hide_log_dialog()

# Function to hide the log dialog
def hide_log_dialog():
    global log_dialog, log_text, log_dialog_open
    log_dialog_open = False
    if log_dialog:
        log_dialog.withdraw()
        log_dialog = None
        log_text = None

# Function to get the last log messages
def get_last_log_messages():
    global log_messages
    return list(log_messages)

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

# Create the system tray icon
def create_system_tray_icon():
    image = Image.open("icon.ico")
    menu = pystray.Menu(
        pystray.MenuItem('Show Log', show_log_dialog, default=True),
        pystray.MenuItem('Exit', exit_application)
    )
    icon = pystray.Icon("my_icon", image, "HotspotAutoLogin", menu)
    icon.run()

# Function to check network status
running = True
errorcount = 0
sleepcount = check_every_second
connected_ssid_lower = None
def check_network_status():
    global running, errorcount, sleepcount, connected_ssid_lower, ssid, response
    while running and errorcount < 10:
        connected_ssid = get_connected_network()
        if (connected_ssid):
            connected_ssid_lower = connected_ssid.lower()
        if (connected_ssid) and ((connected_ssid_lower == expected_ssid_lower) or (connected_ssid == "Ethernet")):
            if (is_internet_available()):
                sleepcount = check_every_second
                message = "Connected to {} and internet connection is available. Checking again in {} seconds...".format(connected_ssid, str(sleepcount))
                errorcount = 0
                add_to_log(message)
            else:
                sleepcount = 1
                message = "Connected to {} but internet is down. Sending the request...".format(connected_ssid)
                add_to_log(message)
                save_to_file(message)
                time.sleep(sleepcount)
                # Send the request and handle potential errors
                try:                        
                    # Function to send request
                    response = send_request()
                    if response.ok:
                        errorcount = 0
                        sleepcount = 10
                        message = "Request was successful. Checking the internet connection in {} seconds...".format(str(sleepcount))
                        add_to_log(message)
                        save_to_file(message)
                except requests.exceptions.RequestException as e:
                    errorcount += 1
                    sleepcount = 1
                    if isinstance(e, requests.exceptions.HTTPError):
                        # Handle HTTP errors with different messages for different status codes
                        status_code = e.response.status_code
                        if status_code == 400:
                            message = "Request failed with 400 Bad Request error. Please check your payload and URL. Trying to reconnect to the network... (Errors: {}/10)".format(errorcount)
                        elif status_code == 404:
                            message = "Request failed with 404 Not Found error. Trying to reconnect to the network... (Errors: {}/10)".format(errorcount)
                        elif status_code == 500:
                            message = "Request failed with 500 Internal Server Error. Trying to reconnect to the network... (Errors: {}/10)".format(errorcount)
                        elif status_code == 503:
                            message = "Request failed with 503 Service Unavailable error. Trying to reconnect to the network... (Errors: {}/10)".format(errorcount)
                        else:
                            message = "Request failed with HTTP error ({}). Trying to reconnect to the network... (Errors: {}/10)".format(status_code, errorcount)
                    else:
                        message = "Request failed with error:{}. Trying to reconnect to the network... (Errors: {}/10)".format(e, errorcount)
                    # Print the response message
                    add_to_log(message)
                    save_to_file(message)
                    time.sleep(sleepcount)
                    # If the payload URL is not reachable, try to reconnect to the network
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    if connected_ssid == "Ethernet":
                        try:
                            # Disable and enable the Ethernet adapter
                            message = "Disconnecting from Ethernet..."
                            add_to_log(message)
                            subprocess.check_output(['ipconfig', '/release', "Ethernet"], shell=True, text=True)
                            time.sleep(5)
                            subprocess.check_output(['ipconfig', '/renew', "Ethernet"], shell=True, text=True)
                            time.sleep(2)
                            message = "Connected to Ethernet. Running the script again..."
                            add_to_log(message)
                        except Exception as e:
                            message += "\nFailed to reconnect to Ethernet: {}".format(e)
                            add_to_log(message)
                            save_to_file(message)
                    else:
                        try:
                            # Disconnect and reconnect to the Wi-Fi network
                            message = "Disconnecting from {}...".format(ssid)
                            add_to_log(message)
                            subprocess.check_output(['netsh', 'wlan', 'disconnect', 'interface=' + "Wi-Fi"], startupinfo=startupinfo).decode("utf-8")
                            time.sleep(5)
                            subprocess.check_output(['netsh', 'wlan', 'connect', 'name=' + ssid], startupinfo=startupinfo).decode("utf-8")
                            time.sleep(2)
                            message = "Connected to {}. Running the script again...".format(ssid)
                            add_to_log(message)
                        except Exception as e:
                            message += "\nFailed to reconnect to {}: {}".format(ssid, e)
                            add_to_log(message)
                            save_to_file(message)
                    continue
        else:
            sleepcount = 10  # Sleep ... seconds before trying again
            message = "Not connected to {} or any other network. Checking again in {} seconds...".format(expected_ssid, str(sleepcount))
            add_to_log(message)
            save_to_file(message)

        time.sleep(sleepcount)  # Sleep ... seconds before trying again

    message = "Maximum error count reached. Exiting in 5 seconds..."
    add_to_log(message)
    save_to_file(message)
    time.sleep(5)
    running = False
    os._exit(0)

if __name__ == '__main__':
    # Create a thread for the system tray icon
    tray_thread = threading.Thread(target=create_system_tray_icon)
    tray_thread.start()

    # Open Log Messages at startup
    open_log_messages_startup = threading.Thread(target=show_log_dialog)
    open_log_messages_startup.start()

    # Start the network status checking in the main thread
    check_network_status()

    # Wait for all threads to finish
    tray_thread.join()