# Rapport qualité

*Généré par `scripts/05_rapport.py` le 24/10/2026. Période : du 13/10/2026 au 19/10/2026. Zone : 9,0–16,5° E, 53,9–58,2° N.*

## 1. Nettoyage des données AIS

**117 610 174 lignes lues, 9 307 222 positions gardées** (7,9 %), pour **2 894 navires** de classe A.

| Étape | Motif | Lignes | Part des lignes lues |
|---:|---|---:|---|
| 1 | type d'émetteur : Base Station | 7 031 075 | 6,0 % |
| 1 | type d'émetteur : Class B | 5 689 837 | 4,8 % |
| 1 | type d'émetteur : AtoN | 2 114 278 | 1,8 % |
| 1 | type d'émetteur : SAR Airborne | 116 320 | 0,1 % |
| 1 | type d'émetteur : Search and Rescue Transponder | 55 | 0,0 % |
| 1 | type d'émetteur : Emergency PIRB | 39 | 0,0 % |
| 1 | type d'émetteur : Man Overboard Device | 5 | 0,0 % |
| 2 | MMSI invalide | 725 314 | 0,6 % |
| 3 | message sans position | 68 799 | 0,1 % |
| 4 | position nulle | 0 | 0,0 % |
| 5 | hors zone d'étude | 18 377 226 | 15,6 % |
| 6 | doublon exact | 33 436 363 | 28,4 % |
| 7 | allègement (1 position par minute) | 40 743 641 | 34,6 % |

Plus d'une ligne sur quatre est un doublon exact : le même message reçu par plusieurs stations côtières. L'allègement à une position par minute retire ensuite l'essentiel du volume sans perte d'information pour des silences de plusieurs heures.

| Jour | Lignes lues | Positions gardées |
|---|---:|---:|
| 2026-10-13 | 16 575 849 | 1 318 784 |
| 2026-10-14 | 16 734 128 | 1 314 539 |
| 2026-10-15 | 17 225 628 | 1 385 031 |
| 2026-10-16 | 17 272 233 | 1 386 469 |
| 2026-10-17 | 16 298 690 | 1 298 731 |
| 2026-10-18 | 16 826 371 | 1 311 270 |
| 2026-10-19 | 16 677 275 | 1 292 398 |

## 2. Identité des navires

| Famille | Navires | IMO valide | IMO à clé fausse | IMO absent |
|---|---:|---:|---:|---:|
| Cargo | 1 011 | 986 | 1 | 24 |
| Other / unknown | 462 | 115 | 7 | 340 |
| Service & authorities | 452 | 211 | 6 | 235 |
| Tanker | 345 | 344 | 0 | 1 |
| Passenger | 317 | 189 | 1 | 127 |
| Fishing | 307 | 70 | 3 | 234 |

L'IMO est contrôlé par sa clé (7ᵉ chiffre). Les navires de servitude, de pêche et les petits navires à passagers n'ont souvent pas d'IMO, ce qui est normal ; un cargo ou un pétrolier sans IMO valide est signalé (`imo_douteux`).

| Pavillon déclaré | Navires |
|---|---:|
| Denmark | 643 |
| Sweden | 384 |
| Germany | 378 |
| Netherlands | 205 |
| Antigua and Barbuda | 127 |
| Portugal (Madeira) | 127 |
| Cyprus | 110 |
| Norway | 109 |
| Liberia | 105 |
| Marshall Islands | 79 |
| Malta | 78 |
| Panama | 67 |

Le pavillon est déduit des trois premiers chiffres du MMSI : c'est le pavillon revendiqué par l'émetteur.

## 3. Couverture du réseau AIS côtier

- 3 591 mailles H3 (résolution 6, ≈ 36 km²) traversées par le trafic, dont 2 535 assez fréquentées pour être jugées.
- **2 188 mailles bien couvertes**, qui portent 91 % des positions de navires en route.
- 288 mailles auraient paru bien couvertes à ne regarder que les navires reçus : elles sont déclassées parce que plus d'un navire attendu sur dix y disparaît. Sans ce correctif, des trous de réception passeraient pour des extinctions volontaires.

## 4. Coupures AIS de 2 heures ou plus

**3 880 coupures**, classées par explication, de la plus ordinaire à l'absence d'explication :

| Catégorie | Coupures | Navires | Durée médiane (h) |
|---|---:|---:|---:|
| position incohérente | 1 | 1 | 2,2 |
| navire de servitude ou d'État | 1 121 | 206 | 5,0 |
| sortie de la zone | 787 | 412 | 8,6 |
| navigation intérieure ou portuaire | 995 | 307 | 5,6 |
| arrêt au port ou au mouillage | 385 | 146 | 5,0 |
| réception insuffisante probable | 496 | 248 | 11,7 |
| escale ou détour côtier possible | 55 | 23 | 9,8 |
| sortie de couverture possible | 29 | 27 | 34,1 |
| coupure inexpliquée | 11 | 10 | 3,2 |

Coupures inexpliquées, en détail :

| Famille | Nature | Coupures | Navires | Durée médiane (h) |
|---|---|---:|---:|---:|
| Cargo | transit silencieux | 8 | 8 | 3,0 |
| Other / unknown | transit silencieux | 2 | 1 | 3,2 |
| Fishing | transit silencieux | 1 | 1 | 6,9 |

« Inexpliquée » signifie que le navire est resté, faute de temps pour en sortir, dans des eaux où le réseau recevait plus de 90 % des navires qui les traversaient, et qu'il s'est tu. Une panne d'émetteur ou une antenne mal placée restent possibles ; c'est le cas où une détection indépendante de l'AIS lève le doute.

