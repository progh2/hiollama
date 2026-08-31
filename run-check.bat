@echo off
REM Ollama class - environment check launcher
REM Keep this file ASCII-only. Korean output comes from check-env.ps1.
chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0check-env.ps1"
