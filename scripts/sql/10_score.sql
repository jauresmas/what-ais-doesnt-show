-- Indice de vigilance par maille H3 de résolution 5 (≈ 250 km²)
--
-- Quatre signaux, comptés en navires distincts (un navire qui saute 30 fois compte une fois)
-- et rapportés au nombre de navires passés dans la maille : sans cette normalisation, la carte
-- ne montrerait que les routes les plus fréquentées.
--   coupures inexpliquées (maille du début et maille de la fin)
--   sauts de position
--   stationnements au-dessus d'une infrastructure
--   rencontres en mer (les deux navires)
-- Chaque part est convertie en rang centile parmi les mailles où elle est non nulle, ramené
-- entre 0,1 et 1 (0 si le signal est absent) ; l'indice est la moyenne des quatre, de 0 à 100.
-- C'est un outil de tri : il dit où regarder en premier, pas ce qui s'y est passé.

DROP TABLE IF EXISTS indic.score;
CREATE TABLE indic.score AS
WITH trafic AS (
    -- une position par minute au plus : 60 positions = 1 heure-navire au maximum
    SELECT h3_lat_lng_to_cell(geom, 5) AS h3, count(*) / 60.0 AS heures_navire,
           count(DISTINCT mmsi) AS nb_navires
    FROM ais.position
    GROUP BY 1
),
coupures AS (
    SELECT h3, count(DISTINCT mmsi) AS n FROM (
        SELECT mmsi, h3_lat_lng_to_cell(geom_debut, 5) AS h3
        FROM indic.coupure WHERE categorie = 'coupure inexpliquée'
        UNION ALL
        SELECT mmsi, h3_lat_lng_to_cell(geom_fin, 5)
        FROM indic.coupure WHERE categorie = 'coupure inexpliquée'
    ) x GROUP BY h3
),
sauts AS (
    SELECT h3_lat_lng_to_cell(geom, 5) AS h3, count(DISTINCT mmsi) AS n
    FROM indic.saut_position GROUP BY 1
),
stationnements AS (
    SELECT h3_lat_lng_to_cell(geom, 5) AS h3, count(DISTINCT mmsi) AS n
    FROM indic.stationnement_infra GROUP BY 1
),
rencontres AS (
    SELECT h3, count(DISTINCT mmsi) AS n FROM (
        SELECT h3_lat_lng_to_cell(geom, 5) AS h3, mmsi_a AS mmsi FROM indic.rencontre
        UNION ALL
        SELECT h3_lat_lng_to_cell(geom, 5), mmsi_b FROM indic.rencontre
    ) x GROUP BY h3
),
parts AS (
    SELECT t.h3, t.heures_navire, t.nb_navires,
           coalesce(c.n, 0) AS nav_coupures, coalesce(s.n, 0) AS nav_sauts,
           coalesce(st.n, 0) AS nav_stationnements, coalesce(r.n, 0) AS nav_rencontres,
           coalesce(c.n, 0)::real / t.nb_navires AS part_coupures,
           coalesce(s.n, 0)::real / t.nb_navires AS part_sauts,
           coalesce(st.n, 0)::real / t.nb_navires AS part_stationnements,
           coalesce(r.n, 0)::real / t.nb_navires AS part_rencontres
    FROM trafic t
    LEFT JOIN coupures c USING (h3)
    LEFT JOIN sauts s USING (h3)
    LEFT JOIN stationnements st USING (h3)
    LEFT JOIN rencontres r USING (h3)
    -- trop peu de trafic pour juger : moins de 50 heures-navire ou de 10 navires dans la semaine
    WHERE t.heures_navire >= 50 AND t.nb_navires >= 10
),
rangs AS (
    SELECT *,
        CASE WHEN part_coupures > 0 THEN percent_rank() OVER (
            PARTITION BY part_coupures > 0 ORDER BY part_coupures) END AS r_coupures,
        CASE WHEN part_sauts > 0 THEN percent_rank() OVER (
            PARTITION BY part_sauts > 0 ORDER BY part_sauts) END AS r_sauts,
        CASE WHEN part_stationnements > 0 THEN percent_rank() OVER (
            PARTITION BY part_stationnements > 0 ORDER BY part_stationnements) END
            AS r_stationnements,
        CASE WHEN part_rencontres > 0 THEN percent_rank() OVER (
            PARTITION BY part_rencontres > 0 ORDER BY part_rencontres) END AS r_rencontres
    FROM parts
)
SELECT h3, heures_navire::real, nb_navires,
       nav_coupures, nav_sauts, nav_stationnements, nav_rencontres,
       part_coupures, part_sauts, part_stationnements, part_rencontres,
       (part_coupures > 0)::int + (part_sauts > 0)::int + (part_stationnements > 0)::int
           + (part_rencontres > 0)::int AS nb_signaux,
       -- un signal présent vaut au moins 0,1, même au plus bas du classement
       (100 * (coalesce(0.1 + 0.9 * r_coupures, 0) + coalesce(0.1 + 0.9 * r_sauts, 0)
             + coalesce(0.1 + 0.9 * r_stationnements, 0) + coalesce(0.1 + 0.9 * r_rencontres, 0))
        / 4)::real AS indice,
       h3_cell_to_boundary_geometry(h3) AS geom
FROM rangs;

ALTER TABLE indic.score ADD PRIMARY KEY (h3);
CREATE INDEX ON indic.score USING gist (geom);
