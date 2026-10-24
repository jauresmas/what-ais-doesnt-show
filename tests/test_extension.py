"""Extension QGIS : l'archive versionnée (sorties/extension) reprend exactement les sources, dont l'outil
qgis/outils/fiche_zone.py ; une modification de l'outil sans nouvelle archive fait échouer ce test.
Les fins de ligne sont comparées normalisées : Git les écrit en CRLF sous Windows, en LF sous Linux.
(Le test de bout en bout dans QGIS : tests/qgis_extension.py, avec le Python de QGIS.)"""
import configparser
import zipfile

from conftest import RACINE
from empaqueter_extension import ENVELOPPE, NOM, SORTIE, fichiers


def test_archive_a_jour():
    with zipfile.ZipFile(SORTIE) as z:
        contenu = {n.split("/", 1)[1]: z.read(n).replace(b"\r\n", b"\n") for n in z.namelist()}
    assert contenu == fichiers(), "archive périmée : relancer python scripts/empaqueter_extension.py"


def test_archive_reproductible(tmp_path, monkeypatch):
    """Deux constructions successives donnent la même archive, octet pour octet."""
    import empaqueter_extension as e
    monkeypatch.setattr(e, "SORTIE", tmp_path / "a.zip")
    a = e.construire()[0].read_bytes()
    monkeypatch.setattr(e, "SORTIE", tmp_path / "b.zip")
    assert e.construire()[0].read_bytes() == a


def test_metadonnees():
    meta = configparser.ConfigParser()
    meta.read(ENVELOPPE / "metadata.txt", encoding="utf-8")
    g = meta["general"]
    assert g["hasProcessingProvider"] == "yes" and g["qgisMinimumVersion"] >= "3.28"
    assert (RACINE / "qgis" / "extension" / NOM / "__init__.py").read_text(encoding="utf-8").count("def classFactory") == 1
