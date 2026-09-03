"""2단계 - 튜터 역할을 부여하기 (콘솔)

system 메시지로 모델의 역할과 답변 형식을 고정한다.
실행:  python step2_tutor.py
"""
import requests

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

에러_예시 = """Traceback (most recent call last):
  File "test.py", line 3, in <module>
    print(nums[5])
IndexError: list index out of range"""


def ask_tutor(error_text):
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
        timeout=180,
    )
    res.raise_for_status()
    return res.json()["message"]["content"]


if __name__ == "__main__":
    print(ask_tutor(에러_예시))
