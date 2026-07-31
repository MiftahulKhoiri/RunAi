import re
import time
from src.config import MAX_MEMORY, MAX_TOKENS, TEMPERATURE, TOP_P, COLOR_THINK, COLOR_RESET
from src.tools import execute_tool
from src.prompts import SYSTEM_PROMPT, format_current_prompt, format_clean_history

TOOL_TAG_HOLDBACK = 10   # Margin karakter untuk mengamankan tag <tool yang terpotong chunk
THINK_TAG_HOLDBACK = 9   # Margin karakter untuk mengamankan tag </think> yang terpotong chunk

# Warna tampilan CLI
COLOR_USER = "\033[92m"
COLOR_AI = "\033[96m"
COLOR_WARN = "\033[93m"
COLOR_OK = "\033[92m"
COLOR_ERR = "\033[91m"
COLOR_DIM = "\033[90m"


def _run_stream(llm, full_prompt, label="AI ="):
    """
    Satu kali stream generate: cetak proses berpikir dan jawaban secara live,
    sekaligus menyembunyikan tag <tool>...</tool> dari layar.
    """
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

    print(f"\n{COLOR_THINK}[Sedang Berpikir]:", flush=True)

    for output in stream:
        chunk = output['choices'][0]['text']
        full_response += chunk
        buffer += chunk

        if state == "THINKING":
            if "</think>" in buffer:
                state = "ANSWERING"
                parts = buffer.split("</think>", 1)
                print(parts[0], end="", flush=True)
                print(f"{COLOR_RESET}\n\n{COLOR_AI}{label}{COLOR_RESET}", end=" ", flush=True)
                buffer = parts[1]
            else:
                if len(buffer) > THINK_TAG_HOLDBACK:
                    to_print = buffer[:-THINK_TAG_HOLDBACK]
                    buffer = buffer[-THINK_TAG_HOLDBACK:]
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

    if state == "THINKING":
        print(f"{COLOR_RESET}\n\n{COLOR_AI}{label}{COLOR_RESET}", end=" ", flush=True)
        print(full_response.replace("<think>", "").strip(), end="", flush=True)
    else:
        if suppress_tool:
            buffer = ""
        elif buffer:
            print(buffer, end="", flush=True)
        print()

    return full_response


def _extract_final_answer(full_response):
    # Hanya cek tag penutup </think> saja
    if "</think>" in full_response:
        final_answer = full_response.split("</think>", 1)[1].strip()
    else:
        # Fallback jika model lupa menutup tag
        final_answer = full_response.replace("<think>", "").strip()

    if "</tool>" in final_answer and "<tool>" not in final_answer:
        final_answer = "<tool>" + final_answer

    return final_answer


def _strip_tool_tags(text):
    return re.sub(r"<tool>.*?</tool>", "", text, flags=re.DOTALL).strip()


def _has_tool_call(text):
    return "<tool>" in text and "</tool>" in text


def chat_loop(llm):
    """Menjalankan loop interaksi CLI dengan tampilan yang rapi dan elegan."""
    print("=" * 50)
    print("  ASISTEN AI LOKAL - RASPBERRY PI 5 (AGENT MODE)")
    print("  Ketik 'exit', 'quit', atau 'keluar' untuk menghentikan.")
    print("=" * 50)

    chat_history = []

    while True:
        try:
            user_input = input(f"\n{COLOR_USER}Anda:{COLOR_RESET} ")
        except (KeyboardInterrupt, EOFError):
            print("\n\nSesi diakhiri secara paksa. Sampai jumpa!")
            break

        if user_input.lower() in ['exit', 'keluar', 'quit']:
            print("\nSesi diakhiri. Sampai jumpa!")
            break

        if not user_input.strip():
            continue

        current_prompt = format_current_prompt(user_input)
        full_prompt = SYSTEM_PROMPT + "".join(chat_history) + current_prompt

        try:
            start_time = time.time()

            full_response = _run_stream(llm, full_prompt, label="AI =")
            final_answer = _extract_final_answer(full_response)

            if not final_answer.strip():
                print(f"\n{COLOR_WARN}[Model tidak menghasilkan jawaban, coba ulangi pertanyaan]{COLOR_RESET}")
                continue

            tool_observation = None
            if _has_tool_call(final_answer):
                print(f"\n{COLOR_WARN}⚡ [AGENT MENGEKSEKUSI TOOL]{COLOR_RESET}")
                try:
                    tool_observation = execute_tool(final_answer)
                except Exception as tool_err:
                    tool_observation = f"[Error saat menjalankan tool: {tool_err}]"
                print(f"{COLOR_OK}✅ [HASIL SISTEM]:{COLOR_RESET} {tool_observation}\n")

            turn_text = format_clean_history(user_input, final_answer, tool_observation)

            if tool_observation is not None:
                followup_prompt = SYSTEM_PROMPT + "".join(chat_history) + turn_text + "<|im_start|>assistant\n<think>\n"

                followup_response = _run_stream(llm, followup_prompt, label="AI (lanjutan) =")
                followup_answer = _extract_final_answer(followup_response)

                if _has_tool_call(followup_answer):
                    # Agent ini belum mendukung tool-call berantai (multi-step) dalam satu giliran.
                    # Tool kedua TIDAK dieksekusi -- hanya diberi tahu ke pengguna agar tidak hilang diam-diam.
                    print(f"\n{COLOR_WARN}[Peringatan] Model mencoba memanggil tool lagi setelah tool "
                          f"pertama, tapi ini belum didukung sehingga diabaikan.{COLOR_RESET}")

                clean_followup = _strip_tool_tags(followup_answer)
                turn_text += f"<|im_start|>assistant\n{clean_followup}<|im_end|>\n"

            chat_history.append(turn_text)

            elapsed = time.time() - start_time
            print(f"{COLOR_DIM}[Waktu proses: {elapsed:.2f} detik]{COLOR_RESET}")

            while len(chat_history) > MAX_MEMORY:
                chat_history.pop(0)

        except KeyboardInterrupt:
            # Ctrl+C saat generate: batalkan giliran ini saja, jangan tutup seluruh sesi
            print(f"\n\n{COLOR_WARN}[Dibatalkan pengguna, giliran ini tidak disimpan]{COLOR_RESET}")
            continue

        except Exception as e:
            print(f"\n{COLOR_ERR}[Error saat generate teks: {e}]{COLOR_RESET}")
            # Heuristik pemulihan: error semacam ini biasanya karena prompt kepanjangan
            # (melebihi context window model), jadi buang riwayat tertua agar giliran berikutnya lebih ringkas.
            if len(chat_history) > 0:
                chat_history.pop(0)