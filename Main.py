# Main python file for the overlay app project
# Project contains both Human and AI Created Code
# AI Created code is 30% or less as in compliance with the rules.
# Big thank you to the random people over the years that solved some of the problems on stackoverflow and reddit :)
# Current Revision: 4
import ctypes
import ctypes.wintypes
import numpy as np
import cv2
import pygetwindow as windowfetch
import tkinter as Gui
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk
from pathlib import Path

filecontents = ""
filepath = Path("OverlayAppSettings.txt")
if filepath.is_file():
    print("File exists")
else:
    print("File Doesnt exsist")
    with open(filepath, "w") as file:
        file.write("True")


with open(filepath, "r") as file:
    contents = file.read()
    print(contents)
    if contents == "True":
        filecontents = "True"
    elif contents == "False":
        filecontents = "False"
    else:
        print("File has invalid data")
        with open(filepath,"w") as file:
            file.write("True")

print("Current Santised setting is: "+filecontents)
ColorMode = "#313131"
TextColor = "#FFFFFF"
ButtonColor = "#5C5C5C"

if filecontents == "False":
    ColorMode = "#FFFFFF"
    TextColor = "#3D3D3D"
    ButtonColor = "#9E9E9E"

# Set up ctypes shortcuts for Windows API
User32 = ctypes.windll.user32
Gdi32 = ctypes.windll.gdi32

def capture_window_ctypes(window_title):
    """Captures the target window and returns it as a standard NumPy RGB array."""
    hwnd = User32.FindWindowW(None, window_title)
    if not hwnd: return None

    rect = ctypes.wintypes.RECT()
    User32.GetWindowRect(hwnd, ctypes.byref(rect))
    w, h = rect.right - rect.left, rect.bottom - rect.top
    if w <= 0 or h <= 0: return None

    hwndDC = User32.GetWindowDC(hwnd)
    mfcDC = Gdi32.CreateCompatibleDC(hwndDC)
    saveBitMap = Gdi32.CreateCompatibleBitmap(hwndDC, w, h)
    Gdi32.SelectObject(mfcDC, saveBitMap)
    User32.PrintWindow(hwnd, mfcDC, 2)

    bmpinfo = bytearray(40)
    np.frombuffer(bmpinfo, dtype=np.uint32, count=1, offset=0)[0] = 40      
    np.frombuffer(bmpinfo, dtype=np.int32, count=2, offset=4)[:] = [w, -h]  
    np.frombuffer(bmpinfo, dtype=np.uint16, count=2, offset=12)[:] = [1, 32] 

    buffer = bytearray(w * h * 4)
    Gdi32.GetDIBits(hwndDC, saveBitMap, 0, h, (ctypes.c_char * len(buffer)).from_buffer(buffer), bytes(bmpinfo), 0)

    Gdi32.DeleteObject(saveBitMap)
    Gdi32.DeleteDC(mfcDC)
    User32.ReleaseDC(hwnd, hwndDC)

    img = np.frombuffer(buffer, dtype=np.uint8).reshape(h, w, 4)
    return cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)

def stream_to_label(label, target_title):
    """Grabs a frame, resizes it to the current overlay size, and updates the label."""
    # Safety check: Stop streaming if the overlay window was closed or hidden
    if not label.winfo_exists():
        return

    frame = capture_window_ctypes(target_title)
    
    # Track the current size of the window dynamically
    w = label.winfo_width()
    h = label.winfo_height()
    if w <= 1 or h <= 1: w, h = 200, 200  # Fallback size

    if frame is not None:
        frame_resized = cv2.resize(frame, (w, h), interpolation=cv2.INTER_LINEAR)
        img_pil = Image.fromarray(frame_resized)
        
        # Keep a reference to prevent garbage collection
        label.img_tk = ImageTk.PhotoImage(image=img_pil) 
        label.config(image=label.img_tk, text="")
    else:
        label.config(image="", text=f"Minimized or Hidden...", fg="white")
        
    # Schedule the next frame update (~30 FPS)
    label.after(33, lambda: stream_to_label(label, target_title))

windowlist = []
CurrentOpenWindows = windowfetch.getAllTitles()

# Initialize the Main Menu to choose an app directly
ChoosingMenu = Gui.Tk()
ChoosingMenu.title("App Overlay")
ChoosingMenu.geometry("500x500")
ChoosingMenu.configure(bg=ColorMode)

messagebox.showwarning(
    "App Overlay - Warning",
    "This Program is bare bones, all apps that are overlayed only work if they are open and not minimized, if any issues occure please relaunch the app."
)

