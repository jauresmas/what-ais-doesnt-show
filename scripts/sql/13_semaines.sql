-- Plusieurs semaines : récurrence des angles morts et des silences inexpliqués.
-- Tables remplies par 10_semaines.py : semaine.chiffres, semaine.couverture, semaine.inexpliquee.

-- Classe de chaque maille H3 semaine après semaine. Une maille n'est jugée qu'une semaine où le trafic
-- suffit ; un angle mort est « chronique » s'il est mauvais trois semaines sur quatre au moins.
DROP TABLE IF EXISTS semaine.recurrence;
CREATE TABLE semaine.recurrence AS
SELECT h3::h3index AS h3,
       count(*) FILTER (WHERE classe <> 'Not enough traffic') AS nb_jugees,
       count(*) FILTER (WHERE classe = 'Reliable') AS nb_fiables,
       count(*) FILTER (WHERE classe = 'Degraded') AS nb_degradees,
       count(*) FILTER (WHERE classe = 'Poor') AS nb_mauvaises
FROM semaine.couverture
GROUP BY 1;
ALTER TABLE semaine.recurrence ADD PRIMARY KEY (h3);
ALTER TABLE semaine.recurrence ADD COLUMN statut text, ADD COLUMN geom geometry(Polygon, 4326);
UPDATE semaine.recurrence SET
    statut = CASE WHEN nb_mauvaises >= 3 THEN 'Chronic'
                  WHEN nb_mauvaises = 2 THEN 'Recurring'
                  WHEN nb_mauvaises = 1 THEN 'One-off'
                  WHEN nb_jugees >= 2 THEN 'Never poor'
                  ELSE 'Not enough traffic' END,
    geom = h3_cell_to_boundary_geometry(h3);

-- Foyers de silences inexpliqués : mailles H3 de résolution 5 (≈ 250 km²) où un silence inexpliqué
-- commence au moins deux semaines différentes
DROP TABLE IF EXISTS semaine.foyer;
CREATE TABLE semaine.foyer AS
SELECT h3_lat_lng_to_cell(geom, 5) AS h3,
       count(DISTINCT semaine) AS nb_semaines,
       count(*) AS nb_silences,
       count(DISTINCT mmsi) AS nb_navires
FROM semaine.inexpliquee
GROUP BY 1;
ALTER TABLE semaine.foyer ADD COLUMN geom geometry(Polygon, 4326);
UPDATE semaine.foyer SET geom = h3_cell_to_boundary_geometry(h3);
