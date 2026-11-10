@echo off
setlocal
cd /d "%~dp0"
call "LANCER_APPLICATION.bat"
exit /b %ERRORLEVEL%
