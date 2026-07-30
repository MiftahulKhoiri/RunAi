import re
import time
from src.config import MAX_MEMORY, MAX_TOKENS, TEMPERATURE, TOP_P, COLOR_THINK, COLOR_RESET
from src.tools import execute_tool
from src.prompts import SYSTEM_PROMPT, format_current_prompt, format_clean_history

TOOL_TAG_HOLDBACK = 10   # Margin karakter untuk mengamankan tag <tool yang terpotong chunk
THINK_TAG_HOLDBACK = 9   # Margin karakter untuk mengamankan tag </think> yang terpotong chunk


def _run_stream(llm, full_prompt, label="AI ="):
    """
    Satu kali stream generate: cetak proses berpikir dan jawaban secara live,
    sekaligus menyembunyikan tag <tool>...</tool> dari layar. Dipakai untuk
    jawaban utama MAUPUN follow-up, supaya keduanya konsisten (dulu follow-up
    mencetak chunk mentah tanpa penyaringan tool).
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
                print(f"{COLOR_RESET}\n\n\033[96m{label}\033[0m", end=" ", flush=True)
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
        print(f"{COLOR_RESET}\n\n\033[96m{label}\033[0m", end=" ", flush=True)
        print(full_response.replace("<think>", "").strip(), end="", flush=True)
    else:
        if suppress_tool:
            buffer = ""
        elif buffer:
            print(buffer, end="", flush=True)
    print()

    return full_response


def _extract_final_answer(full_response):
    if "<think>" in full_response and "</think>" in full_response:
        final_answer = full_response.split("</think>", 1)[1].strip()
    else:
        final_answer = full_response.strip()

    if "</tool>" in final_answer and "<tool>" not in final_answer:
        final_answer = "<tool>" + final_answer

    return final_answer


def _strip_tool_tags(text):
    """Buang blok <tool>...</tool> dari jawaban follow-up. Tool kedua di
    dalam follow-up sengaja TIDAK dieksekusi (mencegah rantai tool tanpa
    batas dalam satu giliran), jadi tag mentahnya tidak boleh bocor ke
    layar maupun ke riwayat."""
    return re.sub(r"<tool>.*?</tool>", "", text, flags=re.DOTALL).strip()


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

        current_prompt = format_current_prompt(user_input)
        full_prompt = SYSTEM_PROMPT + "".join(chat_history) + current_prompt

        try:
            start_time = time.time()

            full_response = _run_stream(llm, full_prompt, label="AI =")
            final_answer = _extract_final_answer(full_response)

            tool_observation = None
            if "<tool>" in final_answer and "</tool>" in final_answer:
                print(f"\n\033[93m⚡ [AGENT MENGEKSEKUSI TOOL]\033[0m")
                tool_observation = execute_tool(final_answer)
                print(f"\033[92m✅ [HASIL SISTEM]:\033[0m {tool_observation}\n")

            # Satu giliran = satu entri riwayat, termasuk follow-up-nya kalau
            # ada tool. Dulu follow-up disimpan sebagai entri terpisah, jadi
            # bisa terpotong sendiri saat MAX_MEMORY tercapai dan membuat
            # riwayat ChatML tidak valid (assistant menggantung tanpa user).
            turn_text = format_clean_history(user_input, final_answer, tool_observation)

            if tool_observation:
                followup_prompt = SYSTEM_PROMPT + "".join(chat_history) + turn_text + "<|im_start|>assistant\n<think>\n"

                followup_response = _run_stream(llm, followup_prompt, label="AI (lanjutan) =")
                clean_followup = _strip_tool_tags(_extract_final_answer(followup_response))

                turn_text += f"<|im_start|>assistant\n{clean_followup}<|im_end|>\n"

            chat_history.append(turn_text)

            elapsed = time.time() - start_time
            print(f"\033[90m[Waktu proses: {elapsed:.2f} detik]\033[0m")

            while len(chat_history) > MAX_MEMORY:
                chat_history.pop(0)

        except Exception as e:
            print(f"\n\033[91m[Error saat generate teks: {e}]\033[0m")
            if len(chat_history) > 0:
                chat_history.pop(0)