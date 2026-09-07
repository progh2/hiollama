# 로컬 LLM으로 바이브코딩 시작하기

고등학교 2학년 대상 **100분 실습**. RTX 2060 6GB / Windows / VS Code + Twinny 환경을 기준으로 합니다.

**[실습 페이지 열기](https://progh2.github.io/hiollama/)**

학생은 HTML 앱 하나를 실행하고, 기능 3개를 확인한 뒤 근거를 들어 한 번 이상 개선합니다. 로컬 AI 구조 설명, 구체적인 요청, 실행 결과 검증이 학습 목표입니다.

## 모델 구성

| 용도 | 모델 | 운영 |
|---|---|---|
| 채팅·코드 생성·수정 | `qwen2.5-coder:3b` | 필수 |
| 커서 앞뒤 코드 자동완성(FIM) | `qwen2.5-coder:1.5b-base` | 선택 체험 |

교사가 위 조합의 VS Code 연결·실행을 확인했습니다. 정확한 버전과 FIM 템플릿, 반복 수정 품질·동시 사용 속도는 [교사용 안내](TEACHER.md)의 수업 전 점검표에 기록합니다. 1.5B 채팅에서 관찰한 반복 응답을 FIM 실패로 일반화하지 않습니다. Qwen3.5로 교체하지 않습니다.

두 모델의 다운로드 합계는 약 2.9GB이며 실행 VRAM과 다릅니다. 모델 응답 후 `ollama ps`로 GPU/CPU 배치를 확인합니다. 느리면 FIM을 끄고 3B 채팅만 사용합니다.

## 자료

| 파일 | 용도 |
|---|---|
| `index.html` | 학생용 실습, 00–13 본 수업·참고 / 14–16 다음 차시, 총 17개 챕터 |
| `LESSON_PLAN.md` | 교사용 수업계획서 — 학생·교사 상호작용, 평가, 참고 문헌·영상 |
| `TEACHER.md` | 사전 배포, 시간표, 설정 기록, 검증·복귀 절차 |
| `worksheet.html` | 작성 후 인쇄/PDF 또는 텍스트 다운로드하는 활동지 |
| `code/game_starter.html` | 오프라인 가위바위보 예제·복귀용 출발 코드 |
| `check-env.bat` | GPU·드라이버·디스크·설치 상태 사전 점검 |
| `code/step1_hello.py` | Ollama API 최소 호출 |
| `code/step2_tutor.py` | system 메시지로 튜터 역할 부여 |
| `tests/test_tutor_app.py` | Qt offscreen GUI·HTTP 계약 검증 |
| `code/requirements.txt` | PySide6·requests 설치 범위 |
| `code/tutor_app.py` | 다음 차시 PySide6 + QThread/Signal 에러 튜터 참고 완성본 |
| `assets/llama-expressions.png` | 치비 라마 10표정 스프라이트 시트. CSS로 각 칸 표시 |

01 PC 점검에서 배치 파일을 받습니다. 배치 파일은 **CP949 + CRLF**를 유지해야 하며, `index.html`의 소스 보기에도 같은 내용을 반영합니다. cmd 기반으로 동작하고 NVIDIA 점검에는 `nvidia-smi`를 사용합니다. 보안 정책에 따라 실행이 제한될 수 있습니다.

페이지·활동지·예제는 외부 CDN 없이 동작합니다. 오프라인 배포 시 HTML뿐 아니라 `assets`, `code`, 배치 파일과 교사용 안내까지 폴더 구조 그대로 복사하세요.

[교사용 수업계획서](LESSON_PLAN.md)에서 단계별 발문·학생 반응·피드백과 참고 영상을 확인할 수 있습니다.

## 100분 운영

0–8 미션·시연 / 8–20 준비 확인 / 20–32 핵심 개념·실험 / 32–42 채팅 연결 / 42–62 함께 제작 / 62–82 개인 제작 / 82–92 짝 테스트·개선 / 92–100 공유·활동지.

설치 파일·두 모델의 `blobs` + `manifests`·Twinny는 사전 배포합니다. 05·06 상세 이론과 FIM은 선택, 14–16 파이썬은 다음 차시입니다. 필수 채팅 실험은 08의 연습 1·5입니다.

## 다음 차시 — Qwen + VS Code로 PySide6 GUI 바이브코딩

14장에서 프로젝트별 venv를 만들고 API를 확인합니다. 15장은 화면 생성 프롬프트 → GUI 개선 → 실제 Ollama 연결 → QThread/Signal로 응답성 유지 → 오류 처리·재검증 순서입니다. 16장에서는 같은 앱을 다른 주제로 확장합니다. 완성본 다운로드는 막혔을 때의 비교 자료입니다.

Windows의 프로젝트 폴더에서 VS Code **Command Prompt(cmd)** 터미널을 사용합니다.

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r code/requirements.txt
python code/tutor_app.py
```

위 명령은 저장소 루트 기준입니다. 학생이 `tutor_app.py`, `requirements.txt`를 별도 프로젝트에 내려받았다면 `code/`를 빼고 실행합니다. Python 확장을 쓰면 `.venv` 인터프리터도 선택합니다. 터미널을 새로 열면 다시 활성화합니다.

Linux/macOS에서는:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r code/requirements.txt
python code/tutor_app.py
```

Debian/Ubuntu에서는 `python3-venv`와 GUI 실행용 시스템 라이브러리가 필요할 수 있습니다. 패키지는 venv에 설치하며, `.venv` 폴더는 PC별로 생성하고 공유하지 않습니다. 참고 앱은 분석 중 창 닫기를 보류하고 완료 후 다시 닫도록 안내합니다. 즉시 요청 취소 기능은 포함하지 않습니다.
