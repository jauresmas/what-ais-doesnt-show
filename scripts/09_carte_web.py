"""Prépare les données de la carte web (carte/donnees/*.geojson) à partir de carto.gpkg.

Couches allégées pour un navigateur : géométries simplifiées, coordonnées arrondies à 5 décimales
(≈ 1 m), attributs utiles seulement, navires sous pseudonyme. La page carte/index.html les lit ;
GitHub Pages la sert telle quelle.

S'y ajoutent les données de la fiche de zone calculée dans le navigateur (carte/donnees/fiche/),
chargées seulement quand on produit une fiche : début de chaque silence et sa catégorie, mailles H3
avec leurs heures en route, leur couverture et les navires qui les traversent (numéros sans lien
avec le MMSI), détections radar, et les zones prédéfinies avec leurs chiffres exacts.
"""
import hashlib
import importlib
import json

import geopandas as gpd
import pandas as pd
import shapely
from shapely import set_precision

import config
from graphique_fiche import CATEGORIES
from outils import log, requete
from regles import pseudonymiser, sel

CARTO = config.PRODUITES / "carto.gpkg"
SORTIE = config.RACINE / "carte" / "donnees"
FICHE = SORTIE / "fiche"

CATEGORIES_EN = {
    "réception insuffisante probable": "Shore reception gap",
    "coupure inexpliquée": "Unexplained",
}
RADAR_EN = {
    "radar seul, eaux bien couvertes": "Radar only, well-covered waters",
    "navire AIS danois à moins de 1,5 km": "Danish AIS vessel within 1.5 km",
    "eaux mal couvertes par le réseau côtier": "Poorly covered waters",
    "navire en silence AIS à cet instant": "Near a vessel silent in AIS at that minute",
}


def lire(couche, colonnes=None, simplifier=None):
    g = gpd.read_file(CARTO, layer=couche, engine="pyogrio")
    if colonnes is not None:
        g = g[colonnes + ["geometry"]]
    if simplifier:
        g["geometry"] = g.geometry.simplify(simplifier, preserve_topology=True)
    g["geometry"] = set_precision(g.geometry.values, 1e-5)
    return g[~g.geometry.is_empty]


