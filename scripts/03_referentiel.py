"""Construit le référentiel géographique à partir de sources ouvertes.

    ref.zee                  zones économiques exclusives (Marine Regions)
    ref.mer_territoriale     eaux territoriales, 12 milles (Marine Regions)
    ref.limite_zee           limites maritimes entre États (Marine Regions)
    ref.terre                terres émergées au 1:1 000 000 (Eurostat GISCO)
    ref.infrastructure       câbles et pipelines sous-marins : EMODnet, TeleGeography, OSM
    ref.parc_eolien          parcs éoliens en mer (EMODnet)
    ref.mouillage            zones de mouillage (OSM)
    ref.mid                  pavillon déduit des 3 premiers chiffres du MMSI (UIT, via Wikipédia)

Chaque réponse brute est conservée dans donnees/brutes/referentiel/ : on sait d'où vient
chaque objet et le script se relance sans rien retélécharger (--force pour rafraîchir).
"""
import argparse
import json
import re

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import LineString, MultiLineString, MultiPolygon, Polygon, box

import config
from outils import log, moteur, psql

UA = {"User-Agent": "what-ais-doesnt-show/1.0 (portfolio project, open data)"}
OUEST, SUD, EST, NORD = config.BBOX
ZONE = box(OUEST, SUD, EST, NORD)
# un peu plus large que la zone d'étude, pour les côtes et les tracés qui en sortent
LARGE = box(OUEST - 1, SUD - 0.5, EST + 1, NORD + 0.5)
BBOX_WFS = f"{SUD},{OUEST},{NORD},{EST},urn:ogc:def:crs:EPSG::4326"
FORCER = False


def telecharger(nom, url, params=None, data=None):
    """Télécharge une fois et garde la réponse brute dans le référentiel."""
    cible = config.REFERENTIEL / nom
    if cible.exists() and not FORCER:
        return cible
    log(f"Téléchargement : {nom}")
    rep = (requests.post(url, data=data, headers=UA, timeout=300) if data
           else requests.get(url, params=params, headers=UA, timeout=300))
    rep.raise_for_status()
    cible.write_bytes(rep.content)
    return cible


def wfs(nom, url, couche):
    params = {"service": "WFS", "version": "2.0.0", "request": "GetFeature",
              "typeNames": couche, "bbox": BBOX_WFS, "outputFormat": "application/json"}
    g = gpd.read_file(telecharger(nom, url, params))
    # le filtre du serveur porte sur les emprises : un polygone qui traverse
    # l'antiméridien (Alaska) a une emprise mondiale et passerait le filtre
    g = g[g.intersects(ZONE)].copy()
    g["geometry"] = g.intersection(LARGE)
    return g


def multi(geom):
    if isinstance(geom, Polygon):
        return MultiPolygon([geom])
    if isinstance(geom, LineString):
        return MultiLineString([geom])
    return geom


def premier(row, champs):
    for c in champs:
        v = row.get(c)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


# --- Zones maritimes et terres ------------------------------------------------------------
def zones_maritimes():
    url = "https://geo.vliz.be/geoserver/MarineRegions/wfs"
    zee = wfs("marineregions_eez.geojson", url, "MarineRegions:eez")
    zee = gpd.GeoDataFrame({
        "mrgid": zee["mrgid"], "nom": zee["geoname"], "souverain": zee["sovereign1"],
        "iso_souverain": zee["iso_sov1"]}, geometry=zee.geometry.map(multi), crs=4326)
    mt = wfs("marineregions_eez_12nm.geojson", url, "MarineRegions:eez_12nm")
    mt = gpd.GeoDataFrame({
        "mrgid": mt["mrgid"], "nom": mt["geoname"], "souverain": mt["sovereign1"],
        "iso_souverain": mt["iso_sov1"]}, geometry=mt.geometry.map(multi), crs=4326)
    return zee, mt


def limites_zee():
    """Limites maritimes entre deux États (traités, lignes médianes) : sur une carte, on trace
    ces lignes et non le contour des ZEE, qui suit le trait de côte îlot par îlot."""
    g = wfs("marineregions_eez_boundaries.geojson", "https://geo.vliz.be/geoserver/MarineRegions/wfs",
            "MarineRegions:eez_boundaries")
    g = g[g["sovereign2"].notna()]
    return gpd.GeoDataFrame({
        "nom": g["line_name"], "nature": g["line_type"],
        "etat_1": g["sovereign1"], "etat_2": g["sovereign2"]},
        geometry=g.geometry.map(multi), crs=4326)


