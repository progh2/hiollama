# Ollama 수업 사전 점검 스크립트
# 실습실 PC에서 실행하여 GPU / 드라이버 / 디스크 / VS Code / Ollama 상태를 확인합니다.

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'SilentlyContinue'

$log = Join-Path $PSScriptRoot ("check-{0}-{1}.txt" -f $env:COMPUTERNAME, (Get-Date -Format 'MMdd-HHmm'))
$out = New-Object System.Collections.ArrayList

function Say($msg, $color = 'Gray') {
    Write-Host $msg -ForegroundColor $color
    [void]$out.Add($msg)
}
function Head($msg) {
    Say ""
    Say ("=" * 60) 'DarkGray'
    Say "  $msg" 'Cyan'
    Say ("=" * 60) 'DarkGray'
}

Head "Ollama 수업 환경 점검  |  $env:COMPUTERNAME  |  $(Get-Date -Format 'yyyy-MM-dd HH:mm')"

# ---------- 1. Windows ----------
Head "1. Windows"
$os = Get-CimInstance Win32_OperatingSystem
$dv = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').DisplayVersion
Say "  버전   : $($os.Caption) ($dv, build $($os.BuildNumber))"
Say ("  메모리 : {0:N1} GB" -f ($os.TotalVisibleMemorySize / 1MB))
if ([int]$os.BuildNumber -ge 19045) { Say "  [OK] Windows 10 22H2 이상 - Ollama 지원" 'Green' }
else { Say "  [경고] Ollama는 Windows 10 22H2 이상 필요" 'Red' }

# ---------- 2. GPU ----------
Head "2. GPU / VRAM"
$gpuFound = $false
$vramGB = 0
$smi = Get-Command nvidia-smi -ErrorAction SilentlyContinue

if ($smi) {
    $gpuFound = $true
    $q = & nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>$null
    foreach ($line in $q) {
        $p = $line -split ',\s*'
        Say "  카드       : $($p[0])"
        Say "  VRAM       : $($p[1])"
        Say "  드라이버   : $($p[2])"
        if ($p[1] -match '(\d+)') { $vramGB = [math]::Round([int]$Matches[1] / 1024, 1) }

        # 드라이버 551.61 이상 필요
        if ($p[2] -match '^(\d+)\.(\d+)') {
            $maj = [int]$Matches[1]; $min = [int]$Matches[2]
            if ($maj -gt 551 -or ($maj -eq 551 -and $min -ge 61)) {
                Say "  [OK] 드라이버 551.61 이상 - GPU 가속 사용 가능" 'Green'
            } else {
                Say "  [경고] 드라이버가 551.61 미만입니다. GPU 가속이 안 되고" 'Red'
                Say "         CPU로 동작하여 매우 느려집니다. 수업 전 업데이트 필요!" 'Red'
            }
        }
    }
} else {
    Say "  [경고] nvidia-smi 없음 - NVIDIA GPU가 없거나 드라이버 미설치" 'Red'
    Say "  아래는 Windows가 인식한 디스플레이 어댑터입니다:" 'DarkGray'
    Get-CimInstance Win32_VideoController | ForEach-Object {
        Say "    - $($_.Name)  (드라이버 $($_.DriverVersion))"
    }
    # 레지스트리에서 VRAM 재확인 (AdapterRAM은 4GB 초과 시 부정확)
    $key = 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000'
    $qw = (Get-ItemProperty $key).'HardwareInformation.qwMemorySize'
    if ($qw) {
        $vramGB = [math]::Round($qw / 1GB, 1)
        Say "    VRAM(레지스트리 기준): $vramGB GB"
    }
}

# ---------- 3. 모델 권장 ----------
Head "3. 권장 모델 등급"
if ($vramGB -ge 7.5)     { Say "  VRAM ${vramGB}GB -> 7~8B급(Q4, ~5GB)까지 여유. 4B급 권장" 'Green' }
elseif ($vramGB -ge 5.5) { Say "  VRAM ${vramGB}GB -> [주력] 4B급 Q4 (~3.3GB) 권장" 'Green' }
elseif ($vramGB -ge 3.5) { Say "  VRAM ${vramGB}GB -> [예비] 1~3B급 Q4 (~1-2GB) 사용" 'Yellow' }
elseif ($vramGB -gt 0)   { Say "  VRAM ${vramGB}GB -> GPU 가속 어려움. 1B급 또는 CPU 실행" 'Red' }
else                     { Say "  VRAM 확인 실패 - 수동 확인 필요" 'Red' }

# ---------- 4. 디스크 ----------
Head "4. 디스크 여유 공간 (C:)"
$c = Get-PSDrive C
$freeGB = [math]::Round($c.Free / 1GB, 1)
Say "  여유 공간: $freeGB GB"
if ($freeGB -ge 10) { Say "  [OK] Ollama(4GB) + 모델 설치 가능" 'Green' }
else { Say "  [경고] 10GB 이상 확보 권장 (Ollama 바이너리만 4GB)" 'Red' }

# ---------- 5. VS Code ----------
Head "5. VS Code"
$code = Get-Command code -ErrorAction SilentlyContinue
if ($code) {
    $ver = (& code --version 2>$null)[0]
    Say "  설치됨: $ver"
    $parts = $ver -split '\.'
    if ([int]$parts[0] -gt 1 -or ([int]$parts[0] -eq 1 -and [int]$parts[1] -ge 127)) {
        Say "  [OK] 1.127 이상 - 공식 Ollama 확장 사용 가능" 'Green'
    } else {
        Say "  [경고] 공식 Ollama 확장은 VS Code 1.127 이상 필요" 'Red'
    }
} else {
    Say "  [경고] code 명령을 찾을 수 없음 (미설치이거나 PATH 미등록)" 'Yellow'
}

# ---------- 6. Ollama ----------
Head "6. Ollama"
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollama) {
    Say "  설치됨: $(& ollama --version 2>$null)"
    $conn = Test-NetConnection -ComputerName 127.0.0.1 -Port 11434 -WarningAction SilentlyContinue
    if ($conn.TcpTestSucceeded) {
        Say "  [OK] 서버 응답 중 (127.0.0.1:11434)" 'Green'
        Say "  보유 모델:"
        (& ollama list 2>$null) | ForEach-Object { Say "    $_" }
    } else {
        Say "  [경고] 설치는 됐으나 서버가 응답하지 않음. Ollama 실행 필요" 'Yellow'
    }
    Say ""
    Say "  모델 경로: $(if ($env:OLLAMA_MODELS) { $env:OLLAMA_MODELS } else { "$env:USERPROFILE\.ollama\models (기본값)" })"
} else {
    Say "  미설치 - OllamaSetup.exe 실행 필요 (관리자 권한 불필요)" 'Yellow'
}

Head "점검 완료"
Say "  결과 저장: $log"
$out | Out-File -FilePath $log -Encoding UTF8
Write-Host ""
Read-Host "엔터를 누르면 종료합니다"
