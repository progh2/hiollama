"""Qwen + VS Code 바이브코딩 실습의 PySide6 참고 완성본.

프로젝트 폴더에서 venv 활성화 후:
    python -m pip install -r requirements.txt
    python tutor_app.py
Ollama 실행 + qwen2.5-coder:3b 모델이 필요합니다.
"""
import sys

import requests
from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QMainWindow, QPlainTextEdit,
    QPushButton, QVBoxLayout, QWidget,
)

MODEL = "qwen2.5-coder:3b"
URL = "http://localhost:11434/api/chat"
SYSTEM = """당신은 고등학생을 돕는 친절한 파이썬 튜터입니다.
에러와 주변 코드를 읽고 [원인], [설명], [해결 방법], [고친 코드 예시] 순서로
한국어로 짧게 답하세요. 모르는 정보는 추측으로 단정하지 말고 필요한 코드를 요청하세요.
불확실하면 불확실하다고 밝히세요. 인사말은 생략하세요.
"""


def ask_tutor(error_text):
    """GUI와 분리된 HTTP 요청. timeout은 연결/읽기 대기 제한입니다."""
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
        timeout=(5, 300),
    ) as response:
        response.raise_for_status()
        answer = response.json()["message"]["content"]
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("모델의 답변이 비어 있거나 문자열이 아닙니다.")
    return answer


class AnalysisThread(QThread):
    """run에서만 HTTP를 호출하고 위젯은 건드리지 않습니다."""
    result = Signal(str, bool)

    def __init__(self, error_text, parent=None):
        super().__init__(parent)
        self.error_text = error_text

    def run(self):
        try:
            answer = ask_tutor(self.error_text)
        except requests.exceptions.Timeout:
            self.result.emit("응답 대기 시간이 초과됐습니다. 입력을 줄인 뒤 다시 시도하세요.", False)
        except requests.exceptions.ConnectionError:
            self.result.emit("Ollama에 연결할 수 없습니다. Ollama를 실행하고 다시 시도하세요.", False)
        except requests.exceptions.HTTPError as err:
            code = err.response.status_code if err.response is not None else "알 수 없음"
            hint = (f"ollama list에서 {MODEL} 모델을 확인하세요."
                    if code == 404 else "Ollama 상태를 확인한 뒤 다시 시도하세요.")
            self.result.emit(f"서버 오류 (HTTP {code}). {hint}", False)
        except (ValueError, KeyError, TypeError):
            self.result.emit("응답 형식을 읽을 수 없습니다. 모델과 Ollama 버전을 확인하세요.", False)
        except requests.exceptions.RequestException as err:
            self.result.emit(f"요청에 실패했습니다 ({type(err).__name__}). 연결 설정을 확인하세요.", False)
        except Exception as err:
            self.result.emit(f"예상하지 못한 오류 ({type(err).__name__}): {err}", False)
        else:
            self.result.emit(answer, True)


class TutorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None  # finished까지 참조를 유지합니다.
        self.setWindowTitle("라마의 파이썬 에러 튜터")
        self.resize(820, 760)
        self.setMinimumSize(560, 560)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        title = QLabel("함께 읽고, 원인을 찾아보자")
        title.setObjectName("title")
        layout.addWidget(title)
        layout.addWidget(QLabel(f"로컬 모델: {MODEL} · 답변은 실행 결과로 확인하세요"))
        input_label = QLabel("에러 로그와 주변 코드")
        layout.addWidget(input_label)
        self.input_box = QPlainTextEdit()
        input_label.setBuddy(self.input_box)
        self.input_box.setPlaceholderText("Traceback과 오류가 난 줄 주변 코드를 붙여넣으세요.")
        layout.addWidget(self.input_box, 1)
        buttons = QHBoxLayout()
        self.analyze_btn = QPushButton("분석하기")
        self.clear_btn = QPushButton("지우기")
        self.analyze_btn.clicked.connect(self.on_analyze)
        self.clear_btn.clicked.connect(self.on_clear)
        buttons.addWidget(self.analyze_btn, 1)
        buttons.addWidget(self.clear_btn)
        layout.addLayout(buttons)
        self.status = QLabel("준비됨")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        output_label = QLabel("튜터의 설명 · 복사해서 직접 검증하세요")
        layout.addWidget(output_label)
        self.output_box = QPlainTextEdit()
        self.output_box.setReadOnly(True)
        output_label.setBuddy(self.output_box)
        layout.addWidget(self.output_box, 2)
        self.setStyleSheet("""
            QWidget { background: #f3f8f7; color: #193b38; font-size: 15px; }
            QLabel#title { font-size: 23px; font-weight: bold; }
            QPlainTextEdit { background: white; border: 1px solid #88aaa5;
                border-radius: 10px; padding: 10px; }
            QPushButton { background: #246b61; color: white; border: 2px solid #246b61;
                border-radius: 10px; padding: 10px; }
            QPushButton:focus { border-color: #da9800; }
            QPushButton:disabled { background: #d6e1df; color: #536b67; border-color: #d6e1df; }
        """)

    @Slot()
    def on_analyze(self):
        if self.worker is not None:
            return
        error_text = self.input_box.toPlainText().strip()
        if not error_text:
            self.status.setText("에러 로그를 먼저 입력하세요.")
            self.input_box.setFocus()
            return
        self.input_box.setReadOnly(True)
        self.analyze_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.output_box.clear()
        self.status.setText("분석 중… 응답을 기다리고 있어요.")
        self.worker = AnalysisThread(error_text, self)
        self.worker.result.connect(self.on_result)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    @Slot(str, bool)
    def on_result(self, answer, ok):
        self.output_box.setPlainText(answer)
        self.status.setText("완료 · 설명과 고친 코드를 직접 확인하세요." if ok else "실패 · 안내를 확인하고 다시 시도하세요.")

    @Slot()
    def on_finished(self):
        worker = self.worker
        self.worker = None
        self.input_box.setReadOnly(False)
        self.analyze_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        if worker is not None:
            worker.deleteLater()

    @Slot()
    def on_clear(self):
        if self.worker is not None:
            return
        self.input_box.clear()
        self.output_box.clear()
        self.status.setText("준비됨")
        self.input_box.setFocus()

    def closeEvent(self, event):
        # 동기 requests 호출은 quit()만으로 취소되지 않습니다.
        # 실행 중 QThread를 파괴하지 않고 완료 후 닫도록 안내합니다.
        if self.worker is not None:
            self.status.setText("분석이 진행 중입니다. 응답 또는 오류 안내가 나온 뒤 다시 닫아주세요.")
            event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TutorWindow()
    window.show()
    sys.exit(app.exec())
