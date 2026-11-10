@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo ERREUR : .venv\Scripts\python.exe est absent. Lancez INSTALLER_WINDOWS.bat.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" "scripts\verify_installation.py"
set "RESULT=%ERRORLEVEL%"
echo.
if not "%RESULT%"=="0" echo Une ou plusieurs verifications ont echoue.
pause
exit /b %RESULT%
