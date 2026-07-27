def chat_loop(llm):
    """Menjalankan loop interaksi tanya-jawab dengan model beserta memori sementara."""
    print("="*50)
    print("Ketik 'exit', 'quit', atau 'keluar' untuk menghentikan program.")
    print("="*50)
    
    # Inisialisasi memori percakapan sementara
    # Variabel ini akan hilang dengan sendirinya saat program ditutup
    chat_history = []
    
    # Batas ingatan AI (simpan 4 pasang interaksi terakhir)
    # Jangan terlalu besar agar RAM 8GB dan context window (2048) tidak jebol
    max_memory = 4 
    
    # Instruksi dasar untuk AI
    system_prompt = "<|im_start|>system\nAnda adalah asisten AI yang cerdas, membantu, dan responsif. Jawablah menggunakan bahasa Indonesia yang baik.<|im_end|>\n"
    
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

        # Format input baru dari user
        current_prompt = f"<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n"
        
        # Gabungkan system prompt + riwayat chat + input terbaru
        full_prompt = system_prompt + "".join(chat_history) + current_prompt
        
        print("AI: ", end="", flush=True)
        
        try:
            stream = llm(
                full_prompt,
                max_tokens=512,      
                temperature=0.7,     
                top_p=0.9,
                stop=["<|im_end|>", "<|endoftext|>"], 
                stream=True          
            )
            
            # Variabel untuk menampung jawaban lengkap AI pada giliran ini
            full_response = ""
            
            for output in stream:
                text = output['choices'][0]['text']
                print(text, end="", flush=True)
                full_response += text
            print() # Baris baru setelah AI selesai menjawab
            
            # Simpan interaksi ini (pertanyaan Anda + jawaban AI) ke dalam memori
            completed_turn = current_prompt + full_response + "<|im_end|>\n"
            chat_history.append(completed_turn)
            
            # Jika memori sudah melebihi batas, hapus ingatan paling lama (index 0)
            if len(chat_history) > max_memory:
                chat_history.pop(0)
                
        except Exception as e:
            print(f"\n[Error saat generate teks: {e}]")
            # Jika terjadi error token (misal kepanjangan), kita hapus 1 riwayat tertua 
            # agar chat selanjutnya bisa berjalan normal lagi
            if len(chat_history) > 0:
                chat_history.pop(0)
