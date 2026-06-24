# Main python file for the overlay app project
# Current Revision: 1
import ctypes
import ctypes.wintypes
import numpy as np
import cv2
import pygetwindow as windowfetch
import tkinter as Gui
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk

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
ChoosingMenu.configure(bg="#313131")

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
style.theme_use('clam')
style.configure("TButton", foreground="#FFFFFF", font=('Impact', 11), padding=10, background="#5C5C5C")


def DisplayClicked(Name):
    messagebox.showinfo("Success", Name + " Was selected!")
    OverlayMenu.deiconify()
    ChoosingMenu.withdraw()
    OverlayMenu.title(Name+" - Overlay")
    stream_to_label(stream_display, Name)

for title in CurrentOpenWindows:
    if not title == "":
        windowlist.append(title)

for i in windowlist:
    button = ttk.Button(ChoosingMenu, text=i, command=lambda window=i: DisplayClicked(window), style="TButton")
    button.pack(pady=10)

ChoosingMenu.mainloop()