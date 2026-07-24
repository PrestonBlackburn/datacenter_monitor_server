CREATE SCHEMA app;

GRANT ALL PRIVILEGES ON DATABASE sensors TO admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO admin;

-- automatic timestamping
CREATE OR REPLACE FUNCTION app.set_updated_time()
RETURNS trigger AS $$
BEGIN
    NEW.updated_time := now();
    NEW.created_time := OLD.created_time;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;



create table if not exists app.audio_sensor (
    received_time    timestamptz not null,
    sensor_id        text not null,
    hz               DOUBLE PRECISION,
    dbfs             DOUBLE PRECISION
) WITH (
    tsdb.hypertable,
    tsdb.segmentby = 'sensor_id',
    tsdb.partition_column = 'received_time'
);
comment on table app.audio_sensor is 'test audio sensors';
COMMENT ON COLUMN app.audio_sensor.received_time is 'The message received timestamp from chirpstack';
CREATE INDEX idx_audio_sensor_id_time ON app.audio_sensor (sensor_id, received_time DESC);


create table if not exists app.audio_sensor_errors (
    created_time     timestamptz not null,
    recieved_time    timestamptz not null,
    sensor_id        text not null,
    data_b64         text,
    tags             JSONB
);
comment on table app.audio_sensor_errors is 'unparsable message tracking';

create table if not exists app.audio_sensor_info (
    sensor_id       text not null,
    created_time    timestamptz not null default now(),
    updated_time    timestamptz not null default now(),
    lat             DOUBLE PRECISION,
    long            DOUBLE PRECISION,
    geo_time_start  timestamptz,
    geo_time_stop   timestamptz,
    tags            JSONB
);
comment on table app.audio_sensor_info is 'metadata for individual sensors';
COMMENT ON COLUMN app.audio_sensor_info.geo_time_start IS 'time that geo coordinates are effective from';
COMMENT ON COLUMN app.audio_sensor_info.geo_time_stop IS 'time that geo coordinates are effective to';

CREATE TRIGGER trg_audio_sensor_info_updated
    BEFORE UPDATE ON app.audio_sensor_info
    FOR EACH ROW
    EXECUTE FUNCTION app.set_updated_time();


create table if not exists app.datacenter_info (
    datacenter_id   text not null,
    created_time    timestamptz not null default now(),
    updated_time    timestamptz not null default now(),
    lat             DOUBLE PRECISION,
    long            DOUBLE PRECISION,
    name            text,
    status          text,
    description     text
);

CREATE TRIGGER trg_datacenter_info_updated
    BEFORE UPDATE ON app.datacenter_info
    FOR EACH ROW
    EXECUTE FUNCTION app.set_updated_time();


---- Prepoulaed data -----
INSERT INTO app.datacenter_info (
    datacenter_id,
    lat,
    long,
    name,
    status,
    description
)
VALUES (
    gen_random_uuid(),
    38.894605, 
    -104.858710,
    'Taurus',
    'Planned',
    '50 MW capacity data center by California-based developer Raeden'
);
