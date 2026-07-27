import os
from src.ui import clear_screen, display_logo
from src.load import list_models, select_model, load_model
from src.run import chat_loop

MODEL_DIR = "models"

def main():
    # 1. Bersihkan layar dan tampilkan logo saat pertama kali program dijalankan
    clear_screen()
    display_logo()
    
    # 2. Pastikan folder model ada
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        print(f"Folder '{MODEL_DIR}' telah dibuat.")
        print(f"Silakan pindahkan file .gguf Anda ke dalam folder '{MODEL_DIR}'.")
        return
    
    # 3. Pindai file model di folder models/
    models = list_models(MODEL_DIR)
    if not models:
        print(f"Tidak ada file .gguf ditemukan di folder '{MODEL_DIR}'.")
        print("Silakan download dan letakkan file GGUF Anda di sana.")
        return
    
    # 4. Pilih model melalui menu CLI
    selected_model_path = select_model(models)
    if not selected_model_path:
        return

    # 5. Muat model ke dalam RAM
    print(f"\nMemuat model: {os.path.basename(selected_model_path)}...")
    print("Harap tunggu, ini mungkin memakan waktu beberapa saat di RAM...")
    llm = load_model(selected_model_path)
    
    if llm:
        # 6. Bersihkan layar LAGI agar sesi chat terlihat sangat bersih dan elegan
        clear_screen()
        display_logo()
        
        print("\nModel berhasil dimuat! Memulai sesi percakapan...\n")
        # 7. Jalankan loop chat
        chat_loop(llm)
    else:
        print("\nGagal memuat model.")

if __name__ == "__main__":
    main()
