# ==========================================
# KONFIGURASI MODEL & CHAT
# ==========================================

# Batas ingatan AI (simpan 6 pasang interaksi terakhir)
MAX_MEMORY = 4

# Parameter Teks
# PENTING: MAX_TOKENS harus jauh lebih kecil dari N_CTX.
# N_CTX menampung system prompt + seluruh riwayat + input + output SEKALIGUS.
# Sebelumnya MAX_TOKENS == N_CTX (4096 == 4096), jadi begitu riwayat mulai
# terisi, tidak ada ruang tersisa untuk generate jawaban -> error context window.
MAX_TOKENS = 1024    # Cukup untuk jawaban + tool call
TEMPERATURE = 0.4    # Fokus pada coding, tidak ngelantur
TOP_P = 0.9

# ==========================================
# KONFIGURASI HARDWARE (Raspberry Pi 5)
# ==========================================
N_CTX = 8192         # Dinaikkan agar ada ruang cukup untuk histori + jawaban
N_THREADS = 4        # Jumlah inti CPU yang digunakan

# ==========================================
# TAMPILAN TERMINAL
# ==========================================
COLOR_THINK = "\033[90m" # Warna abu-abu untuk proses berpikir
COLOR_RESET = "\033[0m"  # Reset ke warna terminal bawaan