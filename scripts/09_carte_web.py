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

CARTO = config.PRODUITES / "carto.gpkg"
SORTIE = config.RACINE / "carte" / "donnees"
FICHE = SORTIE / "fiche"
SEL = config.PRODUITES / "sel_pseudonymes.txt"

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
    log(f"fiche/{chemin.name} : {chemin.stat().st_size / 1e3:.0f} ko")


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
    sel = SEL.read_text(encoding="utf-8").strip()
    ordre = sorted(paires["mmsi"].unique(), key=lambda m: hashlib.sha256(f"n{sel}{int(m)}".encode()).hexdigest())
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
    (SORTIE / "chiffres.json").write_text(json.dumps(chiffres, indent=1), encoding="utf-8")
    log(f"chiffres.json : {len(chiffres)} valeurs")

    donnees_fiche()
    total = sum(f.stat().st_size for f in SORTIE.rglob("*") if f.is_file())
    log(f"Données de la carte : {total / 1e6:.1f} Mo")
