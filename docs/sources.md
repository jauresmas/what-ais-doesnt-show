# Sources de données et licences

Toutes les données d'entrée sont ouvertes. Les téléchargements bruts sont conservés dans `donnees/brutes/` (non versionné) et sont récupérés par `scripts/01_telecharger_ais.py` et `scripts/03_referentiel.py`.

| Couche | Producteur | Accès | Licence, conditions | Usage |
|---|---|---|---|---|
| Positions et données statiques AIS, 13–19 octobre 2026 | Autorité maritime danoise (DMA), AIS historique | `aisdata.ais.dk`, un ZIP par jour (≈ 600 Mo) | Réutilisation libre et gratuite (politique de gestion des données AIS de la DMA) | Tous les indicateurs |
| Zones économiques exclusives, mers territoriales de 12 milles | Flanders Marine Institute, Marine Regions (EEZ v12) | WFS `geo.vliz.be` | CC BY 4.0 depuis la v11 ; pas d'usage juridique ni de navigation | Statistiques par zone, cartes |
| Terres au 1:1 000 000 | Eurostat GISCO, Countries 2024 | API GeoJSON | © EuroGeographics, citation obligatoire | Bande côtière, cartes |
| Pipelines, câbles électriques et de données allemands, parcs éoliens en mer | EMODnet Human Activities (BSH CONTIS pour les câbles allemands) | WFS `ows.emodnet-humanactivities.eu` | CC BY 4.0 (conditions d'utilisation EMODnet), citer EMODnet et le BSH | Couche infrastructures |
| Câbles de télécommunication | TeleGeography, Submarine Cable Map | API `submarinecablemap.com` | CC BY-NC-SA 3.0 : usage non commercial, compatible avec ce projet de démonstration | Couche infrastructures |
| Câbles et pipelines sous-marins, zones de mouillage | Contributeurs OpenStreetMap (balisage OpenSeaMap) | API Overpass | ODbL 1.0 | Couche infrastructures, abris |
| Détections radar Sentinel-1, appariées ou non à l'AIS, 13–19 octobre 2026 | Global Fishing Watch, jeu `public-global-sar-presence` (v5.0) | API v3 4Wings, jeton personnel (non versionné) | CC BY-NC 4.0 : usage non commercial, mention « Powered by Global Fishing Watch » | Contrôle indépendant de la couverture et des silences |
| Préfixes MID (pavillon déduit du MMSI) | Liste UIT, telle que tabulée sur Wikipédia | Source wiki de l'article | CC BY-SA 4.0 | Pavillon des navires |

## Limites connues

- **Couverture AIS.** Le réseau de la DMA est conçu pour les eaux danoises. Plutôt que de supposer sa portée, le projet la mesure à partir du trafic lui-même (`indic.couverture`, voir [methode.md](methode.md)).
- **Tracés des infrastructures.** Aucune source ouverte ne couvre seule tous les câbles de la zone. Les trois sources se recouvrent (un même câble peut figurer chez TeleGeography et dans OpenStreetMap) et leurs tracés sont indicatifs, pas des levés. L'analyse utilise un tampon de 750 m autour de chaque tracé ; les recouvrements ne gonflent pas les comptes, car chaque position de navire n'est rattachée qu'à un seul tracé.
- **Zones de mouillage** issues d'OpenStreetMap. Quand un mouillage n'est cartographié que par un point, on suppose un cercle d'un mille nautique.
- **Pavillon** déduit des trois premiers chiffres du MMSI. Un navire peut émettre un MMSI qui ne correspond pas à son immatriculation réelle : le pavillon affiché est celui que le navire revendique.
