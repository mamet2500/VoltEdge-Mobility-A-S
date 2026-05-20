# MySQL repository for handling chargers, telemetry and incidents
import mysql.connector
from mysql.connector import Error
import os
import uuid
from dotenv import load_dotenv

load_dotenv()


class MySQLRepository:
    def __init__(self, host, database, user, password):
        self.host = host
        self.database = database
        self.user = user
        self.password = password

    def connect(self):
        try:
            connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            if connection.is_connected():
                return connection
        except Error as e:
            print(f"Error while connecting to MySQL: {e}")
            return None

    def execute_query(self, query, params=None):
        connection = self.connect()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, params)
                connection.commit()
                return cursor.lastrowid
            except Error as e:
                print(f"Error while executing query: {e}")
                return None
            finally:
                cursor.close()
                connection.close()
        return None

    def fetch_all(self, query, params=None):
        connection = self.connect()
        if connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(query, params)
                return cursor.fetchall()
            except Error as e:
                print(f"Error while fetching data: {e}")
                return []
            finally:
                cursor.close()
                connection.close()
        return []

    def fetch_one(self, query, params=None):
        connection = self.connect()
        if connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(query, params)
                return cursor.fetchone()
            except Error as e:
                print(f"Error while fetching data: {e}")
                return None
            finally:
                cursor.close()
                connection.close()
        return None

    # ------------------------------------------------------------------
    # Chargers
    # ------------------------------------------------------------------

    def create_charger(self, charger_id, location_id, status):
        query = """
            INSERT INTO chargers (charger_id, location_id, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = %s, last_seen = NOW()
        """
        return self.execute_query(query, (charger_id, location_id, status, status))

    def get_chargers(self):
        query = "SELECT * FROM chargers ORDER BY created_at DESC"
        return self.fetch_all(query)

    def get_charger_by_id(self, charger_id):
        query = "SELECT * FROM chargers WHERE charger_id = %s"
        return self.fetch_one(query, (charger_id,))

    # ------------------------------------------------------------------
    # Telemetry
    # ------------------------------------------------------------------

    def create_telemetry(self, charger_id, connector_id, power_kw,
                         voltage_v, current_a, status, error_code):
        record_id = str(uuid.uuid4())
        query = """
            INSERT INTO telemetry
                (id, charger_id, connector_id, power_kw, voltage_v,
                 current_a, status, error_code, ts)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        self.execute_query(query, (
            record_id, charger_id, connector_id,
            power_kw, voltage_v, current_a,
            status, error_code
        ))
        return record_id

    def get_telemetry_by_charger(self, charger_id, limit=50):
        query = """
            SELECT * FROM telemetry
            WHERE charger_id = %s
            ORDER BY ts DESC
            LIMIT %s
        """
        return self.fetch_all(query, (charger_id, limit))

    def get_telemetry(self):
        query = "SELECT * FROM telemetry ORDER BY ts DESC LIMIT 200"
        return self.fetch_all(query)

    # ------------------------------------------------------------------
    # Incidents
    # ------------------------------------------------------------------

    def create_incident(self, incident_id, charger_id, connector_id,
                        fault_code, priority, description):
        query = """
            INSERT INTO incidents
                (incident_id, charger_id, connector_id, fault_code,
                 priority, status, description)
            VALUES (%s, %s, %s, %s, %s, 'open', %s)
        """
        return self.execute_query(query, (
            incident_id, charger_id, connector_id,
            fault_code, priority, description
        ))

    def get_incidents(self):
        query = "SELECT * FROM incidents ORDER BY created_at DESC LIMIT 200"
        return self.fetch_all(query)

    def get_incident_by_id(self, incident_id):
        query = "SELECT * FROM incidents WHERE incident_id = %s"
        return self.fetch_one(query, (incident_id,))

    def resolve_incident(self, incident_id):
        query = """
            UPDATE incidents
            SET status = 'resolved', resolved_at = NOW()
            WHERE incident_id = %s
        """
        self.execute_query(query, (incident_id,))

    # ------------------------------------------------------------------
    # Analytics (til Power BI)
    # ------------------------------------------------------------------

    def get_fault_summary(self):
        query = """
            SELECT fault_code, priority,
                   COUNT(*) AS total,
                   SUM(status = 'open') AS open_count,
                   SUM(status = 'resolved') AS resolved_count
            FROM incidents
            GROUP BY fault_code, priority
            ORDER BY total DESC
        """
        return self.fetch_all(query)

    def get_uptime_summary(self):
        query = """
            SELECT charger_id,
                   COUNT(*) AS total_readings,
                   SUM(status IN ('available', 'occupied')) AS ok_readings,
                   ROUND(
                       100.0 * SUM(status IN ('available', 'occupied')) / COUNT(*), 1
                   ) AS uptime_pct
            FROM telemetry
            GROUP BY charger_id
            ORDER BY uptime_pct ASC
        """
        return self.fetch_all(query)


if __name__ == "__main__":
    repo = MySQLRepository(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        database=os.environ.get("DB_NAME", "voltedge_monitoring"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", "")
    )

    print("Chargers:")
    print(repo.get_chargers())

    print("Telemetry:")
    print(repo.get_telemetry())

    print("Incidents:")
    print(repo.get_incidents())
