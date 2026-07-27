import os
from datetime import datetime

def get_time():
    """Mengembalikan waktu saat ini."""
    waktu = datetime.now().strftime("%A, %d %B %Y %H:%M:%S")
    return f"Waktu sistem saat ini adalah: {waktu}"

def create_file(filename, content):
    """Membuat file baru dengan isi tertentu di dalam folder 'workspace'."""
    try:
        # Kita buat folder khusus 'workspace' agar file buatan AI tidak berantakan
        os.makedirs("workspace", exist_ok=True)
        filepath = os.path.join("workspace", filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content.strip())
            
        return f"SUKSES: File '{filename}' berhasil dibuat di folder 'workspace'."
    except Exception as e:
        return f"GAGAL: Terjadi kesalahan saat membuat file - {str(e)}"
