"""Outil de traitement QGIS « Produire une fiche de zone ».

Pour n'importe quel polygone (dessiné à la main, importé, ou une sélection d'entités), l'outil
calcule les chiffres clés de la zone à partir des couches du projet, dessine le graphique des
silences AIS et exporte la fiche A4 en PDF (et en PNG), avec la mise en page « Zone sheet ».

Aucune base de données n'est nécessaire : tout est lu dans les GeoPackages du projet
(donnees/produites/carto.gpkg, et traces.gpkg pour le nombre de navires).

Installation : Traitement > Boîte à outils > Scripts > « Ajouter un script à la boîte à outils »,
ou ajouter le dossier qgis/outils aux dossiers de scripts (Options > Traitement > Scripts).
Mode d'emploi : docs/guide_fiche_zone.md.
"""
import re
import sys
import tempfile
from pathlib import Path

from qgis.core import (
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsFeature, QgsFeatureRequest, QgsFillSymbol,
    QgsGeometry, QgsInvertedPolygonRenderer, QgsLayoutExporter, QgsLineSymbol, QgsProcessing,
    QgsProcessingAlgorithm, QgsProcessingException, QgsProcessingOutputNumber,
    QgsProcessingParameterBoolean, QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFileDestination, QgsProcessingParameterString, QgsProject,
    QgsSingleSymbolRenderer, QgsVectorLayer,
)

MISE_EN_PAGE = "Zone sheet"
THEME = "Zone sheet – main map"
COUCHE_ZONES = "My areas of interest"
WGS84 = QgsCoordinateReferenceSystem("EPSG:4326")

# couches d'analyse du projet : des résultats, pas des zones. Les prendre pour zone donne une fiche
# absurde (par exemple les eaux mal couvertes, avec 0 % de trafic bien couvert)
TABLES_INTERDITES = {"lacunes_reception", "couverture", "trafic", "trafic_classes", "indice_vigilance",
                     "terre", "zone_contour"}

CHAMPS = [  # champs lus par la mise en page « Zone sheet »
    ("zone_id", "string"), ("nom", "string"), ("sous_titre", "string"), ("ordre", "integer"),
    ("nb_navires", "integer"), ("nb_silences", "integer"), ("nb_reception", "integer"),
    ("nb_inexpliquees", "integer"), ("nav_inexpliquees", "integer"), ("nav_mmsi_partage", "integer"),
    ("nb_stationnements", "integer"), ("nav_stationnements", "integer"), ("nb_rencontres", "integer"),
    ("part_couverte", "double"), ("graphique", "string"),
]


def couche_projet(projet, table, obligatoire=True):
    """Couche du projet qui lit la table GeoPackage demandée (n'importe laquelle si plusieurs)."""
    motif = re.compile(rf"layername={table}(\||$)")
    for lyr in projet.mapLayers().values():
        if isinstance(lyr, QgsVectorLayer) and motif.search(lyr.source()):
            return lyr
    if obligatoire:
        raise QgsProcessingException(
            f"Couche « {table} » introuvable : ouvrir le projet qgis/what_ais_doesnt_show.qgz avant de lancer l'outil.")
    return None


class Zone:
    """La zone, préparée pour des tests d'intersection rapides dans le système de chaque couche."""

    def __init__(self, geom_wgs84, projet):
        self.geom = geom_wgs84
        self.projet = projet
        self._cache = {}

    def dans(self, lyr):
        crs = lyr.crs()
        if crs.authid() not in self._cache:
            g = QgsGeometry(self.geom)
            if crs != WGS84:
                g.transform(QgsCoordinateTransform(WGS84, crs, self.projet))
            moteur = QgsGeometry.createGeometryEngine(g.constGet())
            moteur.prepareGeometry()
            self._cache[crs.authid()] = (g, moteur)
        return self._cache[crs.authid()]

    def entites(self, lyr):
        """Entités dont l'emprise touche celle de la zone (index spatial du GeoPackage)."""
        g, _ = self.dans(lyr)
        return lyr.getFeatures(QgsFeatureRequest().setFilterRect(g.boundingBox()))

    def contient(self, lyr, geom):
        return self.dans(lyr)[1].intersects(geom.constGet())


def premier_point(geom):
    return QgsGeometry(geom.vertexAt(0).clone())


