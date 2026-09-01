@echo off
setlocal enabledelayedexpansion
title Ollama 수업 환경 점검
color 07
set "LOG=%~dp0check-%COMPUTERNAME%.txt"
if exist "%LOG%" del "%LOG%" >nul 2>&1
set "TMPG=%TEMP%\_ollchk_gpu.txt"
set "TMPL=%TEMP%\_ollchk_list.txt"

call :hd "Ollama 수업 환경 점검"
call :say "  PC 이름 : %COMPUTERNAME%"
call :say "  점검 시각 : %DATE% %TIME:~0,5%"

rem ============================================================
call :hd "1. Windows"
set "WNAME=" & set "WVER=" & set "WBUILD="
for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v ProductName 2^>nul ^| find "REG_SZ"') do set "WNAME=%%b"
for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v DisplayVersion 2^>nul ^| find "REG_SZ"') do set "WVER=%%b"
for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v CurrentBuild 2^>nul ^| find "REG_SZ"') do set "WBUILD=%%b"
call :say "  버전 : !WNAME! !WVER!  (build !WBUILD!)"
set /a BN=!WBUILD! 2>nul
if !BN! GEQ 19045 (call :ok "Windows 10 22H2 이상 - Ollama 지원") else (call :warn "Ollama 는 Windows 10 22H2 이상 필요")

rem ============================================================
call :hd "2. 그래픽카드 / VRAM / 드라이버"
set "VRAMGB=0"
set "HASGPU=0"
where nvidia-smi >nul 2>&1
if errorlevel 1 goto :nosmi

nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader > "%TMPG%" 2>nul
if not exist "%TMPG%" goto :nosmi
for %%S in ("%TMPG%") do if %%~zS EQU 0 goto :nosmi

for /f "usebackq tokens=1,2,3 delims=," %%a in ("%TMPG%") do (
  set "GPU=%%a" & set "VRAM=%%b" & set "DRV=%%c"
)
del "%TMPG%" >nul 2>&1
set "GPU=!GPU: =!" & set "VRAM=!VRAM: =!" & set "DRV=!DRV: =!"
set "HASGPU=1"

call :say "  카드     : !GPU!"
call :say "  VRAM     : !VRAM!"
call :say "  드라이버 : !DRV!"

set "VMB=!VRAM:MiB=!"
set "VMB=!VMB:MB=!"
set /a VRAMGB=!VMB! / 1024 2>nul

for /f "tokens=1,2 delims=." %%x in ("!DRV!") do (set /a DMAJ=%%x & set /a DMIN=%%y)
if !DMAJ! GTR 551 goto :drvok
if !DMAJ! LSS 551 goto :drvbad
if !DMIN! GEQ 61 goto :drvok
goto :drvbad
:drvok
call :ok "드라이버 551.61 이상 - GPU 가속 사용 가능"
goto :gpudone
:drvbad
call :warn "드라이버가 551.61 미만입니다"
call :say "         GPU 를 못 쓰고 CPU 로 동작해 매우 느려집니다."
call :say "         https://www.nvidia.com/ko-kr/drivers/ 에서 업데이트하세요."
goto :gpudone

:nosmi
call :warn "nvidia-smi 없음 - NVIDIA GPU 가 없거나 드라이버 미설치"
call :say "  Windows 가 인식한 디스플레이 어댑터:"
for /f "skip=1 tokens=*" %%d in ('wmic path win32_VideoController get name 2^>nul') do (
  set "L=%%d"
  if not "!L: =!"=="" call :say "    - !L!"
)
:gpudone

