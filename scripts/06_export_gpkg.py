"""Exporte les couches de cartographie dans deux GeoPackages et prépare les fiches de zone.

    donnees/produites/carto.gpkg    référentiel, indicateurs, zones de fiche (versionné, léger)
    donnees/produites/traces.gpkg   traces des navires (lourd, non versionné)
    qgis/graphiques/<zone>.svg      graphique « d'où viennent les silences » de chaque fiche

Les navires n'y figurent que sous un pseudonyme (V-XXXXXX) : voir regles.py.
"""
import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPolygon

import config
from graphique_fiche import CATEGORIES, graphique
from outils import log, moteur, requete
from regles import classe_couverture, pseudonymiser, sel

CARTO = config.PRODUITES / "carto.gpkg"
TRACES = config.PRODUITES / "traces.gpkg"
GRAPHIQUES = config.RACINE / "qgis" / "graphiques"

# repères de lecture de la carte : mers, îles, villes
LIEUX = [
    ("Skagerrak", "mer", 9.9, 57.95), ("Kattegat", "mer", 11.55, 56.85),
    ("Øresund", "mer", 12.72, 55.92), ("Great Belt", "mer", 10.98, 55.42),
    ("Fehmarn Belt", "mer", 11.3, 54.6), ("Arkona Basin", "mer", 13.55, 55.12),
    ("Bornholm Basin", "mer", 15.75, 55.3), ("Pomeranian Bay", "mer", 14.25, 54.2),
    ("Baltic Sea", "mer", 15.6, 54.75),
    ("DENMARK", "pays", 9.55, 56.3), ("SWEDEN", "pays", 13.6, 56.9),
    ("GERMANY", "pays", 10.6, 54.05), ("POLAND", "pays", 16.0, 54.15),
    ("Bornholm", "ile", 14.92, 55.13),
    ("Skagen", "ville", 10.59, 57.72), ("Gothenburg", "ville", 11.97, 57.71),
    ("Aarhus", "ville", 10.2, 56.16), ("Copenhagen", "ville", 12.57, 55.68),
    ("Malmö", "ville", 13.0, 55.6), ("Kiel", "ville", 10.13, 54.32),
    ("Rostock", "ville", 12.13, 54.09), ("Rønne", "ville", 14.7, 55.1),
]

# zones des fiches : l'aire d'étude, puis la part de chaque ZEE qui s'y trouve
ZONES_ZEE = [
    ("danish-eez", "Danish EEZ", "Danish Exclusive Economic Zone"),
    ("swedish-eez", "Swedish EEZ", "Swedish Exclusive Economic Zone"),
    ("german-eez", "German EEZ", "German Exclusive Economic Zone"),
    ("polish-eez", "Polish EEZ", "Polish Exclusive Economic Zone"),
]


def lire(sql, eng):
    return gpd.read_postgis(sql, eng, geom_col="geom")


def ecrire(gdf, couche, fichier=CARTO):
    gdf.to_file(fichier, layer=couche, driver="GPKG", engine="pyogrio")
    log(f"{fichier.name} / {couche} : {len(gdf)} objets")


# --- Zones de fiche et leurs chiffres clés -----------------------------------------------
def zones(eng):
    etude = lire("""SELECT 'study-area' AS zone_id, 'Danish Straits & Bornholm Basin' AS nom,
                           'Study area' AS sous_titre, 1 AS ordre, geom FROM ref.zone_etude""", eng)
    parts = []
    for i, (zone_id, court, nom_mr) in enumerate(ZONES_ZEE, start=2):
        parts.append(lire(f"""
            SELECT '{zone_id}' AS zone_id, '{court}' AS nom,
                   'Within the study area' AS sous_titre, {i} AS ordre,
                   ST_Multi(ST_CollectionExtract(ST_Intersection(z.geom, e.geom), 3)) AS geom
            FROM ref.zee z, ref.zone_etude e WHERE z.nom = '{nom_mr}'""", eng))
    return pd.concat([etude] + parts, ignore_index=True)


