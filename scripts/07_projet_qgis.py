"""Construit le projet QGIS qgis/what_ais_doesnt_show.qgz à partir des GeoPackages exportés.

Couches stylées et rangées par thème, thèmes de carte, signets, et la mise en page
« Zone sheet » (A4, en anglais) : un atlas qui produit une fiche par zone, chiffres clés
lus dans la couche zone_fiche. Les fiches sont exportées en PDF et en PNG dans sorties/fiches/.

    Dans QGIS ouvert (console Python) :
        RACINE_PROJET = r"D:\\...\\what-ais-doesnt-show"
        exec(open(RACINE_PROJET + r"\\scripts\\07_projet_qgis.py", encoding="utf-8").read())
    Hors QGIS :
        python-qgis-ltr.bat scripts/07_projet_qgis.py
"""
from pathlib import Path

from qgis.core import (
    QgsApplication, QgsCategorizedSymbolRenderer, QgsCoordinateReferenceSystem, QgsFillSymbol,
    QgsGeometryGeneratorSymbolLayer, QgsGraduatedSymbolRenderer, QgsInvertedPolygonRenderer,
    QgsLayerTreeLayer, QgsLayerTreeModel, QgsLayout, QgsLayoutExporter, QgsLayoutItemLabel,
    QgsLayoutItemLegend, QgsLayoutItemMap, QgsLayoutItemMapGrid, QgsLayoutItemPicture,
    QgsLayoutItemScaleBar, QgsLayoutItemShape, QgsLayoutMeasurement, QgsLayoutObject,
    QgsLayoutPoint, QgsLayoutSize, QgsLegendStyle, QgsLineSymbol, QgsMapThemeCollection,
    QgsMarkerSymbol, QgsPalLayerSettings, QgsPointClusterRenderer, QgsPrintLayout, QgsProject,
    QgsProperty, QgsRectangle, QgsReferencedRectangle, QgsRendererCategory, QgsRendererRange,
    QgsRuleBasedLabeling, QgsRuleBasedRenderer, QgsScaleBarSettings, QgsSimpleFillSymbolLayer,
    QgsSingleSymbolRenderer, QgsBookmark, QgsTextBufferSettings, QgsTextFormat,
    QgsUnitTypes, QgsVectorLayer, QgsVectorLayerSimpleLabeling, QgsLinePatternFillSymbolLayer,
    QgsCoordinateTransform, QgsFontMarkerSymbolLayer, QgsLayoutItemPage, QgsFeature, QgsGeometry,
    QgsVectorFileWriter, QgsCoordinateTransformContext, QgsDatumTransform,
)
from qgis.PyQt.QtCore import QRectF, Qt
from qgis.PyQt.QtGui import QColor, QFont

# hors QGIS, l'application doit être initialisée avant de créer le moindre système de
# coordonnées : sinon la base PROJ n'est pas chargée et EPSG:3035 est invalide
AUTONOME = QgsApplication.instance() is None
if AUTONOME:
    _APP = QgsApplication([], True)
    _APP.initQgis()

if "RACINE_PROJET" in globals():
    RACINE = Path(RACINE_PROJET)
else:
    RACINE = Path(__file__).resolve().parents[1]
CARTO = RACINE / "donnees" / "produites" / "carto.gpkg"
TRACES = RACINE / "donnees" / "produites" / "traces.gpkg"
FICHIER_PROJET = RACINE / "qgis" / "what_ais_doesnt_show.qgz"
SORTIES = RACINE / "sorties" / "fiches"

CRS_CARTE = QgsCoordinateReferenceSystem("EPSG:3035")  # ETRS89-LAEA : aires et distances justes
POLICE = "Segoe UI"
PERIODE = "13–19 October 2026"

# palette : signaux validés pour les daltoniens (orange, violet, bleu, vert d'eau),
# fond et référentiel en neutres pour qu'ils ne concurrencent pas les signaux
MER = "#edf1f3"
TERRE = "#e7e3db"
COTE = "#b8b0a2"
ENCRE = "#1d1d1b"
ENCRE_2 = "#52514e"
ENCRE_3 = "#8a877f"
ORANGE, VIOLET, BLEU, VERT_EAU = "#eb6834", "#4a3aa7", "#2a78d6", "#1baf7a"


# --- Outils de style ---------------------------------------------------------------------
def couche(nom, table, fichier=CARTO):
    # pas de filtre de source (setSubsetString) : sur un GeoPackage, il verrouille le fichier et
    # les couches ouvertes ensuite ne se lisent plus. Les filtres sont portés par les styles.
    lyr = QgsVectorLayer(f"{fichier}|layername={table}", nom, "ogr")
    if not lyr.isValid():
        raise RuntimeError(f"Couche invalide : {table} ({fichier.name})")
    return lyr


def regles(lyr, liste):
    """Style à règles : liste (symbole, filtre, libellé). Un libellé vide sur une règle unique
    place le symbole sur la ligne du nom de la couche dans la légende."""
    racine = QgsRuleBasedRenderer.Rule(None)
    for symbole, filtre, libelle in liste:
        racine.appendChild(QgsRuleBasedRenderer.Rule(symbole, filterExp=filtre, label=libelle))
    lyr.setRenderer(QgsRuleBasedRenderer(racine))


def remplissage(couleur="#ffffff", contour="#000000", epaisseur=0.2, style_contour="solid",
                style="solid", transparence=1.0):
    s = QgsFillSymbol.createSimple({
        "color": couleur, "style": style, "outline_color": contour,
        "outline_width": str(epaisseur), "outline_style": style_contour,
        "joinstyle": "round"})
    s.setOpacity(transparence)
    return s


def ligne(couleur, epaisseur=0.3, style="solid", tirets=None, transparence=1.0):
    props = {"line_color": couleur, "line_width": str(epaisseur), "line_style": style,
             "capstyle": "round", "joinstyle": "round"}
    if tirets:
        props.update({"use_custom_dash": "1", "customdash": tirets, "customdash_unit": "MM"})
    s = QgsLineSymbol.createSimple(props)
    s.setOpacity(transparence)
    return s


def point(couleur, taille=2.0, forme="circle", contour="#ffffff", epaisseur=0.3):
    return QgsMarkerSymbol.createSimple({
        "name": forme, "color": couleur, "size": str(taille),
        "outline_color": contour, "outline_width": str(epaisseur)})


def hachure(couleur, angle=45, espacement=1.1, epaisseur=0.15):
    s = QgsFillSymbol()
    s.deleteSymbolLayer(0)
    h = QgsLinePatternFillSymbolLayer()
    h.setLineAngle(angle)
    h.setDistance(espacement)
    h.setSubSymbol(ligne(couleur, epaisseur))
    s.appendSymbolLayer(h)
    return s


