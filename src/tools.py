import os
import re
import datetime
import subprocess  # MODUL BARU UNTUK TERMINAL

PROJECT_ROOT = os.path.abspath("workspace")

def get_time():
    waktu = datetime.datetime.now().strftime("%A, %d %B %Y %H:%M:%S")
    return f"Waktu sistem saat ini adalah: {waktu}"

def create_file(filename: str, content: str) -> str:
    try:
        if not filename.strip():
            return "GAGAL: Nama file tidak boleh kosong."

        os.makedirs(PROJECT_ROOT, exist_ok=True)
        filepath = os.path.abspath(os.path.join(PROJECT_ROOT, filename))
        if not filepath.startswith(PROJECT_ROOT + os.sep):
            return f"GAGAL: path '{filename}' berada di luar folder 'workspace' yang diizinkan."

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content.strip())
        return f"SUKSES: File '{filename}' berhasil dibuat."
    except Exception as e:
        return f"GAGAL: {str(e)}"

def read_file(filename: str) -> str:
    try:
        filepath = os.path.abspath(os.path.join(PROJECT_ROOT, filename))
        if not filepath.startswith(PROJECT_ROOT + os.sep):
            return "GAGAL: Akses ditolak."
        if not os.path.exists(filepath):
            return f"GAGAL: File '{filename}' tidak ditemukan."

        max_bytes = 50 * 1024
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            isi = f.read(max_bytes)
            if len(isi) == max_bytes and f.read(1):
                isi += "\n\n[PERINGATAN: File terlalu panjang, sebagian teks dipotong]"

        return f"ISI FILE '{filename}':\n{isi}"
    except Exception as e:
        return f"GAGAL MEMBACA: {str(e)}"

def list_dir(subpath: str = "") -> str:
    try:
        target_dir = os.path.abspath(os.path.join(PROJECT_ROOT, subpath))
        if not target_dir.startswith(PROJECT_ROOT):
            return "GAGAL: Akses ditolak."
        if not os.path.exists(target_dir):
            return f"GAGAL: Folder '{subpath}' tidak ditemukan."
        items = os.listdir(target_dir)
        return f"ISI FOLDER '{subpath or 'workspace'}': {', '.join(items)}" if items else "Folder kosong."
    except Exception as e:
        return f"GAGAL: {str(e)}"

# --- FUNGSI BARU UNTUK MENJALANKAN PERINTAH ---
def run_command(command: str) -> str:
    try:
        # Jika perintah untuk menyalakan aplikasi/Flask, jalankan di background agar AI tidak freeze
        if "app.py" in command or "flask run" in command:
            process = subprocess.Popen(command, shell=True, cwd=PROJECT_ROOT)
            return f"SUKSES: Server '{command}' telah dijalankan di latar belakang (PID: {process.pid}). Silakan cek browser Anda di IP Raspberry Pi port 5000."
        else:
            # Perintah terminal biasa (seperti ls, pip install), tunggu sampai selesai
            result = subprocess.run(command, shell=True, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=15)
            output = result.stdout if result.stdout else result.stderr
            if not output:
                output = "Perintah berhasil dieksekusi tanpa pesan output."
            return f"HASIL PERINTAH:\n{output.strip()}"
    except subprocess.TimeoutExpired:
        return "GAGAL: Perintah memakan waktu terlalu lama (Timeout 15 detik)."
    except Exception as e:
        return f"GAGAL: {str(e)}"

def parse_tool_call(ai_output: str):
    match = re.search(r"<tool>(.*?)</tool>", ai_output, re.DOTALL)
    if not match:
        return None

    tool_block = match.group(1).strip()

    if tool_block == "GET_TIME":
        return {"tool": "GET_TIME"}

    if tool_block.startswith("READ_FILE"):
        parts = tool_block.split("|", 1)
        if len(parts) >= 2:
            path = parts[1].strip().strip('"\'')
            return {"tool": "READ_FILE", "path": path}

    if tool_block.startswith("LIST_DIR"):
        parts = tool_block.split("|", 1)
        path = parts[1].strip().strip('"\'') if len(parts) >= 2 else ""
        return {"tool": "LIST_DIR", "path": path}
        
    # --- DETEKSI TOOL BARU ---
    if tool_block.startswith("RUN_COMMAND"):
        parts = tool_block.split("|", 1)
        if len(parts) >= 2:
            return {"tool": "RUN_COMMAND", "command": parts[1].strip()}

    if "CREATE_FILE" in tool_block or "path:" in tool_block:
        path_str = ""
        content_str = ""
        
        if tool_block.startswith("CREATE_FILE|"):
            parts = tool_block.split("|", 2)
            if len(parts) >= 3:
                return {
                    "tool": "CREATE_FILE",
                    "path": parts[1].strip().strip('"\''),
                    "content": parts[2].strip()
                }

        path_match = re.search(r"(?:path:\s*|CREATE_FILE\s*\|?\s*)([a-zA-Z0-9_\-\./\\]+\.\w+)", tool_block)
        if path_match:
            path_str = path_match.group(1).strip().strip('"\'')
            
            content_match = re.search(r"---BEGIN---\s*(.*?)\s*(?:---END---|$)", tool_block, re.DOTALL)
            if content_match:
                content_str = content_match.group(1).strip()
            else:
                full_matched_path = path_match.group(0)
                parts = tool_block.split(full_matched_path, 1)
                if len(parts) > 1:
                    raw_content = parts[1].strip()
                    if raw_content.startswith("|"):
                        raw_content = raw_content[1:]
                    content_str = raw_content.strip()
                    
        if path_str and content_str:
            return {
                "tool": "CREATE_FILE",
                "path": path_str,
                "content": content_str
            }

    return None

def execute_tool(ai_output: str) -> str:
    tool_call = parse_tool_call(ai_output)
    if tool_call is None:
        return "Format tool salah atau perintah tidak dikenali."

    if tool_call["tool"] == "GET_TIME":
        return get_time()
    if tool_call["tool"] == "CREATE_FILE":
        return create_file(tool_call["path"], tool_call["content"])
    if tool_call["tool"] == "READ_FILE":
        return read_file(tool_call["path"])
    if tool_call["tool"] == "LIST_DIR":
        return list_dir(tool_call["path"])
    if tool_call["tool"] == "RUN_COMMAND": # EKSEKUSI ALAT BARU
        return run_command(tool_call["command"])

    return "Tool tidak dikenali."
