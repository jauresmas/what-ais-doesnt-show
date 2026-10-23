-- Géométries de travail. Les tampons sont calculés en ETRS89-LAEA (EPSG:3035, en mètres),
-- puis ramenés en WGS84 pour profiter de l'index spatial des positions.
-- Toutes sont découpées (ST_Subdivide) : les tests d'intersection restent rapides.

-- Bord de la zone d'étude. ST_Segmentize : en projection, les côtés de l'emprise
-- suivent les parallèles et les méridiens au lieu d'être des segments droits.
DROP TABLE IF EXISTS ref.zone_etude;
CREATE TABLE ref.zone_etude AS
SELECT ST_Segmentize(ST_MakeEnvelope(:ouest, :sud, :est, :nord, 4326), 0.05) AS geom;

DROP TABLE IF EXISTS ref.bord_zone_3035;
CREATE TABLE ref.bord_zone_3035 AS
SELECT ST_Boundary(ST_Transform(geom, 3035)) AS geom FROM ref.zone_etude;

DROP TABLE IF EXISTS ref.terre_3035;
CREATE TABLE ref.terre_3035 AS
SELECT ST_Subdivide(ST_Transform(geom, 3035), 128) AS geom FROM ref.terre;
CREATE INDEX ON ref.terre_3035 USING gist (geom);

-- Abris : bande côtière et mouillages, où un navire arrêté n'a rien d'inhabituel
DROP TABLE IF EXISTS ref.abri;
CREATE TABLE ref.abri AS
WITH u AS (
    SELECT ST_Union(g) AS g FROM (
        SELECT ST_Buffer(ST_SimplifyPreserveTopology(ST_Transform(geom, 3035), 50),
                         :abri_cote_m, 'quad_segs=4') AS g
        FROM ref.terre
        UNION ALL
        SELECT ST_Transform(geom, 3035) FROM ref.mouillage
    ) x
)
SELECT ST_Subdivide(ST_Transform(g, 4326), 128) AS geom FROM u;
CREATE INDEX ON ref.abri USING gist (geom);

-- Tampons autour des câbles et pipelines, un par tracé pour savoir lequel est concerné
DROP TABLE IF EXISTS ref.infra_tampon;
CREATE TABLE ref.infra_tampon AS
SELECT id AS infra_id,
       ST_Subdivide(ST_Transform(ST_Buffer(ST_Transform(geom, 3035), :tampon_infra_m,
                                           'quad_segs=4'), 4326), 128) AS geom
FROM ref.infrastructure;
CREATE INDEX ON ref.infra_tampon USING gist (geom);

DROP TABLE IF EXISTS ref.eolien_tampon;
CREATE TABLE ref.eolien_tampon AS
SELECT ST_Subdivide(ST_Transform(ST_Buffer(ST_Transform(geom, 3035), :tampon_eolien_m,
                                           'quad_segs=4'), 4326), 128) AS geom
FROM ref.parc_eolien;
CREATE INDEX ON ref.eolien_tampon USING gist (geom);

-- Entrée du canal de Kiel (écluses de Holtenau) : un navire qui s'y engage sort de la
-- couverture et réapparaît en mer du Nord, ce n'est pas une coupure suspecte
DROP TABLE IF EXISTS ref.sortie_connue;
CREATE TABLE ref.sortie_connue AS
SELECT 'Kiel Canal (Holtenau locks)'::text AS nom,
       ST_SetSRID(ST_MakePoint(10.145, 54.365), 4326) AS geom;