def format_texte(taille, couleur=ENCRE, gras=False, italique=False, espacement=0.0, police=POLICE):
    f = QFont(police)
    f.setBold(gras)
    f.setItalic(italique)
    f.setLetterSpacing(QFont.AbsoluteSpacing, espacement)
    t = QgsTextFormat()
    t.setFont(f)
    t.setSize(taille)
    t.setSizeUnit(QgsUnitTypes.RenderPoints)
    t.setColor(QColor(couleur))
    return t


def tampon(fmt, couleur, taille=0.6, opacite=0.85):
    b = QgsTextBufferSettings()
    b.setEnabled(True)
    b.setSize(taille)
    b.setColor(QColor(couleur))
    b.setOpacity(opacite)
    fmt.setBuffer(b)
    return fmt


def categorise(lyr, champ, classes):
    """classes : liste (valeur, symbole, libellé)."""
    lyr.setRenderer(QgsCategorizedSymbolRenderer(
        champ, [QgsRendererCategory(v, s, l) for v, s, l in classes]))


def gradue(lyr, champ, classes):
    """classes : liste (min, max, symbole, libellé)."""
    lyr.setRenderer(QgsGraduatedSymbolRenderer(
        champ, [QgsRendererRange(a, b, s, l) for a, b, s, l in classes]))


def unique(lyr, symbole):
    lyr.setRenderer(QgsSingleSymbolRenderer(symbole))


