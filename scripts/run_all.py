"""Lance toute la chaîne, du téléchargement aux fiches de zone et à la carte web.

    python run_all.py                   chaîne complète, avec les trois semaines de comparaison
                                        (≈ 3 heures et 18 Go téléchargés au premier passage)
    python run_all.py --sans-semaines   la semaine d'étude seule (≈ 40 minutes, 4,3 Go)
    python run_all.py --depuis 04       reprend aux indicateurs, sans recharger les données
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
    # 08 avant 05 : le rapport, les fiches et la carte web reprennent les détections radar
    ("08", ["08_sar_gfw.py"]),       # facultatif : jeton Global Fishing Watch dans gfw_token.txt
    ("10", ["10_semaines.py"]),      # semaines de comparaison, chacune dans sa base (sautées si déjà faites)
    ("05", ["05_rapport.py"]),
    ("06", ["06_export_gpkg.py"]),
    ("07", ["07_projet_qgis.py"]),   # lancé avec le Python de QGIS
    ("09", ["09_carte_web.py"]),
]

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--depuis", default="00", help="numéro de la première étape")
    p.add_argument("--sans-semaines", action="store_true", help="sans les semaines de comparaison (étape 10)")
    args = p.parse_args()
    depuis = args.depuis
    ordre = [numero for numero, _ in ETAPES]
    if depuis not in ordre:
        sys.exit(f"Étape inconnue : {depuis} (étapes : {', '.join(ordre)})")
    for rang, (numero, commande) in enumerate(ETAPES):
        # l'instance PostgreSQL doit tourner même quand on reprend en cours de chaîne
        if rang < ordre.index(depuis) and numero != "00":
            continue
        if numero == "10" and args.sans_semaines:
            continue
        if numero == "08" and not any((config.RACINE / f).exists() for f in ("gfw_token.txt", ".gfw_token")):
            log("Étape 08 ignorée : pas de jeton Global Fishing Watch (gfw_token.txt)")
            continue
        log(f"Étape {numero} : {commande[0]}")
        python = [str(config.PYTHON_QGIS)] if numero == "07" else [sys.executable]
        res = subprocess.run([*python, *commande], cwd=config.SCRIPTS)
        if res.returncode != 0:
            sys.exit(f"Échec à l'étape {numero} : reprendre avec --depuis {numero}")
    log("Chaîne terminée")
