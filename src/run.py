def chat_loop(llm):
    """Menjalankan loop interaksi dengan Llama-cpp, filter <think>, dan memori yang bersih."""
    print("="*50)
    print("Ketik 'exit', 'quit', atau 'keluar' untuk menghentikan program.")
    print("="*50)
    
    chat_history = []
    max_memory = 4 
    
    # System prompt yang sangat ketat untuk memaksa format Llama/Qwen
    system_prompt = (
        "<|im_start|>system\n"
        "Anda adalah asisten AI berbahasa Indonesia. Anda wajib berpikir terlebih dahulu, "
        "lalu memberikan jawaban akhir yang ramah, singkat, dan tepat sasaran.<|im_end|>\n"
    )
    
    COLOR_THINK = "\033[90m" 
    COLOR_RESET = "\033[0m"  
    
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

        # KUNCI UTAMA: Kita memancing AI dengan menuliskan <think> agar ia langsung masuk mode berpikir
        current_prompt = f"<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n<think>\n"
        full_prompt = system_prompt + "".join(chat_history) + current_prompt
        
        try:
            stream = llm(
                full_prompt,
                max_tokens=1024,     
                temperature=0.6,     
                top_p=0.9,
                stop=["<|im_end|>", "<|endoftext|>"], 
                stream=True          
            )
            
            # Kita set otomatis state ke THINKING karena sudah kita pancing di current_prompt
            state = "THINKING" 
            buffer = ""
            full_response = "<think>\n" 
            
            print(f"{COLOR_THINK}[Proses Berpikir]:\n", end="", flush=True)
            
            for output in stream:
                chunk = output['choices'][0]['text']
                full_response += chunk
                buffer += chunk
                
                if state == "THINKING":
                    if "</think>" in buffer:
                        state = "ANSWERING"
                        parts = buffer.split("</think>", 1)
                        print(parts[0], end="", flush=True) # Cetak ujung kalimat berpikir
                        
                        # Transisi ke jawaban
                        print(f"{COLOR_RESET}\n\nAI = ", end="", flush=True)
                        buffer = parts[1]
                    else:
                        # Tahan 9 karakter (panjang kata "</think>") di buffer
                        if len(buffer) > 9:
                            to_print = buffer[:-9]
                            buffer = buffer[-9:]
                            print(to_print, end="", flush=True)
                            
                elif state == "ANSWERING":
                    print(buffer, end="", flush=True)
                    buffer = ""
                    
            # Jika AI berhenti generate sebelum menulis </think> (Sering terjadi di model kecil)
            if state == "THINKING":
                print(buffer, end="", flush=True)
                print(f"{COLOR_RESET}\n\n[Peringatan: AI kehabisan napas/bingung dan gagal memberikan jawaban akhir]")
            elif state == "ANSWERING" and buffer:
                print(buffer, end="", flush=True)
                
            print() 
            
            # PEMBERSIHAN MEMORI: Kita hapus isi <think> sebelum disimpan ke riwayat
            if "</think>" in full_response:
                final_answer = full_response.split("</think>", 1)[1].strip()
            else:
                final_answer = "(AI gagal menjawab dengan baik)"
                
            # Hanya simpan input Anda dan jawaban akhir AI (tanpa tag <think>)
            clean_turn = f"<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n{final_answer}<|im_end|>\n"
            chat_history.append(clean_turn)
            
            if len(chat_history) > max_memory:
                chat_history.pop(0)
                
        except Exception as e:
            print(f"\n[Error saat generate teks: {e}]")
            print(COLOR_RESET, end="", flush=True) 
            if len(chat_history) > 0:
                chat_history.pop(0)
