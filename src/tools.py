import os
import re
import datetime

PROJECT_ROOT = os.path.abspath("workspace")


def get_time():
    """Mengembalikan waktu saat ini."""
    waktu = datetime.datetime.now().strftime("%A, %d %B %Y %H:%M:%S")
    return f"Waktu sistem saat ini adalah: {waktu}"


def create_file(filename: str, content: str) -> str:
    """Membuat/menimpa file di dalam folder 'workspace', dengan proteksi path traversal."""
    try:
        os.makedirs(PROJECT_ROOT, exist_ok=True)

        # Gabung manual dulu, baru divalidasi — jangan andalkan os.path.join
        # untuk menahan filename absolut, karena itu akan diabaikan.
        filepath = os.path.abspath(os.path.join(PROJECT_ROOT, filename))

        if not filepath.startswith(PROJECT_ROOT + os.sep):
            return f"GAGAL: path '{filename}' berada di luar folder 'workspace' yang diizinkan."

        os.makedirs(os.path.dirname(filepath), exist_ok=True)  # dukung subfolder

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content.strip())

        return f"SUKSES: File '{filename}' berhasil dibuat di folder 'workspace'."
    except Exception as e:
        return f"GAGAL: Terjadi kesalahan saat membuat file - {str(e)}"


def parse_tool_call(ai_output: str):
    """Ekstrak tool call dari output mentah model."""
    match = re.search(r"<tool>(.*?)</tool>", ai_output, re.DOTALL)
    if not match:
        return None

    tool_block = match.group(1).strip()

    if tool_block == "GET_TIME":
        return {"tool": "GET_TIME"}

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
    """Dispatcher: parse output AI lalu jalankan tool yang sesuai."""
    tool_call = parse_tool_call(ai_output)
    if tool_call is None:
        return "Format tool salah atau perintah tidak dikenali."

    if tool_call["tool"] == "GET_TIME":
        return get_time()

    if tool_call["tool"] == "CREATE_FILE":
        return create_file(tool_call["path"], tool_call["content"])

    return "Tool tidak dikenali."