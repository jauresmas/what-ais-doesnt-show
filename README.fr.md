# What AIS doesn't show

**Ce que l'AIS ne montre pas : angles morts du réseau AIS côtier et silences inexpliqués, détroits danois et bassin de Bornholm, 13–19 octobre 2026**

**[Ouvrir la carte web interactive](https://jauresmas.github.io/what-ais-doesnt-show/carte/)** · [English version](README.md)

Une chaîne SIG reproductible, construite uniquement sur des données ouvertes. Elle mesure où le réseau AIS côtier perd réellement les navires, puis sépare les silences AIS ordinaires de ceux qu'aucune explication ordinaire ne justifie. Elle signale aussi les conflits d'identité, les passages lents au-dessus des câbles sous-marins et les rencontres en mer, et les combine en un indice de vigilance sur une grille H3.

> Projet personnel de démonstration, sur données ouvertes uniquement. Les indicateurs signalent des écarts au comportement attendu, pas des infractions : aucun navire n'est nommé ni mis en cause, et les productions publiques sont agrégées ou pseudonymisées.

## Une semaine en chiffres

| | |
|---|---:|
| Messages AIS traités | 117,6 millions |
| Navires de classe A suivis | 2 894 |
| Silences AIS de 2 heures ou plus | 3 880 |
| … dus aux limites du réseau côtier | 496 |
| … **inexpliqués** : transits silencieux dans des eaux bien couvertes | **11** (10 navires) |
| Navires dont le MMSI est partagé avec un autre émetteur (3 sauts impossibles ou plus) | 10 |
| Passages lents au-dessus d'un câble ou d'un pipeline sous-marin (moins de 2 nœuds, 30 min ou plus) | 121 (42 navires) |
| Rencontres en mer (moins de 500 m, 2 heures ou plus) | 47, dont 45 au large de Skagen |
| Détections radar Sentinel-1 (13 passages du satellite), dont sans aucun AIS | 2 373, dont 238 |

Le réseau danois est l'un des plus denses d'Europe. Même ici, 9 % des positions de navires en route tombent dans des mailles qu'il ne couvre pas de façon fiable, des émetteurs partagent la même identité, et certains navires se taisent dans des eaux où neuf voisins sur dix sont reçus. Dans chacun de ces cas, une détection qui ne dépend pas de l'émission du navire lui-même (géolocalisation radiofréquence, radar satellitaire) apporte l'information manquante.

Tous les chiffres : [docs/rapport_qualite.md](docs/rapport_qualite.md), généré à partir de la base, sans aucun chiffre saisi à la main.

## Fiches de zone

Une fiche A4 par zone d'intérêt, produite par un atlas QGIS : l'aire d'étude, puis la part de chaque ZEE qui s'y trouve. Les chiffres clés sont calculés par zone dans PostGIS et lus par la mise en page ; la carte, le graphique et le contour suivent la zone automatiquement. Les fiches sont en anglais, pour une diffusion internationale.

[![Fiche de zone, aire d'étude](sorties/fiches/zone-sheet_study-area.png)](sorties/fiches/zone-sheets.pdf)

[Les cinq fiches (PDF, 6 Mo)](sorties/fiches/zone-sheets.pdf) · [Vue analyste : couverture mesurée et indice de vigilance](sorties/fiches/coverage-and-vigilance.pdf)

## Carte web

Les mêmes couches dans un navigateur, en français et en anglais : [jauresmas.github.io/what-ais-doesnt-show/carte/](https://jauresmas.github.io/what-ais-doesnt-show/carte/). Un clic sur un signal ouvre sa fiche courte ; la couverture et l'indice de vigilance s'affichent comme vues d'analyse. La page est statique (MapLibre GL JS lit des fichiers GeoJSON écrits par `09_carte_web.py`) et GitHub Pages la sert depuis ce dépôt.

Elle produit aussi une **fiche de zone** sans QGIS : choisir l'aire d'étude ou une ZEE, dessiner une zone sur la carte ou importer un fichier GeoJSON, et la page compose une fiche A4 (carte, chiffres clés, graphique des causes de silence, méthode) qui s'imprime en PDF, avec les chiffres en CSV, la zone en GeoJSON et un lien qui rouvre la même fiche. Les zones prédéfinies portent les chiffres exacts de la chaîne ; pour une zone libre, le navigateur applique les règles de l'outil QGIS avec Turf.js et h3-js, et le nombre de navires est estimé à partir des mailles H3. Les données nécessaires (début des silences, mailles H3 et leurs navires sous des numéros sans lien avec le MMSI, détections radar) ne se chargent qu'à la demande d'une fiche.

## Une fiche pour n'importe quelle zone : un outil de traitement QGIS

`qgis/outils/fiche_zone.py` ajoute **Produire une fiche de zone** à la boîte à outils de traitement de QGIS. On dessine un polygone dans la couche *My areas of interest* (trois exemples sont fournis), on le sélectionne, on lance l'outil : il calcule les chiffres clés à partir des GeoPackages (aucune base de données nécessaire), dessine le graphique et exporte la fiche A4 en PDF et en PNG, avec la même mise en page que l'atlas. Il fonctionne aussi en lot, une ligne par zone.

Validé sur les cinq zones de l'atlas : les signaux sont identiques ; le nombre de navires est inférieur de 1 à 2,5 % (traces au lieu de positions) et la part du trafic bien couvert peut s'écarter jusqu'à 8 points dans une zone côtière à grands ports. Détails et mode d'emploi pas à pas pour les non-spécialistes : [docs/guide_fiche_zone.md](docs/guide_fiche_zone.md).

| | |
|---|---|
| [![Bassin d'Arkona](sorties/fiches/zone-sheet_arkona-basin.png)](sorties/fiches/zone-sheet_arkona-basin.pdf) | [![Rade de Skagen](sorties/fiches/zone-sheet_skagen-roads.png)](sorties/fiches/zone-sheet_skagen-roads.pdf) |
| Bassin d'Arkona | Rade de Skagen |

## Projet QGIS

`qgis/what_ais_doesnt_show.qgz` s'ouvre sur la carte de la fiche et lit `donnees/produites/carto.gpkg` (chemins relatifs, navires pseudonymisés). Il contient :

- des couches rangées par thème (signaux, indicateurs, infrastructures, limites, traces, fond), stylées avec une palette lisible par les daltoniens, vérifiée avec un outil de contrôle des contrastes et de la vision des couleurs ;
- des thèmes de carte : *Zone sheet – main map*, *Shore AIS coverage*, *Vigilance index*, *Infrastructure & loitering*, *All AIS silences*, *Vessel tracks* ;
- des signets : rade de Skagen, bassin d'Arkona, entrée du canal de Kiel, Fehmarn Belt, Øresund, Bornholm, baie de Poméranie ;
- deux mises en page : *Zone sheet* (atlas) et *Coverage & vigilance*.

Le projet est construit par `scripts/07_projet_qgis.py` : un changement de données ou de style se répercute en une commande. Il enregistre sa propre transformation de datum (WGS84 → ETRS89-LAEA) et s'ouvre donc sans aucune question ; l'enquête sur les plantages qui a conduit à ce choix est dans [docs/incidents_qgis.md](docs/incidents_qgis.md). Les traces des navires sont dans un `traces.gpkg` séparé (58 Mo, non versionné, régénéré par `06_export_gpkg.py`).

## Contrôle indépendant par radar satellitaire

Le radar Sentinel-1 voit les navires, qu'ils émettent ou non. Global Fishing Watch publie ses détections et les rapproche de l'AIS mondial ; 13 passages couvrent la semaine d'étude. Chaque détection est datée à la minute (l'instant de l'image, retrouvé grâce aux navires détectés une seule fois), puis confrontée au réseau côtier danois.

| Couverture côtière de la maille | Navires vus au radar et identifiés | Reçus par le réseau danois à cette minute |
|---|---:|---:|
| Fiable | 1 775 | 99,3 % |
| Dégradée | 91 | 81,3 % |
| Trafic insuffisant pour juger | 56 | 71,4 % |
| Mauvaise | 177 | 51,4 % |

La part reçue suit les classes de couverture : une source qui ne doit rien à l'AIS côtier confirme la carte de couverture. Sur les 238 détections sans AIS, 28 sont dans des parcs éoliens (structures fixes), 26 sont proches d'un navire en silence AIS à cette minute, et 72 sont vues seulement au radar dans des eaux bien couvertes. Trois des 11 silences inexpliqués ont eu lieu pendant un passage ; pour l'un d'eux, une détection sans AIS se trouve à moins de 5 km de la position supposée du navire. Les détections sans AIS figurent sur les fiches de zone, dans le projet QGIS et sur la carte web, hors structures des parcs éoliens. Données radar : Powered by [Global Fishing Watch](https://globalfishingwatch.org) (CC BY-NC 4.0).

## Ce qui rend l'analyse fiable

- **La couverture est mesurée, pas supposée.** La réception est calculée par maille H3 à partir du trafic lui-même : part des intervalles d'une minute effectivement reçus, et part des navires attendus perdus en traversant la maille. Cette seconde mesure corrige un biais de sélection découvert pendant la mise au point : des silences se concentraient sur un même tronçon de route, pour des navires différents à des heures différentes, dans des mailles affichant 98 % de réception. Un navire jamais reçu ne laisse aucune trace : la réception seule surestime donc la couverture. La mesure des navires perdus déclasse 288 mailles.
- **« Inexpliqué » se mérite.** Un silence est rangé dans neuf catégories, de la plus ordinaire (bateau-pilote, escale, voie navigable intérieure, bord de l'aire d'étude, trou de réception, sortie possible de la couverture) à *inexpliqué*. Il n'atteint cette dernière que si le navire est resté dans des eaux bien couvertes, si le réseau recevait ses voisins heure par heure, et s'il n'avait pas le temps de sortir de la couverture et d'y revenir.
- **Chaque ligne écartée est comptée.** Le nettoyage consigne chaque ligne rejetée avec son motif (`qualite.bilan_nettoyage`) : 28 % des lignes brutes sont des doublons exacts, reçus par plusieurs stations.
- **Une seule source pour les seuils.** Tous les seuils sont réunis dans `scripts/config.py` et passés au SQL comme variables : en modifier un et relancer `04_indicateurs.py` refait toute l'analyse. Chaque seuil est justifié dans [docs/methode.md](docs/methode.md).

## Chaîne de traitement

```mermaid
flowchart LR
  A[AIS ouvert DMA<br>7 fichiers quotidiens, 4,3 Go] --> B[02 nettoyage<br>117,6 M lignes → 9,3 M positions]
  R[Marine Regions · GISCO · EMODnet<br>TeleGeography · OpenStreetMap] --> C[03 référentiel]
  B --> D[(PostGIS + H3)]
  C --> D
  D --> E[04 indicateurs]
  E --> E1[Couverture mesurée]
  E --> E2[Silences AIS<br>9 catégories]
  E --> E3[Anomalies d'identité]
  E --> E4[Stationnements sur câbles]
  E --> E5[Rencontres en mer]
  E1 & E2 & E3 & E4 & E5 --> F[Indice de vigilance<br>H3 résolution 5]
  F --> G[05 rapport qualité]
  F --> H[06 export GeoPackage<br>navires pseudonymisés]
  H --> I[07 projet QGIS<br>atlas, fiches, outil]
```

| Script | Rôle |
|---|---|
| `00_base.py` | Crée et démarre une instance PostgreSQL propre au projet (PostGIS 3.5, h3-pg 4.1), sans mot de passe, port 5434 |
| `01_telecharger_ais.py` | Télécharge les fichiers AIS quotidiens de l'Autorité maritime danoise, sans retélécharger les fichiers complets |
| `02_nettoyer_ais.py` | Lit chaque ZIP sans le décompresser, nettoie en 7 étapes tracées, charge les positions par `COPY` |
| `03_referentiel.py` | ZEE, mers territoriales, limites maritimes, terres, câbles et pipelines de trois sources, parcs éoliens, mouillages, table des pavillons |
| `04_indicateurs.py` | Exécute `sql/03` à `sql/11` : navires, couverture, géométries de travail, silences, identité, infrastructures, rencontres, indice, cartographie |
| `05_rapport.py` | Écrit `docs/rapport_qualite.md` à partir de la base |
| `06_export_gpkg.py` | Exporte les couches d'affichage en GeoPackage, navires pseudonymisés, chiffres et graphiques des zones |
| `07_projet_qgis.py` | Construit le projet QGIS (styles, thèmes, signets, mises en page) et exporte les fiches ; s'exécute dans QGIS ou avec le Python de QGIS |
| `08_sar_gfw.py` | Facultatif : détections Sentinel-1 de l'API Global Fishing Watch (jeton personnel dans `gfw_token.txt`, non versionné), croisées avec l'AIS danois dans `sql/12_sar.sql` ; s'exécute juste après l'étape 04 |
| `09_carte_web.py` | Écrit les couches GeoJSON allégées et les chiffres clés lus par la carte web (`carte/`), et les données de sa fiche de zone |
| `run_all.py` | Toute la chaîne ; `--depuis 04` reprend à une étape donnée |

## Lancer la chaîne

Prérequis : Python 3.10 avec les paquets de `requirements.txt` ; PostgreSQL 15 avec PostGIS 3.5 et les extensions h3-pg 4.1 (`h3`, `h3_postgis`). Les chemins de PostgreSQL et du Python de QGIS sont dans `scripts/config.py`.

```bash
python scripts/run_all.py
```

Compter une quarantaine de minutes sur un portable, et 4,3 Go téléchargés au premier passage. L'étape 07 utilise le Python de QGIS (`python-qgis-ltr.bat`). Les données brutes ne sont pas versionnées : les scripts les téléchargent à nouveau.

## Organisation du dépôt

```
scripts/        chaîne de traitement (00 à 09), configuration, scripts SQL dans scripts/sql/
docs/           méthode, sources et licences, rapport qualité généré, guide de l'outil, note d'incident
donnees/        téléchargements bruts (non versionnés) et GeoPackages de cartographie
qgis/           projet QGIS, outil de traitement (qgis/outils/) et graphiques des fiches
sorties/        fiches de zone exportées (PDF, PNG)
carte/          carte web (page statique et ses données GeoJSON)
```

## Limites

- Au-delà des eaux danoises, la couverture AIS repose sur une réception à longue distance qui varie avec la météo : le projet la mesure, mais ne peut pas la supprimer.
- Les tracés publics des câbles et pipelines sont indicatifs. Trois sources sont combinées et documentées dans [docs/sources.md](docs/sources.md).
- Un silence inexpliqué peut encore venir d'un émetteur défaillant ou d'une antenne mal placée. Les indicateurs disent où regarder, pas ce qui s'est passé.
- Une semaine de données : les indicateurs décrivent cette semaine, pas une tendance de fond.

## Pour aller plus loin

- Plusieurs semaines de données, pour distinguer les phénomènes récurrents des événements ponctuels.
- Un curseur temporel sur la carte web, pour suivre les silences et les passages radar heure par heure.

## Documentation

[Méthode](docs/methode.md) · [Sources et licences](docs/sources.md) · [Rapport qualité](docs/rapport_qualite.md) · [Guide de l'outil de fiche de zone](docs/guide_fiche_zone.md) · [Note d'incident QGIS](docs/incidents_qgis.md)

## Données

Autorité maritime danoise (AIS), Flanders Marine Institute / Marine Regions (CC BY 4.0), Eurostat GISCO (© EuroGeographics), EMODnet Human Activities et BSH (CC BY 4.0), TeleGeography (CC BY-NC-SA 3.0), © contributeurs OpenStreetMap (ODbL), détections radar Powered by Global Fishing Watch (CC BY-NC 4.0). Détails dans [docs/sources.md](docs/sources.md).