# Initialize the Menu to be the overlay
OverlayMenu = Gui.Toplevel(ChoosingMenu)
OverlayMenu.title("App Overlay - Overlay")
OverlayMenu.attributes("-topmost", True)
OverlayMenu.geometry("400x300")  # Bumped up starting size so you can see it easily
OverlayMenu.configure(bg="black")
OverlayMenu.withdraw()

# Add a label spanning the whole OverlayMenu to act as our video display screen
stream_display = Gui.Label(OverlayMenu, bg="black")
stream_display.pack(fill="both", expand=True)

style = ttk.Style()
style.theme_use('alt')
style.configure("TButton", foreground=TextColor, font=('Impact', 11), padding=10, background=ButtonColor)
style.configure("ColorButton.TButton", foreground=TextColor, font=('Impact', 8), padding=10, background=ButtonColor)

textstyle = ttk.Style()
textstyle.configure(
    "WarningText.TLabel",
    font=("Bold",16, "bold"),
    foreground=TextColor,
    background=ColorMode,
    wraplength=300,
    justify="left"
)

textstyle.configure(
    "ExplainText.TLabel",
    font=("Times New Roman",10),
    foreground=TextColor,
    background=ColorMode,
    wraplength=300,
    justify="left"
)

style.configure(
    "Scroll.TFrame", background=ColorMode
)

def DisplayClicked(Name):
    if Name == "Program Manager":
        messagebox.showinfo("Success", "Desktop" + " Was selected!")
    else:
        messagebox.showinfo("Success", Name + " Was selected!")
    
    OverlayMenu.deiconify()
    ChoosingMenu.withdraw()
    if Name == "Program Manager":
     OverlayMenu.title("Desktop"+" - Overlay")
     stream_to_label(stream_display, "Program Manager")
    else:
        OverlayMenu.title(Name+" - Overlay")
        stream_to_label(stream_display, Name)

for title in CurrentOpenWindows:
    if title == "Program Manager":
        windowlist.append("Desktop")
    else:
        windowlist.append(title)


def ColorChangeFunction():
    print(filecontents)
    if filecontents == "True":
        with open(filepath, "w") as file:
            file.write("False")
    if filecontents == "False":
        with open(filepath, "w") as file:
            file.write("True")
    messagebox.showinfo("Success", "Your change will appear next time this app is restarted.")

buttoncolor = ttk.Button(ChoosingMenu, text="Dark Mode/Light Mode", command=ColorChangeFunction, style="ColorButton.TButton")
buttoncolor.place(relx=1.0, rely=1.0, anchor="se", x=10, y=10)

Label = ttk.Label(ChoosingMenu,text="Welcome to Overlay-App, this project was made by one person with the goal of overlaying apps ontop of other apps, for convienince. This app does not have a ton of features, please expect possible bugs and be patient, if any issues occure please restart the app.", style="ExplainText.TLabel")
Label.pack(pady=10)

buttonlist = []

boundary = ttk.Frame(ChoosingMenu,style="Scroll.TFrame")
boundary.pack(fill="both", expand=True, pady=10)

canvas = Gui.Canvas(boundary, highlightthickness=0, bg=ColorMode)
scrollbar = ttk.Scrollbar(boundary, orient="vertical", command=canvas.yview)
scrollable_frame = Gui.Frame(canvas, bg=ColorMode)

canvas.bind('<Configure>', lambda event: canvas.itemconfig(canvas.create_window((0, 0), window=scrollable_frame, anchor="nw"), width=event.width))

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0,0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)

def Buttons():
    global buttonlist
    windowlist = []
    windowlist = windowfetch.getAllTitles()
    for button in buttonlist:
        button.destroy()

    buttonlist = []

    for i in windowlist:
        if not i == "":
            if not i == "Settings" and not i == "App Overlay":
                if i == "Program Manager":
                    button = ttk.Button(scrollable_frame, text="Desktop", command=lambda window=i: DisplayClicked(window), style="TButton")
                    button.pack(pady=10)
                    buttonlist.append(button)
                else:
                    button = ttk.Button(scrollable_frame, text=i, command=lambda window=i: DisplayClicked(window), style="TButton")
                    button.pack(pady=10)
                    buttonlist.append(button)

Buttons()

Label2 = ttk.Label(ChoosingMenu,text="Some things are disabled from being overlayed, such as settings.", style="WarningText.TLabel")
Label2.pack(side="bottom", anchor="sw",pady=10)

def Refreshes():
    Buttons()
    ChoosingMenu.after(5000, Refreshes)

def closing():
    OverlayMenu.destroy()
    ChoosingMenu.destroy()

ChoosingMenu.protocol("WM_DELETE_WINDOW", closing)
OverlayMenu.protocol("WM_DELETE_WINDOW", closing)

ChoosingMenu.after(5000, Refreshes)

ChoosingMenu.mainloop()
