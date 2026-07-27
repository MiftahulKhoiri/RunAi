def chat_loop(llm):
    """Menjalankan loop interaksi tanya-jawab dengan model."""
    print("="*50)
    print("Ketik 'exit', 'quit', atau 'keluar' untuk menghentikan program.")
    print("="*50)
    
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

        # Format prompt (Menyesuaikan dengan format Qwen)
        # Gunakan format ChatML yang umum dipakai Qwen3
        formatted_prompt = f"<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n"
        
        print("AI: ", end="", flush=True)
        
        try:
            # Gunakan mode streaming agar teks tampil per kata (seperti ChatGPT)
            stream = llm(
                formatted_prompt,
                max_tokens=512,      # Batas maksimal kata jawaban
                temperature=0.7,     # Tingkat kreativitas (0.1 kaku, 0.9 sangat kreatif)
                top_p=0.9,
                stop=["<|im_end|>", "<|endoftext|>"], # Token penghenti
                stream=True          # Stream aktif
            )
            
            for output in stream:
                text = output['choices'][0]['text']
                print(text, end="", flush=True)
            print() # Tambahkan baris baru setelah AI selesai menjawab
            
        except Exception as e:
            print(f"\n[Error saat generate teks: {e}]")