def terres():
    url = ("https://gisco-services.ec.europa.eu/distribution/v2/countries/geojson/"
           "CNTR_RG_01M_2024_4326.geojson")
    pays = gpd.read_file(telecharger("gisco_CNTR_RG_01M_2024_4326.geojson", url))
    pays = pays[pays.intersects(LARGE)].copy()
    pays["geometry"] = pays.intersection(LARGE).map(multi)
    return gpd.GeoDataFrame({"iso": pays["CNTR_ID"], "nom": pays["NAME_ENGL"]},
                            geometry=pays.geometry, crs=4326)


# --- Infrastructures sous-marines ---------------------------------------------------------
def infra_emodnet():
    url = "https://ows.emodnet-humanactivities.eu/wfs"
    morceaux = []
    for couche, categorie in [("pipelines", "pipeline"),
                              ("pcablesbshcontis", "câble électrique"),
                              ("bshcontiscables", "câble de télécommunication")]:
        g = wfs(f"emodnet_{couche}.geojson", url, f"emodnet:{couche}")
        noms = g.apply(lambda r: premier(r, ["name", "name_"]), axis=1)
        etat = g.apply(lambda r: premier(r, ["status"]), axis=1)
        morceaux.append(gpd.GeoDataFrame({
            "source": f"EMODnet ({couche})", "categorie": categorie,
            "nom": noms, "etat": etat}, geometry=g.geometry, crs=4326))
    return morceaux


def infra_telegeography():
    url = "https://www.submarinecablemap.com/api/v3/cable/cable-geo.json"
    g = gpd.read_file(telecharger("telegeography_cable-geo.json", url))
    g = g[g.intersects(LARGE)]
    return gpd.GeoDataFrame({"source": "TeleGeography", "categorie": "câble de télécommunication",
                             "nom": g["name"], "etat": None}, geometry=g.geometry, crs=4326)


def overpass():
    s, o, n, e = SUD, OUEST, NORD, EST
    q = f"""[out:json][timeout:300];
    (
      way["seamark:type"="cable_submarine"]({s},{o},{n},{e});
      way["power"="cable"]["location"="submarine"]({s},{o},{n},{e});
      way["seamark:type"="pipeline_submarine"]({s},{o},{n},{e});
      way["seamark:type"="anchorage"]({s},{o},{n},{e});
      node["seamark:type"="anchorage"]({s},{o},{n},{e});
    );
    out geom tags;"""
    chemin = telecharger("osm_overpass.json", "https://overpass-api.de/api/interpreter",
                         data={"data": q})
    return json.loads(chemin.read_text(encoding="utf-8"))["elements"]


def infra_osm(elements):
    lignes = []
    for el in elements:
        t = el.get("tags", {})
        st = t.get("seamark:type")
        if el["type"] != "way" or st == "anchorage":
            continue
        if st == "pipeline_submarine":
            categorie = "pipeline"
        elif t.get("power") == "cable" or t.get("seamark:cable_submarine:category") == "power":
            categorie = "câble électrique"
        elif t.get("seamark:cable_submarine:category") in ("telephone", "telegraph", "data"):
            categorie = "câble de télécommunication"
        else:
            categorie = "câble (usage non précisé)"
        coords = [(p["lon"], p["lat"]) for p in el["geometry"]]
        if len(coords) < 2:
            continue
        lignes.append({"source": "OpenStreetMap", "categorie": categorie,
                       "nom": t.get("name") or t.get("seamark:name"),
                       "etat": t.get("seamark:status"), "geometry": LineString(coords)})
    return gpd.GeoDataFrame(lignes, crs=4326)


def mouillages(elements):
    zones = []
    for el in elements:
        t = el.get("tags", {})
        if t.get("seamark:type") != "anchorage":
            continue
        nom = t.get("seamark:name") or t.get("name")
        if el["type"] == "way":
            coords = [(p["lon"], p["lat"]) for p in el["geometry"]]
            if len(coords) >= 4 and coords[0] == coords[-1]:
                zones.append({"nom": nom, "nature": "zone cartographiée", "geometry": Polygon(coords)})
        elif el["type"] == "node":
            zones.append({"nom": nom, "nature": "point (rayon de 1 mille)",
                          "geometry": gpd.points_from_xy([el["lon"]], [el["lat"]])[0]})
    g = gpd.GeoDataFrame(zones, crs=4326).to_crs(3035)
    points = g.geom_type == "Point"
    # un mouillage noté par un simple point : hypothèse d'un cercle d'un mille nautique
    g.loc[points, "geometry"] = g.loc[points, "geometry"].buffer(1852)
    g["geometry"] = g.geometry.map(multi)
    return g.to_crs(4326)


