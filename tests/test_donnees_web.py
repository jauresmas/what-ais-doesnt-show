"""Données publiées par la carte web (carte/donnees) : lisibles, cohérentes entre elles, sans identité."""
import json
import re

import pytest

from conftest import RACINE

DONNEES = RACINE / "carte" / "donnees"
BBOX = (8.5, 53.5, 17.0, 58.7)   # aire d'étude et ses abords
CATEGORIES = 9


def lire(nom):
    return json.loads((DONNEES / nom).read_text(encoding="utf-8"))


FICHIERS = sorted(p.relative_to(DONNEES).as_posix() for p in DONNEES.rglob("*.json")) + \
    sorted(p.relative_to(DONNEES).as_posix() for p in DONNEES.rglob("*.geojson"))


@pytest.mark.parametrize("nom", FICHIERS)
def test_fichier_lisible(nom):
    assert lire(nom) is not None


@pytest.mark.parametrize("nom", [n for n in FICHIERS if n.endswith(".geojson")])
def test_geojson_dans_la_zone(nom):
    d = lire(nom)
    assert d["type"] == "FeatureCollection" and d["features"]

    def coords(c):
        if isinstance(c[0], (int, float)):
            yield c
        else:
            for x in c:
                yield from coords(x)
    for f in d["features"]:
        for x, y in coords(f["geometry"]["coordinates"]):
            assert BBOX[0] - 5 <= x <= BBOX[2] + 5 and BBOX[1] - 3 <= y <= BBOX[3] + 3, (nom, x, y)


@pytest.mark.parametrize("nom", FICHIERS)
def test_aucune_identite(nom):
    """Ni champ MMSI, ni nombre à 9 chiffres (un MMSI) dans les propriétés ; navires sous pseudonyme."""
    texte = (DONNEES / nom).read_text(encoding="utf-8")
    assert '"mmsi"' not in texte.lower() and '"imo"' not in texte.lower()
    d = json.loads(texte)
    proprietes = [f.get("properties", {}) for f in d.get("features", [])] if isinstance(d, dict) else []
    for p in proprietes:
        for k, v in p.items():
            assert not re.fullmatch(r"[2-7]\d{8}", str(v)), (nom, k)
            if k.startswith("navire"):
                assert re.fullmatch(r"V-[0-9A-F]{6}", v), (nom, k, v)


def test_chiffres_de_l_aire_d_etude():
    chiffres, zones = lire("chiffres.json"), lire("fiche/zones.json")
    etude = next(f["properties"] for f in zones["features"] if f["properties"]["zone_id"] == "study-area")
    for k, v in chiffres.items():
        if k not in ("validation_radar", "options"):
            assert etude[k] == v, k


@pytest.mark.parametrize("zone", lire("fiche/zones.json")["features"], ids=lambda f: f["properties"]["zone_id"])
def test_comptes_des_zones(zone):
    p = zone["properties"]
    assert len(p["comptes"]) == CATEGORIES
    assert sum(p["comptes"]) == p["nb_silences"]
    assert p["comptes"][5] == p["nb_reception"] and p["comptes"][8] == p["nb_inexpliquees"]
    assert p["nav_inexpliquees"] <= p["nb_inexpliquees"]
    for k in ("part_couverte", "part_radar_recus"):
        assert p[k] is None or 0 <= p[k] <= 1


def test_zones_contenues_dans_l_aire_d_etude():
    zones = {f["properties"]["zone_id"]: f["properties"] for f in lire("fiche/zones.json")["features"]}
    for k in ("nb_silences", "nb_inexpliquees", "nb_stationnements", "nb_rencontres", "nb_radar_sans_ais"):
        assert sum(z[k] for i, z in zones.items() if i != "study-area") <= zones["study-area"][k], k


def test_validation_radar():
    v = lire("chiffres.json")["validation_radar"]
    assert [c["classe"] for c in v] == ["Reliable", "Degraded", "Not enough traffic", "Poor"]
    for c in v:
        assert 0 <= c["recus"] <= c["n"] and abs(c["part"] - c["recus"] / c["n"]) < 1e-3
    # la part reçue suit la qualité de couverture : c'est le contrôle indépendant de la carte
    assert v[0]["part"] > v[1]["part"] > v[3]["part"]


def test_mailles_et_radar_de_la_fiche():
    m = lire("fiche/mailles.json")
    assert len(m["h"]) == len(m["r"]) == len(m["f"]) == len(m["n"])
    assert all(all(d >= 0 for d in ecarts) for ecarts in m["n"])          # écarts entre numéros croissants
    silences = lire("fiche/silences.json")
    assert len(silences["categories"]) == CATEGORIES
    assert len(silences["s"]) == lire("chiffres.json")["nb_silences"]
    for lon, lat, d, apparie, recu, structure in lire("fiche/radar.json"):
        assert d >= 1 and apparie in (0, 1) and recu in (0, 1, None) and structure in (0, 1)


def test_recits():
    r = lire("recits.json")
    s, m = r["silence"], r["identite"]
    assert s["debut"] < s["passe"] < s["fin"] and any(e == 3 for *_, e in s["radar"])
    assert len(m["sauts"]) >= 3                     # règle du MMSI partagé : trois sauts impossibles au moins
    assert all(0 <= ts <= m["positions"][-1][2] for *_, ts in m["sauts"])
    assert re.fullmatch(r"V-[0-9A-F]{6}", s["navire"]) and re.fullmatch(r"V-[0-9A-F]{6}", m["navire"])


OPTIONS = lire("chiffres.json").get("options", [])


@pytest.mark.skipif("semaines" not in OPTIONS, reason="plusieurs semaines non publiées (10_semaines.py)")
def test_semaines():
    sem, chiffres = lire("semaines.json"), lire("chiffres.json")
    etude = sem["semaines"][-1]
    for k in ("nb_navires", "nb_silences", "nb_reception", "nb_inexpliquees", "nav_inexpliquees", "nb_stationnements", "nb_rencontres"):
        assert etude[k] == chiffres[k], k                       # la semaine d'étude est bien la même
    assert abs(etude["part_couverte"] - chiffres["part_couverte"]) < 0.002
    assert [w["semaine"] for w in sem["semaines"]] == sorted(w["semaine"] for w in sem["semaines"])
    i = sem["inexpliquees"]
    assert i["total"] == sum(w["nb_inexpliquees"] for w in sem["semaines"])
    assert i["navires_2_semaines"] <= i["navires"] <= i["total"]
    assert len(lire("inexpliquees_semaines.geojson")["features"]) == i["total"]
    assert sum(sem["chroniques_par_pays"].values()) == sem["mailles"]["Chronic"]
    statuts = {f["properties"]["statut"] for f in lire("recurrence.geojson")["features"]}
    assert statuts <= {"Chronic", "Recurring", "One-off", "Never poor"}
    assert all(f["properties"]["nb_semaines"] >= 2 for f in lire("foyers.geojson")["features"])