# --- Couches -----------------------------------------------------------------------------
def couches():
    c = {}

    c["terre"] = couche("Land", "terre")
    unique(c["terre"], remplissage(TERRE, COTE, 0.15))

    c["trafic"] = couche("Shipping density (vessel-hours per cell)", "trafic")
    rampe = ["#e2e8ec", "#d4dde3", "#c2cfd7", "#aebfc9", "#97aab6"]
    bornes = [(0, 2), (2, 10), (10, 40), (40, 150), (150, 100000)]
    gradue(c["trafic"], "heures_navire", [
        (a, b, remplissage(col, col, 0, "no"), lib) for (a, b), col, lib in zip(
            bornes, rampe, ["< 2", "2 – 10", "10 – 40", "40 – 150", "> 150"])])

    c["couverture"] = couche("Shore AIS coverage", "couverture")
    categorise(c["couverture"], "classe", [
        ("Reliable", remplissage("#d5e5dd", "#d5e5dd", 0, "no"), "Reliable"),
        ("Degraded", remplissage("#f2c79b", "#f2c79b", 0, "no"), "Degraded"),
        ("Poor", remplissage("#d8693f", "#d8693f", 0, "no"), "Poor: vessels lost"),
        ("Not enough traffic", hachure("#bdbdb8", 45, 1.5, 0.1), "Not enough traffic to judge"),
    ])

    # versions fusionnées pour la fiche (export PDF léger, hachures continues)
    c["trafic_fiche"] = couche("Shipping density", "trafic_classes")
    categorise(c["trafic_fiche"], "classe", [
        (i, remplissage(col, col, 0, "no"), lib) for i, col, lib in zip(
            range(1, 6), rampe, ["< 2", "2 – 10", "10 – 40", "40 – 150", "> 150"])])
    c["lacunes"] = couche("Poor shore AIS reception", "lacunes_reception")
    unique(c["lacunes"], hachure("#6f6c66", 45, 0.9, 0.13))

    c["indice"] = couche("Vigilance index", "indice_vigilance")  # indice nul : hors classes, non dessiné
    gradue(c["indice"], "indice", [
        (0.0001, 15, remplissage("#fbd8c7", "#ffffff", 0.1), "Low (1 – 15)"),
        (15, 30, remplissage("#f2a07a", "#ffffff", 0.1), "Medium (15 – 30)"),
        (30, 100, remplissage("#c24f22", "#ffffff", 0.1), "High (> 30)"),
    ])

    c["infra"] = couche("Submarine cables & pipelines", "infrastructure")
    categorise(c["infra"], "categorie", [
        ("pipeline", ligne("#6f675d", 0.55), "Pipeline"),
        ("câble électrique", ligne("#8a8378", 0.3), "Power cable"),
        ("câble de télécommunication", ligne("#8a8378", 0.3, tirets="2;1"), "Telecom cable"),
        ("câble (usage non précisé)", ligne("#a39d93", 0.25, tirets="0.5;1"), "Cable, use not specified"),
    ])
    c["infra_fiche"] = couche("Cable or pipeline", "infrastructure")
    unique(c["infra_fiche"], ligne("#9a9387", 0.25, transparence=0.8))

    c["eolien"] = couche("Offshore wind farms", "parc_eolien")
    unique(c["eolien"], remplissage("#dde5d9", "#9fb39a", 0.2))
    c["mouillage"] = couche("Anchorages", "mouillage")
    unique(c["mouillage"], remplissage("#dfe9f1", "#7c9cb6", 0.25, "dash", transparence=0.9))

    # limites maritimes entre États, et non le contour des ZEE qui suit la côte îlot par îlot
    c["zee"] = couche("EEZ boundary", "limite_zee")
    unique(c["zee"], ligne("#7f8c96", 0.3, tirets="2.2;1.2"))
    c["mer_terr"] = couche("12 NM territorial sea", "mer_territoriale")
    unique(c["mer_terr"], remplissage("#ffffff", "#a3adb4", 0.18, "dot", style="no"))
    c["etude"] = couche("Study area", "zone_etude")
    unique(c["etude"], remplissage("#ffffff", ENCRE, 0.35, style="no"))

    c["station"] = couche("AIS shore stations", "station_ais")
    unique(c["station"], point("#3d3d3a", 1.8, "triangle", "#ffffff", 0.2))

    # silences inexpliqués : trajet supposé en tirets, début creux, fin pleine
    c["inexpl"] = couche("Unexplained AIS silence", "silence_ais")
    s = ligne("#ffffff", 1.1, transparence=0.9)
    # garder une référence au symbole source : sans elle, Python le détruit avant le clone
    # de sa couche et QGIS plante
    tirets_orange = ligne(ORANGE, 0.55, tirets="1.6;1")
    s.appendSymbolLayer(tirets_orange.symbolLayer(0).clone())
    for expr, plein in (("start_point($geometry)", False), ("end_point($geometry)", True)):
        g = QgsGeometryGeneratorSymbolLayer.create({"geometryModifier": expr, "SymbolType": "Marker"})
        g.setSubSymbol(point(ORANGE if plein else "#ffffff", 2.2, "circle", ORANGE if not plein else "#ffffff",
                             0.45 if not plein else 0.3))
        s.appendSymbolLayer(g)
    regles(c["inexpl"], [(s, "\"categorie\" = 'coupure inexpliquée'", "")])

    # tous les silences, au point de départ, pour l'analyse
    c["silences"] = couche("All AIS silences (start point)", "silence_ais")
    gris = {"position incohérente": "#c4c2bc", "navire de servitude ou d'État": "#c4c2bc",
            "sortie de la zone": "#b3b8bc", "navigation intérieure ou portuaire": "#c4c2bc",
            "arrêt au port ou au mouillage": "#c4c2bc", "réception insuffisante probable": "#5f7d95",
            "escale ou détour côtier possible": "#9aa7b1", "sortie de couverture possible": "#9aa7b1",
            "coupure inexpliquée": ORANGE}
    libelles = {"position incohérente": "Inconsistent position",
                "navire de servitude ou d'État": "Service or state vessel",
                "sortie de la zone": "Left the study area",
                "navigation intérieure ou portuaire": "Inland waterway or harbour",
                "arrêt au port ou au mouillage": "Stopped in port or at anchor",
                "réception insuffisante probable": "Shore reception gap",
                "escale ou détour côtier possible": "Possible port call or coastal detour",
                "sortie de couverture possible": "Possible trip out of coverage",
                "coupure inexpliquée": "Unexplained"}
    classes = []
    for cat, col in gris.items():
        sym = QgsMarkerSymbol()
        sym.deleteSymbolLayer(0)
        g = QgsGeometryGeneratorSymbolLayer.create({"geometryModifier": "start_point($geometry)",
                                                    "SymbolType": "Marker"})
        g.setSubSymbol(point(col, 2.4 if cat == "coupure inexpliquée" else 1.5, "circle", "#ffffff", 0.2))
        ls = QgsLineSymbol()
        ls.deleteSymbolLayer(0)
        ls.appendSymbolLayer(g)
        classes.append((cat, ls, libelles[cat]))
    categorise(c["silences"], "categorie", classes)

    # seuls les navires à trois sauts ou plus : deux émetteurs sous un même MMSI. Lignes fines et
    # pâles, extrémités marquées : on lit les deux lieux sans que les traits envahissent la carte
    c["sauts"] = couche("MMSI shared by two transmitters", "saut_position")
    s = ligne(VIOLET, 0.2, transparence=0.45)
    for expr in ("start_point($geometry)", "end_point($geometry)"):
        g = QgsGeometryGeneratorSymbolLayer.create({"geometryModifier": expr, "SymbolType": "Marker"})
        g.setSubSymbol(point(VIOLET, 1.5, "circle", "#ffffff", 0.25))
        s.appendSymbolLayer(g)
    regles(c["sauts"], [(s, "\"mmsi_partage\"", "")])

    c["stationnement"] = couche("Slow passage over a cable or pipeline", "stationnement_infra")
    c["stationnement"].setRenderer(grappes(point(BLEU, 2.5, "diamond", "#ffffff", 0.3), BLEU))

    c["rencontre"] = couche("Ship-to-ship encounter", "rencontre")
    c["rencontre"].setRenderer(grappes(point(VERT_EAU, 2.6, "circle", "#ffffff", 0.3), VERT_EAU))

    # détections radar Sentinel-1 sans AIS (Global Fishing Watch), hors structures fixes probables :
    # petit carré creux à l'encre, distinct des quatre signaux par sa forme et dessiné sous eux ;
    # couche absente tant que 08_sar_gfw.py n'a pas tourné
    radar = QgsVectorLayer(f"{CARTO}|layername=detection_radar", "Radar detection, no AIS", "ogr")
    if radar.isValid():
        regles(radar, [(point("#ffffff", 1.5, "square", ENCRE_2, 0.3),
                        "NOT \"apparie\" AND \"categorie\" <> 'structure fixe probable (parc éolien)'", "")])
        c["radar"] = radar

    # plusieurs semaines (10_semaines.py) : angles morts ponctuels ou chroniques, foyers de silences
    # inexpliqués revenus au moins deux semaines ; couches absentes tant que l'étape n'a pas tourné
    recurrence = QgsVectorLayer(f"{CARTO}|layername=recurrence_couverture", "Blind spots over four weeks", "ogr")
    if recurrence.isValid():
        categorise(recurrence, "statut", [
            ("Chronic", remplissage("#a63c14", "#a63c14", 0, "no"), "Chronic: poor 3 or 4 weeks out of 4"),
            ("Recurring", remplissage("#e0784a", "#e0784a", 0, "no"), "Recurring: poor 2 weeks"),
            ("One-off", remplissage("#f6cdb3", "#f6cdb3", 0, "no"), "One-off: poor a single week"),
            ("Never poor", remplissage("#dfe8e2", "#dfe8e2", 0, "no"), "Never poor"),
        ])
        c["recurrence"] = recurrence
        foyers = QgsVectorLayer(f"{CARTO}|layername=foyer_inexpliquees", "Recurring unexplained silences", "ogr")
        regles(foyers, [(remplissage(ORANGE, ORANGE, 0.5, transparence=0.35), "\"nb_semaines\" >= 2", "")])
        c["foyers"] = foyers

    c["traces"] = couche("Vessel tracks", "trace", fichier=TRACES)
    familles = [("Cargo", "#2a78d6"), ("Tanker", "#eb6834"), ("Passenger", "#1baf7a"),
                ("Fishing", "#eda100"), ("Service & authorities", "#e87ba4"),
                ("Other / unknown", "#008300")]
    categorise(c["traces"], "famille", [(f, ligne(col, 0.18, transparence=0.5), f) for f, col in familles])

    c["lieux"] = couche("Places", "lieu")
    etiquettes_lieux(c["lieux"])

    # zones des fiches : voile hors de la zone en cours et contour de la zone, seulement en atlas
    filtre_atlas = "\"zone_id\" = attribute(@atlas_feature, 'zone_id')"
    c["voile"] = couche("Zone sheet mask", "zone_fiche")
    racine = QgsRuleBasedRenderer.Rule(None)
    racine.appendChild(QgsRuleBasedRenderer.Rule(remplissage("#ffffff", "#ffffff", 0, "no",
                                                             transparence=0.55), filterExp=filtre_atlas))
    c["voile"].setRenderer(QgsInvertedPolygonRenderer(QgsRuleBasedRenderer(racine)))
    c["contour"] = couche("Zone sheet outline", "zone_contour")
    regles(c["contour"], [(ligne("#2b2b2a", 0.45), filtre_atlas, "")])
    c["perso"] = zones_perso()
    c["zones"] = couche("Zone sheets (atlas)", "zone_fiche")
    unique(c["zones"], remplissage("#ffffff", ENCRE_3, 0.3, "dash", style="no"))
    return c


