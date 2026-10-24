"""Test de bout en bout de l'extension QGIS, hors interface, avec le Python de QGIS :

    "C:\\Program Files\\QGIS 3.34.12\\bin\\python-qgis-ltr.bat" tests/qgis_extension.py

Installe l'archive dans un dossier temporaire, charge l'extension comme le ferait QGIS, ouvre le projet
et produit la fiche d'une zone dessinée dans le Grand Belt. Échoue si l'algorithme n'est pas enregistré,
si la fiche n'est pas produite, ou si le PDF ne fait pas une page.
"""
import sys
import tempfile
import zipfile
from pathlib import Path

from qgis.core import QgsApplication, QgsFeature, QgsGeometry, QgsProject, QgsVectorLayer

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))

app = QgsApplication([], True)   # avec affichage : sans lui, pas de polices (voir docs/incidents_qgis.md)
app.initQgis()
sys.path.append(str(Path(QgsApplication.prefixPath()) / "python" / "plugins"))   # extension Processing de QGIS
from processing.core.Processing import Processing  # noqa: E402

Processing.initialize()
import processing  # noqa: E402

from empaqueter_extension import NOM, construire  # noqa: E402

archive, version = construire()
dossier = Path(tempfile.mkdtemp(prefix="extension_"))
with zipfile.ZipFile(archive) as z:
    z.extractall(dossier)
sys.path.insert(0, str(dossier))
extension = __import__(NOM).classFactory(None)
extension.initProcessing()
algo = QgsApplication.processingRegistry().algorithmById("whataisdoesntshow:fiche_zone")
assert algo is not None, "algorithme non enregistré"
print(f"Extension {version} chargée : {algo.displayName()} ({algo.id()})")

assert QgsProject.instance().read(str(RACINE / "qgis" / "what_ais_doesnt_show.qgz")), "projet illisible"
zone = QgsVectorLayer("Polygon?crs=EPSG:4326&field=nom:string", "zone de test", "memory")
f = QgsFeature(zone.fields())
f.setGeometry(QgsGeometry.fromWkt("POLYGON((10.75 55.25, 11.25 55.25, 11.25 55.75, 10.75 55.75, 10.75 55.25))"))
f.setAttributes(["Great Belt"])
zone.dataProvider().addFeatures([f])

sortie = dossier / "zone-sheet_test.pdf"
res = processing.run("whataisdoesntshow:fiche_zone", {"ZONE": zone, "NOM": "Great Belt", "SORTIE": str(sortie), "PNG": False})
assert sortie.exists() and sortie.stat().st_size > 50_000, "fiche non produite"
pages = sortie.read_bytes().count(b"/Type /Page") - sortie.read_bytes().count(b"/Type /Pages")
assert pages == 1, f"{pages} pages"
print(f"Fiche produite : {sortie.stat().st_size / 1e6:.1f} Mo, 1 page ; silences {res['NB_SILENCES']}, "
      f"inexpliqués {res['NB_INEXPLIQUEES']}, navires {res['NB_NAVIRES']}")
extension.unload()
app.exitQgis()
