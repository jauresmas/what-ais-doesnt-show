-- Croisement des détections radar Sentinel-1 (Global Fishing Watch) avec l'AIS danois,
-- la couverture mesurée et les silences AIS.
--
-- Chaque détection est datée à la minute (instant du passage du satellite, 08_sar_gfw.py) et
-- localisée au centre d'une maille de 0,01° (≈ 1,1 km × 0,6 km à cette latitude).

ALTER TABLE indic.sar_detection
    ADD COLUMN classe_couverture text,
    ADD COLUMN dist_ais_m real,          -- navire AIS danois (classe A) le plus proche à ±3 min
    ADD COLUMN recu_par_reseau boolean,  -- appariées : CE navire reçu par le réseau danois à ±5 min
    ADD COLUMN pres_eolien boolean,
    ADD COLUMN dans_abri boolean,
    ADD COLUMN coupure_id integer,
    ADD COLUMN coupure_categorie text,
    ADD COLUMN categorie text;

-- classe de couverture de la maille H3 r6, mêmes règles que la carte (06_export_gpkg.py)
UPDATE indic.sar_detection s SET classe_couverture = x.classe
FROM (
    SELECT d.id, CASE
        WHEN c.h3 IS NULL THEN 'Not enough traffic'
        WHEN c.bonne THEN 'Reliable'
        WHEN c.nb_navires + c.nb_navires_perdus >= 5 AND c.taux_perte > 0.2 THEN 'Poor'
        WHEN c.nb_intervalles < 100 THEN 'Not enough traffic'
        WHEN c.taux_perte > 0.2 OR coalesce(c.taux_reception, 0) < 0.8 THEN 'Poor'
        ELSE 'Degraded' END AS classe
    FROM indic.sar_detection d
    LEFT JOIN indic.couverture c ON c.h3 = h3_lat_lng_to_cell(d.geom, 6)
) x
WHERE x.id = s.id;

-- navire AIS danois le plus proche au moment du passage (filtre grossier en degrés d'abord)
UPDATE indic.sar_detection s SET dist_ais_m = (
    SELECT min(ST_Distance(p.geom::geography, s.geom::geography))
    FROM ais.position p
    WHERE p.ts BETWEEN s.instant - interval '3 minutes' AND s.instant + interval '3 minutes'
      AND ST_DWithin(p.geom, s.geom, 0.05));

-- validation de la couverture : un navire vu au radar et identifié par Global Fishing Watch
-- (MMSI de classe A présent dans nos données) était-il reçu par le réseau danois à cet instant ?
UPDATE indic.sar_detection s SET recu_par_reseau = EXISTS (
    SELECT 1 FROM ais.position p
    WHERE p.mmsi = s.mmsi
      AND p.ts BETWEEN s.instant - interval '5 minutes' AND s.instant + interval '5 minutes'
      AND ST_DWithin(p.geom::geography, s.geom::geography, 3000))
WHERE s.apparie AND s.mmsi IN (SELECT mmsi FROM ais.navire);

UPDATE indic.sar_detection s SET
    pres_eolien = EXISTS (SELECT 1 FROM ref.eolien_tampon e WHERE ST_Intersects(s.geom, e.geom)),
    dans_abri = EXISTS (SELECT 1 FROM ref.abri a WHERE ST_Intersects(s.geom, a.geom));

-- détection sans AIS à moins de 5 km de la position supposée d'un navire en silence AIS au même
-- instant (interpolée sur son trajet) : le radar voit vraisemblablement ce navire silencieux
UPDATE indic.sar_detection s SET coupure_id = x.cid, coupure_categorie = x.categorie
FROM (
    SELECT DISTINCT ON (d.id) d.id, c.id AS cid, c.categorie
    FROM indic.sar_detection d
    JOIN indic.coupure c ON d.instant > c.debut AND d.instant < c.fin
    CROSS JOIN LATERAL (
        SELECT CASE WHEN c.distance_nm > 0.01
                    THEN ST_LineInterpolatePoint(c.trajet, extract(epoch FROM d.instant - c.debut)
                                                       / extract(epoch FROM c.fin - c.debut))
                    ELSE c.geom_debut END AS supposee
    ) i
    WHERE NOT d.apparie
      AND ST_DWithin(i.supposee::geography, d.geom::geography, 5000)
    ORDER BY d.id, ST_Distance(i.supposee::geography, d.geom::geography)
) x
WHERE x.id = s.id;

UPDATE indic.sar_detection SET categorie = CASE
    WHEN pres_eolien THEN 'structure fixe probable (parc éolien)'
    WHEN coupure_id IS NOT NULL THEN 'navire en silence AIS à cet instant'
    WHEN dist_ais_m <= 1500 THEN 'navire AIS danois à moins de 1,5 km'
    WHEN classe_couverture <> 'Reliable' THEN 'eaux mal couvertes par le réseau côtier'
    ELSE 'radar seul, eaux bien couvertes' END
WHERE NOT apparie;

UPDATE indic.sar_detection SET categorie = CASE
    WHEN recu_par_reseau IS NULL THEN 'navire absent de nos données de classe A'
    WHEN recu_par_reseau THEN 'reçu par le réseau danois'
    ELSE 'non reçu par le réseau danois' END
WHERE apparie;
