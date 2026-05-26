import logging
import mysql.connector
from mysql.connector import Error

logger = logging.getLogger(__name__)

class MySQLRepository:
    def __init__(self, host, database, user, password):
        self.host = host
        self.database = database
        self.user = user
        self.password = password

    def _connect(self):
        try:
            conn = mysql.connector.connect(host=self.host, database=self.database, user=self.user, password=self.password)
            if conn.is_connected():
                return conn
        except Error as e:
            logger.error("DB forbindelse fejlede: %s", e)
            return None

    def _execute(self, query, params=None):
        conn = self._connect()
        if not conn: return None
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            logger.error("Query fejlede: %s", e)
            return None
        finally:
            cursor.close(); conn.close()

    def _fetch_all(self, query, params=None):
        conn = self._connect()
        if not conn: return []
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            return cursor.fetchall()
        except Error as e:
            logger.error("Fetch fejlede: %s", e)
            return []
        finally:
            cursor.close(); conn.close()

    def _fetch_one(self, query, params=None):
        conn = self._connect()
        if not conn: return None
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            return cursor.fetchone()
        except Error as e:
            logger.error("Fetch one fejlede: %s", e)
            return None
        finally:
            cursor.close(); conn.close()

    def get_chargers(self):
        return self._fetch_all("SELECT * FROM chargers ORDER BY created_at DESC")

    def get_charger_by_id(self, charger_id):
        return self._fetch_one("SELECT * FROM chargers WHERE id = %s", (charger_id,))

    def update_charger_status(self, charger_id, status):
        self._execute("UPDATE chargers SET status=%s, updated_at=NOW() WHERE id=%s", (status, charger_id))

    def get_connectors_by_charger(self, charger_id):
        return self._fetch_all("SELECT * FROM connectors WHERE charger_id=%s ORDER BY connector_number", (charger_id,))

    def get_connector_by_id(self, connector_id):
        return self._fetch_one("SELECT * FROM connectors WHERE id=%s", (connector_id,))

    def update_connector_status(self, connector_id, status):
        self._execute("UPDATE connectors SET status=%s, updated_at=NOW() WHERE id=%s", (status, connector_id))

    def create_telemetry_reading(self, connector_id, voltage, current_amp, power_kw, temperature, status, error_code):
        return self._execute(
            "INSERT INTO telemetry_readings (connector_id, voltage, current_amp, power_kw, temperature, status, error_code, ts) VALUES (%s,%s,%s,%s,%s,%s,%s,NOW())",
            (connector_id, voltage, current_amp, power_kw, temperature, status, error_code))

    def get_telemetry_by_connector(self, connector_id, limit=50):
        return self._fetch_all("SELECT * FROM telemetry_readings WHERE connector_id=%s ORDER BY ts DESC LIMIT %s", (connector_id, limit))

    def get_all_telemetry(self, limit=200):
        return self._fetch_all("SELECT * FROM telemetry_readings ORDER BY ts DESC LIMIT %s", (limit,))

    def create_incident(self, connector_id, fault_code, priority, description):
        return self._execute(
            "INSERT INTO incidents (connector_id, fault_code, priority, status, description) VALUES (%s,%s,%s,'open',%s)",
            (connector_id, fault_code, priority, description))

    def get_incidents(self, limit=200):
        return self._fetch_all("SELECT * FROM incidents ORDER BY created_at DESC LIMIT %s", (limit,))

    def get_incident_by_id(self, incident_id):
        return self._fetch_one("SELECT * FROM incidents WHERE id=%s", (incident_id,))

    def resolve_incident(self, incident_id):
        self._execute("UPDATE incidents SET status='resolved', resolved_at=NOW(), updated_at=NOW() WHERE id=%s", (incident_id,))

    def get_fault_summary(self):
        return self._fetch_all("""
            SELECT i.fault_code, i.priority, COUNT(*) AS total,
                   SUM(i.status='open') AS open_count, SUM(i.status='resolved') AS resolved_count,
                   ch.serial_number, ch.location
            FROM incidents i
            JOIN connectors c ON i.connector_id=c.id
            JOIN chargers ch ON c.charger_id=ch.id
            GROUP BY i.fault_code, i.priority, ch.serial_number, ch.location
            ORDER BY total DESC""")

    def get_uptime_summary(self):
        return self._fetch_all("""
            SELECT ch.serial_number, ch.location, COUNT(*) AS total_readings,
                   SUM(tr.status IN ('available','occupied')) AS ok_readings,
                   ROUND(100.0*SUM(tr.status IN ('available','occupied'))/COUNT(*),1) AS uptime_pct
            FROM telemetry_readings tr
            JOIN connectors c ON tr.connector_id=c.id
            JOIN chargers ch ON c.charger_id=ch.id
            GROUP BY ch.serial_number, ch.location
            ORDER BY uptime_pct ASC""")
