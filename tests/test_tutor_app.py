"""GUI/HTTP 계약 검증 (tkinter판).

저장소 루트에서:  python -m unittest discover -s tests -v
리눅스 헤드리스:  xvfb-run -a python -m unittest discover -s tests -v
"""
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
import tutor_app as tutor
import tkinter as tk


def disabled(widget):
    return str(widget.cget("state")) == "disabled"


def alive(root):
    try:
        return bool(root.winfo_exists())
    except tk.TclError:
        return False


class TutorTests(unittest.TestCase):
    def setUp(self):
        try:
            self.app = tutor.TutorApp()
        except tk.TclError as err:  # 디스플레이 없음
            self.skipTest(f"디스플레이가 없어 GUI 테스트를 건너뜁니다: {err}")
        self.root = self.app.root
        self.root.update()

    def tearDown(self):
        if alive(self.root):
            self.until(lambda: self.app.worker is None)
            self.root.destroy()

    # ---------- 도우미 ----------
    def until(self, condition):
        deadline = time.monotonic() + 3
        while not condition() and time.monotonic() < deadline:
            if not alive(self.root):
                break
            self.root.update()
            time.sleep(0.01)
        self.assertTrue(condition(), "GUI worker did not finish")

    def set_input(self, text):
        self.app.input_box.delete("1.0", "end")
        self.app.input_box.insert("1.0", text)

    def input_text(self):
        return self.app.input_box.get("1.0", "end").strip()

    def output_text(self):
        return self.app.output_box.get("1.0", "end").strip()

    def status_text(self):
        return str(self.app.status.cget("text"))

    # ---------- 테스트 ----------
    def test_empty_input_does_not_request(self):
        with patch.object(tutor, "ask_tutor") as request:
            self.app.on_analyze()
            request.assert_not_called()
        self.assertIn("먼저 입력", self.status_text())
        self.assertFalse(disabled(self.app.analyze_btn))

    def test_responsive_duplicate_guard_close_and_clear(self):
        def delayed(_):
            time.sleep(0.15)  # 의도적으로 느린 모델을 작업 스레드에서만 흉내냅니다.
            return "[원인] 인덱스 범위를 확인하세요."

        ticks = []

        def tick():
            ticks.append(1)
            if alive(self.root):
                self.root.after(10, tick)

        self.root.after(10, tick)
        with patch.object(tutor, "ask_tutor", side_effect=delayed) as request:
            self.set_input("IndexError")
            self.app.on_analyze()
            self.app.on_analyze()                       # 중복 클릭
            self.assertTrue(disabled(self.app.clear_btn))
            self.assertTrue(disabled(self.app.input_box))
            self.app.on_clear()                         # 분석 중 지우기 → 무시
            self.assertEqual(self.input_text(), "IndexError")
            self.app.on_close()                         # 분석 중 닫기 → 보류
            self.assertTrue(alive(self.root))
            self.assertIn("다시 닫아", self.status_text())
            self.until(lambda: self.app.worker is None)
            request.assert_called_once_with("IndexError")
        self.assertGreater(len(ticks), 2, "메인 이벤트 루프가 멈췄습니다")
        self.assertIn("인덱스", self.output_text())
        self.assertFalse(disabled(self.app.analyze_btn))
        self.assertTrue(disabled(self.app.output_box))  # 결과는 읽기 전용 유지
        self.app.on_clear()
        self.assertEqual(self.output_text(), "")
        self.app.on_close()
        self.assertFalse(alive(self.root))

    def test_failures_restore_controls_and_allow_retry(self):
        response = Mock(status_code=404)
        cases = [
            (tutor.requests.exceptions.ConnectTimeout(), "대기 시간"),
            (tutor.requests.exceptions.ConnectionError(), "연결"),
            (tutor.requests.exceptions.HTTPError(response=response), "404"),
            (ValueError(), "응답 형식"),
        ]
        for error, expected in cases:
            with self.subTest(error=type(error).__name__):
                with patch.object(tutor, "ask_tutor", side_effect=error):
                    self.set_input("TypeError")
                    self.app.on_analyze()
                    self.until(lambda: self.app.worker is None)
                self.assertIn(expected, self.output_text())
                self.assertFalse(disabled(self.app.clear_btn))
                self.assertFalse(disabled(self.app.analyze_btn))
                self.assertFalse(disabled(self.app.input_box))
        with patch.object(tutor, "ask_tutor", return_value="재시도 성공"):
            self.app.on_analyze()
            self.until(lambda: self.app.worker is None)
        self.assertEqual(self.output_text(), "재시도 성공")

    def test_http_request_and_invalid_payloads(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.json.return_value = {"message": {"content": "답변"}}
        with patch.object(tutor.requests, "post", return_value=response) as post:
            self.assertEqual(tutor.ask_tutor("에러"), "답변")
            body = post.call_args.kwargs
            self.assertEqual(body["json"]["model"], "qwen2.5-coder:3b")
            self.assertFalse(body["json"]["stream"])
            self.assertEqual(body["json"]["messages"][1]["content"], "에러")
            self.assertEqual(body["timeout"], (5, 300))
            response.raise_for_status.assert_called_once()
            for payload in [{}, {"message": {}}, {"message": {"content": ""}},
                            {"message": {"content": 2}}]:
                response.json.return_value = payload
                with self.assertRaises((ValueError, KeyError)):
                    tutor.ask_tutor("에러")


if __name__ == "__main__":
    unittest.main()
