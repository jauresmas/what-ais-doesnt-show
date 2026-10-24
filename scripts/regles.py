"""Règles de la chaîne qui ne dépendent ni de la base ni d'un SIG : classe de couverture d'une maille,
pseudonymes des navires. Regroupées ici pour être testées seules (tests/test_regles.py).

Les navires n'apparaissent que sous un pseudonyme (V-XXXXXX), empreinte SHA-256 du MMSI salée.
Le sel reste sur le poste (donnees/produites/sel_pseudonymes.txt, non versionné) : sans lui, on ne
remonte pas au MMSI, et deux exports successifs gardent les mêmes pseudonymes.
"""
import hashlib
import secrets

import config

SEL = config.PRODUITES / "sel_pseudonymes.txt"


def sel():
    if not SEL.exists():
        SEL.parent.mkdir(parents=True, exist_ok=True)
        SEL.write_text(secrets.token_hex(16), encoding="utf-8")
    return SEL.read_text(encoding="utf-8").strip()


def pseudonymiser(serie, grain):
    """Série de MMSI → série de pseudonymes V-XXXXXX, stables pour un même sel."""
    return serie.map(lambda m: "V-" + hashlib.sha256(f"{grain}{int(m)}".encode()).hexdigest()[:6].upper())


def classe_couverture(r):
    """Classe d'une maille H3 à partir des mesures de sql/04_couverture.sql (docs/methode.md, § 2).

    r : bonne, nb_navires, nb_navires_perdus, taux_perte, taux_reception, nb_intervalles.
    """
    attendus = r["nb_navires"] + r["nb_navires_perdus"]
    if r["bonne"]:
        return "Reliable"
    if attendus >= 5 and r["taux_perte"] > 0.2:
        return "Poor"
    if r["nb_intervalles"] < 100:
        return "Not enough traffic"
    if r["taux_perte"] > 0.2 or (r["taux_reception"] or 0) < 0.8:
        return "Poor"
    return "Degraded"
