# VoltEdge Mobility A/S

Flask REST API til overvågning og drift af ladeinfrastruktur for elbiler.

6. semester eksamen – Design og implementering af digitale løsninger  
Erhvervsakademi København

---

## Hvad løsningen gør

- Modtager telemetridata fra ladestandere (IoT-enheder)
- Kører automatisk fejldetektion baseret på domæneregler
- Opretter incidents automatisk ved kritiske fejl
- Gemmer alt i MySQL-database
- Tilbyder predictive maintenance risikovurdering
- Eksponerer analytics-endpoints til Power BI dashboards

---

## Projektstruktur

```
VoltEdge-Mobility-A-S/
├── VoltEdge-Mobility.py       # Flask REST API – alle endpoints
├── mysqlrepo.py               # Database-adgang – alle SQL-forespørgsler
├── fault_detection.py         # Domain Service – fejldetektion
├── predictive_maintenance.py  # Domain Service – predictive maintenance
├── voltedge_db.sql            # SQL-schema – opretter tabeller og testdata
├── docker-compose.yml         # Starter API og MySQL med Docker
├── Dockerfile                 # Bygger API-containeren
├── requirements.txt           # Python-afhængigheder
├── .env.example               # Skabelon til miljøvariabler
└── .github/workflows/ci.yml   # GitHub Actions CI/CD pipeline
```

---

## Lokal opsætning

Opret en `.env` fil baseret på `.env.example`:

```env
DB_HOST=db
DB_NAME=voltedge_monitoring
DB_USER=root
DB_PASSWORD=dit_password_her
```

---

## Kør med Docker

Start løsningen med Docker Compose:

```bash
docker compose up --build
```

API er tilgængeligt på:

```
http://localhost:5001/apidocs
```

---

## Endpoints

| Method | URL | Beskrivelse |
|--------|-----|-------------|
| GET | /health | Liveness check |
| POST | /telemetry | Modtag telemetri fra ladestander |
| GET | /telemetry | Hent alle målinger |
| GET | /chargers | Liste over alle ladestandere |
| GET | /chargers/{id} | Hent én ladestander |
| GET | /chargers/{id}/telemetry | Seneste målinger for én ladestander |
| GET | /chargers/{id}/predict | Predictive maintenance risikovurdering |
| GET | /incidents | Liste over alle incidents |
| GET | /incidents/{id} | Hent én incident |
| PATCH | /incidents/{id}/resolve | Markér incident som løst |
| GET | /analytics/faults | Fejlopsummering til Power BI |
| GET | /analytics/uptime | Oppetid per ladestander til Power BI |

---

## Test flow

En simpel test-sekvens via Swagger UI (http://localhost:5001/apidocs):

1. Send normal telemetri (POST /telemetry med status: available)
2. Send telemetri med fejl (POST /telemetry med status: faulted)
3. Tjek at incident er oprettet (GET /incidents)
4. Løs incidenten (PATCH /incidents/{id}/resolve)
5. Kør predictive maintenance (GET /chargers/CHR-002/predict)
6. Tjek analytics (GET /analytics/faults)

### Eksempel – normal telemetri

```json
{
  "charger_id": "CHR-001",
  "connector_id": "CON-1",
  "location_id": "LOC-CPH-01",
  "power_kw": 11.0,
  "voltage_v": 230.0,
  "current_a": 16.0,
  "status": "available"
}
```

### Eksempel – telemetri med fejl (opretter incident automatisk)

```json
{
  "charger_id": "CHR-002",
  "connector_id": "CON-1",
  "location_id": "LOC-CPH-02",
  "power_kw": 0.0,
  "voltage_v": 150.0,
  "current_a": 0.0,
  "status": "faulted",
  "error_code": "ConnectorLockFailure"
}
```

---

## MySQL Workbench

Forbind til Docker MySQL:

- Host: `127.0.0.1`
- Port: `3307`
- User: `root`
- Password: din værdi fra `.env`

Nyttige SQL-forespørgsler:

```sql
USE voltedge_monitoring;
SELECT * FROM chargers;
SELECT * FROM telemetry;
SELECT * FROM incidents;
```

---

## Nulstil databasen

Hvis du vil starte helt forfra:

```bash
docker compose down -v
docker compose up --build
```

Dette sletter Docker-volumet og genskaber databasen fra SQL-filen.

---

## GitHub Actions CI/CD

Projektet inkluderer en CI/CD pipeline i `.github/workflows/ci.yml`.

Den kører automatisk ved push til `main` og `develop` og gør tre ting:

- Installerer Python-afhængigheder
- Tjekker at Python-filerne kompilerer uden syntaksfejl
- Bygger Docker image og smoke-tester det mod /health

---

## DDD-arkitektur

Løsningen er bygget på Domain Driven Design principper:

| DDD-begreb | Implementering |
|---|---|
| Entity: Charger | chargers-tabellen – unik identitet og status over tid |
| Entity: Incident | incidents-tabellen – livscyklus fra open til resolved |
| Value Object: TelemetryReading | telemetry-tabellen – beskrevet af værdier |
| Domain Service: FaultDetectionService | fault_detection.py |
| Domain Service: PredictiveMaintenanceService | predictive_maintenance.py |
| Repository | mysqlrepo.py – abstraherer databaseadgang |
| Domain Events | TelemetryReceived, FaultDetected, IncidentCreated, IncidentResolved |

---

## Præsentation af løsningen

Løsningen demonstreres ved at vise:

- GitHub repository med commit-historik
- GitHub Actions workflow (grøn pipeline)
- Docker der kører API og MySQL
- Swagger UI med live requests
- Data der gemmes i MySQL Workbench
- Power BI dashboard med analytics-data