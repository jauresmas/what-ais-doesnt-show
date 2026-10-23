"""Télécharge les fichiers AIS quotidiens de l'Autorité maritime danoise.

Un ZIP par jour (environ 600 Mo, un CSV de 3 à 4 Go). Les fichiers déjà présents
et complets ne sont pas retéléchargés.
"""
import sys
import urllib.request

import config
from outils import log


def taille_distante(url):
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req, timeout=60) as rep:
        return int(rep.headers["Content-Length"])


def telecharger(jour):
    url = config.AIS_URL.format(jour=jour.isoformat())
    cible = config.AIS_BRUT / f"aisdk-{jour.isoformat()}.zip"
    attendu = taille_distante(url)
    if cible.exists() and cible.stat().st_size == attendu:
        log(f"{cible.name} déjà présent")
        return
    partiel = cible.with_suffix(".part")
    log(f"{cible.name} : {attendu / 1e6:.0f} Mo")
    with urllib.request.urlopen(url, timeout=120) as rep, open(partiel, "wb") as f:
        while bloc := rep.read(8 * 1024 * 1024):
            f.write(bloc)
    if partiel.stat().st_size != attendu:
        sys.exit(f"{cible.name} incomplet : {partiel.stat().st_size} / {attendu} octets")
    partiel.replace(cible)


if __name__ == "__main__":
    config.AIS_BRUT.mkdir(parents=True, exist_ok=True)
    for jour in config.JOURS:
        telecharger(jour)
    log("Téléchargement terminé")