def json_compact(chemin, donnees):
    chemin.write_text(json.dumps(donnees, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    log(f"{chemin.relative_to(SORTIE).as_posix()} : {chemin.stat().st_size / 1e3:.0f} ko")


def donnees_fiche():
    """Ce qu'il faut à la page pour refaire, sur une zone quelconque, les calculs de l'outil QGIS."""
    FICHE.mkdir(parents=True, exist_ok=True)
    codes = {c: i for i, c in enumerate(CATEGORIES)}

    # silences : rattachés à la zone de leur début, comme dans 06_export_gpkg.py et l'outil QGIS
    s = gpd.read_file(CARTO, layer="silence_ais", columns=["categorie"], engine="pyogrio")
    debut = shapely.get_point(s.geometry.values, 0)
    json_compact(FICHE / "silences.json", {
        "categories": list(CATEGORIES.values()),
        "s": [[round(p.x, 4), round(p.y, 4), codes[c]] for p, c in zip(debut, s["categorie"])]})

    # mailles H3 de résolution 6 : heures en route, maille fiable ou non, navires qui y passent.
    # Les navires sont numérotés dans l'ordre d'un hachage salé : le numéro ne dit rien du MMSI.
    t = gpd.read_file(CARTO, layer="trafic", columns=["h3", "heures_route"], engine="pyogrio")
    cv = gpd.read_file(CARTO, layer="couverture", columns=["h3", "classe"], engine="pyogrio")
    fiables = set(cv.loc[cv["classe"] == "Reliable", "h3"])
    paires = requete("SELECT DISTINCT h3_lat_lng_to_cell(geom, 6)::text AS h3, mmsi FROM ais.position")
    grain = sel()
    ordre = sorted(paires["mmsi"].unique(), key=lambda m: hashlib.sha256(f"n{grain}{int(m)}".encode()).hexdigest())
    numero = {m: i for i, m in enumerate(ordre)}
    navires = paires.assign(n=paires["mmsi"].map(numero)).groupby("h3")["n"].apply(sorted)
    mailles = {"res": 6, "h": [], "r": [], "f": [], "n": []}
    for h3, heures in zip(t["h3"], t["heures_route"]):
        liste = navires.get(h3, [])
        mailles["h"].append(h3)
        mailles["r"].append(round(float(heures), 1))
        mailles["f"].append(int(h3 in fiables))
        # écarts entre numéros successifs : un tiers du poids d'une liste brute
        mailles["n"].append([b - a for a, b in zip([0] + liste[:-1], liste)])
    json_compact(FICHE / "mailles.json", mailles)

    # détections radar : nombre, appariée, reçue par le réseau (null : non jugée), structure fixe
    try:
        rd = gpd.read_file(CARTO, layer="detection_radar", engine="pyogrio")
        # liste Python : une série pandas remettrait NaN à la place de None, invalide en JSON
        recu = [None if pd.isna(v) else int(bool(v)) for v in rd["recu_par_reseau"]]
        json_compact(FICHE / "radar.json", [
            [round(g.x, 4), round(g.y, 4), int(d), int(a), r, int(c == "structure fixe probable (parc éolien)")]
            for g, d, a, r, c in zip(rd.geometry, rd["detections"], rd["apparie"], recu, rd["categorie"])])
    except Exception as e:
        log(f"Pas de détections radar pour la fiche : {e}")

    # zones prédéfinies : chiffres exacts de la chaîne ; comptes des silences par catégorie recalculés
    # dans la base sur la géométrie complète de 06_export_gpkg.py (celle du GeoPackage est simplifiée,
    # et les ports au ras d'une limite basculeraient d'une zone à l'autre)
    zee = importlib.import_module("06_export_gpkg").ZONES_ZEE
    valeurs = ", ".join(f"('{zid}', '{nom_mr}')" for zid, _, nom_mr in zee)
    cats = requete(f"""
        WITH zone AS (
            SELECT 'study-area' AS zone_id, geom FROM ref.zone_etude
            UNION ALL
            SELECT v.zone_id, ST_Intersection(z.geom, e.geom)
            FROM (VALUES {valeurs}) AS v(zone_id, nom) JOIN ref.zee z ON z.nom = v.nom, ref.zone_etude e
        )
        SELECT z.zone_id, c.categorie, count(*) AS n
        FROM zone z JOIN indic.coupure c ON ST_Intersects(c.geom_debut, z.geom) GROUP BY 1, 2""")
    z = gpd.read_file(CARTO, layer="zone_fiche", engine="pyogrio").sort_values("ordre")
    zones = []
    for _, zf in z.iterrows():
        chiffres = {k: (None if pd.isna(v) else v.item() if hasattr(v, "item") else v)
                    for k, v in zf.drop(["geometry", "graphique", "ordre"]).items()}
        n = cats[cats["zone_id"] == zf.zone_id].set_index("categorie")["n"]
        chiffres["comptes"] = [int(n.get(c, 0)) for c in CATEGORIES]
        geom = set_precision(zf.geometry.simplify(0.004, preserve_topology=True), 1e-3)  # affichage seulement
        zones.append({"type": "Feature", "properties": chiffres, "geometry": shapely.geometry.mapping(geom)})
    json_compact(FICHE / "zones.json", {"type": "FeatureCollection", "features": zones})


def recits():
    """Données des trois récits guidés de la carte web, choisies dans la base selon des règles fixes :
    le silence inexpliqué recoupé par une détection radar, le navire au plus grand nombre de sauts
    impossibles. Navires sous pseudonyme ; traces allégées à une position toutes les deux minutes."""
    grain = sel()
    pseudo = lambda m: pseudonymiser(pd.Series([m]), grain).iloc[0]
    minutes = lambda ts, t0: int((ts - t0).total_seconds() // 60)

    # 1. silence inexpliqué pendant un passage radar, avec une détection sans AIS près du navire
    c = requete("""SELECT c.id, c.mmsi, c.famille, c.debut, c.fin, c.duree_h, c.distance_nm, s.instant,
                          ST_X(s.geom) AS lon, ST_Y(s.geom) AS lat
                   FROM indic.sar_detection s JOIN indic.coupure c ON c.id = s.coupure_id
                   WHERE c.categorie = 'coupure inexpliquée' AND NOT s.apparie ORDER BY s.instant LIMIT 1""")
    if c.empty:
        log("Récits : aucun silence inexpliqué recoupé par le radar")
        return
    c = c.iloc[0]
    t0 = c.debut - pd.Timedelta(hours=5)
    tr = requete("""SELECT ts, ST_X(geom) AS lon, ST_Y(geom) AS lat FROM ais.position
                    WHERE mmsi = :m AND ts BETWEEN :a AND :b ORDER BY ts""",
                 {"m": int(c.mmsi), "a": t0, "b": c.fin + pd.Timedelta(hours=4)})
    tr = tr[tr.ts.dt.minute % 2 == 0]
    x0, x1 = tr.lon.min() - 0.25, tr.lon.max() + 0.25
    y0, y1 = tr.lat.min() - 0.12, tr.lat.max() + 0.12
    rd = requete("""SELECT ST_X(geom) AS lon, ST_Y(geom) AS lat, apparie, recu_par_reseau AS recu, id
                    FROM indic.sar_detection
                    WHERE instant BETWEEN :t - interval '10 minutes' AND :t + interval '10 minutes'
                      AND categorie IS DISTINCT FROM 'structure fixe probable (parc éolien)'
                      AND ST_Intersects(geom, ST_MakeEnvelope(:x0, :y0, :x1, :y1, 4326))""",
                 {"t": c.instant, "x0": x0, "y0": y0, "x1": x1, "y1": y1})
    # état : 0 reçu par le réseau, 1 identifié mais non reçu, 2 sans AIS, 3 sans AIS près du navire silencieux
    etat = lambda r: 3 if (not r.apparie and abs(r.lon - c.lon) < 1e-6 and abs(r.lat - c.lat) < 1e-6) else         2 if not r.apparie else 1 if r.recu is False else 0
    iso = lambda ts: ts.strftime("%Y-%m-%dT%H:%MZ")
    silence = {
        "navire": pseudo(c.mmsi), "famille": c.famille, "t0": iso(t0),
        "debut": minutes(c.debut, t0), "fin": minutes(c.fin, t0), "passe": minutes(c.instant, t0),
        "duree_h": round(float(c.duree_h), 1), "distance_nm": round(float(c.distance_nm), 1),
        "trace": [[round(r.lon, 4), round(r.lat, 4), minutes(r.ts, t0)] for r in tr.itertuples()],
        "radar": [[round(r.lon, 4), round(r.lat, 4), etat(r)] for r in rd.itertuples()],
        "cadre": [[round(x0, 3), round(y0, 3)], [round(x1, 3), round(y1, 3)]],
    }

    # 2. un MMSI, deux émetteurs : le navire au plus grand nombre de sauts impossibles
    n = requete("""SELECT s.mmsi, n.famille, count(*) AS sauts, avg(s.distance_nm) AS distance,
                          min(s.ts) AS premier, max(s.ts_suivant) AS dernier
                   FROM indic.saut_position s JOIN indic.anomalie_navire a USING (mmsi)
                   JOIN ais.navire n USING (mmsi)
                   WHERE a.position_incoherente GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 1""").iloc[0]
    t1 = n.premier - pd.Timedelta(hours=1)
    pos = requete("""SELECT ts, ST_X(geom) AS lon, ST_Y(geom) AS lat FROM ais.position
                     WHERE mmsi = :m AND ts BETWEEN :a AND :b ORDER BY ts""",
                  {"m": int(n.mmsi), "a": t1, "b": n.dernier + pd.Timedelta(hours=1)})
    # pas d'attribution des positions à l'un ou l'autre émetteur : quand les deux navires se croisent,
    # toute règle peut intervertir leurs trajets. On montre ce que l'AIS montre : la suite des positions
    # annoncées sous ce MMSI et les sauts impossibles relevés par sql/07_identite.sql
    sauts = requete("""SELECT ST_X(geom) AS x1, ST_Y(geom) AS y1, ST_X(geom_suivant) AS x2,
                              ST_Y(geom_suivant) AS y2, ts_suivant FROM indic.saut_position
                       WHERE mmsi = :m ORDER BY ts""", {"m": int(n.mmsi)})
    tout = pos[["lon", "lat"]]
    identite = {
        "navire": pseudo(n.mmsi), "famille": n.famille, "t0": iso(t1),
        "distance_nm": round(float(n.distance), 0), "duree_h": round((n.dernier - n.premier).total_seconds() / 3600),
        "positions": [[round(r.lon, 4), round(r.lat, 4), minutes(r.ts, t1)]
                      for i, r in enumerate(pos.itertuples()) if i % 2 == 0],
        "sauts": [[round(r.x1, 4), round(r.y1, 4), round(r.x2, 4), round(r.y2, 4), minutes(r.ts_suivant, t1)]
                  for r in sauts.itertuples()],
        "cadre": [[round(tout.lon.min() - 0.3, 3), round(tout.lat.min() - 0.15, 3)],
                  [round(tout.lon.max() + 0.3, 3), round(tout.lat.max() + 0.15, 3)]],
    }
    json_compact(SORTIE / "recits.json", {"silence": silence, "identite": identite})


def semaines():
    """Plusieurs semaines (10_semaines.py, puis 06) : chiffres de chaque semaine, récurrence des angles
    morts par maille H3, foyers de silences inexpliqués. Absent tant que 10_semaines.py n'a pas tourné."""
    import sqlite3
    try:
        rc = lire("recurrence_couverture", ["statut", "nb_mauvaises", "nb_jugees"])
    except Exception:
        log("Pas de données sur plusieurs semaines (10_semaines.py)")
        for nom in ("recurrence.geojson", "foyers.geojson", "inexpliquees_semaines.geojson", "semaines.json"):
            (SORTIE / nom).unlink(missing_ok=True)
        return False
    ecrire(rc[rc["statut"] != "Not enough traffic"], "recurrence")
    fo = lire("foyer_inexpliquees", ["nb_semaines", "nb_silences", "nb_navires"])
    ecrire(fo[fo["nb_semaines"] >= 2], "foyers")
    ix = lire("inexpliquee_semaines", ["semaine", "famille", "debut", "duree_h"])
    ix["semaine"] = pd.to_datetime(ix["semaine"]).dt.strftime("%Y-%m-%d")
    ecrire(ix, "inexpliquees_semaines")
    # angles morts chroniques par pays : la ZEE la plus proche du centre de chaque maille (une maille
    # des eaux territoriales, hors des ZEE de Marine Regions, va au pays dont elle borde la ZEE)
    zee = gpd.read_file(CARTO, layer="zee", engine="pyogrio").to_crs(3035)
    chron = rc[rc["statut"] == "Chronic"].to_crs(3035)
    chron = gpd.GeoDataFrame(geometry=chron.geometry.centroid, crs=3035)
    pays = gpd.sjoin_nearest(chron, zee[["souverain", "geometry"]], how="left")["souverain"].value_counts()
    n = requete("""SELECT count(DISTINCT mmsi) AS navires,
                          (SELECT count(*) FROM (SELECT mmsi FROM semaine.inexpliquee GROUP BY mmsi
                                                 HAVING count(DISTINCT semaine) >= 2) x) AS navires_2
                   FROM semaine.inexpliquee""").iloc[0]
    with sqlite3.connect(CARTO) as cnx:
        cs = pd.read_sql("SELECT * FROM chiffres_semaine ORDER BY semaine", cnx)
    cs["semaine"] = pd.to_datetime(cs["semaine"]).dt.strftime("%Y-%m-%d")
    cs["part_couverte"] = cs["part_couverte"].round(3)
    statuts = rc["statut"].value_counts()
    json_compact(SORTIE / "semaines.json", {
        "semaines": cs.drop(columns=["nb_positions"]).to_dict("records"),
        "mailles": {k: int(v) for k, v in statuts.items()},
        "foyers": int((fo["nb_semaines"] >= 2).sum()),
        "foyers_3": int((fo["nb_semaines"] >= 3).sum()),
        "chroniques_par_pays": {k: int(v) for k, v in pays.items()},
        "chroniques_km2": int(round(rc[rc["statut"] == "Chronic"].to_crs(3035).area.sum() / 1e6, -1)),
        "inexpliquees": {"total": int(len(ix)), "navires": int(n.navires), "navires_2_semaines": int(n.navires_2)},
    })
    return True


def ecrire(g, nom):
    for c in g.columns:
        if pd.api.types.is_datetime64_any_dtype(g[c]):
            g[c] = g[c].dt.strftime("%Y-%m-%d %H:%M")
    chemin = SORTIE / f"{nom}.geojson"
    chemin.write_text(g.to_crs(4326).to_json(drop_id=True, na="drop"), encoding="utf-8")
    log(f"{chemin.name} : {len(g)} objets, {chemin.stat().st_size / 1e3:.0f} ko")


if __name__ == "__main__":
    SORTIE.mkdir(parents=True, exist_ok=True)

    ecrire(lire("terre", [], 0.002), "terre")
    ecrire(lire("zone_etude", []), "zone_etude")
    ecrire(lire("limite_zee", ["nom"]), "limite_zee")
    t = lire("trafic_classes", ["classe"], 0.003)
    ecrire(t, "trafic")
    ecrire(lire("lacunes_reception", [], 0.003), "lacunes")
    cv = lire("couverture", ["classe", "taux_reception", "taux_perte", "nb_navires"])
    cv["taux_reception"] = cv["taux_reception"].round(3)
    cv["taux_perte"] = cv["taux_perte"].round(3)
    ecrire(cv, "couverture")
    iv = lire("indice_vigilance", ["indice", "nb_signaux", "nb_navires"])
    iv["indice"] = iv["indice"].round(1)
    ecrire(iv[iv["indice"] > 0], "indice")
    ecrire(lire("infrastructure", ["categorie", "nom"], 0.0005), "infrastructure")
    ecrire(lire("parc_eolien", ["nom"], 0.0005), "eolien")

    s = lire("silence_ais", ["navire", "famille", "debut", "fin", "duree_h", "distance_nm", "categorie", "nature"])
    s = s[s["categorie"] == "coupure inexpliquée"].copy()
    s["duree_h"] = s["duree_h"].round(1)
    s["distance_nm"] = s["distance_nm"].round(1)
    ecrire(s.drop(columns=["categorie"]), "silences_inexpliques")

    j = lire("saut_position", ["navire", "debut", "distance_nm", "vitesse_implicite", "mmsi_partage"])
    j = j[j["mmsi_partage"].astype(bool)].drop(columns=["mmsi_partage"])
    j["distance_nm"] = j["distance_nm"].round(1)
    j["vitesse_implicite"] = j["vitesse_implicite"].round(0)
    ecrire(j, "mmsi_partages")

    st = lire("stationnement_infra", ["navire", "famille", "debut", "duree_h", "infrastructure", "distance_min_m"])
    st["duree_h"] = st["duree_h"].round(1)
    st["distance_min_m"] = st["distance_min_m"].round(0)
    ecrire(st, "stationnements")

    r = lire("rencontre", ["famille_a", "famille_b", "debut", "duree_h", "distance_moyenne_m"])
    r["duree_h"] = r["duree_h"].round(1)
    r["distance_moyenne_m"] = r["distance_moyenne_m"].round(0)
    ecrire(r, "rencontres")

    validation = []
    try:
        rd = lire("detection_radar", ["instant", "apparie", "recu_par_reseau", "categorie", "classe_couverture"])
        # part des navires identifiés par le radar que le réseau danois a reçus, par classe de couverture
        # (navires absents de nos données de classe A exclus, comme dans le rapport qualité)
        ap = rd[rd["apparie"].astype(bool) & rd["recu_par_reseau"].notna()]
        for classe in ("Reliable", "Degraded", "Not enough traffic", "Poor"):
            r = ap.loc[ap["classe_couverture"] == classe, "recu_par_reseau"].isin([True, 1, "True"])
            if len(r):
                validation.append({"classe": classe, "n": int(len(r)), "recus": int(r.sum()),
                                   "part": round(float(r.mean()), 3)})
        sa = rd[(~rd["apparie"].astype(bool)) & (rd["categorie"] != "structure fixe probable (parc éolien)")].copy()
        sa["categorie"] = sa["categorie"].map(RADAR_EN).fillna(sa["categorie"])
        ecrire(sa.drop(columns=["apparie", "recu_par_reseau"]), "radar_sans_ais")
    except Exception as e:  # couche absente tant que 08_sar_gfw.py n'a pas tourné
        log(f"Pas de détections radar : {e}")

    # chiffres clés de l'aire d'étude, lus par la page
    z = gpd.read_file(CARTO, layer="zone_fiche", engine="pyogrio")
    etude = z[z["zone_id"] == "study-area"].drop(columns="geometry").iloc[0].to_dict()
    chiffres = {k: (None if pd.isna(v) else (float(v) if isinstance(v, float) else v))
                for k, v in etude.items() if k.startswith(("nb_", "nav_", "part_"))}
    chiffres["validation_radar"] = validation

    donnees_fiche()
    recits()
    # données facultatives : la page ne demande que celles qui sont publiées
    chiffres["options"] = ["recurrence", "foyers", "inexpliquees_semaines", "semaines"] if semaines() else []
    (SORTIE / "chiffres.json").write_text(json.dumps(chiffres, indent=1), encoding="utf-8")
    log(f"chiffres.json : {len(chiffres)} valeurs")
    total = sum(f.stat().st_size for f in SORTIE.rglob("*") if f.is_file())
    log(f"Données de la carte : {total / 1e6:.1f} Mo")