def chiffres(zone, projet, feedback):
    """Mêmes définitions que les fiches prédéfinies (06_export_gpkg.py) ; un silence est rattaché à
    la zone de son début, un saut de position à son point de départ."""
    c = {}
    silences = couche_projet(projet, "silence_ais")
    comptes, nav_inexpl = {}, set()
    for f in zone.entites(silences):
        if zone.contient(silences, premier_point(f.geometry())):
            comptes[f["categorie"]] = comptes.get(f["categorie"], 0) + 1
            if f["categorie"] == "coupure inexpliquée":
                nav_inexpl.add(f["navire"])
    c["nb_silences"] = sum(comptes.values())
    c["nb_reception"] = comptes.get("réception insuffisante probable", 0)
    c["nb_inexpliquees"] = comptes.get("coupure inexpliquée", 0)
    c["nav_inexpliquees"] = len(nav_inexpl)

    sauts = couche_projet(projet, "saut_position")
    c["nav_mmsi_partage"] = len({f["navire"] for f in zone.entites(sauts)
                                 if f["mmsi_partage"] and zone.contient(sauts, premier_point(f.geometry()))})

    st = couche_projet(projet, "stationnement_infra")
    dedans = [f for f in zone.entites(st) if zone.contient(st, f.geometry())]
    c["nb_stationnements"] = len(dedans)
    c["nav_stationnements"] = len({f["navire"] for f in dedans})

    rc = couche_projet(projet, "rencontre")
    c["nb_rencontres"] = sum(1 for f in zone.entites(rc) if zone.contient(rc, f.geometry()))

    # navires : traces qui traversent la zone (traces.gpkg, non versionné)
    traces = couche_projet(projet, "trace", obligatoire=False)
    if traces:
        c["nb_navires"] = len({f["navire"] for f in zone.entites(traces) if zone.contient(traces, f.geometry())})
    else:
        c["nb_navires"] = None
        feedback.pushWarning("traces.gpkg absent : nombre de navires non calculé (lancer 06_export_gpkg.py).")

    # part du trafic en route dans des eaux bien couvertes : heures-navire en route de chaque maille H3,
    # au prorata de la surface de la maille comprise dans la zone (le long d'une côte découpée, retenir
    # les mailles par leur centre fausserait le compte)
    trafic = couche_projet(projet, "trafic")
    couverture = couche_projet(projet, "couverture")
    g_zone, _ = zone.dans(trafic)
    heures = {}
    for f in zone.entites(trafic):
        maille = f.geometry()
        if zone.contient(trafic, maille):
            part = maille.intersection(g_zone).area() / maille.area()
            heures[f["h3"]] = f["heures_route"] * part
    fiables = {f["h3"] for f in zone.entites(couverture) if f["classe"] == "Reliable"}
    total = sum(heures.values())
    c["part_couverte"] = sum(h for k, h in heures.items() if k in fiables) / total if total else None
    return c, comptes


def couche_memoire(definition, nom, projet):
    lyr = QgsVectorLayer(definition, nom, "memory")
    projet.addMapLayer(lyr, False)  # hors arbre des couches : seulement pour la mise en page
    return lyr


