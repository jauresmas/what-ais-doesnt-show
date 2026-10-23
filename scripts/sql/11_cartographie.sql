-- Couches de cartographie : densité de trafic et traces des navires

-- Densité de trafic : heures-navire par maille H3 de résolution 6 (≈ 36 km²)
DROP TABLE IF EXISTS indic.trafic;
CREATE TABLE indic.trafic AS
SELECT h3_lat_lng_to_cell(p.geom, 6) AS h3,
       (count(*) / 60.0)::real AS heures_navire,
       (count(*) FILTER (WHERE n.famille = 'Tanker') / 60.0)::real AS heures_petrolier,
       -- navires en route (3 nœuds et plus) : base de la part du trafic bien couvert
       (count(*) FILTER (WHERE p.sog >= 3) / 60.0)::real AS heures_route,
       count(DISTINCT p.mmsi) AS nb_navires
FROM ais.position p
JOIN ais.navire n USING (mmsi)
GROUP BY 1;
ALTER TABLE indic.trafic ADD PRIMARY KEY (h3);
ALTER TABLE indic.trafic ADD COLUMN geom geometry(Polygon, 4326);
UPDATE indic.trafic SET geom = h3_cell_to_boundary_geometry(h3);

-- Traces : positions reliées dans l'ordre, coupées après 30 minutes de silence ou à un saut
-- impossible (plus de 50 nœuds). Distance approchée en milles (1° de latitude = 60 milles),
-- largement suffisante pour repérer un saut et bien moins coûteuse qu'un calcul géodésique.
DROP TABLE IF EXISTS ais.trace;
CREATE TABLE ais.trace AS
WITH suite AS (
    SELECT mmsi, ts, geom, lon, lat,
           lag(ts) OVER w AS ts_prec, lag(lon) OVER w AS lon_prec, lag(lat) OVER w AS lat_prec
    FROM ais.position
    WINDOW w AS (PARTITION BY mmsi ORDER BY ts)
),
ruptures AS (
    SELECT mmsi, ts, geom,
           CASE WHEN ts_prec IS NULL OR ts - ts_prec > interval '30 minutes'
                  OR 60 * sqrt(power((lon - lon_prec) * cos(radians(lat)), 2) + power(lat - lat_prec, 2))
                     / greatest(extract(epoch FROM ts - ts_prec) / 3600.0, 1 / 60.0) > 50
                THEN 1 ELSE 0 END AS nouveau
    FROM suite
),
segments AS (
    SELECT mmsi, ts, geom, sum(nouveau) OVER (PARTITION BY mmsi ORDER BY ts) AS segment
    FROM ruptures
)
SELECT mmsi, segment, min(ts) AS debut, max(ts) AS fin,
       ST_SimplifyPreserveTopology(ST_MakeLine(geom ORDER BY ts), 0.0003) AS geom
FROM segments
GROUP BY mmsi, segment
HAVING count(*) >= 2;
ALTER TABLE ais.trace ADD COLUMN id serial PRIMARY KEY;
