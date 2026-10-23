"""Nettoie les fichiers AIS quotidiens et charge les positions dans PostGIS.

Chaque ZIP est lu par blocs, sans être décompressé sur le disque. Les étapes,
dans l'ordre, et les lignes qu'elles écartent sont consignées dans
qualite.bilan_nettoyage :

    1. type d'émetteur      seules les stations de classe A (navires soumis à l'obligation
                            d'emport : commerce, pêche de plus de 15 m, passagers) sont gardées
    2. MMSI invalide        hors de la plage UIT des navires (201000000 à 775999999)
    3. sans position        messages statiques (latitude 91) : l'identité est gardée à part
    4. position nulle       0°, 0°
    5. hors zone d'étude
    6. doublon exact        même navire, même seconde, même position
    7. allègement           une position par navire et par minute au plus

    python 02_nettoyer_ais.py                 toute la période
    python 02_nettoyer_ais.py 2026-10-15      un ou plusieurs jours
"""
import io
import sys
import zipfile
from collections import Counter
from datetime import date, timedelta

import numpy as np
import pandas as pd

import config
from outils import connexion, log, psql

COLONNES = {
    "Timestamp": "ts", "Type of mobile": "type_mobile", "MMSI": "mmsi",
    "Latitude": "lat", "Longitude": "lon", "Navigational status": "statut",
    "SOG": "sog", "COG": "cog", "Heading": "cap", "IMO": "imo", "Callsign": "indicatif",
    "Name": "nom", "Ship type": "type_navire", "Width": "largeur", "Length": "longueur",
    "Draught": "tirant_eau", "Destination": "destination",
}
IDENTITE = ["mmsi", "nom", "imo", "indicatif", "type_navire", "longueur", "largeur"]
BLOC = 1_000_000

STATUTS = {
    "Under way using engine": 0, "At anchor": 1, "Not under command": 2,
    "Restricted maneuverability": 3, "Constrained by her draught": 4, "Moored": 5,
    "Aground": 6, "Engaged in fishing": 7, "Under way sailing": 8,
    "Reserved for future amendment [HSC]": 9, "Reserved for future amendment [WIG]": 10,
    "Power-driven vessel towing astern": 11,
    "Power-driven vessel pushing ahead or towing alongside": 12,
    "Reserved for future use": 13, "AIS-SART is active": 14, "Unknown value": 15,
}
# valeurs que le fichier danois utilise pour « non renseigné »
INCONNU = {"Unknown": "", "Undefined": "", "Unknown value": ""}


def nombre(serie):
    return pd.to_numeric(serie, errors="coerce")


def lire_blocs(chemin):
    z = zipfile.ZipFile(chemin)
    membre = z.infolist()[0]
    with z.open(membre) as f:
        entete = f.readline().decode("utf-8").lstrip("# ").strip().split(",")
    usecols = [i for i, c in enumerate(entete) if c in COLONNES]
    noms = [COLONNES[entete[i]] for i in usecols]
    # usecols est croissant : les colonnes lues arrivent dans l'ordre de noms
    f = z.open(membre)
    return pd.read_csv(f, skiprows=1, header=None, usecols=usecols,
                       dtype=str, keep_default_na=False, chunksize=BLOC,
                       encoding="utf-8", encoding_errors="replace"), noms


def copier(cnx, table, colonnes, df):
    tampon = io.StringIO()
    df.to_csv(tampon, index=False, header=False)
    tampon.seek(0)
    with cnx.cursor() as cur:
        cur.copy_expert(f"COPY {table} ({', '.join(colonnes)}) FROM STDIN WITH (FORMAT csv)",
                        tampon)


