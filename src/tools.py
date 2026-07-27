import os
import re
import datetime

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
    """Membaca isi file dengan batas maksimal 50KB agar aman di RAM."""
    try:
        filepath = os.path.abspath(os.path.join(PROJECT_ROOT, filename))
        if not filepath.startswith(PROJECT_ROOT + os.sep):
            return "GAGAL: Akses ditolak."
        if not os.path.exists(filepath):
            return f"GAGAL: File '{filename}' tidak ditemukan."

        max_bytes = 50 * 1024
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            isi = f.read(max_bytes)
            # Cek apakah masih ada sisa data (file lebih besar dari max_bytes)
            if len(isi) == max_bytes and f.read(1):
                isi += "\n\n[PERINGATAN: File terlalu panjang, sebagian teks dipotong]"

        return f"ISI FILE '{filename}':\n{isi}"
    except Exception as e:
        return f"GAGAL MEMBACA: {str(e)}"

def list_dir(subpath: str = "") -> str:
    """Melihat daftar file/folder di dalam workspace."""
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

def parse_tool_call(ai_output: str):
    match = re.search(r"<tool>(.*?)</tool>", ai_output, re.DOTALL)
    if not match:
        return None

    tool_block = match.group(1).strip()

    # --- Deteksi GET_TIME ---
    if tool_block == "GET_TIME":
        return {"tool": "GET_TIME"}

    # --- Deteksi READ_FILE ---
    if tool_block.startswith("READ_FILE"):
        parts = tool_block.split("|", 1)
        if len(parts) >= 2:
            path = parts[1].strip().strip('"\'')
            return {"tool": "READ_FILE", "path": path}

    # --- Deteksi LIST_DIR ---
    if tool_block.startswith("LIST_DIR"):
        parts = tool_block.split("|", 1)
        path = parts[1].strip().strip('"\'') if len(parts) >= 2 else ""
        return {"tool": "LIST_DIR", "path": path}

    # --- Deteksi CREATE_FILE ---
    if "CREATE_FILE" in tool_block or "path:" in tool_block:
        path_str = ""
        content_str = ""
        
        # 1. Coba deteksi format PIPE (CREATE_FILE|nama_file|isi_kode)
        if tool_block.startswith("CREATE_FILE|"):
            parts = tool_block.split("|", 2)
            if len(parts) >= 3:
                return {
                    "tool": "CREATE_FILE",
                    "path": parts[1].strip().strip('"\''),
                    "content": parts[2].strip()
                }

        # 2. Jika gagal, coba deteksi format panjang (path: dan ---BEGIN---)
        path_match = re.search(r"(?:path:\s*|CREATE_FILE\s*\|?\s*)([a-zA-Z0-9_\-\./\\]+\.\w+)", tool_block)
        
        if path_match:
            path_str = path_match.group(1).strip().strip('"\'')
            
            content_match = re.search(r"---BEGIN---\s*(.*?)\s*(?:---END---|$)", tool_block, re.DOTALL)
            if content_match:
                content_str = content_match.group(1).strip()
            else:
                # Ambil semua teks yang ada setelah nama file sebagai kode
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

    return "Tool tidak dikenali."
