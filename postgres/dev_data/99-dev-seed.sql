-- ============================================================
-- Dev/test seed data
-- NOT for production. Mount this file into
-- /docker-entrypoint-initdb.d/99-dev-seed.sql for local dev only.
-- Runs once against a fresh (empty) Postgres data volume.
-- ============================================================

-- ---------------------------------------------
-- app.audio_sensor_info (10 sensors, referenced by other tables)
-- ---------------------------------------------
INSERT INTO app.audio_sensor_info (
    sensor_id, lat, long, geo_time_start, geo_time_stop, tags
)
VALUES 
	('sensor-01', 38.89201, -104.859,  now() - (1 || ' days')::interval, NULL, jsonb_build_object('zone', 'zone-1', 'active', true)),
	('sensor-02', 38.89261, -104.85881,  now() - (2 || ' days')::interval, NULL, jsonb_build_object('zone', 'zone-2', 'active', true))
;


-- ---------------------------------------------
-- app.audio_sensor (10 rows, hypertable — spread over the last 10 hours)
-- ---------------------------------------------
INSERT INTO app.audio_sensor (
    received_time, sensor_id, hz, dbfs
)
SELECT
    now() - (i || ' hours')::interval,
    'sensor-' || lpad(i::text, 2, '0'),
    CASE WHEN i <= 5
        THEN 100    -- 100hz range
        ELSE 1000  -- 1000hz range
    END,
    round((-60 + random() * 40)::numeric, 2)
FROM generate_series(1, 10) AS i;


-------- Manual testing (for live data) --------
INSERT INTO app.audio_sensor (
    received_time, sensor_id, hz, dbfs
)
VALUES (
    now(),
    'sensor-01',
    100,
    round((-60 + random() * 40)::numeric, 2)
);
-- ---------------------------------------------
-- app.audio_sensor_errors (10 rows)
-- ---------------------------------------------
INSERT INTO app.audio_sensor_errors (
    created_time, recieved_time, sensor_id, data_b64, tags
)
SELECT
    now() - (i || ' hours')::interval,
    now() - (i || ' hours')::interval - interval '2 seconds',
    'sensor-' || lpad(((i % 10) + 1)::text, 2, '0'),
    encode(('bad-payload-' || i)::bytea, 'base64'),
    jsonb_build_object('error', 'parse_failure', 'code', 400 + i)
FROM generate_series(0, 9) AS i;