ZONES_PERSO = RACINE / "donnees" / "produites" / "zones_perso.gpkg"
EXEMPLES = [  # nom, ouest, sud, est, nord (WGS84)
    ("Arkona Basin", 12.9, 54.75, 14.3, 55.3),
    ("Skagen roads", 10.35, 57.55, 10.95, 57.85),
    ("Fehmarn Belt", 10.95, 54.4, 11.65, 54.7),
]


def zones_perso():
    """Couche modifiable où l'on dessine ses zones avant de lancer l'outil « Produire une fiche de
    zone ». Créée avec trois exemples si elle n'existe pas, jamais écrasée ensuite : elle contient
    le travail des utilisateurs."""
    if not ZONES_PERSO.exists():
        mem = QgsVectorLayer("MultiPolygon?crs=EPSG:4326&field=nom:string(80)", "zone_perso", "memory")
        for nom, o, s, e, n in EXEMPLES:
            f = QgsFeature(mem.fields())
            f["nom"] = nom
            g = QgsGeometry.fromRect(QgsRectangle(o, s, e, n)).densifyByDistance(0.05)
            g.convertToMultiType()
            f.setGeometry(g)
            mem.dataProvider().addFeature(f)
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.layerName = "zone_perso"
        QgsVectorFileWriter.writeAsVectorFormatV3(mem, str(ZONES_PERSO), QgsCoordinateTransformContext(), options)
    lyr = couche("My areas of interest", "zone_perso", fichier=ZONES_PERSO)
    unique(lyr, remplissage("235,104,52,20", ORANGE, 0.5, "dash"))
    p = QgsPalLayerSettings()
    p.fieldName = "nom"
    p.setFormat(tampon(format_texte(7.5, ORANGE, gras=True), "#ffffff", 0.7, 0.9))
    p.placement = QgsPalLayerSettings.Horizontal
    lyr.setLabeling(QgsVectorLayerSimpleLabeling(p))
    lyr.setLabelsEnabled(True)
    return lyr


def grappes(symbole, couleur):
    """Regroupe les points superposés (45 rencontres au même mouillage) avec leur nombre."""
    r = QgsPointClusterRenderer()
    r.setEmbeddedRenderer(QgsSingleSymbolRenderer(symbole))
    r.setTolerance(3)
    r.setToleranceUnit(QgsUnitTypes.RenderMillimeters)
    grappe = point(couleur, 4.2, "circle", "#ffffff", 0.4)
    # le nombre de points de la grappe, écrit par-dessus avec un symbole de police
    n = QgsFontMarkerSymbolLayer(POLICE, "0", 2.3, QColor("#ffffff"))
    n.setDataDefinedProperty(QgsFontMarkerSymbolLayer.PropertyCharacter,
                             QgsProperty.fromExpression("@cluster_size"))
    n.setFontStyle("Bold")
    grappe.appendSymbolLayer(n)
    r.setClusterSymbol(grappe)
    return r


def etiquettes_lieux(lyr):
    # une entité que le style ne dessine pas n'est pas étiquetée : mers, pays et îles reçoivent
    # un symbole invisible
    invisible = QgsMarkerSymbol.createSimple({"name": "circle", "size": "0.01", "color": "0,0,0,0",
                                              "outline_style": "no"})
    regles(lyr, [(point(ENCRE_2, 1.1, "circle", "#ffffff", 0.2), "\"nature\" = 'ville'", "City"),
                 (invisible, "\"nature\" <> 'ville'", "Sea area or country")])

    def regle(filtre, fmt, decalage=False):
        p = QgsPalLayerSettings()
        p.fieldName = "nom"
        p.setFormat(fmt)
        if decalage:
            p.placement = QgsPalLayerSettings.OrderedPositionsAroundPoint
            p.dist = 0.8
        else:
            p.placement = QgsPalLayerSettings.OverPoint
        p.priority = 8
        return QgsRuleBasedLabeling.Rule(p, filterExp=filtre)

    lab = QgsRuleBasedLabeling.Rule(None)
    lab.appendChild(regle("\"nature\" = 'mer'", tampon(format_texte(7.5, "#6c8495", italique=True,
                                                                    espacement=0.6), MER, 0.5)))
    lab.appendChild(regle("\"nature\" = 'pays'", format_texte(8, "#a39b8e", espacement=2.4)))
    lab.appendChild(regle("\"nature\" = 'ile'", format_texte(7, "#7a7266", italique=True)))
    lab.appendChild(regle("\"nature\" = 'ville'", tampon(format_texte(6.5, "#3d3d3a"), "#ffffff", 0.5, 0.7),
                          decalage=True))
    lyr.setLabeling(QgsRuleBasedLabeling(lab))
    lyr.setLabelsEnabled(True)


# --- Arbre des couches, thèmes, signets ---------------------------------------------------
GROUPES = [
    ("Context", ["lieux", "station"]),
    ("Zone sheets", ["perso", "contour", "voile", "zones"]),
    ("Signals", ["inexpl", "sauts", "stationnement", "rencontre", "radar"]),
    ("AIS silences, all categories", ["silences"]),
    ("Indicators", ["indice", "lacunes", "couverture", "trafic_fiche", "trafic"]),
    ("Four weeks", ["foyers", "recurrence"]),
    ("Infrastructure", ["infra_fiche", "infra", "eolien", "mouillage"]),
    ("Boundaries", ["etude", "zee", "mer_terr"]),
    ("Tracks", ["traces"]),
    ("Base", ["terre"]),
]

THEMES = {
    "Zone sheet – main map": ["lieux", "contour", "voile", "inexpl", "sauts", "stationnement", "rencontre", "radar",
                              "lacunes", "trafic_fiche", "infra_fiche", "zee", "terre"],
    "Shore AIS coverage": ["lieux", "station", "couverture", "zee", "etude", "terre"],
    "Four weeks: chronic blind spots": ["lieux", "foyers", "recurrence", "zee", "etude", "terre"],
    "Vigilance index": ["lieux", "indice", "zee", "etude", "terre"],
    "Infrastructure & loitering": ["lieux", "stationnement", "infra", "eolien", "mouillage", "zee", "terre"],
    "All AIS silences": ["lieux", "silences", "lacunes", "zee", "etude", "terre"],
    "Vessel tracks": ["lieux", "traces", "zee", "etude", "terre"],
}

SIGNETS = [  # nom, ouest, sud, est, nord (WGS84)
    ("Skagen roads (encounters)", 10.2, 57.45, 11.1, 57.9),
    ("Arkona Basin", 12.6, 54.6, 14.3, 55.4),
    ("Kiel Canal entrance", 9.8, 54.25, 10.4, 54.5),
    ("Fehmarn Belt", 10.9, 54.35, 11.7, 54.75),
    ("Øresund", 12.4, 55.5, 13.0, 56.15),
    ("Bornholm", 14.5, 54.9, 15.4, 55.4),
    ("Pomeranian Bay (coverage edge)", 13.5, 53.9, 14.7, 54.6),
]


