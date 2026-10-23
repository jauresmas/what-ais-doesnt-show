-- Stationnements au-dessus des infrastructures sous-marines
--
-- Navire à moins de :vitesse_lente_nd nœuds, à moins de :tampon_infra_m m d'un câble ou d'un
-- pipeline, hors bande côtière, hors mouillage et hors parc éolien (navires de maintenance),
-- pendant au moins :duree_stationnement. Les navires de servitude (pose et réparation de câbles,
-- remorqueurs, autorités) sont exclus : leur présence y est normale. Une ancre qui traîne au-dessus d'un câble
-- est la première cause d'avarie connue en mer Baltique : ces épisodes méritent un regard,
-- sans rien présumer de l'intention.

DROP TABLE IF EXISTS indic.stationnement_infra;
CREATE TABLE indic.stationnement_infra AS
WITH lentes AS (
    SELECT DISTINCT ON (p.mmsi, p.ts) p.mmsi, p.ts, p.sog, p.statut, p.geom, t.infra_id
    FROM ais.position p
    JOIN ais.navire n USING (mmsi)
    JOIN ref.infra_tampon t ON ST_Intersects(p.geom, t.geom)
    WHERE p.sog < :vitesse_lente_nd
      AND n.famille <> 'Service & authorities'
      AND NOT EXISTS (SELECT 1 FROM ref.abri a WHERE ST_Intersects(p.geom, a.geom))
      AND NOT EXISTS (SELECT 1 FROM ref.eolien_tampon e WHERE ST_Intersects(p.geom, e.geom))
    ORDER BY p.mmsi, p.ts, t.infra_id
),
ruptures AS (
    -- un nouvel épisode commence après 15 minutes sans position lente
    SELECT *, CASE WHEN ts - lag(ts) OVER (PARTITION BY mmsi ORDER BY ts)
                        <= interval '15 minutes' THEN 0 ELSE 1 END AS nouveau
    FROM lentes
),
episodes AS (
    SELECT *, sum(nouveau) OVER (PARTITION BY mmsi ORDER BY ts) AS episode
    FROM ruptures
)
SELECT mmsi, episode, min(ts) AS debut, max(ts) AS fin,
       (extract(epoch FROM max(ts) - min(ts)) / 3600.0)::real AS duree_h,
       count(*) AS nb_positions,
       mode() WITHIN GROUP (ORDER BY infra_id) AS infra_id,
       mode() WITHIN GROUP (ORDER BY statut) AS statut,
       max(sog) AS sog_max,
       ST_Centroid(ST_Collect(geom)) AS geom
FROM episodes
GROUP BY mmsi, episode
HAVING max(ts) - min(ts) >= interval :'duree_stationnement';

ALTER TABLE indic.stationnement_infra ADD COLUMN id serial PRIMARY KEY,
    ADD COLUMN distance_min_m real;
UPDATE indic.stationnement_infra s SET distance_min_m = (
    SELECT ST_Distance(ST_Transform(s.geom, 3035), ST_Transform(i.geom, 3035))
    FROM ref.infrastructure i WHERE i.id = s.infra_id);
