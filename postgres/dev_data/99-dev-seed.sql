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
SELECT
    'sensor-' || lpad(i::text, 2, '0'),
    38.80 + (i * 0.01),
    -104.80 - (i * 0.01),
    now() - (i || ' days')::interval,
    NULL,
    jsonb_build_object('zone', 'zone-' || (i % 3), 'active', true)
FROM generate_series(1, 10) AS i;

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

-- ---------------------------------------------
-- app.datacenter_info (10 rows)
-- ---------------------------------------------
INSERT INTO app.datacenter_info (
    datacenter_id, lat, long, name, status, description
)
SELECT
    gen_random_uuid(),
    38.80 + (i * 0.02),
    -104.90 + (i * 0.02),
    'dc-' || lpad(i::text, 2, '0'),
    (ARRAY['Planned', 'Under Construction', 'Operational'])[1 + (i % 3)],
    'Dev seed datacenter #' || i
FROM generate_series(1, 10) AS i;