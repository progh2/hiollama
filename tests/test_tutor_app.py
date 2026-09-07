"""GUI/HTTP 계약 검증. 저장소 루트에서 python -m unittest discover -s tests -v."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
import tutor_app as tutor
from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest


class TutorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = tutor.QApplication.instance() or tutor.QApplication([])

    def setUp(self):
        self.window = tutor.TutorWindow()
        self.window.show()

    def tearDown(self):
        self.until(lambda: self.window.worker is None)
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def until(self, condition):
        deadline = time.monotonic() + 3
        while not condition() and time.monotonic() < deadline:
            QTest.qWait(10)
        self.assertTrue(condition(), "GUI worker did not finish")

    def test_empty_input_does_not_request(self):
        with patch.object(tutor, "ask_tutor") as request:
            self.window.on_analyze()
            request.assert_not_called()
        self.assertIn("먼저 입력", self.window.status.text())
        self.assertTrue(self.window.analyze_btn.isEnabled())

    def test_responsive_duplicate_guard_close_and_clear(self):
        def delayed(_):
            time.sleep(0.15)  # 의도적으로 느린 모델을 작업 스레드에서만 흉내냅니다.
            return "[원인] 인덱스 범위를 확인하세요."
        ticks = []
        timer = QTimer()
        timer.timeout.connect(lambda: ticks.append(1))
        timer.start(10)
        with patch.object(tutor, "ask_tutor", side_effect=delayed) as request:
            self.window.input_box.setPlainText("IndexError")
            self.window.on_analyze()
            self.window.on_analyze()
            self.assertFalse(self.window.clear_btn.isEnabled())
            self.assertTrue(self.window.input_box.isReadOnly())
            self.window.on_clear()
            self.assertEqual(self.window.input_box.toPlainText(), "IndexError")
            self.window.close()
            self.assertTrue(self.window.isVisible())
            self.assertIn("다시 닫아", self.window.status.text())
            self.until(lambda: self.window.worker is None)
            request.assert_called_once_with("IndexError")
        timer.stop()
        self.assertGreater(len(ticks), 2, "메인 이벤트 루프가 멈췄습니다")
        self.assertIn("인덱스", self.window.output_box.toPlainText())
        self.assertTrue(self.window.analyze_btn.isEnabled())
        self.assertTrue(self.window.output_box.isReadOnly())
        self.window.on_clear()
        self.assertEqual(self.window.output_box.toPlainText(), "")
        self.window.close()
        self.assertFalse(self.window.isVisible())

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
                    self.window.input_box.setPlainText("TypeError")
                    self.window.on_analyze()
                    self.until(lambda: self.window.worker is None)
                self.assertIn(expected, self.window.output_box.toPlainText())
                self.assertTrue(self.window.clear_btn.isEnabled())
                self.assertTrue(self.window.analyze_btn.isEnabled())
                self.assertFalse(self.window.input_box.isReadOnly())
        with patch.object(tutor, "ask_tutor", return_value="재시도 성공"):
            self.window.on_analyze()
            self.until(lambda: self.window.worker is None)
        self.assertEqual(self.window.output_box.toPlainText(), "재시도 성공")

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
            for payload in [{}, {"message": {}}, {"message": {"content": ""}}, {"message": {"content": 2}}]:
                response.json.return_value = payload
                with self.assertRaises((ValueError, KeyError)):
                    tutor.ask_tutor("에러")


if __name__ == "__main__":
    unittest.main()