rem ============================================================
call :hd "3. 권장 모델"
if "!HASGPU!"=="0" (
  call :say "  GPU 확인 실패 - 조교에게 문의하세요."
) else if !VRAMGB! GEQ 11 (
  call :ok "VRAM !VRAMGB!GB : 7B 급까지 여유. qwen2.5-coder:7b 권장"
) else if !VRAMGB! GEQ 5 (
  call :ok "VRAM !VRAMGB!GB : qwen2.5-coder:3b + 1.5b-base 권장 (합 2.9GB)"
) else if !VRAMGB! GEQ 3 (
  call :warn "VRAM !VRAMGB!GB : qwen2.5-coder:1.5b 사용 (1.0GB)"
) else (
  call :warn "VRAM !VRAMGB!GB : GPU 가속이 어렵습니다. 조교에게 문의하세요."
)

rem ============================================================
call :hd "4. 디스크 여유 공간 (%SystemDrive%)"
set "FREEB="
for /f "tokens=3" %%a in ('dir /-c "%SystemDrive%\" 2^>nul') do set "FREEB=%%a"
set "FREEGB=!FREEB:~0,-9!"
if "!FREEGB!"=="" set "FREEGB=0"
call :say "  여유 공간 : 약 !FREEGB! GB"
set /a FG=!FREEGB! 2>nul
if !FG! GEQ 10 (call :ok "설치 공간 충분") else (call :warn "10GB 이상 확보 권장")

rem ============================================================
call :hd "5. VS Code"
set "CODEVER="
where code >nul 2>&1
if errorlevel 1 (
  call :warn "code 명령을 찾을 수 없음 - 미설치이거나 PATH 미등록"
  call :say "         https://code.visualstudio.com/download"
) else (
  for /f "delims=" %%v in ('code --version 2^>nul') do if not defined CODEVER set "CODEVER=%%v"
  call :say "  버전 : !CODEVER!"
  call :ok "설치됨 - Twinny 확장을 설치해 사용합니다"
)

rem ============================================================
call :hd "6. Ollama"
where ollama >nul 2>&1
if errorlevel 1 (
  call :warn "미설치 - OllamaSetup.exe 실행 필요 (관리자 권한 불필요)"
  call :say "         https://ollama.com/download/windows"
  goto :ollend
)
for /f "delims=" %%v in ('ollama --version 2^>nul') do call :say "  %%v"

netstat -ano 2>nul | find ":11434" | find "LISTENING" >nul
if errorlevel 1 (
  call :warn "설치는 됐으나 서버가 응답하지 않음 - 시작 메뉴에서 Ollama 실행"
) else (
  call :ok "서버 동작 중 (127.0.0.1:11434)"
  call :say "  보유 모델:"
  ollama list > "%TMPL%" 2>nul
  for /f "usebackq skip=1 tokens=*" %%m in ("%TMPL%") do call :say "    %%m"
  del "%TMPL%" >nul 2>&1
)
if defined OLLAMA_MODELS (
  call :say "  모델 경로 : %OLLAMA_MODELS%"
) else (
  call :say "  모델 경로 : %USERPROFILE%\.ollama\models"
)
if defined OLLAMA_KV_CACHE_TYPE (
  call :ok "KV 캐시 설정됨 (%OLLAMA_KV_CACHE_TYPE%)"
) else (
  call :say "  [안내] OLLAMA_KV_CACHE_TYPE 미설정 - 설치 STEP 3 참고"
)
:ollend

rem ============================================================
call :hd "점검 완료"
call :say "  결과 파일 : %LOG%"
echo.
echo   [OK] 만 있으면 통과입니다.
echo   [경고] 가 있으면 그 줄을 조교에게 보여주세요.
echo.
pause
endlocal
exit /b 0

rem ================= 출력 도우미 =================
:say
echo %~1
>>"%LOG%" echo %~1
exit /b 0
:ok
echo   [OK] %~1
>>"%LOG%" echo   [OK] %~1
exit /b 0
:warn
echo   [경고] %~1
>>"%LOG%" echo   [경고] %~1
exit /b 0
:hd
echo.
echo ============================================================
echo   %~1
echo ============================================================
>>"%LOG%" echo.
>>"%LOG%" echo ============================================================
>>"%LOG%" echo   %~1
>>"%LOG%" echo ============================================================
exit /b 0
