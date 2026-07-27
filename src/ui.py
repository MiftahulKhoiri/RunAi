import os

def clear_screen():
    """Membersihkan layar terminal (Mendukung Linux/Mac/Windows)."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_logo():
    """Menampilkan logo ASCII yang keren saat aplikasi dimulai."""
    # Menggunakan warna Cyan (\033[96m) agar terlihat futuristik
    logo = r"""
     █████╗ ██╗    ██████╗  ██████╗  ██████╗ ████████╗
    ██╔══██╗██║    ██╔══██╗██╔═══██╗██╔═══██╗╚══██╔══╝
    ███████║██║    ██████╔╝██║   ██║██║   ██║   ██║   
    ██╔══██║██║    ██╔══██╗██║   ██║██║   ██║   ██║   
    ██║  ██║██║    ██████╔╝╚██████╔╝╚██████╔╝   ██║   
    ╚═╝  ╚═╝╚═╝    ╚═════╝  ╚═════╝  ╚═════╝    ╚═╝   
    ==================================================
          ASISTEN AI LOKAL - RASPBERRY PI 5 (8GB)
    ==================================================
    """
    print(f"\033[96m{logo}\033[0m")
