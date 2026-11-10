"""Read-only checks for a local Windows installation."""
from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULES = {
    "Flask": "flask",
    "Werkzeug": "werkzeug",
    "Dash": "dash",
    "Plotly": "plotly",
    "Pandas": "pandas",
    "ReportLab": "reportlab",
    "OpenPyXL": "openpyxl",
    "Requests": "requests",
    "Beautiful Soup": "bs4",
    "Matplotlib": "matplotlib",
    "pypdf": "pypdf",
    "Cryptography": "cryptography",
    "python-dotenv": "dotenv",
    "Google GenAI SDK": "google.genai",
}


def verify_installation(project_root: Path | str = ROOT, check_modules: bool = True) -> dict:
    """Inspect project files, active interpreter packages and SQLite without writes."""
    root = Path(project_root).resolve()
    checks: list[dict[str, str | bool]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    database_setting=os.getenv('DATABASE')
    if not database_setting:
        config_file=root/'.env' if (root/'.env').is_file() else root/'.env.example'
        try:
            for line in config_file.read_text(encoding='utf-8').splitlines():
                if line.strip().startswith('DATABASE='):
                    database_setting=line.split('=',1)[1].strip().strip('"\'');break
        except OSError:pass
    database_rel=database_setting or 'database/stages_marrakech.db'
    required = ("requirements.txt", ".env.example", "backend/app.py", database_rel)
    for relative in required:
        path = root / relative
        add(relative, path.is_file(), "présent" if path.is_file() else "fichier requis introuvable")

    env_file = root / ".env"
    add(".env", env_file.is_file(), "présent (son contenu n'est pas affiché)" if env_file.is_file()
        else "absent ; lancer INSTALLER_WINDOWS.bat pour le créer depuis .env.example")

    venv_python = root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    add(".venv", venv_python.is_file(), "interpréteur virtuel présent" if venv_python.is_file()
        else "environnement virtuel absent ; lancer INSTALLER_WINDOWS.bat")

    if check_modules:
        expected_venv = (root / ".venv").resolve()
        try:
            active_venv = Path(sys.executable).resolve().is_relative_to(expected_venv)
        except (OSError, ValueError):
            active_venv = False
        add("Interpréteur actif", active_venv,
            "Python du .venv de ce projet" if active_venv else "lancer ce contrôle avec .venv\\Scripts\\python.exe")
        for label, module in MODULES.items():
            try:
                available = importlib.util.find_spec(module) is not None
            except (ImportError, ModuleNotFoundError, ValueError):
                available = False
            add(label, available, "installé" if available else "manquant dans l'environnement courant")

    db_path = Path(database_rel)
    if not db_path.is_absolute():db_path=root/db_path
    if db_path.is_file():
        try:
            uri = db_path.as_uri() + "?mode=ro"
            with sqlite3.connect(uri, uri=True, timeout=5) as db:
                integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
                counts = {}
                for table in ("entreprises", "offres", "candidatures"):
                    # Table names are fixed constants, never user input.
                    counts[table] = db.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            add("SQLite", integrity == "ok", f"intégrité {integrity}; données {json.dumps(counts, ensure_ascii=False)}")
        except (sqlite3.Error, OSError) as exc:
            add("SQLite", False, f"lecture impossible : {exc}")
    else:
        add("SQLite", False, f"base {database_rel} absente")

    result = {"ok": all(item["ok"] for item in checks), "python": sys.version.split()[0], "checks": checks}
    return result


def main() -> int:
    result = verify_installation()
    print(f"Vérification de Stages Marrakech AI — Python {result['python']}")
    for check in result["checks"]:
        state = "OK" if check["ok"] else "À corriger"
        print(f"[{state}] {check['name']}: {check['detail']}")
    if not result["ok"]:
        print("\nUtilisez INSTALLER_WINDOWS.bat pour réparer l'installation. Aucun fichier de données n'a été modifié.")
        return 1
    print("\nInstallation prête. L'application utilise uniquement 127.0.0.1:5000.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
