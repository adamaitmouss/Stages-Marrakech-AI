"""Point WSGI de la passerelle. En production, le backend doit rester privé."""
from .app import create_app

app = create_app()
