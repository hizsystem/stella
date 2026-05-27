@echo off
chcp 65001 > nul
title NDG 보고서 시스템

:: 이미 실행 중인지 확인
netstat -ano | findstr ":8002" > nul 2>&1
if %errorlevel% == 0 (
    echo 서버가 이미 실행 중입니다. 브라우저를 엽니다...
    start "" "http://localhost:8002/"
    exit /b 0
)

:: 서버 시작
echo NDG 보고서 서버를 시작합니다...
set PROJECTDIR=%~dp0
set PYTHONPATH=%PROJECTDIR%

start /min "" "%PROJECTDIR%.venv\Scripts\python.exe" -m uvicorn backend.main:app --host 0.0.0.0 --port 8002

:: 서버 준비 대기 (최대 10초)
set /a tries=0
:wait_loop
timeout /t 1 /nobreak > nul
netstat -ano | findstr ":8002" > nul 2>&1
if %errorlevel% == 0 goto server_ready
set /a tries+=1
if %tries% lss 10 goto wait_loop
echo 서버 시작에 실패했습니다. 로그를 확인해주세요.
pause
exit /b 1

:server_ready
echo 서버 준비 완료! 브라우저를 엽니다...
start "" "http://localhost:8002/"
exit /b 0
