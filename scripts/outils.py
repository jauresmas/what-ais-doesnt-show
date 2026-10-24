"""Fonctions communes : journal, connexion PostGIS, exécution SQL."""
import os
import subprocess
import time

import config

_T0 = time.time()


def log(message):
    print(f"[{time.time() - _T0:7.1f} s] {message}", flush=True)


def connexion(base=config.PG_DB):
    import psycopg2
    return psycopg2.connect(host=config.PG_HOST, port=config.PG_PORT,
                            user=config.PG_USER, dbname=base)


def moteur(base=None):
    from sqlalchemy import create_engine
    return create_engine(f"postgresql+psycopg2://{config.PG_USER}@{config.PG_HOST}:"
                         f"{config.PG_PORT}/{base or config.PG_DB}")


def variables_sql():
    """Zone d'étude et seuils, passés aux scripts SQL comme variables psql (:ouest, :'seuil_coupure'...)."""
    ouest, sud, est, nord = config.BBOX
    return {"ouest": ouest, "sud": sud, "est": est, "nord": nord, **config.SEUILS}


def psql(sql=None, fichier=None, base=config.PG_DB, variables=None):
    """Exécute du SQL avec psql (arrêt à la première erreur)."""
    cmd = [str(config.PG_BIN / "psql.exe"), "-h", config.PG_HOST, "-p", str(config.PG_PORT),
           "-U", config.PG_USER, "-d", base, "-v", "ON_ERROR_STOP=1", "-q", "-X", "-t", "-A"]
    for nom, valeur in (variables or {}).items():
        cmd += ["-v", f"{nom}={valeur}"]
    # le SQL passe par l'entrée standard : sous Windows, un argument de ligne de commande
    # est converti dans la page de code ANSI et les accents arrivent corrompus
    cmd += ["-f", str(fichier) if fichier else "-"]
    env = {**os.environ, "PGCLIENTENCODING": "UTF8", "LC_MESSAGES": "C"}
    res = subprocess.run(cmd, input=None if fichier else sql, capture_output=True, text=True,
                         encoding="utf-8", errors="replace", env=env)
    if res.returncode != 0:
        raise RuntimeError(f"psql : {res.stderr.strip()}")
    return res.stdout


def requete(sql, params=None, base=None):
    """Renvoie le résultat d'une requête sous forme de DataFrame (base de la semaine d'étude par défaut)."""
    import pandas as pd
    from sqlalchemy import text
    with moteur(base).connect() as cnx:
        return pd.read_sql_query(text(sql), cnx, params=params)