class FicheZone(QgsProcessingAlgorithm):
    ZONE, NOM, SORTIE, PNG = "ZONE", "NOM", "SORTIE", "PNG"

    def createInstance(self):
        return FicheZone()

    def name(self):
        return "fiche_zone"

    def displayName(self):
        return "Produire une fiche de zone"

    def group(self):
        return "What AIS doesn't show"

    def groupId(self):
        return "what_ais_doesnt_show"

    def shortHelpString(self):
        return (
            "Produit la fiche A4 (en anglais) d'une zone quelconque : chiffres clés, carte, graphique "
            "des silences AIS, légende, méthode et sources.<br><br>"
            "<b>Zone</b> : une couche de polygones. Cocher « Entités sélectionnées uniquement » pour ne "
            "prendre qu'une partie des polygones ; plusieurs polygones sont fusionnés en une seule zone.<br>"
            "<b>Nom</b> : titre de la fiche, en anglais (par exemple « Fehmarn Belt »).<br><br>"
            "Le projet qgis/what_ais_doesnt_show.qgz doit être ouvert. Données : 13–19 octobre 2026, "
            "détroits danois et bassin de Bornholm ; une zone hors de cette aire donne des chiffres nuls.<br><br>"
            "Le nombre de navires est compté sur les traces qui traversent la zone, la part du trafic "
            "bien couvert sur les mailles H3 dont le centre est dans la zone : de petits écarts avec les "
            "fiches de l'atlas, calculées sur les positions, sont normaux.")

    def flags(self):
        # mise en page et projet : à exécuter dans le fil principal de QGIS
        return super().flags() | QgsProcessingAlgorithm.FlagNoThreading

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.ZONE, "Zone (couche de polygones ; cocher « Entités sélectionnées uniquement »)",
            [QgsProcessing.TypeVectorPolygon], defaultValue=COUCHE_ZONES))
        self.addParameter(QgsProcessingParameterString(
            self.NOM, "Nom de la zone, en anglais (vide : nom du polygone)", defaultValue="", optional=True))
        self.addParameter(QgsProcessingParameterFileDestination(
            self.SORTIE, "Fiche PDF", "PDF (*.pdf)"))
        self.addParameter(QgsProcessingParameterBoolean(
            self.PNG, "Exporter aussi une image PNG (à côté du PDF)", defaultValue=True))
        for nom, libelle in (("NB_SILENCES", "Silences AIS"), ("NB_INEXPLIQUEES", "Silences inexpliqués"),
                             ("NB_NAVIRES", "Navires")):
            self.addOutput(QgsProcessingOutputNumber(nom, libelle))

    def processAlgorithm(self, parameters, context, feedback):
        projet = context.project() or QgsProject.instance()
        modele = projet.layoutManager().layoutByName(MISE_EN_PAGE)
        if modele is None:
            raise QgsProcessingException(f"Mise en page « {MISE_EN_PAGE} » introuvable dans le projet.")
        dossier_scripts = Path(projet.absolutePath()).parent / "scripts"
        if str(dossier_scripts) not in sys.path:
            sys.path.insert(0, str(dossier_scripts))
        from graphique_fiche import graphique  # même graphique que les fiches de l'atlas

        # 1. la zone, fusionnée et en WGS84
        source = self.parameterAsSource(parameters, self.ZONE, context)
        couche_zone = self.parameterAsVectorLayer(parameters, self.ZONE, context)
        nom_couche = couche_zone.name() if couche_zone else source.sourceName()
        table = re.search(r"layername=([^|]+)", couche_zone.source()) if couche_zone else None
        if table and table.group(1) in TABLES_INTERDITES:
            raise QgsProcessingException(
                f"« {nom_couche} » est une couche d'analyse du projet, pas une zone. Choisir la couche "
                f"« {COUCHE_ZONES} » (ou une couche de zones à vous) et cocher « Entités sélectionnées uniquement ».")
        entites = [f for f in source.getFeatures() if f.hasGeometry()]
        if not entites:
            raise QgsProcessingException(
                f"Aucun polygone dans « {nom_couche} » : sélectionner une zone sur la carte, ou décocher "
                "« Entités sélectionnées uniquement ».")
        noms = {str(f[c]) for f in entites for c in ("nom", "name") if c in f.fields().names() and f[c]}
        if len(noms) > 1 and not (self.parameterAsString(parameters, self.NOM, context) or "").strip():
            raise QgsProcessingException(
                f"{len(entites)} zones de « {nom_couche} » seraient fusionnées ({', '.join(sorted(noms))}). "
                "Cocher « Entités sélectionnées uniquement » et sélectionner une zone, ou donner un nom pour "
                "confirmer la fusion.")
        feedback.pushInfo(f"Zone : {len(entites)} polygone(s) de la couche « {nom_couche} »")
        geom = QgsGeometry.unaryUnion([f.geometry() for f in entites])
        geom.transform(QgsCoordinateTransform(source.sourceCrs(), WGS84, projet))
        geom = geom.makeValid()
        geom.convertToMultiType()
        # nom saisi, sinon celui du polygone (champ « nom » ou « name ») s'il n'y en a qu'un
        nom = (self.parameterAsString(parameters, self.NOM, context) or "").strip()
        if not nom and len(entites) == 1:
            for champ in ("nom", "name"):
                if champ in entites[0].fields().names() and entites[0][champ]:
                    nom = str(entites[0][champ])
                    break
        nom = nom or "Area of interest"
        sortie = Path(self.parameterAsFileOutput(parameters, self.SORTIE, context))
        feedback.pushInfo(f"Zone « {nom} » : {geom.area():.3f} degrés carrés")

        # 2. chiffres clés et graphique
        feedback.setProgressText("Calcul des chiffres clés")
        c, comptes = chiffres(Zone(geom, projet), projet, feedback)
        feedback.setProgress(40)
        svg = Path(tempfile.mkdtemp(prefix="fiche_zone_")) / "graphique.svg"
        graphique(svg, comptes)
        for k, v in c.items():
            feedback.pushInfo(f"  {k} : {v}")

        # 3. couche de la zone (couverture de l'atlas), voile et contour pour la carte
        champs = "&".join(f"field={n}:{t}" for n, t in CHAMPS)
        zone_lyr = couche_memoire(f"MultiPolygon?crs=EPSG:4326&{champs}", "zone", projet)
        f = QgsFeature(zone_lyr.fields())
        f.setGeometry(geom)
        valeurs = {"zone_id": "custom", "nom": nom, "sous_titre": "Custom area", "ordre": 1,
                   "graphique": str(svg), **c}
        for n, _ in CHAMPS:
            f[n] = valeurs.get(n)
        zone_lyr.dataProvider().addFeature(f)

        # voile et contour : la géométrie seule (ces couches n'ont pas de champs)
        forme = QgsFeature()
        forme.setGeometry(geom)
        voile = couche_memoire("MultiPolygon?crs=EPSG:4326", "voile", projet)
        voile.dataProvider().addFeature(QgsFeature(forme))
        fond = QgsFillSymbol.createSimple({"color": "255,255,255,140", "outline_style": "no"})
        voile.setRenderer(QgsInvertedPolygonRenderer(QgsSingleSymbolRenderer(fond)))
        contour = couche_memoire("MultiPolygon?crs=EPSG:4326", "contour", projet)
        contour.dataProvider().addFeature(QgsFeature(forme))
        trait = QgsFillSymbol.createSimple({"style": "no", "outline_color": "#2b2b2a", "outline_width": "0.45"})
        contour.setRenderer(QgsSingleSymbolRenderer(trait))

        # 4. copie de la mise en page, branchée sur cette zone
        feedback.setProgressText("Mise en page")
        mise = modele.clone()
        carte = mise.itemById("main map")
        couches = []
        for lyr in projet.mapThemeCollection().mapThemeVisibleLayers(THEME):
            if "layername=zone_fiche" in lyr.source():
                couches.append(voile)
            elif "layername=zone_contour" in lyr.source():
                couches.append(contour)
            else:
                couches.append(lyr)
        carte.setFollowVisibilityPreset(False)
        carte.setLayers(couches)
        carte.setKeepLayerSet(True)
        atlas = mise.atlas()
        atlas.setCoverageLayer(zone_lyr)
        atlas.setFilterFeatures(False)
        atlas.setSortFeatures(False)
        atlas.setEnabled(True)

        # 5. export
        feedback.setProgressText("Export de la fiche")
        sortie.parent.mkdir(parents=True, exist_ok=True)
        pdf = QgsLayoutExporter.PdfExportSettings()
        pdf.dpi = 300
        resultat, erreur = QgsLayoutExporter.exportToPdf(atlas, str(sortie), pdf)
        if resultat != QgsLayoutExporter.Success:
            raise QgsProcessingException(f"Export PDF impossible : {erreur}")
        feedback.setProgress(80)
        if self.parameterAsBool(parameters, self.PNG, context):
            image = QgsLayoutExporter.ImageExportSettings()
            image.dpi = 150
            atlas.beginRender()
            atlas.first()
            QgsLayoutExporter(mise).exportToImage(str(sortie.with_suffix(".png")), image)
            atlas.endRender()

        # 6. ménage : la copie de mise en page d'abord, puis les couches temporaires
        del carte, atlas, mise
        projet.removeMapLayers([zone_lyr.id(), voile.id(), contour.id()])
        feedback.setProgress(100)
        feedback.pushInfo(f"Fiche écrite : {sortie}")
        return {self.SORTIE: str(sortie), "NB_SILENCES": c["nb_silences"],
                "NB_INEXPLIQUEES": c["nb_inexpliquees"], "NB_NAVIRES": c["nb_navires"]}
