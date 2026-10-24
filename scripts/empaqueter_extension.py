"""Construit l'extension QGIS installable « What AIS doesn't show – Zone sheet ».

L'archive réunit l'enveloppe de qgis/extension/what_ais_fiche_zone/ et le code de l'outil,
qgis/outils/fiche_zone.py, qui reste la seule source : l'extension et le script de traitement
ne peuvent pas diverger. Dans QGIS : Extensions → Installer/Gérer → Installer depuis un ZIP.

    python empaqueter_extension.py        → sorties/extension/what_ais_fiche_zone.zip
"""
import configparser
import zipfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
NOM = "what_ais_fiche_zone"
ENVELOPPE = RACINE / "qgis" / "extension" / NOM
OUTIL = RACINE / "qgis" / "outils" / "fiche_zone.py"
SORTIE = RACINE / "sorties" / "extension" / f"{NOM}.zip"


def fichiers():
    """Fichiers de l'extension : {nom dans l'archive : contenu}, fins de ligne Unix (LF). Sous Windows,
    Git écrit les fichiers avec des fins CRLF : sans normalisation, l'archive changerait selon le poste."""
    sources = {f.name: f for f in sorted(ENVELOPPE.glob("*")) if f.is_file() and f.suffix in (".py", ".txt")}
    sources["fiche_zone.py"] = OUTIL
    return {nom: f.read_bytes().replace(b"\r\n", b"\n") for nom, f in sources.items()}


def construire():
    meta = configparser.ConfigParser()
    meta.read(ENVELOPPE / "metadata.txt", encoding="utf-8")
    general = meta["general"]
    for champ in ("name", "qgisMinimumVersion", "description", "about", "version", "author", "repository"):
        assert general.get(champ), f"metadata.txt : champ {champ} manquant"
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(SORTIE, "w", zipfile.ZIP_DEFLATED) as z:
        for nom, contenu in fichiers().items():
            # date fixe : la même source donne toujours la même archive, octet pour octet
            info = zipfile.ZipInfo(f"{NOM}/{nom}", date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, contenu)
    return SORTIE, general["version"]


if __name__ == "__main__":
    chemin, version = construire()
    with zipfile.ZipFile(chemin) as z:
        contenu = z.namelist()
    print(f"{chemin.relative_to(RACINE).as_posix()} (version {version}) : {', '.join(n.split('/')[-1] for n in contenu)}")
