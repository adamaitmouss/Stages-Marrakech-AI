"""Run a local, read-only demo using only the bundled synthetic database."""
import os
import tempfile
from pathlib import Path

from backend.config import ROOT
from backend.web import create_app

port=int(os.getenv('PORT','5000'))
private=tempfile.TemporaryDirectory(prefix='stages_public_demo_')
app=create_app({
    'DATABASE':str(ROOT/'database/stages_marrakech_public_demo.db'),
    'PRIVATE_DIR':str(Path(private.name)/'private'),
    'BACKUP_DIR':str(Path(private.name)/'backups'),
    'TRUSTED_HOSTS':['127.0.0.1','localhost','[::1]'],
    'PUBLIC_DEMO_MODE':True,'PUBLIC_DEMO_DATA_CONFIRMED':True,
    'GEMINI_ENABLED':False,'GEMINI_SEARCH_ENABLED':False,'SMTP_ENABLED':False,'MAPS_ENABLED':False,
    'DISABLE_BACKGROUND_SCHEDULER':True,
})
if __name__=='__main__':
    app.run(host='127.0.0.1',port=port,debug=False)
