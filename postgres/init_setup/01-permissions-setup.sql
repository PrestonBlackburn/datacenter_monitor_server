CREATE SCHEMA app;

GRANT ALL PRIVILEGES ON DATABASE sensors TO admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO admin;

create table if not exists app.audio_sensor (
    created_time     timestamptz,
    recieved_time    timestamptz,
    device_model     text,
    hz_4000_dbfs     real,
    hz_1000_dbfs     real,
    hz_440_dbfs      real,
    hz_110_dbfs      real
);
comment on table app.audio_sensor is 'test audio sensors';
