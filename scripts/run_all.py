"""Lance toute la chaîne, du téléchargement aux fiches de zone.

    python run_all.py               chaîne complète (≈ 35 minutes, 4,3 Go téléchargés au premier passage)
    python run_all.py --depuis 04   reprend aux indicateurs, sans recharger les données
"""
import argparse
import subprocess
import sys

import config
from outils import log

ETAPES = [
    ("00", ["00_base.py"]),
    ("01", ["01_telecharger_ais.py"]),
    ("02", ["02_nettoyer_ais.py"]),
    ("03", ["03_referentiel.py"]),
    ("04", ["04_indicateurs.py"]),
    ("05", ["05_rapport.py"]),
    ("06", ["06_export_gpkg.py"]),
    ("07", ["07_projet_qgis.py"]),   # lancé avec le Python de QGIS
]

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--depuis", default="00", help="numéro de la première étape")
    depuis = p.parse_args().depuis
    for numero, commande in ETAPES:
        # l'instance PostgreSQL doit tourner même quand on reprend en cours de chaîne
        if numero < depuis and numero != "00":
            continue
        log(f"Étape {numero} : {commande[0]}")
        python = [str(config.PYTHON_QGIS)] if numero == "07" else [sys.executable]
        res = subprocess.run([*python, *commande], cwd=config.SCRIPTS)
        if res.returncode != 0:
            sys.exit(f"Échec à l'étape {numero} : reprendre avec --depuis {numero}")
    log("Chaîne terminée")