def parcs_eoliens():
    g = wfs("emodnet_windfarmspoly.geojson", "https://ows.emodnet-humanactivities.eu/wfs",
            "emodnet:windfarmspoly")
    return gpd.GeoDataFrame({"nom": g["name"], "pays": g["country"], "etat": g["status"],
                             "puissance_mw": g["power_mw"], "nb_eoliennes": g["n_turbines"]},
                            geometry=g.geometry.map(multi), crs=4326)


# --- Pavillons ----------------------------------------------------------------------------
def table_mid():
    """Table des MID de l'UIT, lue dans la source wiki de l'article Wikipédia."""
    url = "https://en.wikipedia.org/w/index.php"
    texte = telecharger("wikipedia_maritime_identification_digits.txt", url,
                        {"title": "Maritime_identification_digits", "action": "raw"}
                        ).read_text(encoding="utf-8")
    lignes, pays = [], None
    for ligne in texte.splitlines():
        if not ligne.startswith("|") or ligne.startswith(("|-", "|}", "{|")):
            continue
        cellule = ligne[1:].strip()
        m = re.search(r"\{\{flag\|([^}|]+)", cellule) or re.search(r"\[\[([^\]|]+)", cellule)
        if m and not re.match(r"^\d", cellule):
            pays = m.group(1).strip()
        elif pays and re.match(r"^\d", cellule):
            # la remarque entre parenthèses peut citer d'autres codes : on ne la lit pas
            for code in re.findall(r"\b([2-7]\d{2})\b", cellule.split("(")[0]):
                lignes.append((int(code), pays))
            pays = None
    mid = pd.DataFrame(lignes, columns=["mid", "pays"]).drop_duplicates("mid")
    # registres rattachés à un État, que l'article liste comme des pays à part
    mid["pays"] = mid["pays"].replace({"Madeira": "Portugal (Madeira)", "Azores": "Portugal (Azores)",
                                       "Alaska": "United States (Alaska)"})
    return mid.sort_values("mid")


def charger(gdf, table, eng):
    gdf = gdf.rename_geometry("geom")
    gdf.to_postgis(table, eng, schema="ref", if_exists="replace", index=False)
    psql(f"ALTER TABLE ref.{table} ADD COLUMN id serial PRIMARY KEY;"
         f"CREATE INDEX ON ref.{table} USING gist (geom); ANALYZE ref.{table};")
    log(f"ref.{table} : {len(gdf)} objets")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true", help="retélécharge toutes les sources")
    FORCER = p.parse_args().force
    config.REFERENTIEL.mkdir(parents=True, exist_ok=True)
    eng = moteur()

    zee, mt = zones_maritimes()
    charger(zee, "zee", eng)
    charger(mt, "mer_territoriale", eng)
    charger(limites_zee(), "limite_zee", eng)
    charger(terres(), "terre", eng)

    osm = overpass()
    infra = pd.concat(infra_emodnet() + [infra_telegeography(), infra_osm(osm)],
                      ignore_index=True)
    infra = gpd.GeoDataFrame(infra, geometry="geometry", crs=4326)
    infra = infra[infra.intersects(LARGE) & infra.geometry.notna()].copy()
    infra["geometry"] = infra.intersection(LARGE).map(multi)
    infra = infra[infra.geom_type == "MultiLineString"]
    charger(infra, "infrastructure", eng)
    charger(parcs_eoliens(), "parc_eolien", eng)
    charger(mouillages(osm), "mouillage", eng)

    mid = table_mid()
    mid.to_sql("mid", eng, schema="ref", if_exists="replace", index=False)
    psql("ALTER TABLE ref.mid ADD PRIMARY KEY (mid)")
    log(f"ref.mid : {len(mid)} codes")
    log(psql("SELECT source, categorie, count(*) FROM ref.infrastructure GROUP BY 1, 2 ORDER BY 1, 2"))
