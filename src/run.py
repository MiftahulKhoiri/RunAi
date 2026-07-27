def chat_loop(llm):
    """Menjalankan loop interaksi tanya-jawab dengan model beserta memori sementara dan filter <think>."""
    print("="*50)
    print("Ketik 'exit', 'quit', atau 'keluar' untuk menghentikan program.")
    print("="*50)
    
    chat_history = []
    max_memory = 4 
    
    system_prompt = "<|im_start|>system\nAnda adalah asisten AI yang cerdas, membantu, dan responsif. Jawablah menggunakan bahasa Indonesia yang baik.<|im_end|>\n"
    
    # Kode Warna ANSI untuk Terminal
    COLOR_THINK = "\033[90m" # Warna abu-abu gelap untuk proses berpikir
    COLOR_RESET = "\033[0m"  # Reset ke warna terminal bawaan
    
    while True:
        try:
            user_input = input("\nAnda: ")
        except (KeyboardInterrupt, EOFError):
            print("\nSesi diakhiri secara paksa.")
            break
            
        if user_input.lower() in ['exit', 'keluar', 'quit']:
            print("Sesi diakhiri. Sampai jumpa!")
            break
        
        if not user_input.strip():
            continue

        current_prompt = f"<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n"
        full_prompt = system_prompt + "".join(chat_history) + current_prompt
        
        try:
            stream = llm(
                full_prompt,
                max_tokens=512,      
                temperature=0.7,     
                top_p=0.9,
                stop=["<|im_end|>", "<|endoftext|>"], 
                stream=True          
            )
            
            full_response = ""
            buffer = ""
            state = "START" # Status deteksi: START, THINKING, ANSWERING
            
            for output in stream:
                chunk = output['choices'][0]['text']
                full_response += chunk
                buffer += chunk
                
                # --- STATE 1: Mengecek apakah AI mulai dengan <think> ---
                if state == "START":
                    if "<think>" in buffer:
                        state = "THINKING"
                        print(f"{COLOR_THINK}[Proses Berpikir]:\n", end="", flush=True)
                        # Buang tag <think> dari layar
                        buffer = buffer.split("<think>", 1)[1]
                    elif len(buffer) > 7 and "<think>" not in buffer:
                        # Jika sudah lewat 7 karakter dan tidak ada <think>, berarti AI langsung menjawab
                        state = "ANSWERING"
                        print("AI = ", end="", flush=True)
                        print(buffer, end="", flush=True)
                        buffer = ""
                
                # --- STATE 2: Menampilkan proses berpikir dengan warna Abu-abu ---
                elif state == "THINKING":
                    if "</think>" in buffer:
                        state = "ANSWERING"
                        parts = buffer.split("</think>", 1)
                        print(parts[0], end="", flush=True) # Cetak sisa pikiran sebelum tag penutup
                        
                        # Kembalikan warna ke normal dan cetak awalan jawaban
                        print(f"{COLOR_RESET}\n\nAI = ", end="", flush=True) 
                        buffer = parts[1]
                    else:
                        # Tahan 8 karakter terakhir di memori visual jaga-jaga tag </think> terpotong saat streaming
                        if len(buffer) > 8:
                            to_print = buffer[:-8]
                            buffer = buffer[-8:]
                            print(to_print, end="", flush=True)
                
                # --- STATE 3: Menampilkan jawaban utama secara normal ---
                elif state == "ANSWERING":
                    print(buffer, end="", flush=True)
                    buffer = ""
                    
            # Bersihkan sisa karakter di buffer jika AI sudah selesai bicara
            if buffer:
                if state == "START":
                    print("AI = " + buffer, end="", flush=True)
                else:
                    print(buffer, end="", flush=True)
                    
            # Pastikan warna terminal kembali normal meskipun AI "lupa" memberi tag </think> (sering terjadi jika max_tokens habis)
            if state == "THINKING":
                print(COLOR_RESET, end="", flush=True)
                
            print() # Tambahkan jarak baris baru
            
            # Simpan riwayat lengkap (termasuk tag <think> mentah) agar AI ingat alur logikanya sendiri
            completed_turn = current_prompt + full_response + "<|im_end|>\n"
            chat_history.append(completed_turn)
            
            if len(chat_history) > max_memory:
                chat_history.pop(0)
                
        except Exception as e:
            print(f"\n[Error saat generate teks: {e}]")
            print(COLOR_RESET, end="", flush=True) 
            if len(chat_history) > 0:
                chat_history.pop(0)
