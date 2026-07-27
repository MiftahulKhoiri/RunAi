import os
from src.config import N_CTX, N_THREADS

try:
    from llama_cpp import Llama
except ImportError:
    print("Error: Library 'llama-cpp-python' belum terinstal.")
    print("Silakan install dengan: CMAKE_ARGS=\"-DGGML_NATIVE=OFF\" pip install llama-cpp-python")
    exit(1)

def list_models(model_dir):
    """Mencari semua file berakhiran .gguf di direktori model."""
    models = []
    for f in os.listdir(model_dir):
        if f.lower().endswith(".gguf"):
            models.append(os.path.join(model_dir, f))
    return sorted(models)

def select_model(models):
    """Menampilkan antarmuka CLI untuk memilih model."""
    print("\nModel yang tersedia:")
    for i, model in enumerate(models):
        print(f"[{i + 1}] {os.path.basename(model)}")
    
    while True:
        try:
            choice = input("\nPilih nomor model yang ingin dijalankan (atau 'q' untuk keluar): ")
            if choice.lower() == 'q':
                return None
                
            choice_idx = int(choice)
            if 1 <= choice_idx <= len(models):
                return models[choice_idx - 1]
            else:
                print("Pilihan tidak valid. Silakan masukkan nomor yang benar.")
        except ValueError:
            print("Masukkan angka yang valid.")

def load_model(model_path):
    """Memuat model GGUF ke dalam memori menggunakan konfigurasi dari config.py"""
    try:
        return Llama(
            model_path=model_path,
            n_ctx=N_CTX,
            n_threads=N_THREADS,
            verbose=False    
        )
    except Exception as e:
        print(f"Error saat memuat model: {e}")
        return None