def arbre(projet, c):
    racine = projet.layerTreeRoot()
    for groupe, cles in GROUPES:
        if not any(k in c for k in cles):   # groupe d'une étape facultative qui n'a pas tourné
            continue
        g = racine.addGroup(groupe)
        for k in cles:
            if k in c:  # la couche radar n'existe qu'après 08_sar_gfw.py
                projet.addMapLayer(c[k], False)
                g.addLayer(c[k])
    return racine


def themes(projet, racine, c):
    modele = QgsLayerTreeModel(racine)
    collection = projet.mapThemeCollection()
    for nom, cles in THEMES.items():
        visibles = {c[k].id() for k in cles if k in c}
        for n in racine.findLayers():
            n.setItemVisibilityChecked(n.layerId() in visibles)
        for g in racine.findGroups():
            g.setItemVisibilityChecked(True)
        collection.insert(nom, QgsMapThemeCollection.createThemeFromCurrentState(racine, modele))
    # état affiché à l'ouverture : la carte de la fiche, plus les zones à dessiner
    visibles = {c[k].id() for k in THEMES["Zone sheet – main map"] + ["perso"] if k in c}
    for n in racine.findLayers():
        n.setItemVisibilityChecked(n.layerId() in visibles)
    for g in racine.findGroups():
        g.setExpanded(g.name() in ("Zone sheets", "Signals", "Indicators"))


def transformation(projet):
    """Fixe dans le projet la transformation WGS84 -> ETRS89-LAEA. Sans elle, un QGIS réglé pour
    « demander la transformation » ouvre une fenêtre modale par couche au chargement du projet :
    gênant pour un utilisateur, et cause de blocages quand QGIS est piloté à distance."""
    wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
    disponibles = [op for op in QgsDatumTransform.operations(wgs84, CRS_CARTE) if op.isAvailable]
    if not disponibles:
        return None
    retenue = disponibles[0]  # QGIS les classe par préférence : la plus précise disponible
    contexte = projet.transformContext()
    contexte.addCoordinateOperation(wgs84, CRS_CARTE, retenue.proj, True)
    projet.setTransformContext(contexte)
    return retenue.name


def signets(projet):
    wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
    vers = QgsCoordinateTransform(wgs84, CRS_CARTE, projet)
    gestion = projet.bookmarkManager()
    gestion.clear()
    for nom, o, s, e, n in SIGNETS:
        b = QgsBookmark()
        b.setName(nom)
        b.setGroup("What AIS doesn't show")
        b.setExtent(QgsReferencedRectangle(vers.transformBoundingBox(QgsRectangle(o, s, e, n)), CRS_CARTE))
        gestion.addBookmark(b)


# --- Mise en page « Zone sheet » ----------------------------------------------------------
def texte(mise, contenu, x, y, l, h, fmt, aligne=Qt.AlignLeft, valigne=Qt.AlignTop, html=False):
    t = QgsLayoutItemLabel(mise)
    t.setText(contenu)
    t.setTextFormat(fmt)
    t.setHAlign(aligne)
    t.setVAlign(valigne)
    t.setMode(QgsLayoutItemLabel.ModeHtml if html else QgsLayoutItemLabel.ModeFont)
    t.attemptMove(QgsLayoutPoint(x, y))
    t.attemptResize(QgsLayoutSize(l, h))
    mise.addLayoutItem(t)
    return t


def rectangle(mise, x, y, l, h, couleur, contour=None):
    r = QgsLayoutItemShape(mise)
    r.setShapeType(QgsLayoutItemShape.Rectangle)
    r.setSymbol(remplissage(couleur, contour or couleur, 0.2 if contour else 0, "solid" if contour else "no"))
    r.attemptMove(QgsLayoutPoint(x, y))
    r.attemptResize(QgsLayoutSize(l, h))
    mise.addLayoutItem(r)
    return r


def nombre(champ):
    return f"[% format_number(\"{champ}\", 0, 'en') %]"


def carroyage(carte):
    """Méridiens et parallèles tous les degrés, latitudes à gauche et longitudes en bas."""
    grille = QgsLayoutItemMapGrid("Graticule", carte)
    carte.grids().addGrid(grille)
    grille.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
    grille.setIntervalX(1)
    grille.setIntervalY(1)
    grille.setStyle(QgsLayoutItemMapGrid.Solid)
    grille.setGridLineColor(QColor("#c9d2d8"))
    grille.setGridLineWidth(0.1)
    grille.setAnnotationEnabled(True)
    grille.setAnnotationFormat(QgsLayoutItemMapGrid.DecimalWithSuffix)
    grille.setAnnotationPrecision(0)
    grille.setAnnotationTextFormat(format_texte(5.5, ENCRE_3))
    grille.setAnnotationFrameDistance(1.0)
    for bord in (QgsLayoutItemMapGrid.Left, QgsLayoutItemMapGrid.Right,
                 QgsLayoutItemMapGrid.Top, QgsLayoutItemMapGrid.Bottom):
        grille.setAnnotationPosition(QgsLayoutItemMapGrid.InsideMapFrame, bord)
        grille.setAnnotationDirection(QgsLayoutItemMapGrid.Horizontal, bord)
        grille.setAnnotationDisplay(QgsLayoutItemMapGrid.HideAll, bord)
    grille.setAnnotationDisplay(QgsLayoutItemMapGrid.LatitudeOnly, QgsLayoutItemMapGrid.Left)
    grille.setAnnotationDisplay(QgsLayoutItemMapGrid.LongitudeOnly, QgsLayoutItemMapGrid.Bottom)
    return grille


def carte_simple(mise, projet, c, theme, x, y, l, h):
    """Carte de l'aire d'étude, figée sur un thème, avec carroyage et échelle."""
    carte = QgsLayoutItemMap(mise)
    carte.attemptMove(QgsLayoutPoint(x, y))
    carte.attemptResize(QgsLayoutSize(l, h))
    carte.setCrs(CRS_CARTE)
    carte.setBackgroundColor(QColor(MER))
    carte.setFrameEnabled(True)
    carte.setFrameStrokeColor(QColor(ENCRE_3))
    carte.setFrameStrokeWidth(QgsLayoutMeasurement(0.2))
    carte.setFollowVisibilityPreset(True)
    carte.setFollowVisibilityPresetName(theme)
    carte.setId(theme)
    mise.addLayoutItem(carte)
    etendue = QgsCoordinateTransform(c["etude"].crs(), CRS_CARTE, projet).transformBoundingBox(
        c["etude"].extent())
    etendue.scale(1.03)
    carte.zoomToExtent(etendue)
    carroyage(carte)
    echelle = QgsLayoutItemScaleBar(mise)
    echelle.setStyle("Line Ticks Up")
    echelle.setLinkedMap(carte)
    echelle.setUnits(QgsUnitTypes.DistanceNauticalMiles)
    echelle.setUnitLabel("NM")
    echelle.setUnitsPerSegment(25)
    echelle.setNumberOfSegments(2)
    echelle.setNumberOfSegmentsLeft(0)
    echelle.setTextFormat(format_texte(6, ENCRE_2))
    echelle.setHeight(1.6)
    echelle.attemptMove(QgsLayoutPoint(x, y + h + 1.5))
    mise.addLayoutItem(echelle)
    return carte


