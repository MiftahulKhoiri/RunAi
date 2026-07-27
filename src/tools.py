import os
import re
import datetime

PROJECT_ROOT = os.path.abspath("workspace")

def get_time():
    waktu = datetime.datetime.now().strftime("%A, %d %B %Y %H:%M:%S")
    return f"Waktu sistem saat ini adalah: {waktu}"

def create_file(filename: str, content: str) -> str:
    try:
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
    """Membaca isi file agar AI bisa merevisi kode yang sudah ada."""
    try:
        filepath = os.path.abspath(os.path.join(PROJECT_ROOT, filename))
        if not filepath.startswith(PROJECT_ROOT + os.sep):
            return "GAGAL: Akses ditolak."
        if not os.path.exists(filepath):
            return f"GAGAL: File '{filename}' tidak ditemukan."
        with open(filepath, "r", encoding="utf-8") as f:
            isi = f.read()
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

    # Gunakan .strip() agar aman dari spasi/enter yang tidak disengaja oleh AI
    tool_block = match.group(1).strip()

    if tool_block == "GET_TIME":
        return {"tool": "GET_TIME"}

    if tool_block.startswith("READ_FILE"):
        parts = tool_block.split("|")
        if len(parts) >= 2:
            return {"tool": "READ_FILE", "path": parts[1].strip()}

    if tool_block.startswith("LIST_DIR"):
        parts = tool_block.split("|")
        path = parts[1].strip() if len(parts) >= 2 else ""
        return {"tool": "LIST_DIR", "path": path}

    if tool_block.startswith("CREATE_FILE"):
        file_match = re.search(
            r"CREATE_FILE\s*\npath:\s*(.+?)\s*\n---BEGIN---\n(.*?)\n---END---",
            tool_block,
            re.DOTALL,
        )
        if file_match:
            return {
                "tool": "CREATE_FILE",
                "path": file_match.group(1).strip(),
                "content": file_match.group(2),
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
