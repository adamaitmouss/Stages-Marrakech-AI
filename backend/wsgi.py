"""WSGI entry point used by production servers such as Gunicorn."""
from .web import create_app

app=create_app()
