import time
import shutil
import os
import subprocess
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

sumber = r"C:\10LBinB"
tujuan = r"\\172.16.104.18\for_PEBMT\Prism Inspection Log (Jangan Di Hapus)\BIB\Packing Step 2"
server_ip = "172.16.104.18"

log_file = r"D:\Log Script\autocopy.log"

# =========================
# SETUP LOGGING
# =========================
logger = logging.getLogger("AutoCopy")
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(
    log_file,
    maxBytes=5*1024*1024,  # 5MB
    backupCount=3
)

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)

handler.setFormatter(formatter)
logger.addHandler(handler)

console = logging.StreamHandler()
console.setFormatter(formatter)
logger.addHandler(console)

# =========================
# FUNCTIONS
# =========================
def cek_ping(ip):
    try:
        result = subprocess.run(
            ["ping", "-n", "1", ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
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
while True:
    try:
        logger.info("===================================")
        logger.info("Mulai proses")

        # 1️⃣ Cek folder sumber
        if not os.path.exists(sumber):
            logger.error(f"Folder sumber tidak ditemukan! -> {sumber}")
            time.sleep(900)
            continue

        # 2️⃣ Cek koneksi server
        if not cek_ping(server_ip):
            logger.error("Gagal terhubung ke jaringan!")
            time.sleep(900)
            continue

        # 3️⃣ Cek folder tujuan
        if not os.path.exists(tujuan):
            logger.error(f"Folder tujuan tidak ditemukan! -> {tujuan}")
            time.sleep(900)
            continue

        # 4️⃣ Logic hapus file sesuai jam
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

        # 5️⃣ Ambil file terbaru
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