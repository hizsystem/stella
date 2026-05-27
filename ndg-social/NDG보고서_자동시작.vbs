Dim projectDir, pythonExe, oShell

projectDir = "c:\AI_stella\NDG\NDG_소셜 보고서\ndg-report-system"
pythonExe  = projectDir & "\.venv\Scripts\pythonw.exe"

Set oShell = CreateObject("WScript.Shell")

' 이미 실행 중이면 종료
Dim port
port = oShell.Run("cmd /c netstat -ano | findstr :8002", 0, True)
If port = 0 Then WScript.Quit

' 환경변수 및 작업 디렉토리 설정
oShell.Environment("Process")("PYTHONPATH") = projectDir
oShell.CurrentDirectory = projectDir

' 창 없이 백그라운드 실행 (0=숨김, False=기다리지 않음)
oShell.Run """" & pythonExe & """ -m uvicorn backend.main:app --host 0.0.0.0 --port 8002", 0, False
