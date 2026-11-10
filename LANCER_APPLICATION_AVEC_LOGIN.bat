@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call "LANCER_MON_PROJET.bat"
exit /b %ERRORLEVEL%