def traiter_jour(jour):
    chemin = config.AIS_BRUT / f"aisdk-{jour.isoformat()}.zip"
    ouest, sud, est, nord = config.BBOX
    bilan = Counter()
    identites, destinations, stations = [], [], []
    derniere_minute = pd.Series(dtype="datetime64[ns]")
    nb_gardees = 0

    cnx = connexion()
    with cnx.cursor() as cur:
        lendemain = jour + timedelta(days=1)
        cur.execute("DELETE FROM ais.position WHERE ts >= %s AND ts < %s", (jour, lendemain))
        for table in ("ais.identite_brute", "ais.destination_brute", "ais.station_brute",
                      "qualite.bilan_nettoyage"):
            cur.execute(f"DELETE FROM {table} WHERE jour = %s", (jour,))

    blocs, noms = lire_blocs(chemin)
    for bloc in blocs:
        bloc.columns = noms
        bilan[(0, "lignes lues")] += len(bloc)

        # 1. type d'émetteur ; on garde au passage la position des stations de base
        st = bloc[bloc["type_mobile"] == "Base Station"]
        if len(st):
            st = st.assign(mmsi=nombre(st["mmsi"]), lat=nombre(st["lat"]), lon=nombre(st["lon"]))
            st = st[st["lat"].between(-90, 90) & st["lon"].between(-180, 180)]
            stations.append(st.groupby("mmsi").agg(lon=("lon", "median"), lat=("lat", "median"),
                                                   nb_messages=("lat", "size")))
        for t, n in bloc.loc[bloc["type_mobile"] != "Class A", "type_mobile"].value_counts().items():
            bilan[(1, f"type d'émetteur : {t or 'non renseigné'}")] += n
        a = bloc[bloc["type_mobile"] == "Class A"].copy()

        # 2. MMSI dans la plage UIT des stations de navire
        a["mmsi"] = nombre(a["mmsi"])
        ok = a["mmsi"].between(201_000_000, 775_999_999)
        bilan[(2, "MMSI invalide")] += int((~ok).sum())
        a = a[ok]
        a["mmsi"] = a["mmsi"].astype(np.int64)
        a["ts"] = pd.to_datetime(a["ts"], format="%d/%m/%Y %H:%M:%S")

        # identité déclarée : comptée sur tous les messages, avec ou sans position
        for c in ("nom", "imo", "indicatif", "type_navire", "destination"):
            a[c] = a[c].replace(INCONNU).str.strip()
        a["longueur"] = nombre(a["longueur"])
        a["largeur"] = nombre(a["largeur"])
        identites.append(a.groupby(IDENTITE, dropna=False).size().rename("nb_messages"))
        d = a[a["destination"] != ""]
        destinations.append(d.groupby(["mmsi", "destination"]).agg(
            premier=("ts", "min"), dernier=("ts", "max"), nb_messages=("ts", "size")))

        # 3. et 4. position absente ou nulle
        a["lat"] = nombre(a["lat"])
        a["lon"] = nombre(a["lon"])
        sans = ~(a["lat"].between(-90, 90, inclusive="neither") &
                 a["lon"].between(-180, 180, inclusive="neither"))
        bilan[(3, "message sans position")] += int(sans.sum())
        a = a[~sans]
        nulle = (a["lat"] == 0) & (a["lon"] == 0)
        bilan[(4, "position nulle")] += int(nulle.sum())
        a = a[~nulle]

        # 5. zone d'étude
        dedans = a["lon"].between(ouest, est) & a["lat"].between(sud, nord)
        bilan[(5, "hors zone d'étude")] += int((~dedans).sum())
        a = a[dedans]

        # 6. doublons exacts
        doublon = a.duplicated(["mmsi", "ts", "lat", "lon"])
        bilan[(6, "doublon exact")] += int(doublon.sum())
        a = a[~doublon]

        # 7. allègement : première position de chaque minute (le fichier est trié par heure)
        a["minute"] = a["ts"].dt.floor(f"{config.PAS_MINUTES}min")
        garde = ~a.duplicated(["mmsi", "minute"])
        garde &= a["mmsi"].map(derniere_minute).ne(a["minute"]).to_numpy()
        bilan[(7, f"allègement ({config.PAS_MINUTES} position par minute)")] += int((~garde).sum())
        a = a[garde]
        derniere_minute = pd.concat([derniere_minute, a.groupby("mmsi")["minute"].max()])
        derniere_minute = derniere_minute[~derniere_minute.index.duplicated(keep="last")]

        # valeurs « non disponible » du standard AIS
        sog, cog, cap = nombre(a["sog"]), nombre(a["cog"]), nombre(a["cap"])
        pos = pd.DataFrame({
            "mmsi": a["mmsi"], "ts": a["ts"].dt.strftime("%Y-%m-%d %H:%M:%S"),
            "lon": a["lon"].round(6), "lat": a["lat"].round(6),
            "statut": a["statut"].map(STATUTS).fillna(15).astype(int),
            "sog": sog.where(sog < 102.2).round(1),
            "cog": cog.where(cog < 360).round(1),
            "cap": cap.where(cap < 360).astype("Int16"),
            "tirant_eau": nombre(a["tirant_eau"]).where(lambda s: s > 0),
        })
        copier(cnx, "ais.position", list(pos.columns), pos)
        nb_gardees += len(pos)

    bilan[(8, "positions gardées")] = nb_gardees

    ident = pd.concat(identites).groupby(level=list(range(len(IDENTITE))), dropna=False).sum()
    ident = ident.reset_index()
    ident.insert(0, "jour", jour)
    copier(cnx, "ais.identite_brute", list(ident.columns), ident)

    dest = pd.concat(destinations).groupby(level=[0, 1]).agg(
        premier=("premier", "min"), dernier=("dernier", "max"), nb_messages=("nb_messages", "sum"))
    dest = dest.reset_index()
    dest.insert(0, "jour", jour)
    copier(cnx, "ais.destination_brute", list(dest.columns), dest)

    if stations:
        st = pd.concat(stations).groupby(level=0).agg(
            lon=("lon", "median"), lat=("lat", "median"), nb_messages=("nb_messages", "sum"))
        st = st.reset_index()
        st.insert(0, "jour", jour)
        st["mmsi"] = st["mmsi"].astype(np.int64)
        copier(cnx, "ais.station_brute", list(st.columns), st)

    b = pd.DataFrame([(jour, e, m, n) for (e, m), n in sorted(bilan.items())],
                     columns=["jour", "etape", "motif", "nb_lignes"])
    copier(cnx, "qualite.bilan_nettoyage", list(b.columns), b)
    cnx.commit()
    cnx.close()
    log(f"{jour} : {bilan[(0, 'lignes lues')]:,} lignes lues, {nb_gardees:,} positions gardées")


if __name__ == "__main__":
    jours = [date.fromisoformat(j) for j in sys.argv[1:]] or config.JOURS
    for jour in jours:
        traiter_jour(jour)
    log("Index et statistiques")
    psql(fichier=config.SQL / "02_index.sql")
    log("Nettoyage terminé")
