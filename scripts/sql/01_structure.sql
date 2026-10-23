-- Structure de la base : un schéma par étape de la chaîne
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS h3;
CREATE EXTENSION IF NOT EXISTS h3_postgis CASCADE;

CREATE SCHEMA IF NOT EXISTS ais;      -- positions et navires nettoyés
CREATE SCHEMA IF NOT EXISTS ref;      -- référentiel : zones maritimes, câbles, mouillages
CREATE SCHEMA IF NOT EXISTS indic;    -- indicateurs et score de croisement
CREATE SCHEMA IF NOT EXISTS qualite;  -- bilan du nettoyage, contrôles

-- Statuts de navigation AIS (recommandation UIT-R M.1371)
CREATE TABLE ais.statut (
    code smallint PRIMARY KEY,
    libelle text NOT NULL
);
INSERT INTO ais.statut VALUES
    (0, 'Under way using engine'), (1, 'At anchor'), (2, 'Not under command'),
    (3, 'Restricted maneuverability'), (4, 'Constrained by her draught'), (5, 'Moored'),
    (6, 'Aground'), (7, 'Engaged in fishing'), (8, 'Under way sailing'),
    (9, 'Reserved for future amendment [HSC]'), (10, 'Reserved for future amendment [WIG]'),
    (11, 'Power-driven vessel towing astern'),
    (12, 'Power-driven vessel pushing ahead or towing alongside'),
    (13, 'Reserved for future use'), (14, 'AIS-SART is active'), (15, 'Unknown value');

-- Positions de classe A, une par navire et par minute au plus
CREATE TABLE ais.position (
    mmsi integer NOT NULL,
    ts timestamp NOT NULL,          -- horodatage de la station de base, UTC
    lon double precision NOT NULL,
    lat double precision NOT NULL,
    statut smallint REFERENCES ais.statut,
    sog real,                       -- vitesse fond, nœuds
    cog real,                       -- route fond, degrés
    cap smallint,                   -- cap vrai, degrés
    tirant_eau real,                -- mètres, déclaré par l'équipage
    geom geometry(Point, 4326) GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(lon, lat), 4326)) STORED
);

-- Combinaisons d'identité déclarées par chaque MMSI, avec leur nombre de messages
CREATE TABLE ais.identite_brute (
    jour date NOT NULL,
    mmsi integer NOT NULL,
    nom text, imo text, indicatif text, type_navire text,
    longueur real, largeur real,
    nb_messages integer NOT NULL
);

CREATE TABLE ais.destination_brute (
    jour date NOT NULL,
    mmsi integer NOT NULL,
    destination text,
    premier timestamp, dernier timestamp,
    nb_messages integer NOT NULL
);

-- Stations de base AIS vues dans les données (récepteurs à terre et sur plates-formes)
CREATE TABLE ais.station_brute (
    jour date NOT NULL,
    mmsi integer NOT NULL,
    lon double precision, lat double precision,
    nb_messages integer NOT NULL
);

-- Bilan du nettoyage : lignes écartées par jour et par motif
CREATE TABLE qualite.bilan_nettoyage (
    jour date NOT NULL,
    etape smallint NOT NULL,
    motif text NOT NULL,
    nb_lignes bigint NOT NULL,
    PRIMARY KEY (jour, etape, motif)
);
