import time
from src.config import MAX_MEMORY, MAX_TOKENS, TEMPERATURE, TOP_P, COLOR_THINK, COLOR_RESET
from src.tools import execute_tool
from src.prompts import SYSTEM_PROMPT, format_current_prompt, format_clean_history

TOOL_TAG_HOLDBACK = 10  # Margin karakter untuk mengamankan tag <tool yang terpotong chunk

def chat_loop(llm):
    """Menjalankan loop interaksi CLI dengan tampilan yang rapi dan elegan."""
    print("=" * 50)
    print("  ASISTEN AI LOKAL - RASPBERRY PI 5 (AGENT MODE)")
    print("  Ketik 'exit', 'quit', atau 'keluar' untuk menghentikan.")
    print("=" * 50)

    chat_history = []

    while True:
        try:
            user_input = input("\n\033[92mAnda:\033[0m ")
        except (KeyboardInterrupt, EOFError):
            print("\n\nSesi diakhiri secara paksa. Sampai jumpa!")
            break

        if user_input.lower() in ['exit', 'keluar', 'quit']:
            print("\nSesi diakhiri. Sampai jumpa!")
            break

        if not user_input.strip():
            continue

        # 1. Susun prompt lengkap
        current_prompt = format_current_prompt(user_input)
        full_prompt = SYSTEM_PROMPT + "".join(chat_history) + current_prompt

        try:
            start_time = time.time()

            # 2. Generate stream dari model
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
            full_response = ""
            suppress_tool = False

            print(f"\n{COLOR_THINK}[Proses Berpikir]:", flush=True)

            for output in stream:
                chunk = output['choices'][0]['text']
                full_response += chunk
                buffer += chunk

                if state == "THINKING":
                    if "</think>" in buffer:
                        state = "ANSWERING"
                        parts = buffer.split("</think>", 1)
                        # Cetak sisa teks berpikir sebelum tag penutup
                        print(parts[0], end="", flush=True)
                        
                        # Transisi bersih ke mode jawaban
                        print(f"{COLOR_RESET}\n\n\033[96mAI =\033[0m", end=" ", flush=True)
                        buffer = parts[1]
                    else:
                        # Tahan 9 karakter terakhir agar tag </think> tidak terpotong di tengah chunk
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
                            parts = buffer.split("</tool>", 1)
                            if len(parts) > 1 and parts[1]:
                                print(parts[1], end="", flush=True)
                            buffer = ""
                            suppress_tool = False

            # 3. Pembersihan akhir buffer stream utama
            if state == "THINKING":
                # Jika model mendadak selesai tanpa menutup tag </think>
                print(f"{COLOR_RESET}\n\n\033[96mAI =\033[0m", end=" ", flush=True)
                print(full_response.replace("<think>", "").strip(), end="", flush=True)
            else:
                if suppress_tool:
                    buffer = ""
                elif buffer:
                    print(buffer, end="", flush=True)
            print()

            # 4. Ekstrak jawaban final dari full_response
            if "<think>" in full_response and "</think>" in full_response:
                final_answer = full_response.split("</think>", 1)[1].strip()
            else:
                final_answer = full_response.strip()

            # Proteksi jika AI lupa tag pembuka <tool>
            if "</tool>" in final_answer and "<tool>" not in final_answer:
                final_answer = "<tool>" + final_answer

            # 5. Eksekusi Tool jika terdeteksi
            tool_observation = None
            if "<tool>" in final_answer and "</tool>" in final_answer:
                print(f"\n\033[93m⚡ [AGENT MENGEKSEKUSI TOOL]\033[0m")
                tool_observation = execute_tool(final_answer)
                print(f"\033[92m✅ [HASIL SISTEM]:\033[0m {tool_observation}\n")

            # 6. Simpan riwayat interaksi utama
            clean_turn = format_clean_history(user_input, final_answer, tool_observation)
            chat_history.append(clean_turn)

            # 7. Follow-up otomatis jika tool dijalankan
            if tool_observation:
                followup_prompt = SYSTEM_PROMPT + "".join(chat_history) + "<|im_start|>assistant\n<think>\n"

                print(f"\033[96mAI =\033[0m (menanggapi hasil sistem)... ", end="", flush=True)
                followup_stream = llm(
                    followup_prompt,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                    stop=["<|im_end|>", "<|endoftext|>"],
                    stream=True
                )

                followup_response = ""
                in_followup_think = True

                for output in followup_stream:
                    chunk = output['choices'][0]['text']
                    followup_response += chunk

                    if in_followup_think:
                        if "</think>" in followup_response:
                            in_followup_think = False
                            # Hapus teks indikator loading sementara lalu cetak jawaban asli
                            print("\r\033[K" + "\033[96mAI =\033[0m ", end="", flush=True)
                            actual_text = followup_response.split("</think>", 1)[1]
                            print(actual_text, end="", flush=True)
                    else:
                        print(chunk, end="", flush=True)
                print()

                if "</think>" in followup_response:
                    clean_followup = followup_response.split("</think>", 1)[1].strip()
                else:
                    clean_followup = followup_response.strip()

                chat_history.append(f"<|im_start|>assistant\n{clean_followup}<|im_end|>\n")

            # Cetak informasi waktu proses di bagian bawah dengan warna redup
            elapsed = time.time() - start_time
            print(f"\033[90m[Waktu proses: {elapsed:.2f} detik]\033[0m")

            # 8. Batasi memori riwayat
            while len(chat_history) > MAX_MEMORY:
                chat_history.pop(0)

        except Exception as e:
            print(f"\n\033[91m[Error saat generate teks: {e}]\033[0m")
            if len(chat_history) > 0:
                chat_history.pop(0)
