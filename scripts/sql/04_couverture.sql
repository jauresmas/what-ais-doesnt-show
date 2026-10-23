-- Couverture AIS empirique, sur une maille H3 de résolution 6 (≈ 36 km²)
--
-- Un navire de classe A en route émet toutes les 2 à 10 secondes. Après l'allègement
-- à une position par minute, deux positions consécutives d'un navire en route sont donc
-- espacées d'une minute là où la réception est bonne. Le taux de réception d'une maille
-- est la part des intervalles de 3 minutes au plus, pour les navires à plus de 3 nœuds.
-- C'est la réception réelle du réseau, mesurée par le trafic lui-même.

DROP TABLE IF EXISTS indic.couverture;
CREATE TABLE indic.couverture AS
WITH suite AS (
    SELECT mmsi, sog, geom, lead(ts) OVER w - ts AS dt
    FROM ais.position
    WINDOW w AS (PARTITION BY mmsi ORDER BY ts)
)
SELECT h3_lat_lng_to_cell(geom, 6) AS h3,
       count(*) AS nb_intervalles,
       count(*) FILTER (WHERE dt <= interval '3 minutes') AS nb_reguliers,
       count(DISTINCT mmsi) AS nb_navires
FROM suite
WHERE sog >= 3 AND dt IS NOT NULL AND dt <= interval '6 hours'
GROUP BY 1;

ALTER TABLE indic.couverture ADD PRIMARY KEY (h3);

-- Navires perdus : le taux de réception ci-dessus ne voit que les navires reçus. Un navire qui
-- traverse une maille sans y être reçu n'y laisse aucune position : biais de sélection. On suit
-- donc le trajet supposé (ligne droite, un point tous les 2 km) de chaque silence de 15 minutes
-- à 6 heures d'un navire en mouvement (3 à 30 nœuds de vitesse implicite), et l'on compte par
-- maille les navires distincts perdus. Compter des navires et non des minutes : un seul navire
-- qui se tait dans une maille fréquentée ne la déclasse pas, il reste repérable.
DROP TABLE IF EXISTS perdus;
CREATE TEMP TABLE perdus AS
WITH suite AS (
    SELECT mmsi, ts, geom, lead(ts) OVER w AS ts_fin, lead(geom) OVER w AS geom_fin
    FROM ais.position
    WINDOW w AS (PARTITION BY mmsi ORDER BY ts)
),
silences AS (
    SELECT mmsi, ST_MakeLine(geom, geom_fin) AS ligne
    FROM suite
    WHERE ts_fin - ts > interval '15 minutes' AND ts_fin - ts <= interval '6 hours'
      AND ST_Distance(geom::geography, geom_fin::geography) / 1852.0
          / (extract(epoch FROM ts_fin - ts) / 3600.0) BETWEEN 3 AND 30
)
SELECT DISTINCT mmsi, h3_lat_lng_to_cell(
           (ST_DumpPoints(ST_Segmentize(ligne::geography, 2000)::geometry)).geom, 6) AS h3
FROM silences;

ALTER TABLE indic.couverture
    ADD COLUMN nb_navires_perdus integer,
    ADD COLUMN taux_perte real,
    ADD COLUMN taux_reception real,
    ADD COLUMN bonne boolean,
    ADD COLUMN geom geometry(Polygon, 4326);

-- les mailles traversées sans aucune réception n'ont pas encore de ligne
INSERT INTO indic.couverture (h3, nb_intervalles, nb_reguliers, nb_navires)
SELECT DISTINCT h3, 0, 0, 0 FROM perdus
WHERE h3 NOT IN (SELECT h3 FROM indic.couverture);

UPDATE indic.couverture c SET nb_navires_perdus = x.n
FROM (SELECT h3, count(*) AS n FROM perdus GROUP BY h3) x
WHERE x.h3 = c.h3;

UPDATE indic.couverture SET
    nb_navires_perdus = coalesce(nb_navires_perdus, 0),
    taux_reception = CASE WHEN nb_intervalles > 0 THEN nb_reguliers::real / nb_intervalles END,
    taux_perte = coalesce(nb_navires_perdus, 0)::real
                 / greatest(nb_navires + coalesce(nb_navires_perdus, 0), 1),
    geom = h3_cell_to_boundary_geometry(h3);

-- bien couverte : assez de trafic pour juger, 9 intervalles sur 10 reçus dans les 3 minutes,
-- et au plus 1 navire attendu sur 10 perdu en la traversant
UPDATE indic.couverture SET bonne =
    nb_intervalles >= 100 AND taux_reception >= 0.9 AND taux_perte <= 0.1;
CREATE INDEX ON indic.couverture USING gist (geom);

-- Réception heure par heure, sur une maille H3 de résolution 5 (≈ 250 km²) :
-- nombre de navires reçus. Sert à vérifier que le réseau recevait bien les autres
-- navires du voisinage pendant qu'un navire se taisait.
DROP TABLE IF EXISTS indic.reception_horaire;
CREATE TABLE indic.reception_horaire AS
SELECT h3_lat_lng_to_cell(geom, 5) AS h3, date_trunc('hour', ts) AS heure,
       count(DISTINCT mmsi) AS nb_navires
FROM ais.position
GROUP BY 1, 2;
ALTER TABLE indic.reception_horaire ADD PRIMARY KEY (h3, heure);

-- Mailles où la réception est mesurée comme mauvaise (moins de 80 % des intervalles reçus
-- dans les 3 minutes, ou plus d'un navire sur 5 perdu) : un navire qui s'y rend sort de la vue
-- du réseau.
-- Les mailles trop peu fréquentées pour être jugées n'y figurent pas : le test de réception
-- heure par heure (06_coupures.sql) couvre ce cas.
DROP TABLE IF EXISTS indic.zone_mal_couverte;
CREATE TABLE indic.zone_mal_couverte AS
SELECT h3, ST_Transform(geom, 3035) AS geom
FROM indic.couverture
WHERE (nb_intervalles >= 30 AND taux_reception < 0.8) OR taux_perte > 0.2;
CREATE INDEX ON indic.zone_mal_couverte USING gist (geom);
