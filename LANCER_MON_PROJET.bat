@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo  STAGES MARRAKECH AI — VERSION HISTORIQUE LOCALE
echo  ------------------------------------------------
if not exist ".venv\Scripts\python.exe" (
  echo ERREUR : environnement Python absent. Lancez INSTALLER_WINDOWS.bat.
  pause
  exit /b 1
)
if not exist "auth_gateway\.env.auth" (
  echo ERREUR : configuration locale Login absente. Aucun profil Demo ne sera cree automatiquement.
  echo Restaurez la configuration locale privee avant de relancer.
  pause
  exit /b 1
)

rem Profil local multi-utilisateur : chaque compte etudiant obtient son SQLite prive.
rem L'administrateur conserve la base historique; les anciens dossiers personnels ne sont pas copies.
set "AUTH_CONFIG_FILE=%CD%\auth_gateway\.env.auth"
set "AUTH_PROFILE=multi_user"
set "AUTH_INTERNAL_SECRET_FILE=%CD%\private\auth_gateway_internal.secret"
set "AUTH_APP_DATABASE=%CD%\database\stages_marrakech.db"
set "AUTH_ALLOW_REGISTRATION=true"
set "AUTH_GATEWAY_PORT=5000"
set "AUTH_BACKEND_PORT=5101"
set "DATABASE=%CD%\database\stages_marrakech.db"
set "PRIVATE_DIR=%CD%\private"
set "BACKUP_DIR=%CD%\backups"
set "PUBLIC_DEMO_MODE=false"
set "PUBLIC_DEMO_DATA_CONFIRMED=false"
set "COOKIE_SECURE=false"
set "TRUST_PROXY=false"
set "SMTP_ENABLED=false"
set "GEMINI_ENABLED=false"
set "GEMINI_SEARCH_ENABLED=false"
set "MAPS_ENABLED=false"

".venv\Scripts\python.exe" "scripts\verify_soutenance.py"
if errorlevel 1 (
  echo.
  echo Aucun processus existant n'a ete arrete. Si le port 5000 est occupe, fermez uniquement la fenetre du serveur que vous avez lancee.
  pause
  exit /b 1
)

echo.
echo Profil historique avec Login : http://127.0.0.1:5000
echo Si ce port est deja occupe, le lancement s'arrete sans toucher au processus existant.
echo Ctrl+C arrete uniquement les serveurs demarres par cette fenetre.
echo.
".venv\Scripts\python.exe" -m auth_gateway.launcher
if errorlevel 1 (
  echo.
  echo Le lancement a echoue. Aucun processus externe n'a ete arrete.
  pause
  exit /b 1
)
pause
exit /b 0