## 5. Anomalies d'identité

- 198 sauts de position (vitesse implicite de plus de 50 nœuds), sur 53 navires.
- **10 navires avec trois sauts ou plus.** Le motif dominant est un aller-retour toutes les minutes entre deux lieux distants de plusieurs dizaines de milles : deux émetteurs partagent le même MMSI.
- 17 navires ont déclaré plusieurs noms, IMO ou types dans la semaine.
- 26 cargos ou pétroliers sans IMO valide.

## 6. Stationnements au-dessus des infrastructures sous-marines

| Famille | Épisodes | Navires | Durée médiane (h) |
|---|---:|---:|---:|
| Other / unknown | 70 | 13 | 1,3 |
| Fishing | 21 | 14 | 0,7 |
| Passenger | 21 | 6 | 1,8 |
| Cargo | 6 | 6 | 1,6 |
| Tanker | 3 | 3 | 1,4 |

| Infrastructure | Épisodes |
|---|---:|
| câble de télécommunication | 84 |
| câble (usage non précisé) | 17 |
| câble électrique | 15 |
| pipeline | 5 |

Navires de servitude exclus. Les épisodes des navires de type « autre ou inconnu » (navires de recherche, d'études, offshore) relèvent en général de travaux ; ceux des cargos et pétroliers sont les plus à surveiller.

## 7. Rencontres en mer

**47 rencontres** d'au moins 2 heures, dont 45 au large de Skagen, grande zone de soutage où ont aussi lieu des transbordements de navire à navire. 45 impliquent au moins un pétrolier.

## 8. Indice de vigilance

| Signaux présents | Mailles |
|---:|---:|
| 0 | 223 |
| 1 | 89 |
| 2 | 15 |
| 3 | 1 |

Mailles H3 de résolution 5 totalisant au moins 50 heures-navire et 10 navires dans la semaine.

## 9. Contrôle indépendant par radar satellitaire (Sentinel-1, Global Fishing Watch)

**13 passages de Sentinel-1** sur la semaine, **2 373 détections** de navires, dont 238 sans AIS correspondant (10,0 %).

Validation de la couverture : les navires vus au radar et identifiés par Global Fishing Watch étaient-ils reçus par le réseau danois au même instant ?

| Couverture de la maille | Navires vus au radar | Reçus par le réseau danois | Part reçue |
|---|---:|---:|---|
| Reliable | 1 775 | 1 762 | 99,3 % |
| Degraded | 91 | 74 | 81,3 % |
| Not enough traffic | 56 | 40 | 71,4 % |
| Poor | 177 | 91 | 51,4 % |

La part reçue suit les classes de la carte de couverture : une source qui ne doit rien à l'AIS côtier confirme la mesure.

Détections sans AIS :

| Catégorie | Détections |
|---|---:|
| radar seul, eaux bien couvertes | 72 |
| navire AIS danois à moins de 1,5 km | 60 |
| eaux mal couvertes par le réseau côtier | 52 |
| structure fixe probable (parc éolien) | 28 |
| navire en silence AIS à cet instant | 26 |

Sur les silences inexpliqués, 3 ont eu lieu pendant un passage du satellite ; pour 1 d'entre eux, une détection sans AIS se trouve à moins de 5 km de la position supposée du navire. Une détection « radar seul » n'est pas une infraction : bien des navires assez grands pour être vus au radar ne sont pas tenus d'émettre en AIS (plaisance, pêche de moins de 15 m, petits navires de servitude).

*Détections radar : Powered by Global Fishing Watch (CC BY-NC 4.0).*

## 10. Plusieurs semaines : ponctuel ou chronique ?

La même chaîne, sans aucune modification, a tourné sur chaque semaine, dans sa propre base (`10_semaines.py`). La semaine d'étude est la dernière.

| Semaine du | Navires | Positions | Silences | Trous de réception | Inexpliqués | MMSI partagés | Rencontres | Trafic bien couvert |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 22/09 | 3 156 | 10 090 264 | 4 974 | 471 | 4 | 11 | 64 | 89,6 % |
| 29/09 | 3 136 | 10 247 892 | 4 927 | 302 | 7 | 17 | 74 | 88,9 % |
| 06/10 | 2 837 | 9 127 334 | 3 836 | 476 | 11 | 13 | 58 | 91,9 % |
| 13/10 | 2 894 | 9 307 222 | 3 880 | 496 | 11 | 10 | 47 | 91,3 % |

Classe de couverture de chaque maille H3, semaine après semaine (une maille n'est jugée qu'une semaine où son trafic suffit) :

| Maille H3 | Mailles |
|---|---:|
| chronique (mauvaise 3 ou 4 semaines) | 168 |
| récurrente (2 semaines) | 143 |
| ponctuelle (1 semaine) | 207 |
| jamais mauvaise | 2 430 |
| trafic insuffisant pour juger | 1 073 |

Silences inexpliqués : 33 sur les 4 semaines. 4 mailles H3 de résolution 5 (≈ 250 km²) en voient commencer au moins deux semaines différentes, aucune trois semaines ou plus ; un seul navire a un silence inexpliqué au moins deux semaines différentes. Les silences inexpliqués ne reviennent donc pas aux mêmes endroits, ce qu'ils feraient s'ils tenaient à un défaut de la méthode ou de la couverture ; les angles morts chroniques, eux, sont durables. Ces récurrences désignent des lieux à suivre, pas des infractions.
