"""Plusieurs semaines : un angle mort ou un silence est-il ponctuel ou chronique ?

Chaque semaine de config.SEMAINES passe par la même chaîne (étapes 00 à 04), sans aucune
modification, dans sa propre base (ais_AAAA_MM_JJ) ; la semaine d'étude reste dans « ais ».
Les semaines déjà calculées sont sautées. Les résultats sont ensuite rassemblés dans la base
de la semaine d'étude (schéma « semaine »).

    python 10_semaines.py                 calcule les semaines manquantes, puis rassemble
    python 10_semaines.py --rassembler    rassemble seulement
"""
import argparse
import os
import subprocess
import sys

import pandas as pd

import config
from outils import log, moteur, psql, requete
from regles import classe_couverture

ETAPES = ["00_base.py", "01_telecharger_ais.py", "02_nettoyer_ais.py", "03_referentiel.py", "04_indicateurs.py"]


def base(semaine):
    return "ais" if semaine == config.SEMAINE_ETUDE else f"ais_{semaine:%Y_%m_%d}"


def calculee(semaine):
    existe = psql(f"SELECT 1 FROM pg_database WHERE datname = '{base(semaine)}'", base="postgres").strip()
    return bool(existe) and psql("SELECT to_regclass('indic.score') IS NOT NULL", base=base(semaine)).strip() == "t"


def produire(semaine):
    env = {**os.environ, "AIS_DEBUT": semaine.isoformat(), "AIS_BASE": base(semaine)}
    for etape in ETAPES:
        log(f"Semaine du {semaine:%d/%m} : {etape}")
        if subprocess.run([sys.executable, etape], cwd=config.SCRIPTS, env=env).returncode != 0:
            sys.exit(f"Échec : semaine du {semaine:%d/%m}, {etape}")


def mesures(semaine):
    """Chiffres, couverture et silences inexpliqués d'une semaine, lus dans sa base."""
    b = base(semaine)
    chiffres = requete("""
        SELECT (SELECT count(*) FROM ais.navire) AS nb_navires,
               (SELECT count(*) FROM ais.position) AS nb_positions,
               (SELECT count(*) FROM indic.coupure) AS nb_silences,
               (SELECT count(*) FROM indic.coupure WHERE categorie = 'réception insuffisante probable') AS nb_reception,
               (SELECT count(*) FROM indic.coupure WHERE categorie = 'coupure inexpliquée') AS nb_inexpliquees,
               (SELECT count(DISTINCT mmsi) FROM indic.coupure WHERE categorie = 'coupure inexpliquée') AS nav_inexpliquees,
               (SELECT count(*) FROM indic.anomalie_navire WHERE position_incoherente) AS nav_mmsi_partage,
               (SELECT count(*) FROM indic.stationnement_infra) AS nb_stationnements,
               (SELECT count(*) FROM indic.rencontre) AS nb_rencontres,
               -- part du trafic en route dans des mailles bien couvertes (même définition que les fiches)
               (SELECT avg(CASE WHEN c.bonne THEN 1.0 ELSE 0.0 END)
                FROM ais.position p JOIN ref.zone_etude z ON ST_Intersects(p.geom, z.geom)
                LEFT JOIN indic.couverture c ON c.h3 = h3_lat_lng_to_cell(p.geom, 6)
                WHERE p.sog >= 3) AS part_couverte""", base=b)
    chiffres.insert(0, "semaine", semaine)
    cv = requete("""SELECT h3::text AS h3, bonne, nb_navires, nb_navires_perdus, taux_perte, taux_reception,
                           nb_intervalles FROM indic.couverture""", base=b)
    cv["classe"] = cv.apply(classe_couverture, axis=1)
    cv.insert(0, "semaine", semaine)
    ix = requete("""SELECT mmsi, famille, debut, duree_h, ST_X(geom_debut) AS lon, ST_Y(geom_debut) AS lat
                    FROM indic.coupure WHERE categorie = 'coupure inexpliquée'""", base=b)
    ix.insert(0, "semaine", semaine)
    return chiffres, cv[["semaine", "h3", "classe"]], ix


def rassembler():
    """Rassemble les semaines dans la base de la semaine d'étude (schéma « semaine »)."""
    parties = [mesures(s) for s in config.SEMAINES if calculee(s)]
    if len(parties) < 2:
        log("Moins de deux semaines calculées : rien à rassembler")
        return
    psql("DROP SCHEMA IF EXISTS semaine CASCADE; CREATE SCHEMA semaine;")
    eng = moteur()
    pd.concat([p[0] for p in parties]).to_sql("chiffres", eng, schema="semaine", index=False)
    pd.concat([p[1] for p in parties]).to_sql("couverture", eng, schema="semaine", index=False)
    pd.concat([p[2] for p in parties]).to_sql("inexpliquee", eng, schema="semaine", index=False)
    psql("""ALTER TABLE semaine.inexpliquee ADD COLUMN geom geometry(Point, 4326);
            UPDATE semaine.inexpliquee SET geom = ST_SetSRID(ST_MakePoint(lon, lat), 4326);""")
    psql(fichier=config.SQL / "13_semaines.sql")
    log(requete("""SELECT semaine, nb_navires, nb_silences, nb_inexpliquees, round(part_couverte::numeric, 3) AS part_couverte
                   FROM semaine.chiffres ORDER BY 1""").to_string(index=False))
    log(requete("SELECT statut, count(*) AS mailles FROM semaine.recurrence GROUP BY 1 ORDER BY 2 DESC").to_string(index=False))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--rassembler", action="store_true", help="ne calcule aucune semaine")
    args = p.parse_args()
    subprocess.run([sys.executable, "00_base.py"], cwd=config.SCRIPTS, check=True)  # instance démarrée
    if not args.rassembler:
        for semaine in config.SEMAINES:
            if calculee(semaine):
                log(f"Semaine du {semaine:%d/%m} déjà calculée ({base(semaine)})")
            else:
                produire(semaine)
    rassembler()
