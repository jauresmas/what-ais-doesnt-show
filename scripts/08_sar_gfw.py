"""Détections radar Sentinel-1 de Global Fishing Watch sur l'aire et la période d'étude.

Le radar voit les navires qu'ils émettent ou non : c'est la source indépendante de l'AIS qui
manquait au projet. Global Fishing Watch rapproche chaque détection de l'AIS mondial (stations
côtières et satellites) ; une détection « non appariée » est un navire vu par le radar sans
émission AIS correspondante.

    API v3, 4Wings, jeu public-global-sar-presence:latest (licence CC BY-NC 4.0,
    usage non commercial, mention « Powered by Global Fishing Watch »)

Jeton d'accès : à créer sur https://globalfishingwatch.org/our-apis/tokens, puis à coller seul
dans un fichier gfw_token.txt (ou .gfw_token) à la racine du projet. Ces fichiers ne sont pas
versionnés et le jeton n'est jamais affiché. La variable d'environnement GFW_TOKEN marche aussi.

    python 08_sar_gfw.py           récupère (une fois) puis charge dans PostGIS
    python 08_sar_gfw.py --force   retélécharge
"""
import argparse
import io
import json
import os
import sys
import time
import zipfile
from datetime import timedelta

import pandas as pd
import requests

import config
from outils import connexion, log, psql

URL = "https://gateway.api.globalfishingwatch.org/v3/4wings/report"
URL_DERNIER = "https://gateway.api.globalfishingwatch.org/v3/4wings/last-report"
JEU = "public-global-sar-presence:latest"
BRUT = config.BRUTES / "gfw"


def jeton():
    valeur = os.environ.get("GFW_TOKEN", "").strip()
    for nom in ("gfw_token.txt", ".gfw_token"):
        f = config.RACINE / nom
        if not valeur and f.exists():
            valeur = f.read_text(encoding="utf-8-sig").strip()
    if not valeur:
        sys.exit("Jeton Global Fishing Watch introuvable : créer gfw_token.txt à la racine du projet "
                 "(jeton généré sur https://globalfishingwatch.org/our-apis/tokens).")
    return valeur


def region():
    o, s, e, n = config.BBOX
    return {"type": "Polygon", "coordinates": [[[o, s], [e, s], [e, n], [o, n], [o, s]]]}


def lire_reponse(rep):
    """La réponse est du JSON, ou un zip qui contient le JSON et un avertissement d'usage."""
    if rep.content[:2] == b"PK":
        z = zipfile.ZipFile(io.BytesIO(rep.content))
        nom = next(n for n in z.namelist() if n.lower().endswith(".json"))
        return json.loads(z.read(nom).decode("utf-8"))
    return rep.json()


def rapport(apparie, forcer=False):
    cible = BRUT / f"sar_{'apparie' if apparie else 'non_apparie'}.json"
    if cible.exists() and not forcer:
        return json.loads(cible.read_text(encoding="utf-8"))
    params = {
        "spatial-resolution": "HIGH",          # mailles de 0,01°
        "temporal-resolution": "HOURLY",       # l'heure du passage, pour croiser avec l'AIS danois
        "datasets[0]": JEU,
        "date-range": f"{config.DEBUT},{config.FIN + timedelta(days=1)}",
        "format": "JSON",
        "filters[0]": f"matched='{'true' if apparie else 'false'}'",
    }
    entetes = {"Authorization": f"Bearer {jeton()}", "Content-Type": "application/json"}
    for essai in range(6):
        rep = requests.post(URL, params=params, json={"geojson": region()}, headers=entetes, timeout=200)
        if rep.status_code == 429:      # un seul rapport à la fois par utilisateur
            log("API occupée (429), nouvel essai dans 30 s")
            time.sleep(30)
            continue
        if rep.status_code == 524:      # rapport trop long : on le récupère une fois prêt
            log("Rapport en cours de calcul (524), récupération par last-report")
            time.sleep(30)
            rep = requests.get(URL_DERNIER, headers=entetes, timeout=200)
        if rep.status_code in (401, 403):
            sys.exit(f"Jeton refusé par Global Fishing Watch (HTTP {rep.status_code}) : vérifier gfw_token.txt.")
        if rep.status_code >= 400:
            sys.exit(f"Erreur de l'API (HTTP {rep.status_code}) : {rep.text[:400]}")
        donnees = lire_reponse(rep)
        BRUT.mkdir(parents=True, exist_ok=True)
        cible.write_text(json.dumps(donnees), encoding="utf-8")
        return donnees
    sys.exit("API toujours occupée après plusieurs essais : relancer plus tard.")


