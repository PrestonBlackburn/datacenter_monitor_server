CREATE SCHEMA app;

GRANT ALL PRIVILEGES ON DATABASE sensors TO admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO admin;

create table if not exists app.audio_sensor (
    received_time    timestamptz not null,
    sensor_id        text not null,
    hz_4000_dbfs     DOUBLE PRECISION,
    hz_1000_dbfs     DOUBLE PRECISION,
    hz_440_dbfs      DOUBLE PRECISION,
    hz_110_dbfs      DOUBLE PRECISION
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
    object           JSONB
);
comment on table app.audio_sensor_errors is 'unparsable message tracking';

create table if not exists app.audio_sensor_info (
    sensor_id       text not null,
    created_time    timestamptz not null,
    lat             DOUBLE PRECISION,
    long            DOUBLE PRECISION,
    geo_time_start  timestamptz,
    geo_time_stop   timestamptz,
    object          JSONB
);
comment on table app.audio_sensor_info is 'metadata for individual sensors';
COMMENT ON COLUMN app.audio_sensor_info.geo_time_start IS 'time that geo coordinates are effective from';
COMMENT ON COLUMN app.audio_sensor_info.geo_time_stop IS 'time that geo coordinates are effective to';