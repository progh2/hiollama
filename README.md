# 로컬 LLM으로 바이브코딩 시작하기

100분 수업용 실습 자료. **RTX 2060(6GB) / Windows 데스크톱 / VS Code** 환경 기준.

👉 **[실습 페이지 열기](https://progh2.github.io/hiollama/)**

## 구성

| 파일 | 용도 |
|---|---|
| `index.html` | 실습 페이지 (이론 → 설치 → 바이브코딩). 단일 파일, 외부 CDN 없음 |
| `check-env.bat` | 학생 PC 사전 점검 — 더블클릭 실행 (GPU·VRAM·드라이버·디스크·VS Code·Ollama) |

실습 페이지 `06 PC 점검` 챕터에서 바로 내려받을 수 있습니다.

> **순수 cmd 배치입니다.** PowerShell 실행 정책·백신·관리자 권한 문제를 피하려고
> 윈도우 기본 명령(`reg`/`dir`/`where`/`netstat`)만 사용합니다.
> 한국어 Windows 콘솔에서 바로 읽히도록 **CP949 + CRLF**로 저장되어 있으니
> 편집 시 인코딩을 유지하세요.

## 환경 전제

- **GPU**: RTX 2060 6GB (NVIDIA 드라이버 551.61 이상)
- **모델**: `qwen2.5-coder:3b` (1.9GB) — 코딩 전용, 6GB에 여유롭게 적재
- **VS Code**: 1.127 이상 + 공식 Ollama 확장 (GitHub 로그인·Copilot 구독 불필요)
- 모델 확보는 두 경로를 모두 안내: **넷클래스/USB 사전 배포**(`blobs` + `manifests`, 권장) 또는 `ollama pull qwen2.5-coder:3b` 직접 다운로드

> ⚠️ `gemma4:e2b`는 이름이 "2B"지만 실제 용량 **7.2GB** (MatFormer, effective 파라미터 표기) + thinking 모드로 매우 느림 → 6GB 카드에 부적합

## 수업 설계 메모

- 실습 과제는 **단일 HTML 파일 웹앱** — 의존성 설치 0, 브라우저에서 즉시 확인
- 프롬프트에 **"외부 라이브러리·CDN 금지"** 필수 (없으면 빈 화면 사고 다발)
- 발표에 **"끝까지 안 된 것"**을 필수 항목으로 → 작은 모델의 한계를 학습 소재로 전환