def lignes(donnees, apparie):
    # l'API range les résultats sous la version réelle du jeu (public-global-sar-presence:v5.0),
    # pas sous l'alias :latest demandé
    enregistrements = []
    for entree in donnees.get("entries", []):
        for cle, valeurs in entree.items():
            if cle.startswith(JEU.split(":")[0]):
                enregistrements += valeurs
    df = pd.DataFrame(enregistrements)
    if df.empty:
        return df
    df["apparie"] = apparie
    df["heure"] = pd.to_datetime(df["date"], errors="coerce")
    return df


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true", help="retélécharge les rapports")
    forcer = p.parse_args().force

    tables = []
    for apparie in (False, True):
        d = rapport(apparie, forcer)
        df = lignes(d, apparie)
        log(f"Détections {'appariées' if apparie else 'non appariées'} à l'AIS : "
            f"{int(df['detections'].sum()) if not df.empty else 0} dans {len(df)} mailles-heures")
        tables.append(df)
    sar = pd.concat([t for t in tables if not t.empty], ignore_index=True) if any(
        not t.empty for t in tables) else pd.DataFrame()
    if sar.empty:
        sys.exit("Aucune détection sur la période : données pas encore publiées (délai d'environ 5 jours) "
                 "ou pas de passage Sentinel-1.")
    debut, fin = pd.Timestamp(config.DEBUT), pd.Timestamp(config.FIN) + pd.Timedelta(days=1)
    sar = sar[(sar["heure"] >= debut) & (sar["heure"] < fin)].copy()
    log(f"Jours couverts : {sorted(sar['heure'].dt.date.astype(str).unique())}")

    # instant exact de chaque passage : un navire détecté une seule fois dans la semaine a un
    # horodatage d'entrée égal à celui de sortie, c'est l'instant de l'image ; dans un passage,
    # ces instants tiennent en moins de deux minutes, leur médiane date tout le passage
    exacts = sar[(sar["apparie"]) & (sar["entryTimestamp"] == sar["exitTimestamp"])].copy()
    exacts["t"] = pd.to_datetime(exacts["entryTimestamp"], utc=True).dt.tz_localize(None)
    passages = exacts.groupby("date")["t"].agg(["median", "min", "max", "count"])
    log(f"{len(passages)} passages Sentinel-1, étalement maximal "
        f"{(passages['max'] - passages['min']).max().total_seconds() / 60:.1f} min")
    sar["instant"] = sar["date"].map(passages["median"]).fillna(sar["heure"] + pd.Timedelta(minutes=30))
    # MMSI des détections appariées : sert seulement à vérifier en base si le réseau danois recevait
    # ce navire au même instant ; jamais exporté
    sar["mmsi"] = pd.to_numeric(sar.get("mmsi"), errors="coerce").where(sar["apparie"]).astype("Int64")

    psql("""DROP TABLE IF EXISTS indic.sar_detection;
            CREATE TABLE indic.sar_detection (
                id serial PRIMARY KEY, heure timestamp, instant timestamp, lat double precision,
                lon double precision, detections integer, apparie boolean, mmsi bigint,
                geom geometry(Point, 4326) GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(lon, lat), 4326)) STORED);""")
    with connexion() as cnx, cnx.cursor() as cur:
        tampon = io.StringIO()
        sar[["heure", "instant", "lat", "lon", "detections", "apparie", "mmsi"]].to_csv(tampon, index=False, header=False)
        tampon.seek(0)
        cur.copy_expert("COPY indic.sar_detection (heure, instant, lat, lon, detections, apparie, mmsi) "
                        "FROM STDIN WITH (FORMAT csv)", tampon)
    psql("CREATE INDEX ON indic.sar_detection USING gist (geom); ANALYZE indic.sar_detection;")
    log("Croisement avec l'AIS danois, la couverture et les silences (sql/12_sar.sql)")
    psql(fichier=config.SQL / "12_sar.sql")
    log(psql("SELECT categorie, count(*) FROM indic.sar_detection WHERE NOT apparie GROUP BY 1 ORDER BY 2 DESC"))