def legende_simple(mise, carte, couches_legende, x, y, colonnes=1):
    legende = QgsLayoutItemLegend(mise)
    legende.setLinkedMap(carte)
    legende.setAutoUpdateModel(False)
    legende.setTitle("")
    racine = legende.model().rootGroup()
    racine.removeAllChildren()
    for lyr in couches_legende:
        racine.addLayer(lyr)
    legende.setColumnCount(colonnes)
    legende.setSplitLayer(True)
    legende.setSymbolWidth(5.5)
    legende.setSymbolHeight(3.2)
    legende.setColumnSpace(4)
    legende.rstyle(QgsLegendStyle.SymbolLabel).setTextFormat(format_texte(6.4, ENCRE_2))
    legende.rstyle(QgsLegendStyle.Group).setTextFormat(format_texte(6.6, ENCRE, gras=True))
    legende.rstyle(QgsLegendStyle.Subgroup).setTextFormat(format_texte(6.6, ENCRE, gras=True))
    # légende serrée : 1 mm entre les symboles, 1,5 mm sous le titre de couche
    legende.rstyle(QgsLegendStyle.Symbol).setMargin(QgsLegendStyle.Top, 1.0)
    legende.rstyle(QgsLegendStyle.Subgroup).setMargin(QgsLegendStyle.Bottom, 1.5)
    legende.rstyle(QgsLegendStyle.Group).setMargin(QgsLegendStyle.Top, 0)
    legende.setBackgroundEnabled(False)
    legende.attemptMove(QgsLayoutPoint(x, y))
    mise.addLayoutItem(legende)
    legende.adjustBoxSize()
    legende.refresh()
    return legende


def vues_analyse(projet, c):
    """A4 paysage : la couverture mesurée et l'indice de vigilance, côte à côte."""
    gestion = projet.layoutManager()
    ancienne = gestion.layoutByName("Coverage & vigilance")
    if ancienne:
        gestion.removeLayout(ancienne)
    mise = QgsPrintLayout(projet)
    mise.initializeDefaults()  # A4 paysage
    mise.setName("Coverage & vigilance")
    gestion.addLayout(mise)

    texte(mise, "ANALYST VIEW  ·  SHORE-BASED AIS  ·  OPEN DATA", 12, 9, 273, 5,
          format_texte(6.8, ORANGE, gras=True, espacement=1.2))
    texte(mise, "How well the shore network sees, and where to look first", 12, 13, 273, 9,
          format_texte(17, ENCRE, gras=True))
    texte(mise, f"Danish Straits & Bornholm Basin  ·  {PERIODE}", 12, 22, 273, 6,
          format_texte(10, ENCRE_2))
    rectangle(mise, 12, 28.5, 273, 0.35, ENCRE)

    gauche = carte_simple(mise, projet, c, "Shore AIS coverage", 12, 32, 133, 120)
    droite = carte_simple(mise, projet, c, "Vigilance index", 152, 32, 133, 120)
    for x, carte in ((12, gauche), (152, droite)):
        nord = QgsLayoutItemPicture(mise)
        nord.setPicturePath(":/images/north_arrows/layout_default_north_arrow.svg")
        nord.setLinkedMap(carte)
        nord.setNorthMode(QgsLayoutItemPicture.TrueNorth)
        nord.attemptMove(QgsLayoutPoint(x + 125, 35))
        nord.attemptResize(QgsLayoutSize(5, 7))
        mise.addLayoutItem(nord)

    texte(mise, "SHORE AIS COVERAGE, MEASURED FROM THE TRAFFIC", 12, 163, 133, 4,
          format_texte(6.8, ENCRE_2, gras=True, espacement=1))
    texte(mise,
          "Each H3 cell (≈ 36 km²) is rated from the vessels that crossed it during the week: share of "
          "1-minute intervals actually received, and share of expected vessels lost on the way. Counting lost "
          "vessels corrects a selection bias: a vessel that is never received leaves no position behind. "
          "Triangles: AIS base stations heard by the network.",
          12, 168, 80, 24, format_texte(6.4, ENCRE_2))
    legende_simple(mise, gauche, [c["couverture"]], 96, 167)

    texte(mise, "VIGILANCE INDEX: WHERE TO LOOK FIRST", 152, 163, 133, 4,
          format_texte(6.8, ENCRE_2, gras=True, espacement=1))
    texte(mise,
          "Mean percentile rank, per H3 cell (≈ 250 km²), of four signals measured as a share of the vessels "
          "present: unexplained silences, shared MMSI, slow passages over cables or pipelines, encounters at "
          "sea. Cells with fewer than 10 vessels in the week are not rated. A triage tool, not evidence.",
          152, 168, 80, 24, format_texte(6.4, ENCRE_2))
    legende_simple(mise, droite, [c["indice"]], 236, 167)

    rectangle(mise, 12, 197, 273, 0.25, "#c9c6bf")
    texte(mise,
          "Sources: Danish Maritime Authority (AIS) · Flanders Marine Institute, Marine Regions (EEZ, CC BY 4.0) · "
          "Eurostat GISCO (© EuroGeographics) · OpenStreetMap contributors (ODbL). "
          "Projection ETRS89-LAEA (EPSG:3035).", 12, 198.5, 200, 5, format_texte(5.6, ENCRE_3))
    texte(mise, "Independent portfolio project  ·  Jaurès Daa-Hingbanon, GIS analyst", 185, 198.5, 100, 5,
          format_texte(5.8, ENCRE_2, gras=True), aligne=Qt.AlignRight)
    return mise


