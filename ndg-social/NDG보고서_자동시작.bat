@echo off
:: 작업 스케줄러 전용 — 창 없이 서버만 시작 (브라우저 열지 않음)

:: 이미 실행 중이면 종료
netstat -ano | findstr ":8002" > nul 2>&1
if %errorlevel% == 0 exit /b 0

set PROJECTDIR=%~dp0
set PYTHONPATH=%PROJECTDIR%

start "" /min "%PROJECTDIR%.venv\Scripts\pythonw.exe" -m uvicorn backend.main:app --host 0.0.0.0 --port 8002
