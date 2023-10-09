# HotspotAutoLogin - Wi-Fi / Hotspot Auto Login Script (Automate WEB Logins)
HotspotAutoLogin is a Python script designed to automate the login process for public Wi-Fi or hotspot networks that require web-based authentication. This script is intended for situations where you often connect to networks that require a web login, such as public hotspots in cafes, hotels, or airports. The script continuously monitors your network connection and automatically logs you in when necessary.

## `How It Works`
### Configuration
The script reads its configuration from a config.json file. This file contains the necessary information, such as your login credentials, the URL of the authentication portal, the SSID (network name) to which you want to connect, and the frequency of network checks in seconds.

### Network Monitoring
The script will continuously monitor your network connection. When you connect to the specified SSID without internet access, it will attempt to log in automatically.

### Auto Login
If you are connected to the correct SSID but lack internet access, the script attempts to log in by sending an HTTP POST request to the provided URL with the specified credentials. If the login is successful (HTTP status code 200), the script will continue monitoring. If the login fails, it retries up to 10 times before waiting for a predefined time period.

### Logging
Any important events or actions taken by the script are logged both in a log file (log.txt) and in the log window that can be accessed via the system tray icon.

### Exit Gracefully
If the script encounters too many login failures (10 consecutive errors), it will exit gracefully.



## `Usage` 
### Configuration
Edit the config.json file with your specific information, including your login credentials, the portal URL, the SSID of the network you want to connect to, and the check interval in seconds.

### System Tray Icon
Run the script, and a system tray icon will appear. Right-click on the icon to access options like showing the log or exiting the application.

### Log
You can view the log of the script's actions by clicking the "Show Log" option in the system tray menu.

## Dependencies
The script uses various Python libraries, including requests for making HTTP requests, pystray for creating the system tray icon, and tkinter for the log window. Make sure you have all the required libraries.

## Notes
- The script relies on the assumption that the web portal uses basic HTTP authentication. If the portal uses a more complex login mechanism, additional adjustments may be necessary.
- This script is primarily intended for Windows. Adaptations might be needed for other operating systems.

## Disclaimer
> Use this script responsibly and only on networks where you have the right to access and use the provided services. Unauthorized access to networks is illegal and unethical.
