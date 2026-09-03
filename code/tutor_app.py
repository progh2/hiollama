"""파이썬 에러 튜터 - 로컬 LLM GUI 앱 (완성본)

에러 로그를 붙여넣으면 로컬 LLM 이 원인을 분석하고 해결책을 알려줍니다.
인터넷 없이, 내 컴퓨터에서만 동작합니다.

준비:  pip install requests
       Ollama 실행 + qwen2.5-coder:3b 모델
실행:  python tutor_app.py
"""
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

import requests

# ---------------------------------------------------------------- 설정
MODEL = "qwen2.5-coder:3b"
URL = "http://localhost:11434/api/chat"

SYSTEM = """당신은 친절한 파이썬 튜터입니다.
학생이 붙여넣은 에러 메시지를 보고 아래 형식으로만 답하세요.
각 항목의 제목은 그대로 쓰세요.

[원인]
무엇이 잘못됐는지 한두 문장

[설명]
왜 이런 일이 생기는지 초보자가 이해할 수 있게

[해결 방법]
1. 첫 번째 방법
2. 두 번째 방법
3. 세 번째 방법

[고친 코드 예시]
짧은 코드 한 토막

규칙:
- 한국어로 답하세요.
- 확실하지 않으면 "확실하지 않습니다"라고 먼저 밝히세요.
- 형식 밖의 인사말이나 사족은 쓰지 마세요.
"""


# ---------------------------------------------------------------- 모델 호출
def ask_tutor(error_text):
    """로컬 LLM 에 물어보고 답변 문자열을 돌려준다."""
    res = requests.post(
        URL,
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": error_text},
            ],
            "stream": False,
            "options": {"temperature": 0.3},
        },
        timeout=300,
    )
    res.raise_for_status()
    return res.json()["message"]["content"]


# ---------------------------------------------------------------- 동작
def on_analyze():
    """[분석하기] 버튼을 눌렀을 때."""
    error_text = input_box.get("1.0", "end").strip()
    if not error_text:
        messagebox.showinfo("알림", "에러 로그를 먼저 붙여넣어 주세요.")
        return

    analyze_btn.config(state="disabled")
    set_status("분석 중입니다... (10~40초)", "#B4700A")
    write_output("")

    # GUI 가 멈추지 않도록 별도 스레드에서 요청한다
    threading.Thread(target=worker, args=(error_text,), daemon=True).start()


def worker(error_text):
    """백그라운드 스레드 - 여기서 GUI 를 직접 건드리면 안 된다."""
    try:
        answer = ask_tutor(error_text)
        ok = True
    except requests.exceptions.ConnectionError:
        answer = ("모델에 연결할 수 없습니다.\n\n"
                  "· Ollama 가 실행 중인지 확인하세요 (작업표시줄 아이콘)\n"
                  "· 검은 창에서  ollama list  로 모델이 있는지 확인하세요")
        ok = False
    except requests.exceptions.Timeout:
        answer = "시간이 너무 오래 걸려서 중단했습니다. 에러 로그를 줄여서 다시 시도해 보세요."
        ok = False
    except Exception as err:                      # noqa: BLE001
        answer = f"예상하지 못한 오류입니다.\n\n{type(err).__name__}: {err}"
        ok = False

    # GUI 갱신은 반드시 메인 스레드에서 - after() 로 넘긴다
    root.after(0, done, answer, ok)


def done(answer, ok):
    write_output(answer)
    set_status("완료" if ok else "실패", "#1F9D57" if ok else "#C0392B")
    analyze_btn.config(state="normal")


def write_output(text):
    output_box.config(state="normal")
    output_box.delete("1.0", "end")
    output_box.insert("1.0", text)
    output_box.config(state="disabled")


def set_status(text, color="#5C6B85"):
    status.config(text=text, fg=color)


def on_clear():
    input_box.delete("1.0", "end")
    write_output("")
    set_status("준비됨")


# ---------------------------------------------------------------- 화면
root = tk.Tk()
root.title(f"파이썬 에러 튜터  ({MODEL})")
root.geometry("780x720")
root.minsize(560, 520)

tk.Label(root, text="에러 로그를 붙여넣으세요",
         font=("맑은 고딕", 11, "bold"), anchor="w").pack(fill="x", padx=14, pady=(14, 4))

input_box = scrolledtext.ScrolledText(root, height=10, wrap="word",
                                      font=("Consolas", 10))
input_box.pack(fill="x", padx=14)

btn_row = tk.Frame(root)
btn_row.pack(fill="x", padx=14, pady=8)

analyze_btn = tk.Button(btn_row, text="분석하기", command=on_analyze,
                        height=2, font=("맑은 고딕", 11, "bold"))
analyze_btn.pack(side="left", fill="x", expand=True)

tk.Button(btn_row, text="지우기", command=on_clear,
          height=2, width=10).pack(side="left", padx=(8, 0))

status = tk.Label(root, text="준비됨", anchor="w", fg="#5C6B85")
status.pack(fill="x", padx=14)

tk.Label(root, text="튜터의 설명",
         font=("맑은 고딕", 11, "bold"), anchor="w").pack(fill="x", padx=14, pady=(10, 4))

output_box = scrolledtext.ScrolledText(root, height=18, wrap="word",
                                       font=("맑은 고딕", 10), state="disabled")
output_box.pack(fill="both", expand=True, padx=14, pady=(0, 14))

input_box.insert("1.0",
                 'Traceback (most recent call last):\n'
                 '  File "test.py", line 3, in <module>\n'
                 '    print(nums[5])\n'
                 'IndexError: list index out of range')

root.mainloop()
