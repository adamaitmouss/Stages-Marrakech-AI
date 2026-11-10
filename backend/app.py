"""Point d'entrée conservé : python backend/app.py."""
import sys
from pathlib import Path
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.web import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=False)
