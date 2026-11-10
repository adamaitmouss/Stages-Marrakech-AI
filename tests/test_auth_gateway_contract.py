"""Expose les tests isolés de la passerelle au `pytest -q` habituel du projet."""
from auth_gateway.tests.test_gateway import *  # noqa: F401,F403