def fiche(projet, c):
    gestion = projet.layoutManager()
    ancienne = gestion.layoutByName("Zone sheet")
    if ancienne:
        gestion.removeLayout(ancienne)
    mise = QgsPrintLayout(projet)
    mise.initializeDefaults()  # une page A4 paysage, que l'on passe en portrait
    mise.setName("Zone sheet")
    mise.pageCollection().page(0).setPageSize("A4", QgsLayoutItemPage.Portrait)
    gestion.addLayout(mise)

    # en-tête
    texte(mise, "ZONE SHEET  ·  SHORE-BASED AIS  ·  OPEN DATA", 12, 9, 186, 5,
          format_texte(6.8, ORANGE, gras=True, espacement=1.2))
    texte(mise, "What AIS doesn't show", 12, 13, 186, 11, format_texte(22, ENCRE, gras=True))
    texte(mise, f"[% \"nom\" %]  ·  [% \"sous_titre\" %]  ·  {PERIODE}", 12, 24, 186, 6,
          format_texte(10.5, ENCRE_2))
    rectangle(mise, 12, 31, 186, 0.35, ENCRE)

    # carte principale, pilotée par l'atlas
    carte = QgsLayoutItemMap(mise)
    carte.attemptMove(QgsLayoutPoint(12, 33))
    carte.attemptResize(QgsLayoutSize(186, 148))
    carte.setCrs(CRS_CARTE)
    carte.setBackgroundColor(QColor(MER))
    carte.setFrameEnabled(True)
    carte.setFrameStrokeColor(QColor(ENCRE_3))
    carte.setFrameStrokeWidth(QgsLayoutMeasurement(0.2))
    carte.setFollowVisibilityPreset(True)
    carte.setFollowVisibilityPresetName("Zone sheet – main map")
    carte.setAtlasDriven(True)
    carte.setAtlasScalingMode(QgsLayoutItemMap.Auto)
    carte.setAtlasMargin(0.04)
    carte.setId("main map")
    mise.addLayoutItem(carte)
    carte.zoomToExtent(QgsCoordinateTransform(c["etude"].crs(), CRS_CARTE, projet)
                       .transformBoundingBox(c["etude"].extent()))

    carroyage(carte)

    nord = QgsLayoutItemPicture(mise)
    nord.setPicturePath(":/images/north_arrows/layout_default_north_arrow.svg")
    nord.setLinkedMap(carte)
    nord.setNorthMode(QgsLayoutItemPicture.TrueNorth)
    nord.attemptMove(QgsLayoutPoint(188, 36))
    nord.attemptResize(QgsLayoutSize(6.5, 9))
    mise.addLayoutItem(nord)

    echelle = QgsLayoutItemScaleBar(mise)
    echelle.setStyle("Line Ticks Up")
    echelle.setLinkedMap(carte)
    echelle.setUnits(QgsUnitTypes.DistanceNauticalMiles)
    echelle.setUnitLabel("NM")
    echelle.setSegmentSizeMode(QgsScaleBarSettings.SegmentSizeFitWidth)
    echelle.setMinimumBarWidth(22)
    echelle.setMaximumBarWidth(36)
    echelle.setNumberOfSegments(2)
    echelle.setNumberOfSegmentsLeft(0)
    echelle.setTextFormat(format_texte(6, ENCRE_2))
    echelle.setHeight(1.6)
    echelle.attemptMove(QgsLayoutPoint(12, 182.5))
    mise.addLayoutItem(echelle)
    texte(mise, "Projection ETRS89-LAEA (EPSG:3035). Grey shading: shipping density.",
          60, 183.5, 138, 4, format_texte(5.8, ENCRE_3), aligne=Qt.AlignRight)

    # chiffres clés
    texte(mise, "KEY FIGURES", 12, 191, 100, 4, format_texte(6.8, ENCRE_2, gras=True, espacement=1))
    tuiles = [
        (nombre("nb_navires"), "class A vessels tracked", "#c9c6bf"),
        (nombre("nb_silences"), "AIS silences of 2 hours or more", "#c9c6bf"),
        (nombre("nb_reception"), "silences explained by\nshore reception gaps", "#c9c6bf"),
        (nombre("nb_inexpliquees"), "unexplained: silent transits\nin well-covered waters", ORANGE),
        ("[% format_number(\"part_couverte\" * 100, 0, 'en') %] %",
         "of underway traffic in reliably\ncovered waters", "#c9c6bf"),
        (nombre("nav_mmsi_partage"), "vessels whose MMSI is shared\nby two transmitters", VIOLET),
        (nombre("nb_stationnements"), "slow passages over a cable\nor pipeline (30 min or more)", BLEU),
        (nombre("nb_rencontres"), "ship-to-ship encounters\n(2 hours or more)", VERT_EAU),
    ]
    if "radar" in c:
        tuiles.insert(5, (nombre("nb_radar_sans_ais"),
                          "radar detections without AIS\n(Sentinel-1, wind farms excluded)", ENCRE))
        tuiles.append(("[% if(\"part_radar_recus\" IS NULL, '–', "
                       "format_number(\"part_radar_recus\" * 100, 0, 'en') || ' %') %]",
                       "of radar-seen vessels received\nby the shore AIS network", "#c9c6bf"))
    # 4 lignes de 14,5 mm, ou 5 de 12 mm quand le radar ajoute ses deux chiffres
    lignes_par_colonne = (len(tuiles) + 1) // 2
    pas = 12 if lignes_par_colonne > 4 else 14.5
    for i, (valeur, libelle, couleur) in enumerate(tuiles):
        x = 12 if i < lignes_par_colonne else 63
        y = 196.5 + (i % lignes_par_colonne) * pas
        rectangle(mise, x, y + 0.6, 1.1, pas - 2, couleur)
        texte(mise, valeur, x + 3, y - 0.6, 45, 6.5,
              format_texte(14 if pas < 14 else 15, ORANGE if couleur == ORANGE else ENCRE, gras=True))
        texte(mise, libelle, x + 3, y + 5.2, 46, 6.5, format_texte(6.0, ENCRE_2))

    # graphique des silences de la zone (SVG préparé par 06_export_gpkg.py)
    texte(mise, "WHERE THE AIS SILENCES COME FROM", 118, 191, 80, 4,
          format_texte(6.8, ENCRE_2, gras=True, espacement=1))
    graphe = QgsLayoutItemPicture(mise)
    graphe.attemptMove(QgsLayoutPoint(117, 195.5))
    graphe.attemptResize(QgsLayoutSize(81, 36))
    graphe.setResizeMode(QgsLayoutItemPicture.Zoom)
    graphe.setId("chart")
    # chemin relatif au projet pour les zones prédéfinies, absolu pour celles de l'outil fiche_zone
    graphe.dataDefinedProperties().setProperty(
        QgsLayoutObject.PictureSource, QgsProperty.fromExpression(
            "if(regexp_match(\"graphique\", '^([A-Za-z]:|/|\\\\\\\\)'), \"graphique\", "
            "@project_folder || '/' || \"graphique\")"))
    mise.addLayoutItem(graphe)

    # légende de la carte principale
    legende = QgsLayoutItemLegend(mise)
    legende.setLinkedMap(carte)
    legende.setAutoUpdateModel(False)
    legende.setTitle("")
    racine = legende.model().rootGroup()
    racine.removeAllChildren()
    for k in ("inexpl", "sauts", "stationnement", "rencontre", "radar", "infra_fiche", "lacunes", "zee"):
        if k in c:
            racine.addLayer(c[k])
    legende.setColumnCount(2)
    legende.setSplitLayer(True)
    legende.setSymbolWidth(5.5)
    legende.setSymbolHeight(3.2)
    legende.setColumnSpace(3)
    for style in (QgsLegendStyle.SymbolLabel, QgsLegendStyle.Subgroup, QgsLegendStyle.Group):
        legende.rstyle(style).setTextFormat(format_texte(6.2, ENCRE_2))
    legende.rstyle(QgsLegendStyle.Symbol).setMargin(QgsLegendStyle.Top, 1.2)
    legende.setBackgroundEnabled(False)
    legende.attemptMove(QgsLayoutPoint(117, 234))
    mise.addLayoutItem(legende)
    legende.adjustBoxSize()
    legende.refresh()

    # pied de page
    rectangle(mise, 12, 259.5, 186, 0.25, "#c9c6bf")
    texte(mise,
          "<b>About these figures.</b> One week of positions broadcast by commercial vessels (AIS class A) and "
          "received by Denmark's coastal stations. A silence is a gap of 2 hours or more between two positions of "
          "the same vessel; it is called unexplained only when no ordinary cause fits (port stay, poor coastal "
          "reception, leaving the area…). These are signals worth a closer look, not proof of wrongdoing, and no "
          "vessel is named. Full method: github.com/jauresmas/what-ais-doesnt-show",
          12, 261, 186, 13, format_texte(6.1, ENCRE_2), html=True)
    texte(mise,
          "Sources: Danish Maritime Authority (AIS) · Flanders Marine Institute, Marine Regions (EEZ, CC BY 4.0) · "
          "Eurostat GISCO (© EuroGeographics) · EMODnet Human Activities and BSH (CC BY 4.0) · TeleGeography "
          "(CC BY-NC-SA 3.0) · © OpenStreetMap contributors (ODbL) · Radar detections: Powered by Global "
          "Fishing Watch (CC BY-NC 4.0).",
          12, 274.5, 186, 8, format_texte(5.6, ENCRE_3))
    texte(mise, "Independent portfolio project  ·  Jaurès Daa-Hingbanon, GIS analyst", 12, 284, 120, 4,
          format_texte(5.8, ENCRE_2, gras=True))
    texte(mise, "Sheet [% @atlas_featurenumber %] / [% @atlas_totalfeatures %]", 150, 284, 48, 4,
          format_texte(5.8, ENCRE_2), aligne=Qt.AlignRight)

    atlas = mise.atlas()
    atlas.setCoverageLayer(c["zones"])
    atlas.setEnabled(True)
    atlas.setHideCoverage(False)
    atlas.setSortFeatures(True)
    atlas.setSortExpression("\"ordre\"")
    atlas.setPageNameExpression("\"nom\"")
    atlas.setFilenameExpression("'zone-sheet_' || \"zone_id\"")
    return mise


