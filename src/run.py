from src.config import MAX_MEMORY, MAX_TOKENS, TEMPERATURE, TOP_P, COLOR_THINK, COLOR_RESET
from src.prompts import SYSTEM_PROMPT, format_current_prompt, format_clean_history
from src.tools import execute_tool

TOOL_TAG_HOLDBACK = 10 

def chat_loop(llm):
    """Menjalankan loop interaksi dengan kemampuan AI Agent mandiri."""
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
            suppress_tool = False 

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
                    if not suppress_tool:
                        if "<tool" in buffer:
                            idx = buffer.find("<tool")
                            print(buffer[:idx], end="", flush=True)
                            buffer = buffer[idx:]
                            suppress_tool = True
                        elif len(buffer) > TOOL_TAG_HOLDBACK:
                            to_print = buffer[:-TOOL_TAG_HOLDBACK]
                            buffer = buffer[-TOOL_TAG_HOLDBACK:]
                            print(to_print, end="", flush=True)
                    else:
                        if "</tool>" in buffer:
                            suppress_tool = False
                            buffer = "" 

            if state == "THINKING":
                print(f"{COLOR_RESET}\n\n[AI kehabisan napas/bingung]")
            elif not suppress_tool and buffer:
                print(buffer, end="", flush=True)

            print()

            # 1. Bersihkan tag <think>
            if "</think>" in full_response:
                final_answer = full_response.split("</think>", 1)[1].strip()
            else:
                final_answer = full_response

            # 2. LOGIKA AGENT: Parsing & Eksekusi Tool
            tool_observation = None
            if "<tool>" in final_answer and "</tool>" in final_answer:
                print(f"\n\033[93m⚡ [AGENT MENGEKSEKUSI TOOL]\033[0m")
                tool_observation = execute_tool(final_answer)
                print(f"\033[92m✅ [HASIL SISTEM]: {tool_observation}\033[0m\n")

            # 3. Simpan Riwayat Sesi Pertama
            clean_turn = format_clean_history(user_input, final_answer, tool_observation)
            chat_history.append(clean_turn)

            # 4. RESPONS OTOMATIS: Berikan kesempatan AI merespons hasil eksekusi tool
            if tool_observation:
                followup_prompt = SYSTEM_PROMPT + "".join(chat_history) + f"<|im_start|>user\n[SISTEM]: Hasil eksekusi tool: {tool_observation}. Berikan tanggapan singkat ke pengguna.<|im_end|>\n<|im_start|>assistant\n"
                
                print(f"AI = ", end="", flush=True)
                followup_stream = llm(
                    followup_prompt,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                    stop=["<|im_end|>", "<|endoftext|>"],
                    stream=True
                )
                
                followup_text = ""
                for output in followup_stream:
                    chunk = output['choices'][0]['text']
                    print(chunk, end="", flush=True)
                    followup_text += chunk
                print()
                
                # Simpan tanggapan akhir ke memori
                chat_history.append(f"<|im_start|>assistant\n{followup_text}<|im_end|>\n")

            if len(chat_history) > MAX_MEMORY:
                chat_history.pop(0)

        except Exception as e:
            print(f"\n[Error saat generate teks: {e}]")
            print(COLOR_RESET, end="", flush=True)
            if len(chat_history) > 0:
                chat_history.pop(0)
