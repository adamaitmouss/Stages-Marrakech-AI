@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo ERREUR : environnement Python absent. Lancez INSTALLER_WINDOWS.bat puis reessayez.
  pause
  exit /b 1
)

rem Profil local explicite : ne jamais selectionner la base de demonstration.
set "DATABASE=%CD%\database\stages_marrakech.db"
set "PRIVATE_DIR=%CD%\private"
set "BACKUP_DIR=%CD%\backups"
set "COOKIE_SECURE=false"
set "TRUST_PROXY=false"
set "PUBLIC_DEMO_MODE=false"
set "PUBLIC_DEMO_DATA_CONFIRMED=false"

".venv\Scripts\python.exe" "scripts\verify_soutenance.py"
if errorlevel 1 (
  echo.
  echo Le serveur n'a pas demarre. Corrigez les erreurs ci-dessus; aucune base n'a ete modifiee.
  pause
  exit /b 1
)

echo.
echo Profil local prive : donnees historiques. URL : http://127.0.0.1:5000
echo Pour arreter le serveur, appuyez sur Ctrl+C dans cette fenetre.
echo.
".venv\Scripts\python.exe" "backend\app.py"
if errorlevel 1 echo ERREUR : le serveur s'est arrete. Consultez le message ci-dessus.
pause
