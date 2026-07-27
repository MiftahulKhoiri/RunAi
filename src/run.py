from src.config import MAX_MEMORY, MAX_TOKENS, TEMPERATURE, TOP_P, COLOR_THINK, COLOR_RESET
from src.prompts import SYSTEM_PROMPT, format_current_prompt, format_clean_history
from src.tools import get_time, create_file

def chat_loop(llm):
    """Menjalankan loop interaksi dengan kemampuan AI Agent."""
    print("="*50)
    print("Ketik 'exit', 'quit', atau 'keluar' untuk menghentikan program.")
    print("="*50)
    
    chat_history = []
    
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

        current_prompt = format_current_prompt(user_input)
        full_prompt = SYSTEM_PROMPT + "".join(chat_history) + current_prompt
        
        try:
            stream = llm(
                full_prompt,
                max_tokens=MAX_TOKENS,     
                temperature=TEMPERATURE,     
                top_p=TOP_P,
                stop=["<|im_end|>", "<|endoftext|>"], 
                stream=True          
            )
            
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
                        print(parts[0], end="", flush=True)
                        
                        print(f"{COLOR_RESET}\n\nAI = ", end="", flush=True)
                        buffer = parts[1]
                    else:
                        if len(buffer) > 9:
                            to_print = buffer[:-9]
                            buffer = buffer[-9:]
                            print(to_print, end="", flush=True)
                            
                elif state == "ANSWERING":
                    # Agar tidak mencetak format tool ke layar saat streaming, kita deteksi '<tool'
                    if "<tool" not in buffer:
                        print(buffer, end="", flush=True)
                        buffer = ""
                    elif "</tool>" in buffer:
                        # Jangan cetak tag tool, reset buffer
                        buffer = ""
                    
            if state == "THINKING":
                print(f"{COLOR_RESET}\n\n[AI kehabisan napas/bingung]")
                
            print() 
            
            # 1. Bersihkan tag <think>
            if "</think>" in full_response:
                final_answer = full_response.split("</think>", 1)[1].strip()
            else:
                final_answer = full_response

            # 2. LOGIKA AGENT: Deteksi dan Jalankan Tool
            tool_observation = None
            if "<tool>" in final_answer and "</tool>" in final_answer:
                tool_data = final_answer.split("<tool>")[1].split("</tool>")[0]
                parts = tool_data.split("|")
                command = parts[0]
                
                print(f"\n\033[93m⚡ [AGENT MENGEKSEKUSI TOOL: {command}]\033[0m")
                
                if command == "GET_TIME":
                    tool_observation = get_time()
                elif command == "CREATE_FILE" and len(parts) >= 3:
                    filename = parts[1]
                    content = "|".join(parts[2:]) # Gabungkan kembali jika ada karakter | di isi kode
                    tool_observation = create_file(filename, content)
                else:
                    tool_observation = "Format tool salah atau perintah tidak dikenali."
                
                print(f"\033[92m✅ [HASIL SISTEM]: {tool_observation}\033[0m\n")

            # 3. Simpan Riwayat
            clean_turn = format_clean_history(user_input, final_answer, tool_observation)
            chat_history.append(clean_turn)
            
            if len(chat_history) > MAX_MEMORY:
                chat_history.pop(0)
                
        except Exception as e:
            print(f"\n[Error saat generate teks: {e}]")
            print(COLOR_RESET, end="", flush=True) 
            if len(chat_history) > 0:
                chat_history.pop(0)