def chiffres_positions(zs):
    """Navires, heures-navire et part du trafic bien couvert, toutes zones en un seul passage
    sur les positions (les zones sont découpées pour que l'index spatial travaille)."""
    valeurs = ", ".join(f"('{z.zone_id}', '{z.geom.wkt}')" for _, z in zs.iterrows())
    return requete(f"""
        WITH zone AS (
            SELECT zone_id, ST_Subdivide(ST_GeomFromText(wkt, 4326), 64) AS g
            FROM (VALUES {valeurs}) AS v(zone_id, wkt)
        )
        SELECT z.zone_id, count(DISTINCT p.mmsi) AS nb_navires, count(*) / 60.0 AS heures_navire,
               avg(CASE WHEN p.sog >= 3 THEN CASE WHEN c.bonne THEN 1.0 ELSE 0.0 END END) AS part_couverte
        FROM zone z
        JOIN ais.position p ON ST_Intersects(p.geom, z.g)
        LEFT JOIN indic.couverture c ON c.h3 = h3_lat_lng_to_cell(p.geom, 6)
        GROUP BY z.zone_id""").set_index("zone_id")


def chiffres_signaux(geom_wkt):
    """Silences et signaux d'une zone ; les silences sont rattachés à la zone de leur début."""
    z = f"ST_GeomFromText('{geom_wkt}', 4326)"
    s = requete(f"""
        SELECT
          (SELECT count(*) FROM indic.coupure WHERE ST_Intersects(geom_debut, {z})) AS nb_silences,
          (SELECT count(*) FROM indic.coupure WHERE ST_Intersects(geom_debut, {z})
             AND categorie = 'réception insuffisante probable') AS nb_reception,
          (SELECT count(*) FROM indic.coupure WHERE ST_Intersects(geom_debut, {z})
             AND categorie = 'coupure inexpliquée') AS nb_inexpliquees,
          (SELECT count(DISTINCT mmsi) FROM indic.coupure WHERE ST_Intersects(geom_debut, {z})
             AND categorie = 'coupure inexpliquée') AS nav_inexpliquees,
          (SELECT count(DISTINCT mmsi) FROM indic.saut_position WHERE ST_Intersects(geom, {z})) AS nav_sauts,
          (SELECT count(DISTINCT s.mmsi) FROM indic.saut_position s
             JOIN indic.anomalie_navire a USING (mmsi)
             WHERE a.position_incoherente AND ST_Intersects(s.geom, {z})) AS nav_mmsi_partage,
          (SELECT count(*) FROM indic.stationnement_infra WHERE ST_Intersects(geom, {z})) AS nb_stationnements,
          (SELECT count(DISTINCT mmsi) FROM indic.stationnement_infra WHERE ST_Intersects(geom, {z})) AS nav_stationnements,
          (SELECT count(*) FROM indic.rencontre WHERE ST_Intersects(geom, {z})) AS nb_rencontres""").iloc[0]
    if requete("SELECT to_regclass('indic.sar_detection') IS NOT NULL AS ok")["ok"][0]:
        r = requete(f"""
            SELECT coalesce(sum(detections) FILTER (WHERE NOT apparie
                       AND categorie <> 'structure fixe probable (parc éolien)'), 0) AS nb_radar_sans_ais,
                   (count(*) FILTER (WHERE recu_par_reseau))::float
                   / nullif(count(*) FILTER (WHERE recu_par_reseau IS NOT NULL), 0) AS part_radar_recus
            FROM indic.sar_detection WHERE ST_Intersects(geom, {z})""").iloc[0]
        s = pd.concat([s, r])
    cats = requete(f"""SELECT categorie, count(*) AS n FROM indic.coupure
                       WHERE ST_Intersects(geom_debut, {z}) GROUP BY 1""")
    return s.to_dict(), dict(zip(cats["categorie"], cats["n"]))


