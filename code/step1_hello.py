"""1단계 - 로컬 LLM에 말 걸어보기 (콘솔)

Ollama 가 실행 중이어야 합니다.
실행:  python step1_hello.py
"""
import requests

MODEL = "qwen2.5-coder:3b"
URL = "http://localhost:11434/api/chat"


def ask(prompt):
    """프롬프트를 보내고 답변 문자열을 돌려준다."""
    res = requests.post(
        URL,
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        timeout=180,
    )
    res.raise_for_status()
    return res.json()["message"]["content"]


if __name__ == "__main__":
    답 = ask("파이썬에서 IndexError 가 나는 이유를 한 문장으로 설명해줘.")
    print(답)
