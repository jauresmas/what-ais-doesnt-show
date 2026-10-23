"""Crée et démarre l'instance PostgreSQL du projet, puis la base et ses schémas.

L'instance est locale (port 5434, connexion sans mot de passe depuis la machine),
ses fichiers sont dans .pgdata/ et ne sont pas versionnés.

    python 00_base.py            démarre l'instance (la crée si besoin)
    python 00_base.py --neuve    recrée la base vide
"""
import argparse
import subprocess
import time

import config
from outils import log, psql

PG_CTL = str(config.PG_BIN / "pg_ctl.exe")


def instance():
    if not (config.PG_DATA / "PG_VERSION").exists():
        log(f"Création de l'instance PostgreSQL ({config.PG_DATA})")
        subprocess.run([str(config.PG_BIN / "initdb.exe"), "-D", str(config.PG_DATA),
                        "-U", config.PG_USER, "-A", "trust", "-E", "UTF8",
                        "--locale=C", "--lc-messages=C"],
                       check=True, capture_output=True)
        conf = config.PG_DATA / "postgresql.conf"
        conf.write_text(conf.read_text() + f"\nport = {config.PG_PORT}\n"
                        "listen_addresses = 'localhost'\nshared_buffers = 512MB\n"
                        "work_mem = 64MB\nmaintenance_work_mem = 1GB\n"
                        "max_wal_size = 4GB\ntimezone = 'UTC'\n")
    etat = subprocess.run([PG_CTL, "status", "-D", str(config.PG_DATA)], capture_output=True)
    if etat.returncode != 0:
        log(f"Démarrage de PostgreSQL sur le port {config.PG_PORT}")
        # sorties vers NUL : le serveur hérite des descripteurs, les capturer
        # bloquerait le script jusqu'à l'arrêt de PostgreSQL
        subprocess.run([PG_CTL, "start", "-D", str(config.PG_DATA), "-w",
                        "-l", str(config.RACINE / "postgresql.log")],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       stdin=subprocess.DEVNULL)
        time.sleep(1)


def base_neuve():
    log(f"Base {config.PG_DB} : création")
    psql(f"DROP DATABASE IF EXISTS {config.PG_DB} WITH (FORCE)", base="postgres")
    psql(f"CREATE DATABASE {config.PG_DB} ENCODING 'UTF8' TEMPLATE template0", base="postgres")
    psql(fichier=config.SQL / "01_structure.sql")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--neuve", action="store_true", help="recrée la base vide")
    args = p.parse_args()
    instance()
    existe = psql(f"SELECT 1 FROM pg_database WHERE datname = '{config.PG_DB}'",
                  base="postgres").strip()
    if args.neuve or not existe:
        base_neuve()
    log(psql("SELECT postgis_version(), h3_get_extension_version()").strip())
