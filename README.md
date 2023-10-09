# HotspotAutoLogin Wi-Fi / Hotspot Auto Login Script (Automate WEB Logins)
HotspotAutoLogin is a Python script designed to automate the login process for public Wi-Fi or hotspot networks that require web-based authentication. This script is intended for situations where you often connect to networks that require a web login, such as public hotspots in cafes, hotels, or airports. The script continuously monitors your network connection and automatically logs you in when necessary.

## `How It Works`
### Network Monitoring
The script will continuously monitor your network connection. When you connect to the specified SSID but there is no internet access, it will attempt to log in automatically.

### Auto Login
If you are connected to the correct SSID but lack internet access, the script attempts to log in by sending an HTTP POST request to the provided URL with the specified credentials. If the login is successful (HTTP status code 200), the script will continue monitoring.

### Logging
Any important events or actions taken by the script are logged both in a log file (log.txt) and in the log window that can be accessed via the system tray icon.

### Configuration
The script reads its configuration from a config.json file. This file contains the necessary information, such as your login credentials, the URL of the authentication portal, the SSID (network name) to which you want to connect, and the frequency of network checks in seconds.

## `Usage` 
### Configuration
Edit the config.json file with your specific information, including your login credentials, the portal URL, the SSID of the network you want to connect to, and the check interval in seconds. [Click to learn how to Configure the config.json](#how-to-configure-the-configjson)

### System Tray Icon
When you run the script, a system tray icon will appear. Right-click on the icon to access options like showing the log or exiting the application.

### Log
You can view the log of the script's actions by clicking the "Show Log" option in the system tray menu.

## `How to Configure the config.json?`
`"payload":` You need to find your own payload values. These are the values that your browser sends when you try to login with your credentials. For example username, phone number, password... To find that:

- When you're in the login page, open your browser's Developer Tools, press F12 or Ctrl + Shift + I (or Cmd + Option + I on Mac) to open the Developer Tools. Alternatively, you can right-click anywhere on the page and select "Inspect" or "Inspect Element."
- **Navigate to the Network Tab:** In the Developer Tools, click on the "Network" tab at the top.
- **Trigger the POST Request:** Perform the action that sends the POST request. **(Try to login with incorrect password)**. The network tab will capture all network requests made by the page, including the POST request.
- **Locate the POST Request:** Look for the specific POST request in the list of network requests. It will typically have a method of "POST" and the URL it was sent to. Click on the POST request to select it.
- **Inspect the POST Data:** In the right-hand pane, you will see various tabs. Click on the "Payload" tab.
In the "Payload" tab, you can find your form data or request payload that displays the data being sent with the POST request. This is where you can see your POST payload. You need to enter the same payload values to config.json.

`"url":` **DO NOT USE HTTPS, USE HTTP.** This is **NOT** the base URL of the login page. You can find this URL from the same page that you find your payload. It is called "Request URL", in the "Headers" tab. For example: "**http**://site.com/auth"

`"ssid":` This is your network's SSID. For example "MyHome_5G"

`"check_every_second":` The frequency of the script for checking your internet connection status. For example "100", it will try to access the internet every 100 seconds.

## Dependencies
The script uses various Python libraries, including requests for making HTTP requests, pystray for creating the system tray icon, and tkinter for the log window. Make sure you have all the required libraries.

## Notes
- The script relies on the assumption that the web portal uses basic HTTP authentication. If the portal uses a more complex login mechanism, additional adjustments may be necessary.
- This script is primarily intended for Windows. Adaptations might be needed for other operating systems.

## Disclaimer
> Use this script responsibly and only on networks where you have the right to access and use the provided services. Unauthorized access to networks is illegal and unethical.
