"""Tests de la chaîne : règles, données publiées, carte web. Aucun ne demande la base PostgreSQL :
ils tournent sur les fichiers versionnés, sur le poste comme sur GitHub Actions.

    python -m pytest                 tous les tests
    python -m pytest -m "not web"    sans navigateur
"""
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))


def pytest_configure(config):
    config.addinivalue_line("markers", "web: test dans un navigateur (Playwright)")
