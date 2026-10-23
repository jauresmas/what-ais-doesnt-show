-- Coupures AIS : silence d'au moins :seuil_coupure entre deux positions d'un même navire
--
-- Une coupure n'est dite « inexpliquée » qu'après avoir écarté toutes les explications
-- ordinaires. Catégories, testées dans cet ordre :
--   1. position incohérente          le navire « réapparaît » trop loin pour y être allé
--                                    (plus de 30 nœuds sur plus de 5 milles) : erreur ou MMSI
--                                    partagé, traité avec les anomalies d'identité
--   2. navire de servitude ou d'État pilotes, remorqueurs, autorités : la convention SOLAS
--                                    dispense les navires d'État, et couper l'AIS fait partie
--                                    du métier de certains
--   3. sortie de la zone             début ou fin près du bord de la zone, ou de l'entrée
--                                    du canal de Kiel
--   4. navigation intérieure ou portuaire  début ou fin à terre au 1:1 000 000 : canal de Kiel,
--                                    fleuve, bassin portuaire, où la réception est hachée
--   5. arrêt au port ou au mouillage immobile aux deux bouts (moins d'un mille, moins de
--                                    3 nœuds) et dans un abri
--   6. réception insuffisante probable  moins de 80 % du trajet supposé en maille bien couverte,
--                                    ou, pendant au moins 20 % du silence, le réseau ne recevait
--                                    pas non plus les autres navires du voisinage
--   Le navire a-t-il poursuivi sa route pendant le silence (« transit silencieux » : vitesse
--   implicite entre la moitié et une fois et demie sa vitesse déclarée, d'au moins 5 nœuds) ?
--   Si oui, il a traversé des eaux où le réseau recevait ses voisins : on passe à 9.
--   7. escale ou détour côtier possible  début ou fin dans un abri (bande côtière, mouillage)
--   8. sortie de couverture possible à sa vitesse, le navire avait le temps d'aller jusqu'à une
--                                    zone mesurée comme mal couverte et d'en revenir
--   9. coupure inexpliquée           aucune explication ordinaire ne tient ; la colonne nature
--                                    précise : transit silencieux, arrêt en mer, autre

DROP TABLE IF EXISTS indic.coupure;
CREATE TABLE indic.coupure AS
WITH suite AS (
    SELECT mmsi, ts, statut, sog, geom,
           lead(ts) OVER w AS ts_fin, lead(geom) OVER w AS geom_fin,
           lead(statut) OVER w AS statut_fin, lead(sog) OVER w AS sog_fin
    FROM ais.position
    WINDOW w AS (PARTITION BY mmsi ORDER BY ts)
)
SELECT s.mmsi, n.famille, s.ts AS debut, s.ts_fin AS fin,
       (extract(epoch FROM s.ts_fin - s.ts) / 3600.0)::real AS duree_h,
       s.statut AS statut_debut, s.statut_fin, s.sog AS sog_debut, s.sog_fin,
       s.geom AS geom_debut, s.geom_fin,
       (ST_Distance(s.geom::geography, s.geom_fin::geography) / 1852.0)::real AS distance_nm
FROM suite s
JOIN ais.navire n USING (mmsi)
WHERE s.ts_fin - s.ts >= interval :'seuil_coupure';

ALTER TABLE indic.coupure
    ADD COLUMN id serial PRIMARY KEY,
    ADD COLUMN vitesse_implicite real,
    ADD COLUMN a_l_arret boolean,
    ADD COLUMN pres_du_bord boolean,
    ADD COLUMN sortie_connue boolean,
    ADD COLUMN abri_debut boolean,
    ADD COLUMN abri_fin boolean,
    ADD COLUMN a_terre boolean,
    ADD COLUMN part_couverte real,
    ADD COLUMN transit_coherent boolean,
    ADD COLUMN part_reception real,
    ADD COLUMN distance_fuite_km real,
    ADD COLUMN excursion_possible boolean,
    ADD COLUMN categorie text,
    ADD COLUMN nature text,
    ADD COLUMN trajet geometry(LineString, 4326);

UPDATE indic.coupure c SET
    vitesse_implicite = distance_nm / duree_h,
    a_l_arret = distance_nm < 1 AND coalesce(sog_debut, 0) < 3 AND coalesce(sog_fin, 0) < 3,
    trajet = ST_MakeLine(geom_debut, geom_fin),
    pres_du_bord = EXISTS (
        SELECT 1 FROM ref.bord_zone_3035 b
        WHERE ST_DWithin(ST_Transform(c.geom_debut, 3035), b.geom, :marge_limite_m)
           OR ST_DWithin(ST_Transform(c.geom_fin, 3035), b.geom, :marge_limite_m)),
    sortie_connue = EXISTS (
        SELECT 1 FROM ref.sortie_connue s
        WHERE ST_DWithin(c.geom_debut::geography, s.geom::geography, 5000)
           OR ST_DWithin(c.geom_fin::geography, s.geom::geography, 5000)),
    abri_debut = EXISTS (SELECT 1 FROM ref.abri a WHERE ST_Intersects(c.geom_debut, a.geom)),
    abri_fin = EXISTS (SELECT 1 FROM ref.abri a WHERE ST_Intersects(c.geom_fin, a.geom)),
    a_terre = EXISTS (SELECT 1 FROM ref.terre t
                      WHERE ST_Intersects(c.geom_debut, t.geom) OR ST_Intersects(c.geom_fin, t.geom)),
    transit_coherent = greatest(coalesce(sog_debut, 0), coalesce(sog_fin, 0)) >= 5
        AND distance_nm / duree_h BETWEEN 0.5 * greatest(coalesce(sog_debut, 0), coalesce(sog_fin, 0))
                                      AND 1.5 * greatest(coalesce(sog_debut, 0), coalesce(sog_fin, 0));

-- Test 1 : le trajet supposé (ligne droite, un point tous les 2 km) passe-t-il par des
-- mailles bien couvertes ?
WITH points AS (
    SELECT id, (ST_DumpPoints(ST_Segmentize(trajet::geography, 2000)::geometry)).geom AS g
    FROM indic.coupure
)
UPDATE indic.coupure c SET part_couverte = x.part
FROM (
    SELECT p.id, avg(CASE WHEN cv.bonne THEN 1.0 ELSE 0.0 END) AS part
    FROM points p
    LEFT JOIN indic.couverture cv ON cv.h3 = h3_lat_lng_to_cell(p.g, 6)
    GROUP BY p.id
) x
WHERE x.id = c.id;

-- Test 2 : le réseau recevait-il le voisinage pendant le silence ?
-- Un échantillon par heure de silence, placé sur le trajet supposé ; on y cherche au moins
-- 2 navires reçus dans la même heure, dans la maille de résolution 5 ou ses 6 voisines
-- (≈ 1 750 km²). Deux et non un : dans l'heure du début, le navire lui-même est compté.
WITH echantillons AS (
    SELECT c.id,
           c.debut + (c.fin - c.debut) * ((g.k + 0.5) / n.n) AS t,
           CASE WHEN c.distance_nm > 0.01
                THEN ST_LineInterpolatePoint(c.trajet, (g.k + 0.5) / n.n)
                ELSE c.geom_debut END AS p
    FROM indic.coupure c
    CROSS JOIN LATERAL (SELECT greatest(1, ceil(c.duree_h))::int AS n) n
    CROSS JOIN LATERAL generate_series(0, n.n - 1) AS g(k)
),
controle AS (
    SELECT e.id, EXISTS (
        SELECT 1 FROM indic.reception_horaire r
        WHERE r.heure = date_trunc('hour', e.t)
          AND r.h3 IN (SELECT h3_grid_disk(h3_lat_lng_to_cell(e.p, 5), 1))
          AND r.nb_navires >= 2) AS recu
    FROM echantillons e
)
UPDATE indic.coupure c SET part_reception = x.part
FROM (SELECT id, avg(recu::int) AS part FROM controle GROUP BY id) x
WHERE x.id = c.id;

-- Test 3 : le navire avait-il le temps de sortir de la couverture et d'y revenir ?
-- Distance du début et de la fin à la plus proche zone mal couverte, au bord de la zone
-- d'étude ou à l'entrée du canal de Kiel ; vitesse supposée : la plus grande vitesse déclarée
-- aux deux bouts, et au moins 12 nœuds (vitesse de service courante d'un navire de commerce).
WITH points AS (
    SELECT c.id, ST_Transform(c.geom_debut, 3035) AS p0, ST_Transform(c.geom_fin, 3035) AS p1,
           least(greatest(coalesce(c.sog_debut, 0), coalesce(c.sog_fin, 0), 12), 35) AS vitesse
    FROM indic.coupure c
),
fuites AS (
    SELECT p.id, p.vitesse,
        least(
            (SELECT ST_Distance(z.geom, p.p0) FROM indic.zone_mal_couverte z
             ORDER BY z.geom <-> p.p0 LIMIT 1),
            (SELECT ST_Distance(b.geom, p.p0) FROM ref.bord_zone_3035 b),
            (SELECT ST_Distance(ST_Transform(s.geom, 3035), p.p0) FROM ref.sortie_connue s)
        ) AS d0,
        least(
            (SELECT ST_Distance(z.geom, p.p1) FROM indic.zone_mal_couverte z
             ORDER BY z.geom <-> p.p1 LIMIT 1),
            (SELECT ST_Distance(b.geom, p.p1) FROM ref.bord_zone_3035 b),
            (SELECT ST_Distance(ST_Transform(s.geom, 3035), p.p1) FROM ref.sortie_connue s)
        ) AS d1
    FROM points p
)
UPDATE indic.coupure c SET
    distance_fuite_km = (f.d0 + f.d1) / 1000.0,
    excursion_possible = (f.d0 + f.d1) / (f.vitesse * 1852.0) <= c.duree_h
FROM fuites f
WHERE f.id = c.id;

UPDATE indic.coupure SET categorie = CASE
    WHEN vitesse_implicite > 30 AND distance_nm > 5 THEN 'position incohérente'
    WHEN famille = 'Service & authorities' THEN 'navire de servitude ou d''État'
    WHEN pres_du_bord OR sortie_connue THEN 'sortie de la zone'
    WHEN a_terre THEN 'navigation intérieure ou portuaire'
    WHEN a_l_arret AND abri_debut THEN 'arrêt au port ou au mouillage'
    WHEN part_couverte < 0.8 OR part_reception < 0.8 THEN 'réception insuffisante probable'
    WHEN NOT transit_coherent AND (abri_debut OR abri_fin) THEN 'escale ou détour côtier possible'
    WHEN NOT transit_coherent AND excursion_possible THEN 'sortie de couverture possible'
    ELSE 'coupure inexpliquée' END;

UPDATE indic.coupure SET nature = CASE
    WHEN transit_coherent THEN 'transit silencieux'
    WHEN a_l_arret THEN 'arrêt en mer'
    ELSE 'autre' END
WHERE categorie = 'coupure inexpliquée';

CREATE INDEX ON indic.coupure (mmsi);
CREATE INDEX ON indic.coupure USING gist (geom_debut);
