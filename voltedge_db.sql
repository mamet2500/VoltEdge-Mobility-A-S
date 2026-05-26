cat > voltedge_db.sql << 'EOF'
CREATE DATABASE IF NOT EXISTS voltedge_monitoring;
USE voltedge_monitoring;

CREATE TABLE IF NOT EXISTS chargers (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    serial_number   VARCHAR(100) NOT NULL UNIQUE,
    model           VARCHAR(100),
    location        VARCHAR(255) NOT NULL,
    status          VARCHAR(50)  NOT NULL DEFAULT 'unknown',
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_serial (serial_number),
    INDEX idx_status (status)
);

CREATE TABLE IF NOT EXISTS connectors (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    charger_id       INT          NOT NULL,
    connector_number INT          NOT NULL,
    type             VARCHAR(50)  NOT NULL DEFAULT 'Type2',
    status           VARCHAR(50)  NOT NULL DEFAULT 'unknown',
    created_at       DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (charger_id) REFERENCES chargers(id) ON DELETE CASCADE,
    INDEX idx_charger (charger_id),
    INDEX idx_status (status)
);

CREATE TABLE IF NOT EXISTS telemetry_readings (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    connector_id INT              NOT NULL,
    ts           DATETIME         DEFAULT CURRENT_TIMESTAMP,
    voltage      DECIMAL(10,2)    NOT NULL,
    current_amp  DECIMAL(10,2)    NOT NULL,
    power_kw     DECIMAL(10,2)    NOT NULL,
    temperature  DECIMAL(10,2),
    status       VARCHAR(50)      NOT NULL,
    error_code   VARCHAR(100),
    FOREIGN KEY (connector_id) REFERENCES connectors(id) ON DELETE CASCADE,
    INDEX idx_connector (connector_id),
    INDEX idx_ts (ts)
);

CREATE TABLE IF NOT EXISTS incidents (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    connector_id INT          NOT NULL,
    fault_code   VARCHAR(100) NOT NULL,
    priority     VARCHAR(50)  NOT NULL DEFAULT 'medium',
    status       VARCHAR(50)  NOT NULL DEFAULT 'open',
    description  TEXT,
    created_at   DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    resolved_at  DATETIME,
    FOREIGN KEY (connector_id) REFERENCES connectors(id) ON DELETE CASCADE,
    INDEX idx_connector (connector_id),
    INDEX idx_status (status)
);

INSERT IGNORE INTO chargers (serial_number, model, location, status) VALUES
    ('CHR-001', 'ABB Terra 24', 'København, Nørreport', 'available'),
    ('CHR-002', 'Zaptec Pro',   'København, Østerbro',  'available'),
    ('CHR-003', 'ABB Terra 24', 'Aarhus, Banegård',     'available');

INSERT IGNORE INTO connectors (charger_id, connector_number, type, status) VALUES
    (1, 1, 'Type2', 'available'),
    (1, 2, 'Type2', 'available'),
    (2, 1, 'CCS',   'available'),
    (3, 1, 'Type2', 'available');
EOF