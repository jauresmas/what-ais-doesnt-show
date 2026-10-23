"""Paramètres du projet : période, zone d'étude, chemins, base PostGIS."""
from datetime import date, timedelta
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
SCRIPTS = RACINE / "scripts"
SQL = SCRIPTS / "sql"
BRUTES = RACINE / "donnees" / "brutes"
AIS_BRUT = BRUTES / "ais"
REFERENTIEL = BRUTES / "referentiel"
PRODUITES = RACINE / "donnees" / "produites"
SORTIES = RACINE / "sorties"
DOCS = RACINE / "docs"

# Période : la dernière semaine complète publiée par l'Autorité maritime danoise
DEBUT = date(2026, 10, 13)
FIN = date(2026, 10, 19)
JOURS = [DEBUT + timedelta(days=i) for i in range((FIN - DEBUT).days + 1)]

# Zone d'étude : détroits danois et bassin de Bornholm (WGS84)
BBOX = (9.0, 53.9, 16.5, 58.2)  # ouest, sud, est, nord

# Données AIS ouvertes de l'Autorité maritime danoise (un ZIP par jour)
AIS_URL = "http://aisdata.ais.dk.s3.eu-central-1.amazonaws.com/aisdk-{jour}.zip"

# Une position conservée par navire et par minute : largement suffisant pour
# repérer des coupures de plusieurs heures, sans garder 20 millions de lignes par jour
PAS_MINUTES = 1

# Seuils des indicateurs, justifiés dans docs/methode.md
SEUILS = {
    "seuil_coupure": "2 hours",       # silence AIS minimal pour parler de coupure
    "marge_limite_m": 10000,          # une coupure qui commence ou finit à moins de 10 km
                                      # du bord de la zone est une sortie de zone
    "abri_cote_m": 3000,              # bande côtière où l'arrêt d'un navire est banal
    "tampon_infra_m": 750,            # distance à un câble ou un pipeline
    "tampon_eolien_m": 1000,          # navires de maintenance des parcs éoliens
    "vitesse_lente_nd": 2,            # navire quasi immobile
    "duree_stationnement": "30 minutes",
    "distance_rencontre_m": 500,      # deux navires bord à bord ou presque
    "duree_rencontre": "2 hours",
    "saut_vitesse_nd": 50,            # vitesse implicite impossible pour un navire de commerce
}

# Instance PostgreSQL propre au projet : locale, sans mot de passe
PG_BIN = Path(r"C:\Program Files\PostgreSQL\15\bin")
PG_DATA = RACINE / ".pgdata"
PG_HOST = "localhost"
PG_PORT = 5434
PG_USER = "ais"
PG_DB = "ais"

# Python de QGIS, pour construire le projet et les fiches hors interface (étape 07)
PYTHON_QGIS = Path(r"C:\Program Files\QGIS 3.34.12\bin\python-qgis-ltr.bat")
