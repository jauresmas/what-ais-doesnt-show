-- Anomalies d'identité
--
-- Saut de position : deux positions à moins de 30 minutes d'intervalle, distantes de plus
-- de 2 milles, avec une vitesse implicite supérieure à :saut_vitesse_nd nœuds. Un navire
-- de commerce n'en est pas capable : soit la position est fausse, soit deux navires
-- émettent sous le même MMSI.

DROP TABLE IF EXISTS indic.saut_position;
CREATE TABLE indic.saut_position AS
WITH suite AS (
    SELECT mmsi, ts, geom, lead(ts) OVER w AS ts_suivant, lead(geom) OVER w AS geom_suivant
    FROM ais.position
    WINDOW w AS (PARTITION BY mmsi ORDER BY ts)
),
candidats AS (
    -- filtre grossier en degrés avant le calcul géodésique, bien plus coûteux
    SELECT * FROM suite
    WHERE ts_suivant - ts <= interval '30 minutes'
      AND ST_Distance(geom, geom_suivant) > 0.03
),
mesures AS (
    SELECT mmsi, ts, ts_suivant, geom, geom_suivant,
           ST_Distance(geom::geography, geom_suivant::geography) / 1852.0 AS distance_nm,
           greatest(extract(epoch FROM ts_suivant - ts), 1) / 3600.0 AS duree_h
    FROM candidats
)
SELECT mmsi, ts, ts_suivant, geom, geom_suivant,
       distance_nm::real, (distance_nm / duree_h)::real AS vitesse_implicite
FROM mesures
WHERE distance_nm > 2 AND distance_nm / duree_h > :saut_vitesse_nd;

ALTER TABLE indic.saut_position ADD COLUMN id serial PRIMARY KEY;
CREATE INDEX ON indic.saut_position (mmsi);

-- Synthèse par navire
DROP TABLE IF EXISTS indic.anomalie_navire;
CREATE TABLE indic.anomalie_navire AS
SELECT n.mmsi, n.famille, n.pavillon, n.imo_statut, n.nb_noms, n.nb_imo, n.nb_types,
       coalesce(s.nb_sauts, 0) AS nb_sauts,
       coalesce(c.nb_coupures_inexpliquees, 0) AS nb_coupures_inexpliquees,
       coalesce(c.heures_inexpliquees, 0) AS heures_inexpliquees,
       -- 3 sauts ou plus : erreur isolée peu probable
       coalesce(s.nb_sauts, 0) >= 3 AS position_incoherente,
       n.nb_noms > 1 OR n.nb_imo > 1 OR n.nb_types > 1 AS identite_variable,
       -- un cargo ou un pétrolier de commerce a un numéro IMO ; les petits navires à passagers
       -- (vedettes, bacs) en sont souvent dépourvus, ils ne sont pas retenus ici
       n.famille IN ('Tanker', 'Cargo') AND n.imo_statut <> 'valide' AS imo_douteux
FROM ais.navire n
LEFT JOIN (SELECT mmsi, count(*) AS nb_sauts FROM indic.saut_position GROUP BY 1) s USING (mmsi)
LEFT JOIN (SELECT mmsi, count(*) AS nb_coupures_inexpliquees, sum(duree_h) AS heures_inexpliquees
           FROM indic.coupure WHERE categorie = 'coupure inexpliquée' GROUP BY 1) c USING (mmsi);

ALTER TABLE indic.anomalie_navire ADD PRIMARY KEY (mmsi);
