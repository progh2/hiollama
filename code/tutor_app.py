"""Qwen + VS Code 바이브코딩 실습의 tkinter 참고 완성본.

에러 로그를 붙여넣으면 로컬 LLM(qwen2.5-coder:3b)이 원인·설명·해결책을 알려줍니다.
tkinter는 파이썬에 기본 포함이라 추가 GUI 설치가 없습니다.

실행:  python tutor_app.py   (venv 활성화 + Ollama 실행 상태에서)
"""
import threading
import tkinter as tk
from tkinter import scrolledtext

import requests

MODEL = "qwen2.5-coder:3b"
URL = "http://localhost:11434/api/chat"

SYSTEM = (
    "친절한 파이썬 튜터로서 [원인], [설명], [해결 방법], [고친 코드 예시] 순서로 "
    "한국어로 짧게 답하세요. 정보가 부족하면 필요한 코드를 요청하고 "
    "확실하지 않으면 \"확실하지 않습니다\"라고 먼저 밝히세요. "
    "형식 밖의 인사말이나 사족은 쓰지 마세요."
)


def ask_tutor(error_text):
    """로컬 LLM에 물어보고 답변 문자열을 돌려준다.

    실패 시 requests 예외 또는 ValueError/KeyError(응답 형식 오류)를 던진다.
    """
    with requests.post(
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
        timeout=(5, 300),  # (연결, 읽기) 초
    ) as response:
        response.raise_for_status()
        data = response.json()
        content = data["message"]["content"]  # 없으면 KeyError
    if not isinstance(content, str) or not content.strip():
        raise ValueError("응답 형식 오류: message.content가 비어 있습니다")
    return content


class TutorApp:
    """에러 튜터 창. 위젯 배치와 상태 전환을 담당한다."""

    def __init__(self, root=None):
        self.root = root or tk.Tk()
        self.root.title(f"파이썬 에러 튜터  ({MODEL})")
        self.root.geometry("780x720")
        self.root.minsize(560, 520)
        self.worker = None    # 분석 중이면 Thread, 아니면 None
        self._pending = None  # 작업 스레드가 넣어 두는 (답변, 성공 여부)

        tk.Label(self.root, text="에러 로그를 붙여넣으세요",
                 font=("맑은 고딕", 11, "bold"), anchor="w"
                 ).pack(fill="x", padx=14, pady=(14, 4))

        self.input_box = scrolledtext.ScrolledText(
            self.root, height=10, wrap="word", font=("Consolas", 10))
        self.input_box.pack(fill="x", padx=14)

        btn_row = tk.Frame(self.root)
        btn_row.pack(fill="x", padx=14, pady=8)
        self.analyze_btn = tk.Button(
            btn_row, text="분석하기", command=self.on_analyze,
            height=2, font=("맑은 고딕", 11, "bold"))
        self.analyze_btn.pack(side="left", fill="x", expand=True)
        self.clear_btn = tk.Button(
            btn_row, text="지우기", command=self.on_clear, height=2, width=10)
        self.clear_btn.pack(side="left", padx=(8, 0))

        self.status = tk.Label(self.root, text="준비됨", anchor="w", fg="#5C6B85")
        self.status.pack(fill="x", padx=14)

        tk.Label(self.root, text="튜터의 설명",
                 font=("맑은 고딕", 11, "bold"), anchor="w"
                 ).pack(fill="x", padx=14, pady=(10, 4))
        self.output_box = scrolledtext.ScrolledText(
            self.root, height=18, wrap="word", font=("맑은 고딕", 10),
            state="disabled")
        self.output_box.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        # 닫기 버튼도 우리가 처리한다 (분석 중 종료 방지)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------------- 동작 ----------------
    def on_analyze(self):
        if self.worker is not None:      # 중복 클릭 방지
            return
        error_text = self.input_box.get("1.0", "end").strip()
        if not error_text:
            self.set_status("에러 로그를 먼저 입력해 주세요.", "#B4700A")
            return
        self.set_busy(True)
        self.set_status("분석 중입니다... (10~40초)", "#B4700A")
        self.write_output("")
        self.worker = threading.Thread(
            target=self._work, args=(error_text,), daemon=True)
        self.worker.start()
        self.root.after(100, self._poll)  # 메인 스레드가 결과를 살핀다

    def _work(self, error_text):
        """작업 스레드. 여기서는 위젯을 직접 건드리지 않는다."""
        try:
            answer, ok = ask_tutor(error_text), True
        except requests.exceptions.Timeout:            # ConnectionError보다 먼저
            answer, ok = ("대기 시간이 초과되었습니다.\n"
                          "에러 로그를 줄여서 다시 시도해 보세요."), False
        except requests.exceptions.ConnectionError:
            answer, ok = ("모델에 연결할 수 없습니다.\n\n"
                          "· Ollama가 실행 중인지 확인하세요 (작업표시줄 아이콘)\n"
                          "· 확인 후 분석하기를 다시 눌러 주세요"), False
        except requests.exceptions.HTTPError as err:
            code = getattr(getattr(err, "response", None), "status_code", "?")
            if code == 404:
                answer = ("HTTP 404: 모델을 찾지 못했습니다.\n"
                          "검은 창에서 ollama list 로 qwen2.5-coder:3b가 "
                          "있는지 확인하세요.")
            else:
                answer = f"HTTP {code} 오류가 났습니다. 잠시 후 다시 시도해 보세요."
            ok = False
        except (ValueError, KeyError):
            answer, ok = ("응답 형식 오류: 모델의 답을 읽지 못했습니다.\n"
                          "다시 시도해 보세요."), False
        except Exception as err:                       # noqa: BLE001
            answer, ok = f"예상하지 못한 오류입니다.\n\n{type(err).__name__}: {err}", False
        # 작업 스레드는 결과를 저장만 한다. 위젯은 절대 건드리지 않는다.
        self._pending = (answer, ok)

    def _poll(self):
        """메인 스레드에서 0.1초마다 결과가 도착했는지 확인한다."""
        if self._pending is None:
            try:
                self.root.after(100, self._poll)
            except tk.TclError:
                pass  # 창이 이미 닫힌 경우
            return
        answer, ok = self._pending
        self._pending = None
        self._done(answer, ok)

    def _done(self, answer, ok):
        self.worker = None
        self.write_output(answer)
        self.set_busy(False)
        self.set_status("완료" if ok else "실패 - 안내를 확인하세요",
                        "#1F9D57" if ok else "#C0392B")

    def on_clear(self):
        if self.worker is not None:      # 분석 중에는 무시
            return
        self.input_box.delete("1.0", "end")
        self.write_output("")
        self.set_status("준비됨")

    def on_close(self):
        if self.worker is not None:      # 분석 중 종료 방지
            self.set_status("분석이 끝난 뒤 다시 닫아 주세요.", "#B4700A")
            return
        self.root.destroy()

    # ---------------- 화면 도우미 ----------------
    def set_busy(self, busy):
        state = "disabled" if busy else "normal"
        self.input_box.config(state=state)
        self.analyze_btn.config(state=state)
        self.clear_btn.config(state=state)

    def write_output(self, text):
        self.output_box.config(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.insert("1.0", text)
        self.output_box.config(state="disabled")

    def set_status(self, text, color="#5C6B85"):
        self.status.config(text=text, fg=color)


if __name__ == "__main__":
    app = TutorApp()
    app.input_box.insert(
        "1.0",
        'Traceback (most recent call last):\n'
        '  File "test.py", line 3, in <module>\n'
        '    print(nums[5])\n'
        'IndexError: list index out of range')
    app.root.mainloop()
