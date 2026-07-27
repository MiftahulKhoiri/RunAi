import os
from src.load import list_models, select_model, load_model
from src.run import chat_loop

MODEL_DIR = "models"

def main():
    print("=== AI Model Runner - Raspberry Pi 5 ===")
    
    # Pastikan folder model ada
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        print(f"Folder '{MODEL_DIR}' telah dibuat.")
        print(f"Silakan pindahkan file .gguf Anda ke dalam folder '{MODEL_DIR}'.")
        return
    
    # Pindai file model di folder models/
    models = list_models(MODEL_DIR)
    if not models:
        print(f"Tidak ada file .gguf ditemukan di folder '{MODEL_DIR}'.")
        print("Silakan download dan letakkan file GGUF Anda di sana.")
        return
    
    # Pilih model
    selected_model_path = select_model(models)
    if not selected_model_path:
        return

    # Muat model
    print(f"\nMemuat model: {os.path.basename(selected_model_path)}...")
    print("Harap tunggu, ini mungkin memakan waktu beberapa saat di RAM...")
    llm = load_model(selected_model_path)
    
    if llm:
        print("\nModel berhasil dimuat! Memulai sesi inference...\n")
        # Jalankan loop chat
        chat_loop(llm)
    else:
        print("\nGagal memuat model.")

if __name__ == "__main__":
    main()
