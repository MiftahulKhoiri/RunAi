# ==========================================
# KONFIGURASI MODEL & CHAT
# ==========================================

# Batas ingatan AI (simpan 6 pasang interaksi terakhir)
# Ini sudah pas, tapi butuh N_CTX yang lebih besar agar tidak error
MAX_MEMORY = 6 

# Parameter Teks
MAX_TOKENS = 1024    # Diturunkan sedikit agar AI tidak terlalu memaksakan diri menulis panjang lebar
TEMPERATURE = 0.4    # Diturunkan agar AI lebih logis, fokus pada coding, dan tidak ngelantur
TOP_P = 0.9

# ==========================================
# KONFIGURASI HARDWARE (Raspberry Pi 5)
# ==========================================
N_CTX = 4096         # DITINGKATKAN: Kapasitas total memori bacaan (Prompt + Riwayat + Jawaban)
N_THREADS = 4        # Jumlah inti CPU yang digunakan (sudah optimal)

# ==========================================
# TAMPILAN TERMINAL
# ==========================================
COLOR_THINK = "\033[90m" # Warna abu-abu untuk proses berpikir
COLOR_RESET = "\033[0m"  # Reset ke warna terminal bawaan
