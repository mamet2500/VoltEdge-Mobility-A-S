-- VoltEdge Monitoring – Database Setup
-- Kør denne fil i MySQL Workbench for at oprette tabellerne

CREATE DATABASE IF NOT EXISTS voltedge_monitoring;
USE voltedge_monitoring;

-- Ladestandere
CREATE TABLE IF NOT EXISTS chargers (
    charger_id   VARCHAR(64)  PRIMARY KEY,
    location_id  VARCHAR(64)  NOT NULL,
    status       ENUM('available','occupied','faulted','offline','unknown')
                 NOT NULL DEFAULT 'unknown',
    last_seen    DATETIME,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Telemetrimålinger fra ladestandere
CREATE TABLE IF NOT EXISTS telemetry (
    id           VARCHAR(36)  PRIMARY KEY,
    charger_id   VARCHAR(64)  NOT NULL,
    connector_id VARCHAR(64)  NOT NULL,
    power_kw     FLOAT        NOT NULL,
    voltage_v    FLOAT        NOT NULL,
    current_a    FLOAT        NOT NULL,
    status       ENUM('available','occupied','faulted','offline','unknown') NOT NULL,
    error_code   VARCHAR(128),
    ts           DATETIME     DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_charger (charger_id),
    INDEX idx_ts (ts)
);

-- Incidents oprettet ved fejldetektion
CREATE TABLE IF NOT EXISTS incidents (
    incident_id  CHAR(36)     PRIMARY KEY,
    charger_id   VARCHAR(64)  NOT NULL,
    connector_id VARCHAR(64)  NOT NULL,
    fault_code   VARCHAR(64),
    priority     ENUM('low','medium','high') NOT NULL DEFAULT 'medium',
    status       ENUM('open','in_progress','resolved') NOT NULL DEFAULT 'open',
    description  TEXT,
    created_at   DATETIME     DEFAULT CURRENT_TIMESTAMP,
    resolved_at  DATETIME,
    INDEX idx_charger (charger_id),
    INDEX idx_status (status)
);

-- Eksempeldata
INSERT IGNORE INTO chargers (charger_id, location_id, status) VALUES
    ('CHR-001', 'LOC-CPH-01', 'available'),
    ('CHR-002', 'LOC-CPH-02', 'available'),
    ('CHR-003', 'LOC-AAR-01', 'available');
