-- Index posés après le chargement (plus rapide que pendant les COPY)
CREATE INDEX IF NOT EXISTS position_mmsi_ts ON ais.position (mmsi, ts);
CREATE INDEX IF NOT EXISTS position_geom ON ais.position USING gist (geom);
CREATE INDEX IF NOT EXISTS position_ts ON ais.position USING brin (ts);
ANALYZE ais.position;
