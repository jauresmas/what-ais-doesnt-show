# Méthode

Ce document décrit chaque étape de la chaîne, les seuils retenus et leurs raisons. Les seuils sont réunis dans `scripts/config.py` (dictionnaire `SEUILS`) et passés aux scripts SQL comme variables : en changer un et relancer `04_indicateurs.py` suffit à refaire toute l'analyse.

## 1. Nettoyage des données AIS (`02_nettoyer_ais.py`)

Les fichiers de l'Autorité maritime danoise contiennent tous les messages reçus par son réseau de stations côtières, un fichier par jour (≈ 17 millions de lignes). Chaque ligne écartée est comptée avec son motif dans `qualite.bilan_nettoyage`.

| Étape | Règle | Raison |
|---|---|---|
| 1. Type d'émetteur | On ne garde que la classe A | Seule la classe A est obligatoire (convention SOLAS : navires de commerce de plus de 300 UMS, navires à passagers) et émet à cadence réglementée. La classe B (plaisance, petite pêche) émet de façon irrégulière : une coupure n'y signifie rien. |
| 2. MMSI invalide | Hors de 201 000 000 – 775 999 999 | Plage UIT des stations de navire (préfixe MID de 2 à 7). |
| 3. Sans position | Latitude 91 ou longitude 181 | Valeurs « non disponible » du standard AIS. Ces messages portent l'identité du navire (nom, IMO, type), conservée à part avant de les écarter. |
| 4. Position nulle | 0°, 0° | Récepteur GPS sans signal. |
| 5. Hors zone | Hors de l'emprise 9,0–16,5° E, 53,9–58,2° N | Détroits danois et bassin de Bornholm. |
| 6. Doublon exact | Même MMSI, même seconde, même position | Un même message reçu par plusieurs stations. |
| 7. Allègement | Une position par navire et par minute | Un navire en route émet toutes les 2 à 10 secondes. Une position par minute suffit à repérer des silences de plusieurs heures, et réduit le volume d'un facteur 10. |

L'identité retenue pour un navire est la combinaison (nom, IMO, indicatif, type, dimensions) la plus déclarée sur la semaine. Une variante ne compte comme changement d'identité que si elle apparaît dans au moins 10 messages : un message isolé mal décodé ne fait pas un changement de nom.

Le numéro IMO est contrôlé par sa clé : le 7ᵉ chiffre est la somme des six premiers pondérés de 7 à 2, modulo 10. Un IMO absent ou faux sur un cargo ou un pétrolier est un signal en soi.

## 2. Couverture AIS mesurée (`sql/04_couverture.sql`)

Une coupure n'a de sens que là où le navire *aurait dû* être reçu. Plutôt que de supposer une portée théorique des stations, on mesure la réception réelle à partir du trafic, sur une maille H3 de résolution 6 (≈ 36 km²), avec deux mesures complémentaires.

**Taux de réception.** Après allègement, deux positions consécutives d'un navire en route (plus de 3 nœuds) sont espacées d'une minute là où la réception est bonne. Le taux est la part des intervalles de 3 minutes au plus.

**Taux de perte.** Le taux de réception ne voit que les navires reçus : un navire qui traverse une maille sans y être reçu n'y laisse aucune position. C'est un biais de sélection, et il est réel. Lors de la mise au point, des coupures se concentraient sur un même tronçon du bassin d'Arkona, pour des navires différents à des heures différentes, alors que les mailles y affichaient 98 % de réception. On suit donc le trajet supposé de chaque silence de 15 minutes à 6 heures d'un navire en mouvement, et l'on compte, par maille, les navires distincts perdus. Compter des navires plutôt que des minutes a une conséquence voulue : un seul navire qui se tait dans une maille fréquentée ne la déclasse pas, il reste repérable.

Une maille est **bien couverte** si elle compte au moins 100 intervalles, un taux de réception d'au moins 90 % et au plus un navire attendu sur dix perdu.

