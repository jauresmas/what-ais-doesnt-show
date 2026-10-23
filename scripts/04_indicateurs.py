"""Calcule les indicateurs dans PostGIS, script SQL par script SQL.

La zone d'étude et les seuils (config.py) sont passés aux scripts comme variables psql.

    python 04_indicateurs.py              toute la chaîne d'indicateurs
    python 04_indicateurs.py --depuis 06  reprend à partir d'un script
"""
import argparse

import config
from outils import log, psql, variables_sql

ETAPES = ["03_navires", "04_couverture", "05_zones_travail", "06_coupures",
          "07_identite", "08_infrastructures", "09_rencontres", "10_score",
          "11_cartographie"]

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--depuis", default="03", help="numéro du premier script SQL à exécuter")
    depuis = p.parse_args().depuis
    variables = variables_sql()
    for etape in ETAPES:
        if etape[:2] < depuis:
            continue
        log(f"{etape}.sql")
        psql(fichier=config.SQL / f"{etape}.sql", variables=variables)
    log(psql("""
        SELECT 'navires', count(*) FROM ais.navire
        UNION ALL SELECT 'coupures : ' || categorie, count(*) FROM indic.coupure GROUP BY categorie
        UNION ALL SELECT 'sauts de position', count(*) FROM indic.saut_position
        UNION ALL SELECT 'stationnements sur infrastructure', count(*) FROM indic.stationnement_infra
        UNION ALL SELECT 'rencontres en mer', count(*) FROM indic.rencontre
        UNION ALL SELECT 'mailles notées', count(*) FROM indic.score"""))
