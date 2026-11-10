from pathlib import Path

from backend.config import ROOT, settings


def test_relative_database_and_private_paths_are_anchored_to_project_root(tmp_path, monkeypatch):
    for key in ('DATABASE', 'PRIVATE_DIR', 'BACKUP_DIR'):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.chdir(tmp_path)

    config = settings({'DATABASE': 'database/stages_marrakech.db', 'PRIVATE_DIR': 'private', 'BACKUP_DIR': 'backups'})

    assert Path(config['DATABASE']) == (ROOT / 'database/stages_marrakech.db').resolve()
    assert Path(config['PRIVATE_DIR']) == (ROOT / 'private').resolve()
    assert Path(config['BACKUP_DIR']) == (ROOT / 'backups').resolve()


def test_absolute_override_paths_are_preserved(tmp_path):
    config = settings({'DATABASE': str(tmp_path / 'data.db'), 'PRIVATE_DIR': str(tmp_path / 'private'),
                       'BACKUP_DIR': str(tmp_path / 'backups')})
    assert config['DATABASE'] == str((tmp_path / 'data.db').resolve())
    assert config['PRIVATE_DIR'] == str((tmp_path / 'private').resolve())
    assert config['BACKUP_DIR'] == str((tmp_path / 'backups').resolve())


def test_soutenance_port_check_detects_another_listener():
    import socket
    from scripts.verify_soutenance import port_is_available

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(('127.0.0.1', 0))
        port=listener.getsockname()[1]
        available, detail=port_is_available(port)
        assert available is False and 'occupé' in detail

    available, detail=port_is_available(port)
    assert available is True and 'libre' in detail


def test_soutenance_verifier_rejects_public_demo_mode(monkeypatch):
    from scripts.verify_soutenance import inspect_environment

    monkeypatch.setenv('DATABASE',str(ROOT/'database'/'stages_marrakech.db'))
    monkeypatch.setenv('PUBLIC_DEMO_MODE','true')
    result=inspect_environment(check_port=False)

    assert result['ok'] is False
    assert any(label=='Mode privé' and not passed for label,passed,_ in result['checks'])