def contours(zs, eng):
    """Contour à tracer pour chaque fiche : limites maritimes et cadre de l'aire d'étude, sans le
    trait de côte (les ZEE le suivent îlot par îlot, ce qui noircirait la carte)."""
    from shapely.ops import unary_union
    limites = lire("SELECT geom FROM ref.limite_zee", eng).geometry
    cadre = lire("SELECT ST_Boundary(geom) AS geom FROM ref.zone_etude", eng).geometry
    guides = unary_union(list(limites) + list(cadre)).buffer(0.003)
    lignes = []
    for _, z in zs.iterrows():
        bord = z.geom.boundary
        trait = bord if z.zone_id == "study-area" else bord.intersection(guides)
        lignes.append({"zone_id": z.zone_id, "geom": trait.simplify(0.001)})
    return gpd.GeoDataFrame(lignes, geometry="geom", crs=4326)


if __name__ == "__main__":
    config.PRODUITES.mkdir(parents=True, exist_ok=True)
    eng = moteur()
    grain = sel()
    for f in (CARTO, TRACES):
        f.unlink(missing_ok=True)

    # zones de fiche, chiffres clés et graphiques
    zs = zones(eng)
    positions = chiffres_positions(zs)
    lignes = []
    for _, z in zs.iterrows():
        chiffres, comptes = chiffres_signaux(z.geom.wkt)
        chiffres.update(positions.loc[z.zone_id].to_dict())
        GRAPHIQUES.mkdir(parents=True, exist_ok=True)
        graphique(GRAPHIQUES / f"{z.zone_id}.svg", comptes)
        lignes.append(chiffres)
        log(f"Fiche {z.zone_id} : {int(chiffres['nb_navires'])} navires, "
            f"{int(chiffres['nb_silences'])} silences, {int(chiffres['nb_inexpliquees'])} inexpliqués")
    zs = pd.concat([zs, pd.DataFrame(lignes)], axis=1)
    for c in zs.columns:
        if c.startswith(("nb_", "nav_")):
            zs[c] = zs[c].astype(int)
    zs["heures_navire"] = zs["heures_navire"].astype(float).round(0)
    zs["part_couverte"] = zs["part_couverte"].astype(float).round(3)
    if "part_radar_recus" in zs:
        zs["part_radar_recus"] = zs["part_radar_recus"].astype(float).round(3)
    zs["graphique"] = "graphiques/" + zs["zone_id"] + ".svg"
    ecrire(contours(zs, eng), "zone_contour")
    # géométrie simplifiée (≈ 150 m) pour l'affichage seulement : les chiffres ci-dessus ont été
    # calculés sur la géométrie exacte, dont le tracé côtier surchargerait la carte
    zs = gpd.GeoDataFrame(zs, geometry="geom", crs=4326)
    # (puis densifiée : en projection, les côtés de l'aire d'étude suivent les parallèles)
    zs["geom"] = [g if g.geom_type == "MultiPolygon" else MultiPolygon([g]) for g in
                  zs.geometry.simplify(0.002, preserve_topology=True).segmentize(0.05)]
    ecrire(zs, "zone_fiche")

    # référentiel
    ecrire(lire("SELECT geom FROM ref.zone_etude", eng), "zone_etude")
    ecrire(lire("SELECT iso, nom, geom FROM ref.terre", eng), "terre")
    ecrire(lire("SELECT nom, souverain, geom FROM ref.zee", eng), "zee")
    ecrire(lire("SELECT nom, souverain, geom FROM ref.mer_territoriale", eng), "mer_territoriale")
    ecrire(lire("SELECT nom, nature, etat_1, etat_2, geom FROM ref.limite_zee", eng), "limite_zee")
    # tracés simplifiés à ≈ 20 m pour l'affichage (les câbles allemands d'EMODnet comptent près d'un
    # million de sommets) ; l'analyse, elle, a utilisé les tracés complets dans PostGIS
    ecrire(lire("SELECT id, source, categorie, nom, etat, "
                "ST_Multi(ST_SimplifyPreserveTopology(geom, 0.0002)) AS geom FROM ref.infrastructure", eng),
           "infrastructure")
    ecrire(lire("SELECT nom, pays, etat, puissance_mw, nb_eoliennes, geom FROM ref.parc_eolien", eng), "parc_eolien")
    ecrire(lire("SELECT nom, nature, geom FROM ref.mouillage", eng), "mouillage")
    ecrire(lire("SELECT s.mmsi AS id_station, s.nb_messages, s.geom FROM ais.station s, ref.zone_etude z "
                "WHERE ST_Intersects(s.geom, ST_Buffer(z.geom, 1))", eng), "station_ais")
    lieux = pd.DataFrame(LIEUX, columns=["nom", "nature", "lon", "lat"])
    ecrire(gpd.GeoDataFrame(lieux[["nom", "nature"]], crs=4326,
                            geometry=gpd.points_from_xy(lieux.lon, lieux.lat)).rename_geometry("geom"), "lieu")

    # grilles H3
    ecrire(lire("SELECT h3::text, heures_navire, heures_route, heures_petrolier, nb_navires, geom "
                "FROM indic.trafic", eng), "trafic")
    cv = lire("""SELECT h3::text, nb_intervalles, nb_navires, nb_navires_perdus, taux_reception,
                        taux_perte, bonne, geom FROM indic.couverture""", eng)
    cv["classe"] = cv.apply(classe_couverture, axis=1)
    ecrire(cv, "couverture")

    # versions fusionnées pour la fiche : quelques polygones au lieu de milliers d'hexagones,
    # PDF léger et hachures continues
    tf = lire("SELECT heures_navire, geom FROM indic.trafic", eng)
    bornes = [0, 2, 10, 40, 150, float("inf")]
    tf["classe"] = pd.cut(tf["heures_navire"], bornes, labels=range(1, 6), right=False).astype(int)
    ecrire(tf.dissolve("classe").reset_index()[["classe", "geom"]], "trafic_classes")
    lac = cv[cv["classe"] == "Poor"].dissolve().reset_index(drop=True)[["geom"]]
    ecrire(lac, "lacunes_reception")
    ecrire(lire("""SELECT h3::text, heures_navire, nb_navires, nav_coupures, nav_sauts, nav_stationnements,
                          nav_rencontres, nb_signaux, indice, geom FROM indic.score""", eng), "indice_vigilance")

    # signaux, navires pseudonymisés
    cp = lire("""SELECT c.id, c.mmsi, c.famille, c.debut, c.fin, c.duree_h, c.distance_nm,
                        c.categorie, c.nature, c.part_couverte, c.part_reception,
                        c.trajet AS geom FROM indic.coupure c""", eng)
    cp.insert(1, "navire", pseudonymiser(cp.pop("mmsi"), grain))
    cp.insert(cp.columns.get_loc("categorie") + 1, "categorie_en", cp["categorie"].map(CATEGORIES))
    ecrire(cp, "silence_ais")

    # mmsi_partage : navire à trois sauts ou plus, deux émetteurs sous le même MMSI
    sp = lire("""SELECT s.id, s.mmsi, s.ts AS debut, s.ts_suivant AS fin, s.distance_nm, s.vitesse_implicite,
                        a.position_incoherente AS mmsi_partage,
                        ST_MakeLine(s.geom, s.geom_suivant) AS geom
                 FROM indic.saut_position s JOIN indic.anomalie_navire a USING (mmsi)""", eng)
    sp.insert(1, "navire", pseudonymiser(sp.pop("mmsi"), grain))
    ecrire(sp, "saut_position")

    st = lire("""SELECT s.id, s.mmsi, n.famille, s.debut, s.fin, s.duree_h, s.sog_max,
                        s.distance_min_m, i.categorie AS infrastructure, i.source, i.nom AS nom_infrastructure,
                        s.geom
                 FROM indic.stationnement_infra s JOIN ais.navire n USING (mmsi)
                 JOIN ref.infrastructure i ON i.id = s.infra_id""", eng)
    st.insert(1, "navire", pseudonymiser(st.pop("mmsi"), grain))
    ecrire(st, "stationnement_infra")

    rc = lire("""SELECT r.id, r.mmsi_a, r.mmsi_b, na.famille AS famille_a, nb.famille AS famille_b,
                        r.debut, r.fin, r.duree_h, r.distance_moyenne_m, r.geom
                 FROM indic.rencontre r JOIN ais.navire na ON na.mmsi = r.mmsi_a
                 JOIN ais.navire nb ON nb.mmsi = r.mmsi_b""", eng)
    rc.insert(1, "navire_a", pseudonymiser(rc.pop("mmsi_a"), grain))
    rc.insert(2, "navire_b", pseudonymiser(rc.pop("mmsi_b"), grain))
    ecrire(rc, "rencontre")

    # détections radar Sentinel-1 (Global Fishing Watch) : sans MMSI ni identité
    if requete("SELECT to_regclass('indic.sar_detection') IS NOT NULL AS ok")["ok"][0]:
        rd = lire("""SELECT id, instant, detections, apparie, recu_par_reseau, classe_couverture, categorie,
                         round(dist_ais_m) AS dist_ais_m, geom FROM indic.sar_detection""", eng)
        # booléen avec valeurs nulles : sans type explicite, il partirait en texte 'True' / 'False'
        rd["recu_par_reseau"] = rd["recu_par_reseau"].astype("boolean")
        ecrire(rd, "detection_radar")

    # plusieurs semaines (10_semaines.py) : récurrence des angles morts, silences inexpliqués semaine
    # par semaine (sans MMSI) et leurs foyers, chiffres de chaque semaine
    if requete("SELECT to_regclass('semaine.recurrence') IS NOT NULL AS ok")["ok"][0]:
        ecrire(lire("""SELECT h3::text AS h3, nb_jugees, nb_fiables, nb_degradees, nb_mauvaises, statut, geom
                       FROM semaine.recurrence""", eng), "recurrence_couverture")
        ecrire(lire("""SELECT semaine, famille, debut, round(duree_h::numeric, 1) AS duree_h, geom
                       FROM semaine.inexpliquee""", eng), "inexpliquee_semaines")
        ecrire(lire("""SELECT h3::text AS h3, nb_semaines, nb_silences, nb_navires, geom FROM semaine.foyer""", eng),
               "foyer_inexpliquees")
        cs = requete("SELECT * FROM semaine.chiffres ORDER BY semaine")
        cs.to_sql("chiffres_semaine", f"sqlite:///{CARTO}", index=False, if_exists="replace")
        log(f"{CARTO.name} / chiffres_semaine : {len(cs)} semaines (table sans géométrie)")

    nv = requete("""SELECT n.mmsi, n.famille, n.pavillon, n.longueur, n.imo_statut, n.nb_noms, n.nb_imo,
                           n.nb_types, n.nb_positions, a.nb_sauts, a.nb_coupures_inexpliquees,
                           a.position_incoherente, a.identite_variable, a.imo_douteux
                    FROM ais.navire n JOIN indic.anomalie_navire a USING (mmsi)""")
    nv.insert(0, "navire", pseudonymiser(nv.pop("mmsi"), grain))
    nv.to_sql("navire", f"sqlite:///{CARTO}", index=False, if_exists="replace")
    log(f"{CARTO.name} / navire : {len(nv)} lignes (table sans géométrie)")

    # traces, à part
    tr = lire("""SELECT t.id, t.mmsi, n.famille, t.debut, t.fin,
                        ST_SimplifyPreserveTopology(t.geom, 0.0005) AS geom
                 FROM ais.trace t JOIN ais.navire n USING (mmsi)""", eng)
    tr.insert(1, "navire", pseudonymiser(tr.pop("mmsi"), grain))
    ecrire(tr, "trace", TRACES)
    log(f"carto.gpkg : {CARTO.stat().st_size / 1e6:.1f} Mo, traces.gpkg : {TRACES.stat().st_size / 1e6:.1f} Mo")