def exporter(mise):
    SORTIES.mkdir(parents=True, exist_ok=True)
    atlas = mise.atlas()
    pdf = QgsLayoutExporter.PdfExportSettings()
    pdf.dpi = 300
    pdf.rasterizeWholeImage = False
    resultat, erreur = QgsLayoutExporter.exportToPdf(atlas, str(SORTIES / "zone-sheets.pdf"), pdf)
    if resultat != QgsLayoutExporter.Success:
        raise RuntimeError(f"Export PDF : {erreur}")
    image = QgsLayoutExporter.ImageExportSettings()
    image.dpi = 150
    exp = QgsLayoutExporter(mise)
    atlas.beginRender()
    atlas.first()
    fichiers = []
    while True:
        nom = SORTIES / f"{atlas.currentFilename()}.png"
        exp.exportToImage(str(nom), image)
        fichiers.append(nom.name)
        if not atlas.next():
            break
    atlas.endRender()
    return fichiers


def exporter_vue(mise, nom):
    pdf = QgsLayoutExporter.PdfExportSettings()
    pdf.dpi = 300
    exp = QgsLayoutExporter(mise)
    exp.exportToPdf(str(SORTIES / f"{nom}.pdf"), pdf)
    image = QgsLayoutExporter.ImageExportSettings()
    image.dpi = 150
    exp.exportToImage(str(SORTIES / f"{nom}.png"), image)
    return [f"{nom}.png"]


# --- Assemblage ---------------------------------------------------------------------------
def construire(exporter_fiches=True):
    projet = QgsProject.instance()
    projet.clear()
    FICHIER_PROJET.parent.mkdir(parents=True, exist_ok=True)
    projet.setFileName(str(FICHIER_PROJET))
    projet.setTitle("What AIS doesn't show — Danish Straits & Bornholm Basin, 13–19 October 2026")
    projet.setCrs(CRS_CARTE)
    projet.setBackgroundColor(QColor(MER))
    projet.writeEntry("Paths", "/Absolute", False)
    print("Transformation WGS84 -> ETRS89-LAEA :", transformation(projet))
    c = couches()
    etendue = QgsCoordinateTransform(c["etude"].crs(), CRS_CARTE, projet).transformBoundingBox(
        c["etude"].extent())
    etendue.scale(1.05)
    projet.viewSettings().setDefaultViewExtent(QgsReferencedRectangle(etendue, CRS_CARTE))
    racine = arbre(projet, c)
    themes(projet, racine, c)
    signets(projet)
    mise = fiche(projet, c)
    vue = vues_analyse(projet, c)
    projet.write()
    fichiers = []
    if exporter_fiches:
        fichiers = exporter(mise) + exporter_vue(vue, "coverage-and-vigilance")
    try:
        from qgis.utils import iface
        if iface:
            iface.mapCanvas().setExtent(QgsCoordinateTransform(c["etude"].crs(), CRS_CARTE, projet)
                                        .transformBoundingBox(c["etude"].extent()))
            iface.mapCanvas().refresh()
    except ImportError:
        pass
    return fichiers


if __name__ == "__main__" or "RACINE_PROJET" in globals():
    if not CRS_CARTE.isValid():
        raise RuntimeError("EPSG:3035 invalide : base PROJ non chargée")
    print("Fiches exportées :", construire(globals().get("EXPORTER_FICHES", True)))
    if AUTONOME:
        _APP.exitQgis()