Deux tables complètent la mesure : la **réception horaire** (navires reçus par maille de résolution 5 et par heure) et les **zones mesurées comme mal couvertes** (taux de réception inférieur à 80 % ou plus d'un navire sur cinq perdu).

## 3. Coupures AIS (`sql/06_coupures.sql`)

Une coupure est un silence d'au moins **2 heures** entre deux positions d'un même navire. Un navire de classe A émet au moins toutes les 3 minutes, même à quai : 2 heures représentent plus de 40 émissions manquées.

Le principe : n'appeler « inexpliquée » une coupure qu'après avoir écarté toutes les explications ordinaires. Chaque coupure reçoit la première catégorie qui s'applique :

| # | Catégorie | Règle |
|---|---|---|
| 1 | Position incohérente | Le navire réapparaît à plus de 5 milles avec une vitesse implicite de plus de 30 nœuds : position fausse ou MMSI partagé, traité avec les anomalies d'identité. |
| 2 | Navire de servitude ou d'État | Pilotes, remorqueurs, sauvetage, autorités. La convention SOLAS dispense les navires d'État, et couper l'AIS entre deux missions est courant pour les pilotes. |
| 3 | Sortie de la zone | Début ou fin à moins de 10 km du bord de la zone d'étude, ou à moins de 5 km de l'entrée du canal de Kiel. |
| 4 | Navigation intérieure ou portuaire | Début ou fin à terre au 1:1 000 000 : canal de Kiel, fleuves, bassins portuaires, où la réception est hachée. |
| 5 | Arrêt au port ou au mouillage | Immobile aux deux bouts (moins d'un mille, moins de 3 nœuds) et dans un abri : bande côtière de 3 km ou zone de mouillage. |
| 6 | Réception insuffisante probable | Moins de 80 % du trajet supposé (un point tous les 2 km) en maille bien couverte, **ou** le réseau ne recevait pas les autres navires du voisinage pendant au moins 20 % du silence. Ce second test place un échantillon par heure sur le trajet et cherche au moins deux navires reçus dans la même heure, dans la maille de résolution 5 ou ses six voisines (≈ 1 750 km²). |
| 7 | Escale ou détour côtier possible | Début ou fin dans un abri, sans transit cohérent (voir ci-dessous). |
| 8 | Sortie de couverture possible | Sans transit cohérent, et le navire avait le temps d'aller jusqu'à une zone mal couverte, au bord de la zone ou au canal de Kiel, puis d'en revenir, à la plus grande de ses vitesses déclarées et au moins 12 nœuds. |
| 9 | **Coupure inexpliquée** | Aucune des explications précédentes ne tient. |

**Transit cohérent** : le navire a poursuivi sa route pendant le silence. Sa vitesse implicite est comprise entre la moitié et une fois et demie sa vitesse déclarée, d'au moins 5 nœuds. Un tel navire a traversé des eaux où le réseau recevait ses voisins : les explications 7 et 8 ne s'appliquent pas à lui, même s'il partait d'un port.

Les coupures inexpliquées portent une **nature** : transit silencieux, arrêt en mer, ou autre.

« Inexpliquée » ne veut pas dire « illicite » : panne d'émetteur, antenne mal placée, maintenance ou extinction volontaire restent possibles. C'est précisément le cas où une détection indépendante de l'AIS (radiofréquence, radar satellite) apporte l'information manquante.

## 4. Anomalies d'identité (`sql/07_identite.sql`)

- **Saut de position** : deux positions à moins de 30 minutes d'intervalle, distantes de plus de 2 milles, avec une vitesse implicite de plus de 50 nœuds. Aucun navire de commerce n'en est capable. Trois sauts ou plus pour un même MMSI : erreur isolée peu probable (MMSI partagé par deux navires, ou position falsifiée).
- **Identité variable** : plusieurs noms, IMO ou types déclarés dans la semaine (au moins 10 messages chacun).
- **IMO douteux** : cargo ou pétrolier sans IMO valide (les petits navires à passagers en sont souvent dépourvus en toute légalité).

## 5. Stationnements au-dessus des infrastructures (`sql/08_infrastructures.sql`)

Un épisode est une suite de positions d'un navire à moins de 2 nœuds, à moins de 750 m d'un câble ou d'un pipeline, d'au moins 30 minutes (une interruption de plus de 15 minutes clôt l'épisode). Sont exclus la bande côtière de 3 km, les zones de mouillage, un rayon d'un kilomètre autour des parcs éoliens, où les navires de maintenance travaillent, et les navires de servitude (pose et réparation de câbles, remorqueurs, autorités), dont la présence au-dessus des câbles est normale.

Le tampon de 750 m tient compte de l'imprécision des tracés publics. Le seuil de 2 nœuds correspond à un navire arrêté ou dérivant, ancre mouillée ou non : c'est la configuration de la plupart des avaries de câbles connues en mer Baltique (ancre qui traîne au-dessus d'un câble).

## 6. Rencontres en mer (`sql/09_rencontres.sql`)

Deux navires à moins de 500 m l'un de l'autre, tous deux à moins de 2 nœuds, hors abri, pendant au moins 2 heures. Le calcul se fait sur une position par navire et par tranche de 10 minutes ; une interruption de plus de 30 minutes sépare deux rencontres. La méthode s'inspire des travaux de Global Fishing Watch sur les transbordements (Miller et al., 2018). Les navires de servitude (remorqueurs, pilotes, sauvetage, autorités) sont exclus : se rapprocher d'autres navires est leur métier.

## 7. Indice de vigilance (`sql/10_score.sql`)

Pour chaque maille H3 de résolution 5 (≈ 250 km²) qui totalise au moins 50 heures-navire et 10 navires dans la semaine :

1. chaque signal (coupures inexpliquées, sauts de position, stationnements sur infrastructure, rencontres) est compté en **navires distincts** et rapporté au nombre de navires passés dans la maille. Un navire qui saute trente fois compte une fois ; sans normalisation, la carte ne montrerait que les routes les plus fréquentées ;
2. chaque part est convertie en rang centile parmi les mailles où elle est non nulle, ramené entre 0,1 et 1 (0 si le signal est absent) ;
3. l'indice est la moyenne des quatre, de 0 à 100. La table donne aussi le nombre de signaux présents (0 à 4), plus simple à lire sur une carte.

Le rang centile rend l'indice insensible aux valeurs extrêmes et lisible (« cette maille est dans les 10 % les plus marquées pour ce signal »). L'indice est un outil de tri : il dit où regarder en premier, pas ce qui s'y est passé.

## 8. Contrôle indépendant par radar satellitaire (`08_sar_gfw.py`, `sql/12_sar.sql`)

Le radar Sentinel-1 voit les navires, qu'ils émettent ou non. Global Fishing Watch publie ses détections et les rapproche de l'AIS mondial (stations côtières et satellites) : une détection « non appariée » est un navire vu par le radar sans émission AIS correspondante. Les détections sont récupérées par l'API 4Wings (jeu `public-global-sar-presence`, mailles de 0,01°, résolution horaire) sur l'aire et la semaine d'étude.

**Instant du passage.** L'API date les détections à l'heure près ; un navire à 12 nœuds parcourt 22 km en une heure. Pour un navire détecté une seule fois dans la semaine, l'horodatage d'entrée égale celui de sortie : c'est l'instant de l'image. Dans un même passage, ces instants tiennent en moins de deux minutes, et leur médiane date tout le passage à la minute près.

**Validation de la couverture.** Pour chaque navire vu au radar et identifié par Global Fishing Watch, présent dans nos données de classe A, on vérifie si le réseau danois l'a reçu à 5 minutes et 3 km près de l'instant de l'image. La part reçue, par classe de couverture, contrôle la carte de couverture avec une source qui ne doit rien à l'AIS côtier.

**Détections sans AIS.** Chacune reçoit la première catégorie qui s'applique :

1. structure fixe probable : à moins d'un kilomètre d'un parc éolien ;
2. navire en silence AIS à cet instant : à moins de 5 km de la position supposée d'un navire en silence (interpolée sur son trajet) ;
3. navire AIS danois à moins de 1,5 km : un navire de classe A était reçu tout près au même instant ;
4. eaux mal couvertes par le réseau côtier ;
5. radar seul, eaux bien couvertes.

Limites : Sentinel-1 ne voit pas bien les navires de moins de 15 à 20 m, qui ne sont souvent pas tenus d'émettre en AIS ; chaque zone n'est imagée que tous les quelques jours ; l'API ne donne pas l'emprise des images, si bien qu'une absence de détection ne prouve rien.

## 9. Confidentialité

Les livrables publics (cartes, fiche de zone, page web) n'affichent que des agrégats par maille ou par zone, et des navires pseudonymisés (empreinte du MMSI salée, le sel restant sur le poste). Aucun navire n'est présenté comme fautif : les indicateurs signalent des écarts au comportement attendu, pas des infractions.
