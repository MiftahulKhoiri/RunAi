import time
from src.config import MAX_MEMORY, MAX_TOKENS, TEMPERATURE, TOP_P, COLOR_THINK, COLOR_RESET
from src.prompts import SYSTEM_PROMPT, format_current_prompt, format_clean_history
from src.tools import execute_tool

TOOL_TAG_HOLDBACK = 10  # margin karakter untuk deteksi tag <tool yang terpotong

def chat_loop(llm):
    """Menjalankan loop interaksi dengan kemampuan AI Agent mandiri."""
    print("=" * 50)
    print("Ketik 'exit', 'quit', atau 'keluar' untuk menghentikan program.")
    print("=" * 50)

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

        # 1. Susun prompt lengkap
        current_prompt = format_current_prompt(user_input)
        full_prompt = SYSTEM_PROMPT + "".join(chat_history) + current_prompt

        try:
            start_time = time.time()

            # 2. Generate stream
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
            full_response = ""          # Tidak perlu menambahkan "<think>\n" buatan
            suppress_tool = False       # Menyembunyikan tag tool dari tampilan

            print(f"{COLOR_THINK}[Proses Berpikir]:\n", end="", flush=True)

            for output in stream:
                chunk = output['choices'][0]['text']
                full_response += chunk
                buffer += chunk

                if state == "THINKING":
                    if "</think>" in buffer:
                        state = "ANSWERING"
                        parts = buffer.split("</think>", 1)
                        # Cetak bagian berpikir (tanpa tag)
                        print(parts[0], end="", flush=True)
                        # Ganti warna untuk jawaban
                        print(f"{COLOR_RESET}\n\nAI = ", end="", flush=True)
                        buffer = parts[1]  # sisanya adalah jawaban
                    else:
                        # Tahan 9 karakter terakhir untuk mencegah pemotongan tag </think>
                        if len(buffer) > 9:
                            to_print = buffer[:-9]
                            buffer = buffer[-9:]
                            print(to_print, end="", flush=True)

                elif state == "ANSWERING":
                    if not suppress_tool:
                        # Cek apakah tag <tool mulai muncul
                        if "<tool" in buffer:
                            idx = buffer.find("<tool")
                            # Cetak semua teks sebelum tag
                            print(buffer[:idx], end="", flush=True)
                            buffer = buffer[idx:]  # simpan tag untuk disembunyikan
                            suppress_tool = True
                        elif len(buffer) > TOOL_TAG_HOLDBACK:
                            # Tahan beberapa karakter terakhir untuk deteksi tag
                            to_print = buffer[:-TOOL_TAG_HOLDBACK]
                            buffer = buffer[-TOOL_TAG_HOLDBACK:]
                            print(to_print, end="", flush=True)
                    else:
                        # Sedang menyembunyikan tag tool, cari penutup
                        if "</tool>" in buffer:
                            # Pisahkan buffer menjadi sebelum dan sesudah </tool>
                            parts = buffer.split("</tool>", 1)
                            # parts[0] berisi tag (tidak dicetak)
                            # parts[1] adalah teks setelah tag, harus dicetak
                            if len(parts) > 1 and parts[1]:
                                print(parts[1], end="", flush=True)
                            buffer = ""
                            suppress_tool = False

            # 3. Setelah stream selesai, bersihkan sisa buffer
            if state == "THINKING":
                print(f"{COLOR_RESET}\n\n[AI kehabisan napas/bingung]")
            else:
                if suppress_tool:
                    buffer = ""  # buang sisa tag yang tidak lengkap
                elif buffer:
                    print(buffer, end="", flush=True)
            print()

            elapsed = time.time() - start_time
            print(f"\033[90m[Waktu proses: {elapsed:.2f} detik]\033[0m")

            # 4. Bersihkan tag <think> dari full_response untuk mendapatkan jawaban final
            if "<think>" in full_response and "</think>" in full_response:
                final_answer = full_response.split("</think>", 1)[1].strip()
            else:
                final_answer = full_response.strip()

            # 5. Eksekusi tool jika ada
            tool_observation = None
            if "<tool>" in final_answer and "</tool>" in final_answer:
                print(f"\n\033[93m⚡ [AGENT MENGEKSEKUSI TOOL]\033[0m")
                tool_observation = execute_tool(final_answer)
                print(f"\033[92m✅ [HASIL SISTEM]: {tool_observation}\033[0m\n")

            # 6. Simpan riwayat interaksi utama
            clean_turn = format_clean_history(user_input, final_answer, tool_observation)
            chat_history.append(clean_turn)

            # 7. Follow-up otomatis jika ada eksekusi tool
            if tool_observation:
                followup_prompt = SYSTEM_PROMPT + "".join(chat_history) + "<|im_start|>assistant\n"

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

                # Simpan follow-up sebagai jawaban asisten tambahan
                chat_history.append(f"<|im_start|>assistant\n{followup_text.strip()}<|im_end|>\n")

            # 8. Batasi riwayat agar tidak melebihi MAX_MEMORY
            while len(chat_history) > MAX_MEMORY:
                chat_history.pop(0)

        except Exception as e:
            print(f"\n[Error saat generate teks: {e}]")
            print(COLOR_RESET, end="", flush=True)
            if len(chat_history) > 0:
                chat_history.pop(0)
