import os
import subprocess
import tkinter as tk
from tkinter import messagebox
from winreg import ConnectRegistry, OpenKey, QueryValueEx, HKEY_CURRENT_USER
from PIL import Image
import ctypes
import json
import threading
Image.MAX_IMAGE_PIXELS = None
with open("config.json", "r") as f:
    config = json.load(f)
bottom_margin = config["bottom_margin"]
min_width = config["min_width"]
alpha = config["alpha"]
indicator_update_frequency = config["indicator_update_frequency"]
text_size = config["text_size"]
text_font = config["text_font"]
text_color = config["text_color"]
background_color = config["background_color"]
show_title = config["show_title"]
show_size = config["show_size"]
show_resolution = config["show_resolution"]
show_location = config["show_location"]
display_mouse_tips = config["display_mouse_tips"]
always_on_top = config["always_on_top"]
position = config["position"]
text_align = config["text_align"]
title_as_filename = config["title_as_filename"]
mutex = ctypes.windll.kernel32.CreateMutexW(None, 1, "Global\\EasyWallpaperInfoMutex")
if ctypes.windll.kernel32.GetLastError() == 183:
    ctypes.windll.kernel32.CloseHandle(mutex)
    messagebox.showwarning("Warning", "The program is already running. If you can't see the program, right click on your desktop.")
    os._exit(0)
def get_wallpaper_path():
    try:
        reg = ConnectRegistry(None, HKEY_CURRENT_USER)
        key = OpenKey(reg, r"Control Panel\Desktop")
        value, _ = QueryValueEx(key, "TranscodedImageCache")
        wallpaper_path = value[24:].decode('utf-16-le').rstrip('\x00')
        return wallpaper_path
    finally:
        key.Close()
        reg.Close()
def get_image_size(image_path):
    size = os.path.getsize(image_path)
    if size < 1024:
        size_str = f"{size} bytes"
    elif size < 1048576:
        size_str = f"{round(size / 1024, 2)} KB"
    elif size < 1073741824:
        size_str = f"{round(size / 1048576, 2)} MB"
    else:
        size_str = f"{round(size / 1073741824, 2)} GB"
    return size_str
def get_image_resolution(image_path):
    try:
        img = Image.open(image_path)
    finally:
        img.close()
    resolution = f"{img.width}x{img.height}"
    return resolution
def get_image_title(image_path):
    try:
        img = Image.open(image_path)
    finally:
        img.close()
    if title_as_filename:
        title = os.path.basename(image_path)
        title = os.path.splitext(title)[0]
    else:
        exif_data = img._getexif()
        try:
            title = exif_data.get(270)
            if title:
                title = title.encode('latin-1').decode('utf-8')
            else:
                title = None
        except AttributeError:
            title = None
    return title
def exit_application():
    indicator.destroy()
    os._exit(0)
def open_wallpaper_location():
    location = get_wallpaper_path()
    subprocess.Popen(['explorer', '/select,', location])
def open_wallpaper():
    location = get_wallpaper_path()
    subprocess.Popen(['start', '', location], shell=True)
def copy_title_text():
    wallpaper_path = get_wallpaper_path()
    title = get_image_title(wallpaper_path)
    indicator.clipboard_clear()
    indicator.clipboard_append(title)
    indicator.update()
def show_menu(event):
    menu.post(event.x_root, event.y_root)
def on_left_click(event):
    label.config(cursor="arrow")
def on_right_click(event):
    show_menu(event)
def reset_cursor(event):
    label.after(10, lambda: label.config(cursor="hand2"))
    subprocess.call("NextBackground.exe")
def update_label():
    details = ""
    wallpaper_path = get_wallpaper_path()
    if show_title:
        title = get_image_title(wallpaper_path)
        details += f"Title: {title}\n"
    if show_size:
        size = get_image_size(wallpaper_path)
        details += f"Filesize: {size}\n"
    if show_resolution:
        resolution = get_image_resolution(wallpaper_path)
        details += f"Resolution: {resolution}\n"
    if show_location:
        details += f"Location: {wallpaper_path}\n"
    details = details[:-1]
    label.config(text=details)
    indicator.after(indicator_update_frequency, update_label)
def display_message(message):
    background_color = config["background_color"]
    text_color = config["text_color"]
    msg_window = tk.Tk()
    msg_window.title("Message")
    msg_window.overrideredirect(True)
    msg_window.attributes("-topmost", True)
    screen_width = msg_window.winfo_screenwidth()
    screen_height = msg_window.winfo_screenheight()
    x = (screen_width - 300) // 2
    y = (screen_height - 100) // 2
    msg_window.geometry(f"300x100+{x}+{y}")
    label2 = tk.Label(msg_window, text=message, font=(text_font, 14), bg=background_color, fg=text_color)
    label2.pack(expand=True, fill='both')
    msg_window.after(5000, msg_window.destroy)
    msg_window.mainloop()
