# VoltEdge Mobility A/S

Flask REST API til overvågning og drift af ladeinfrastruktur for elbiler.
6. semester eksamen - Erhvervsakademi København

## Live Azure URL

API kører på Azure Container Apps (Switzerland North):

https://voltedge-api.wittydesert-a5a60432.switzerlandnorth.azurecontainerapps.io/apidocs

Alle endpoints kræver header: X-API-Key: voltedge-prod-2024

Power BI endpoints (ingen API key):
- /powerbi/faults
- /powerbi/uptime

## Arkitektur

Flask REST API → Azure Container Registry → Azure Container Apps
MySQL kører som intern container i samme Container Apps miljø.

## DDD Arkitektur

| DDD Begreb | Klasse | Fil |
|---|---|---|
| Aggregate Root | Charger | domain/aggregates/charger.py |
| Entity | Connector | domain/entities/connector.py |
| Entity | Incident | domain/entities/incident.py |
| Value Object | TelemetryReading | domain/value_objects/telemetry_reading.py |
| Domain Event | TelemetryReceived, FaultDetected, IncidentCreated, IncidentResolved | domain/events/domain_events.py |
| Domain Service | FaultDetectionService | domain/services/fault_detection.py |
| Domain Service | PredictiveMaintenanceService | domain/services/predictive_maintenance.py |
| Repository | MySQLRepository | infrastructure/mysqlrepo.py |

## Lokal opsætning

Kopier .env.example til .env og udfyld værdier.

Start med Docker: docker compose up --build

API kører på: http://localhost:5001/apidocs

## Endpoints

| Method | URL | Beskrivelse |
|--------|-----|-------------|
| GET | /health | Liveness check |
| GET | /chargers | Alle ladestandere |
| GET | /chargers/{id} | Ladestander med connectors |
| POST | /telemetry | Modtag telemetri og kør fault detection |
| GET | /telemetry | Alle målinger |
| GET | /incidents | Alle incidents |
| PATCH | /incidents/{id}/resolve | Løs incident |
| GET | /analytics/faults | Fejlopsummering til Power BI |
| GET | /analytics/uptime | Oppetid til Power BI |
| GET | /connectors/{id}/predict | Predictive maintenance |
| GET | /powerbi/faults | Fejlopsummering uden API key |
| GET | /powerbi/uptime | Oppetid uden API key |

## Tests

Kør: pytest tests/ -v

## CI/CD

GitHub Actions kører ved push til main, develop og feature branches.
Pipeline: syntax check, unit tests, Docker build (linux/amd64), push til Azure Container Registry, smoke test.

## Azure ressourcer

| Ressource | Navn | Region |
|-----------|------|--------|
| Resource Group | voltedge-rg | Switzerland North |
| Container Registry | voltedgeacr.azurecr.io | Switzerland North |
| Container Apps miljø | voltedge-env | Switzerland North |
| Flask API | voltedge-api | Switzerland North |
| MySQL | voltedge-mysql | Switzerland North |
| Log Analytics | voltedge-logs | Switzerland North |
