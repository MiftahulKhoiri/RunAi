# ==========================================
# KONFIGURASI MODEL & CHAT
# ==========================================

# Batas ingatan AI (simpan 4 pasang interaksi terakhir)
MAX_MEMORY = 6 

# Parameter Teks
MAX_TOKENS = 2048   # Batas panjang kata AI
TEMPERATURE = 0.8    # Kreativitas (0.1 kaku, 0.9 kreatif)
TOP_P = 0.9

# ==========================================
# KONFIGURASI HARDWARE (Raspberry Pi 5)
# ==========================================
N_CTX = 2048         # Context window (memori RAM untuk membaca teks)
N_THREADS = 4        # Jumlah inti CPU yang digunakan

# ==========================================
# TAMPILAN TERMINAL
# ==========================================
COLOR_THINK = "\033[90m" # Warna abu-abu untuk proses berpikir
COLOR_RESET = "\033[0m"  # Reset ke warna terminal bawaan