def set_indicator_position(position):
    if position == "center":
        x = (indicator.winfo_screenwidth() - indicator.winfo_width()) // 2
        y = (indicator.winfo_screenheight() - indicator.winfo_height()) // 2
    elif position == "top_center":
        x = (indicator.winfo_screenwidth() - indicator.winfo_width()) // 2
        y = 0
    elif position == "bottom_center":
        x = (indicator.winfo_screenwidth() - indicator.winfo_width()) // 2
        y = indicator.winfo_screenheight() - bottom_margin
    elif position == "top_left":
        x, y = 0, 0
    elif position == "top_right":
        x = indicator.winfo_screenwidth() - indicator.winfo_width()
        y = 0
    elif position == "bottom_left":
        x, y = 0, indicator.winfo_screenheight() - bottom_margin
    elif position == "bottom_right":
        x = indicator.winfo_screenwidth() - indicator.winfo_width()
        y = indicator.winfo_screenheight() - bottom_margin
    else:
        messagebox.showwarning("Warning", "Invalid position value in config.json")
        os._exit(0)
    indicator.geometry("+{}+{}".format(x, y))
    config["position"] = position
def change_position(position, check_var):
    set_indicator_position(position)
    check_var.set(1)
    for other_position, other_var in position_vars.items():
        if other_position != position:
            other_var.set(0)
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)
def update_label_text_align():
    if config["text_align"] == "center":
        anchor = "center"
    elif config["text_align"] == "left":
        anchor = "w"
    elif config["text_align"] == "right":
        anchor = "e"
    else:
        messagebox.showwarning("Warning", "Invalid text_align value in config.json")
        os._exit(0)
    label.config(anchor=anchor, justify=config["text_align"])
def change_text_align(align, check_var):
    check_var.set(1)
    for other_align, other_var in text_align_vars.items():
        if other_align != align:
            other_var.set(0)
    config["text_align"] = align
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)
    update_label_text_align()
def toggle_mouse_tips(variable):
    config["display_mouse_tips"] = bool(variable.get())
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)
if __name__ == "__main__":
    if display_mouse_tips:
        display_message("Hover on widget,\nLeft Click: Next Wallpaper\nRight Click: Menu")
    indicator = tk.Tk()
    indicator.title("Easy Wallpaper Info")
    indicator.overrideredirect(True)
    indicator.minsize(min_width, 0)
    indicator.maxsize(indicator.winfo_screenwidth(), 0)
    indicator.attributes("-alpha", alpha)
    if always_on_top:
        indicator.attributes("-topmost", True)
    details = ""
    wallpaper_path = get_wallpaper_path()
    if show_title:
        title = get_image_title(wallpaper_path)
        details += f"Title: {title}\n"
    if show_size:
        size = get_image_size(wallpaper_path)
        details += f"Filesize: {size}\n"
    if show_resolution:
        resolution = get_image_resolution(wallpaper_path)
        details += f"Resolution: {resolution}\n"
    if show_location:
        details += f"Location: {wallpaper_path}\n"
    details = details[:-1]
    if text_align == "center":
        anchor = "center"
    elif text_align == "left":
        anchor = "w"
    elif text_align == "right":
        anchor = "e"
    else:
        messagebox.showwarning("Warning", "Invalid text_align value in config.json")
        os._exit(0)
    label = tk.Label(indicator, text=details, font=(text_font, text_size), bg=background_color, fg=text_color, anchor=anchor, justify=text_align)
    label.pack(expand=True, fill='both')
    label.config(cursor="hand2")
    label.bind("<Button-1>", on_left_click)
    label.bind("<Button-3>", on_right_click)
    label.bind("<ButtonRelease-1>", reset_cursor)
    menu = tk.Menu(indicator, tearoff=0)
    version = "v1.3"
    github_link = "https://github.com/denizsafak/EasyWallpaperInfo"
    menu.add_command(label=f"EasyWallpaperInfo {version}", command=lambda: os.startfile(github_link), foreground="grey")
    menu.add_separator()
    menu.add_command(label="Open wallpaper", command=open_wallpaper)
    menu.add_command(label="Go to wallpaper location", command=open_wallpaper_location)
    menu.add_command(label="Copy title text", command=copy_title_text)
    menu.add_separator()
    position_menu = tk.Menu(indicator, tearoff=0)
    position_vars = {}
    for pos in ["center", "top_center", "bottom_center", "top_left", "top_right", "bottom_left", "bottom_right"]:
        label_text = pos.replace("_", " ").capitalize()
        var = tk.IntVar(value=1 if config["position"] == pos else 0)
        position_vars[pos] = var
        position_menu.add_checkbutton(label=label_text, variable=var, command=lambda p=pos, v=var: change_position(p, v))
    menu.add_cascade(label="Position", menu=position_menu)
    text_align_menu = tk.Menu(indicator, tearoff=0)
    text_align_vars = {}
    for align in ["left", "center", "right"]:
        label_text = align.capitalize()
        var = tk.IntVar(value=1 if config["text_align"] == align else 0)
        text_align_vars[align] = var
        text_align_menu.add_checkbutton(label=label_text, variable=var, command=lambda a=align, v=var: change_text_align(a, v))
    menu.add_cascade(label="Text Align", menu=text_align_menu)
    mouse_tips_var = tk.IntVar(value=1 if config["display_mouse_tips"] else 0)
    menu.add_checkbutton(label="Display Mouse Tips", variable=mouse_tips_var, command=lambda: toggle_mouse_tips(mouse_tips_var))
    menu.add_command(label="Edit config.json", command=lambda: os.startfile("config.json"))
    menu.add_command(label="Exit", command=exit_application)
    update_label()
    indicator.bind("<Configure>", lambda e: set_indicator_position(config["position"]))
    indicator.mainloop()
    ctypes.windll.kernel32.CloseHandle(mutex)