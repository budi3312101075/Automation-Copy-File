# ---- > MENCEGAH DOUBLE INSTANCE PROGRAM BERJALAN < ---- # 
import sys
import ctypes

mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "AutoCopyMutex")
if ctypes.windll.kernel32.GetLastError() == 183:
    sys.exit(0)

# ---- > SCRIPT PROGRAM < ---- # 
import time
import shutil
import os
import subprocess
import logging
import threading
import tkinter as tk
from tkinter import messagebox
from logging.handlers import RotatingFileHandler
from datetime import datetime

import pystray
from PIL import Image, ImageDraw

sumber = r"D:\TES-SCRIPT"
tujuan = r"\\172.16.112.10\shared\TES SCRIPT"
server_ip = "172.16.112.10"

log_file = r"D:\TES-SCRIPT\log\autocopylog.txt"

# =========================
# LOGGING
# =========================
logger = logging.getLogger("AutoCopy")
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(
    log_file,
    maxBytes=5*1024*1024,
    backupCount=3
)

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)

handler.setFormatter(formatter)
logger.addHandler(handler)

# =========================
# FUNCTIONS
# =========================
def cek_ping(ip):
    try:
        result = subprocess.run(
            ["ping", "-n", "1", ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Ping error: {e}")
        return False

def hapus_file_lama(folder):
    try:
        for file in os.listdir(folder):
            file_path = os.path.join(folder, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        logger.info("File lama berhasil dihapus.")
    except Exception as e:
        logger.error(f"Error saat hapus file: {e}")

# =========================
# MAIN LOOP
# =========================
def main_loop():
    while True:
        try:
            logger.info("===================================")
            logger.info("Mulai proses")

            if not os.path.exists(sumber):
                logger.error(f"Folder sumber tidak ditemukan! -> {sumber}")
                time.sleep(900)
                continue

            if not cek_ping(server_ip):
                logger.error("Gagal terhubung ke jaringan!")
                time.sleep(900)
                continue

            if not os.path.exists(tujuan):
                logger.error(f"Folder tujuan tidak ditemukan! -> {tujuan}")
                time.sleep(900)
                continue

            now = datetime.now()
            jam = now.hour
            menit = now.minute

            logger.info(f"DEBUG: JAM = {jam}, MENIT = {menit}")

            if jam == 0:
                if menit >= 10:
                    logger.info("Menghapus file lama...")
                    hapus_file_lama(tujuan)
            elif jam >= 1:
                logger.info("Menghapus file lama...")
                hapus_file_lama(tujuan)

            files = sorted(
                [f for f in os.listdir(sumber) if os.path.isfile(os.path.join(sumber, f))],
                key=lambda x: os.path.getmtime(os.path.join(sumber, x)),
                reverse=True
            )

            if files:
                terbaru = files[0]
                logger.info(f"Menyalin file terbaru: {terbaru}")
                shutil.copy2(
                    os.path.join(sumber, terbaru),
                    os.path.join(tujuan, terbaru)
                )
                logger.info("File berhasil dicopy!")
            else:
                logger.warning("Tidak ada file ditemukan di folder sumber!")

        except Exception as e:
            logger.exception(f"Error besar: {e}")

        logger.info("Tunggu 15 menit...\n")
        time.sleep(900)


# =========================
# TKINTER UI - MAIN THREAD
# =========================

# Antrian perintah dari tray ke main thread
pending_action = None
action_lock = threading.Lock()

def request_action(action_name):
    """Dipanggil dari tray thread untuk minta UI action ke main thread."""
    global pending_action
    with action_lock:
        pending_action = action_name

def process_pending_actions():
    """Loop ini jalan di main thread via root.after()."""
    global pending_action
    with action_lock:
        action = pending_action
        pending_action = None

    if action == "show_window":
        _do_show_window()
    elif action == "show_about":
        _do_show_about()
    elif action == "exit":
        _do_exit()

    root.after(100, process_pending_actions)  # cek lagi 100ms kemudian

def _do_show_window():
    root.deiconify()
    root.lift()
    root.focus_force()

def _do_show_about():
    # Pastikan window tidak sedang hidden saat about dibuka
    messagebox.showinfo(
        "About",
        "Auto Copy System\nVersion 1.0\nCopyright: PT Epson Batam (IK Engineering)"
    )

def _do_exit():
    icon.stop()
    root.destroy()
    os._exit(0)

def on_close_window():
    """Tombol X hanya menyembunyikan window, tidak menutup app."""
    root.withdraw()


# =========================
# TRAY ICON
# =========================
def create_image():
    img = Image.new("RGB", (64, 64), "black")
    d = ImageDraw.Draw(img)
    d.rectangle((16, 16, 48, 48), fill="white")
    return img

def tray_show_window(icon, item):
    request_action("show_window")

def tray_show_about(icon, item):
    request_action("show_about")

def tray_exit(icon, item):
    request_action("exit")

tray_menu = pystray.Menu(
    pystray.MenuItem("Open", tray_show_window),
    pystray.MenuItem("About", tray_show_about),
    pystray.MenuItem("Exit", tray_exit)
)

icon = pystray.Icon(
    "AutoCopy",
    create_image(),
    "Auto Copy System",
    tray_menu
)

# =========================
# START
# =========================

# Background thread: logic copy
threading.Thread(target=main_loop, daemon=True).start()

# Background thread: tray icon
threading.Thread(target=icon.run, daemon=True).start()

# Main thread: Tkinter
root = tk.Tk()
root.title("Auto Copy System")
root.geometry("300x150")
root.protocol("WM_DELETE_WINDOW", on_close_window)

label = tk.Label(root, text="Auto Copy Running\nVersion 1.0")
label.pack(expand=True)

# Sembunyikan window saat pertama kali (langsung ke tray)
root.withdraw()

# Mulai polling action dari tray
root.after(100, process_pending_actions)

# Jalankan main loop Tkinter di main thread
root.mainloop()