def chat_loop(llm):
    """Menjalankan loop interaksi tanya-jawab dengan model beserta memori sementara dan filter <think> yang diperbaiki."""
    print("="*50)
    print("Ketik 'exit', 'quit', atau 'keluar' untuk menghentikan program.")
    print("="*50)
    
    chat_history = []
    max_memory = 4 
    
    # SYSTEM PROMPT DIPERTEGAS: Memaksa model untuk disiplin menggunakan format
    system_prompt = (
        "<|im_start|>system\n"
        "Anda adalah asisten AI yang cerdas. Anda WAJIB menjabarkan proses berpikir Anda di dalam tag <think> dan </think>. "
        "Setelah menulis </think>, Anda harus memberikan jawaban akhir kepada pengguna dalam bahasa Indonesia yang baik dan natural.<|im_end|>\n"
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

        current_prompt = f"<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n"
        full_prompt = system_prompt + "".join(chat_history) + current_prompt
        
        try:
            stream = llm(
                full_prompt,
                max_tokens=1024,     # DITINGKATKAN: Agar AI tidak kehabisan kata saat berpikir
                temperature=0.6,     # Sedikit diturunkan agar AI lebih fokus dan tidak ngelantur
                top_p=0.9,
                stop=["<|im_end|>", "<|endoftext|>"], 
                stream=True          
            )
            
            full_response = ""
            buffer = ""
            state = "START" 
            
            for output in stream:
                chunk = output['choices'][0]['text']
                full_response += chunk
                buffer += chunk
                
                if state == "START":
                    if "<think>" in buffer:
                        state = "THINKING"
                        print(f"{COLOR_THINK}[Proses Berpikir]:\n", end="", flush=True)
                        buffer = buffer.split("<think>", 1)[1]
                    # Jika AI tidak mau berpikir dan langsung menjawab
                    elif len(buffer) > 10 and "<think>" not in buffer:
                        state = "ANSWERING"
                        print("AI = ", end="", flush=True)
                        print(buffer, end="", flush=True)
                        buffer = ""
                
                elif state == "THINKING":
                    if "</think>" in buffer:
                        state = "ANSWERING"
                        parts = buffer.split("</think>", 1)
                        print(parts[0], end="", flush=True) 
                        
                        print(f"{COLOR_RESET}\n\nAI = ", end="", flush=True) 
                        buffer = parts[1]
                    else:
                        if len(buffer) > 10:
                            to_print = buffer[:-10]
                            buffer = buffer[-10:]
                            print(to_print, end="", flush=True)
                
                elif state == "ANSWERING":
                    print(buffer, end="", flush=True)
                    buffer = ""
                    
            # PENANGANAN JIKA AI LUPA TAG PENUTUP ATAU TERPOTONG
            if buffer:
                if state == "START":
                    print("AI = " + buffer, end="", flush=True)
                elif state == "THINKING":
                    # Cetak sisa pikiran, lalu paksa transisi ke jawaban akhir
                    print(buffer, end="", flush=True)
                    print(f"{COLOR_RESET}\n\n[Peringatan: Proses berpikir terpotong/format tidak sempurna]")
                else:
                    print(buffer, end="", flush=True)
                    
            if state == "THINKING" or state == "START":
                print(COLOR_RESET, end="", flush=True)
                
            print() 
            
            completed_turn = current_prompt + full_response + "<|im_end|>\n"
            chat_history.append(completed_turn)
            
            if len(chat_history) > max_memory:
                chat_history.pop(0)
                
        except Exception as e:
            print(f"\n[Error saat generate teks: {e}]")
            print(COLOR_RESET, end="", flush=True) 
            if len(chat_history) > 0:
                chat_history.pop(0)
