-- Fiche navire : identité la plus déclarée sur la période, pavillon, contrôles d'identité

-- Numéro IMO : 7 chiffres dont le dernier est une clé de contrôle
-- (somme des 6 premiers chiffres pondérés de 7 à 2, modulo 10)
CREATE OR REPLACE FUNCTION ais.imo_valide(imo text) RETURNS boolean
LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE WHEN imo ~ '^[1-9][0-9]{6}$' THEN
        (substr(imo, 1, 1)::int * 7 + substr(imo, 2, 1)::int * 6 + substr(imo, 3, 1)::int * 5
       + substr(imo, 4, 1)::int * 4 + substr(imo, 5, 1)::int * 3 + substr(imo, 6, 1)::int * 2) % 10
        = substr(imo, 7, 1)::int
    ELSE false END
$$;

DROP TABLE IF EXISTS ais.navire CASCADE;
CREATE TABLE ais.navire AS
WITH ident AS (
    SELECT mmsi, coalesce(nom, '') AS nom, coalesce(imo, '') AS imo,
           coalesce(indicatif, '') AS indicatif, coalesce(type_navire, '') AS type_navire,
           longueur, largeur, sum(nb_messages) AS n
    FROM ais.identite_brute
    GROUP BY 1, 2, 3, 4, 5, 6, 7
),
modal AS (
    -- combinaison la plus fréquente, en préférant celles qui portent un nom
    SELECT DISTINCT ON (mmsi) mmsi, nom, imo, indicatif, type_navire, longueur, largeur
    FROM ident
    ORDER BY mmsi, (nom <> '') DESC, n DESC
),
-- une variante ne compte que si elle revient dans au moins 10 messages :
-- un message isolé mal décodé ne fait pas un changement d'identité
noms AS (SELECT mmsi, nom FROM ident WHERE nom <> '' GROUP BY 1, 2 HAVING sum(n) >= 10),
imos AS (SELECT mmsi, imo FROM ident WHERE imo NOT IN ('', '0') GROUP BY 1, 2 HAVING sum(n) >= 10),
types AS (SELECT mmsi, type_navire FROM ident WHERE type_navire <> '' GROUP BY 1, 2 HAVING sum(n) >= 10),
variantes AS (
    SELECT m.mmsi,
           (SELECT count(*) FROM noms x WHERE x.mmsi = m.mmsi) AS nb_noms,
           (SELECT count(*) FROM imos x WHERE x.mmsi = m.mmsi) AS nb_imo,
           (SELECT count(*) FROM types x WHERE x.mmsi = m.mmsi) AS nb_types
    FROM modal m
),
pos AS (
    SELECT mmsi, count(*) AS nb_positions, min(ts) AS premier, max(ts) AS dernier
    FROM ais.position
    GROUP BY mmsi
)
SELECT p.mmsi,
       nullif(m.nom, '') AS nom,
       nullif(m.imo, '') AS imo,
       nullif(m.indicatif, '') AS indicatif,
       coalesce(nullif(m.type_navire, ''), 'Undefined') AS type_navire,
       m.longueur, m.largeur,
       p.mmsi / 1000000 AS mid,
       coalesce(f.pays, 'Unknown') AS pavillon,
       CASE WHEN m.imo IN ('', '0') OR m.imo IS NULL THEN 'non renseigné'
            WHEN ais.imo_valide(m.imo) THEN 'valide'
            ELSE 'invalide' END AS imo_statut,
       coalesce(v.nb_noms, 0) AS nb_noms,
       coalesce(v.nb_imo, 0) AS nb_imo,
       coalesce(v.nb_types, 0) AS nb_types,
       p.nb_positions, p.premier, p.dernier
FROM pos p
LEFT JOIN modal m USING (mmsi)
LEFT JOIN variantes v USING (mmsi)
LEFT JOIN ref.mid f ON f.mid = p.mmsi / 1000000;

ALTER TABLE ais.navire ADD PRIMARY KEY (mmsi);

-- Familles de navires pour les cartes et la fiche de synthèse
ALTER TABLE ais.navire ADD COLUMN famille text;
UPDATE ais.navire SET famille = CASE
    WHEN type_navire = 'Tanker' THEN 'Tanker'
    WHEN type_navire = 'Cargo' THEN 'Cargo'
    WHEN type_navire IN ('Passenger', 'HSC') THEN 'Passenger'
    WHEN type_navire = 'Fishing' THEN 'Fishing'
    WHEN type_navire IN ('Tug', 'Towing', 'Towing long/wide', 'Pilot', 'SAR', 'Port tender',
                         'Law enforcement', 'Dredging', 'Diving', 'Military', 'Medical',
                         'Anti-pollution') THEN 'Service & authorities'
    ELSE 'Other / unknown' END;

-- Stations de base vues dans les données
DROP TABLE IF EXISTS ais.station;
CREATE TABLE ais.station AS
SELECT mmsi, percentile_cont(0.5) WITHIN GROUP (ORDER BY lon) AS lon,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY lat) AS lat,
       sum(nb_messages) AS nb_messages
FROM ais.station_brute
GROUP BY mmsi;
ALTER TABLE ais.station ADD COLUMN geom geometry(Point, 4326);
UPDATE ais.station SET geom = ST_SetSRID(ST_MakePoint(lon, lat), 4326);
