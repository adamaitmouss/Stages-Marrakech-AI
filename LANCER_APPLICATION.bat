@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo ERREUR : environnement Python absent. Lancez d'abord INSTALLER_WINDOWS.bat.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" "scripts\verify_installation.py"
if errorlevel 1 (
  echo.
  echo L'application n'a pas demarre : corrigez les points signales ci-dessus.
  pause
  exit /b 1
)
echo.
echo Ouverture disponible dans votre navigateur : http://127.0.0.1:5000
echo Le serveur reste local a cet ordinateur. Pour l'arreter, appuyez sur Ctrl+C.
echo.
".venv\Scripts\python.exe" "backend\app.py"
if errorlevel 1 echo ERREUR : le serveur s'est arrete avec une erreur. Consultez le message ci-dessus.
pause
