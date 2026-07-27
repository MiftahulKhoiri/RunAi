# Instruksi utama yang mendikte kepribadian dan aturan AI
SYSTEM_PROMPT = (
    "<|im_start|>system\n"
    "Anda adalah asisten AI berbahasa Indonesia. Anda wajib berpikir terlebih dahulu, "
    "lalu memberikan jawaban akhir yang ramah, singkat, dan tepat sasaran.<|im_end|>\n"
)

def format_current_prompt(user_input):
    """Memformat input pengguna dan langsung memancing AI dengan tag <think>"""
    return f"<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n<think>\n"

def format_clean_history(user_input, final_answer):
    """Menyimpan riwayat tanpa tag <think> agar ingatan AI tetap bersih"""
    return f"<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n{final_answer}<|im_end|>\n"
