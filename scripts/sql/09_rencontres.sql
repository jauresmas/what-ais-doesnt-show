-- Rencontres en mer : deux navires à moins de :distance_rencontre_m m l'un de l'autre,
-- tous deux à moins de :vitesse_lente_nd nœuds, hors abri, pendant au moins :duree_rencontre.
-- Méthode inspirée de Global Fishing Watch (Miller et al., 2018, transbordements en mer).
-- Les navires de servitude (remorqueurs, pilotes, sauvetage, autorités) sont exclus :
-- leurs rencontres sont leur métier.

-- Une position par navire et par tranche de 10 minutes
DROP TABLE IF EXISTS lent10;
CREATE TEMP TABLE lent10 AS
SELECT DISTINCT ON (p.mmsi, tranche) p.mmsi,
       date_bin('10 minutes', p.ts, timestamp '2000-01-01') AS tranche,
       ST_Transform(p.geom, 3035) AS g
FROM ais.position p
JOIN ais.navire n USING (mmsi)
WHERE p.sog < :vitesse_lente_nd
  AND n.famille <> 'Service & authorities'
  AND NOT EXISTS (SELECT 1 FROM ref.abri a WHERE ST_Intersects(p.geom, a.geom))
ORDER BY p.mmsi, tranche, p.ts;
CREATE INDEX ON lent10 USING gist (g);
CREATE INDEX ON lent10 (tranche);
ANALYZE lent10;

DROP TABLE IF EXISTS paires;
CREATE TEMP TABLE paires AS
SELECT a.mmsi AS mmsi_a, b.mmsi AS mmsi_b, a.tranche,
       ST_Distance(a.g, b.g) AS distance_m,
       ST_Centroid(ST_Collect(a.g, b.g)) AS g
FROM lent10 a
JOIN lent10 b ON b.tranche = a.tranche AND a.mmsi < b.mmsi
             AND ST_DWithin(a.g, b.g, :distance_rencontre_m);

DROP TABLE IF EXISTS indic.rencontre;
CREATE TABLE indic.rencontre AS
WITH ruptures AS (
    -- une interruption de plus de 30 minutes sépare deux rencontres
    SELECT *, CASE WHEN tranche - lag(tranche) OVER w <= interval '30 minutes'
                   THEN 0 ELSE 1 END AS nouveau
    FROM paires
    WINDOW w AS (PARTITION BY mmsi_a, mmsi_b ORDER BY tranche)
),
episodes AS (
    SELECT *, sum(nouveau) OVER (PARTITION BY mmsi_a, mmsi_b ORDER BY tranche) AS episode
    FROM ruptures
)
SELECT mmsi_a, mmsi_b, episode, min(tranche) AS debut,
       max(tranche) + interval '10 minutes' AS fin,
       (extract(epoch FROM max(tranche) + interval '10 minutes' - min(tranche)) / 3600.0)::real
           AS duree_h,
       avg(distance_m)::real AS distance_moyenne_m,
       ST_Transform(ST_Centroid(ST_Collect(g)), 4326) AS geom
FROM episodes
GROUP BY mmsi_a, mmsi_b, episode
HAVING max(tranche) + interval '10 minutes' - min(tranche) >= interval :'duree_rencontre';

ALTER TABLE indic.rencontre ADD COLUMN id serial PRIMARY KEY;
