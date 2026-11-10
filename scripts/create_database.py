"""Import non destructif ; point d?entr?e historique conserv?."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.import_data import import_excel

if __name__ == "__main__":
    import_excel()
