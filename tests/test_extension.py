"""Extension QGIS : l'archive versionnée (sorties/extension) reprend exactement les sources, dont l'outil
qgis/outils/fiche_zone.py ; une modification de l'outil sans nouvelle archive fait échouer ce test.
(Le test de bout en bout dans QGIS : tests/qgis_extension.py, avec le Python de QGIS.)"""
import configparser
import zipfile

from conftest import RACINE
from empaqueter_extension import ENVELOPPE, NOM, OUTIL, SORTIE


def test_archive_a_jour():
    with zipfile.ZipFile(SORTIE) as z:
        contenu = {n.split("/", 1)[1]: z.read(n) for n in z.namelist()}
    sources = {f.name: f.read_bytes() for f in ENVELOPPE.glob("*") if f.suffix in (".py", ".txt")}
    sources["fiche_zone.py"] = OUTIL.read_bytes()
    assert contenu == sources, "archive périmée : relancer python scripts/empaqueter_extension.py"


def test_metadonnees():
    meta = configparser.ConfigParser()
    meta.read(ENVELOPPE / "metadata.txt", encoding="utf-8")
    g = meta["general"]
    assert g["hasProcessingProvider"] == "yes" and g["qgisMinimumVersion"] >= "3.28"
    assert (RACINE / "qgis" / "extension" / NOM / "__init__.py").read_text(encoding="utf-8").count("def classFactory") == 1
