from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from scripts.verify_installation import verify_installation


ROOT = Path(__file__).resolve().parents[1]


def make_project(root: Path) -> Path:
    for relative in ("backend/app.py", ".env.example", "requirements.txt"):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# fixture\n", encoding="utf-8")
    (root / "database").mkdir(parents=True, exist_ok=True)
    (root / ".env").write_text("SMTP_ENABLED=false\n", encoding="utf-8")
    (root / ".venv/Scripts").mkdir(parents=True)
    (root / ".venv/Scripts/python.exe").write_bytes(b"fixture")
    database = root / "database/stages_marrakech.db"
    with sqlite3.connect(database) as db:
        db.executescript(
            "CREATE TABLE entreprises(name TEXT);"
            "CREATE TABLE offres(name TEXT);"
            "CREATE TABLE candidatures(name TEXT);"
            "INSERT INTO entreprises VALUES ('A'),('B');"
            "INSERT INTO offres VALUES ('X');"
        )
    return database


def test_installation_checker_reads_required_files_and_sqlite(tmp_path,monkeypatch):
    database = make_project(tmp_path)
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    monkeypatch.delenv('DATABASE',raising=False)

    result = verify_installation(tmp_path, check_modules=False)

    assert result["ok"] is True
    sqlite_check = next(item for item in result["checks"] if item["name"] == "SQLite")
    assert "\"entreprises\": 2" in sqlite_check["detail"]
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before


def test_installation_checker_explains_missing_env_and_venv(tmp_path):
    make_project(tmp_path)
    (tmp_path / ".env").unlink()
    (tmp_path / ".venv/Scripts/python.exe").unlink()

    result = verify_installation(tmp_path, check_modules=False)

    assert result["ok"] is False
    detail = " ".join(str(item["detail"]) for item in result["checks"])
    assert "INSTALLER_WINDOWS.bat" in detail


def test_installer_and_launcher_preserve_env_and_require_confirmation():
    installer = (ROOT / "INSTALLER_WINDOWS.bat").read_text(encoding="utf-8").lower()
    launcher = (ROOT / "LANCER_APPLICATION.bat").read_text(encoding="utf-8").lower()
    source = (ROOT / "backend/app.py").read_text(encoding="utf-8")

    assert 'if not exist ".env"' in installer
    assert "choice /c on" in installer
    assert 'pip install -r "requirements.txt"' in installer
    assert 'set "python_cmd="' in installer
    assert "python -c \"import sys;" in installer
    assert "127.0.0.1" in source
    assert "backend\\app.py" in launcher
    assert "runas" not in installer + launcher
    assert "rmdir" not in installer + launcher
    assert "del /" not in installer + launcher


def test_soutenance_launcher_pins_private_database_and_fails_closed():
    launcher_path=ROOT/'LANCER_SOUTENANCE_LOCALE.bat'
    if not launcher_path.is_file():
        pytest.skip('Le lanceur de soutenance locale privée est exclu de la copie publique.')
    launcher=launcher_path.read_text(encoding='utf-8').lower()
    verifier=(ROOT/'scripts/verify_soutenance.py').read_text(encoding='utf-8').lower()
    assert 'database\\stages_marrakech.db' in launcher
    assert 'public_demo_mode=false' in launcher
    assert 'cookie_secure=false' in launcher and 'trust_proxy=false' in launcher
    assert 'scripts\\verify_soutenance.py' in launcher
    assert 'if errorlevel 1' in launcher
    assert 'integrity_check' in verifier and 'port_is_available' in verifier
    assert 'deployment_metadata' in verifier and "'synthetic_public_demo'" in verifier


def test_legacy_launcher_forwards_to_new_launcher():
    content = (ROOT / "LANCER_WINDOWS.bat").read_text(encoding="utf-8").lower()
    assert "lancer_application.bat" in content
