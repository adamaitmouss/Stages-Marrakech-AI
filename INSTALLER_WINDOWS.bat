@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo  Installation de Stages Marrakech AI
echo  -----------------------------------
if not exist "requirements.txt" (
  echo ERREUR : requirements.txt est absent. Extrayez l'archive complete et relancez ce fichier.
  pause
  exit /b 1
)
if not exist ".env.example" (
  echo ERREUR : .env.example est absent. Le dossier extrait semble incomplet.
  pause
  exit /b 1
)
if not exist "backend\app.py" (
  echo ERREUR : backend\app.py est absent. Le dossier extrait semble incomplet.
  pause
  exit /b 1
)

set "PYTHON_CMD="
where py >nul 2>&1
if not errorlevel 1 (
  py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>&1
  if not errorlevel 1 set "PYTHON_CMD=py -3.12"
)
if not defined PYTHON_CMD (
  where python >nul 2>&1
  if not errorlevel 1 (
    python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python"
  )
)
if not defined PYTHON_CMD (
  echo ERREUR : Python 3.12 est requis. Installez Python 3.12 pour votre compte Windows, puis relancez ce fichier.
  echo Aucun droit administrateur ni modification de Python global n'est necessaire.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creation de l'environnement virtuel local .venv...
  %PYTHON_CMD% -m venv .venv
  if errorlevel 1 (
    echo ERREUR : creation de .venv impossible. Verifiez que Python 3.12 inclut le module venv.
    pause
    exit /b 1
  )
)

if not exist ".env" (
  copy /Y ".env.example" ".env" >nul
  if errorlevel 1 (
    echo ERREUR : impossible de creer .env depuis .env.example.
    pause
    exit /b 1
  )
  echo Configuration locale .env creee avec les services externes desactives.
) else (
  echo Votre fichier .env existant est conserve sans modification.
)

echo.
echo L'installation des dependances telecharge des paquets depuis Internet.
choice /C ON /N /M "Installer maintenant depuis Internet ? [O]ui / [N]on : "
if errorlevel 2 (
  echo Installation des dependances annulee. Vous pourrez relancer ce fichier plus tard.
  pause
  exit /b 0
)

echo Installation des dependances dans .venv uniquement...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
  echo ERREUR : mise a jour de pip impossible. Verifiez Internet puis relancez l'installation.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r "requirements.txt"
if errorlevel 1 (
  echo ERREUR : certaines dependances n'ont pas pu etre installees.
  echo Verifiez la connexion Internet et relancez ce fichier ; les donnees n'ont pas ete supprimees.
  pause
  exit /b 1
)

echo.
echo Installation terminee. Lancez LANCER_MON_PROJET.bat pour l'application historique avec Login.
pause
exit /b 0
