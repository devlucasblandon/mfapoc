
# MediSupply POCs (Local, Python)

Proyecto base en **Python** para 4 POC en local con `docker-compose`:
- POC 1: Inventario (p95 ≤ 2 s) con Postgres + Redis + FastAPI.
- POC 2: Motor de rutas (≤ 3 s por lote) con OR-Tools + cola Redis Streams.
- POC 3: Seguridad (MFA con Keycloak) + cifrado de campos (envelope).
- POC 4: Pedidos offline-first (API idempotente + outbox + sync worker).

## Requisitos
- Docker Desktop (o compatible)
- Python 3.11+ (opcional para ejecución local sin contenedores)
- Node para k6 (opcional)
- mkcert (opcional TLS local)

## Inicio rápido
```bash
docker compose up -d
# POC1 API:
uvicorn poc1_inventory.api:app --reload --port 8080
# POC2 API:
uvicorn poc2_routing.api:app --reload --port 8081
# POC3 API:
uvicorn poc3_security.api:app --reload --port 8083
# POC4 API:
uvicorn poc4_offline.api:app --reload --port 8084
```
> Puedes dockerizar cada API con su propio `Dockerfile` (plantilla incluida) o correrlas en local con venv.

## Observabilidad (recomendada)
- Prometheus (http://localhost:9090)
- Grafana (http://localhost:3000) (user/pass: admin/admin)
- Jaeger (http://localhost:16686)

## Estructura
- `common/`: utilidades compartidas (DB, Redis, observabilidad, config).
- `poc1_inventory/`, `poc2_routing/`, `poc3_security/`, `poc4_offline/`: módulos por POC.
- `observability/`: Prometheus/Grafana config.
- `scripts/`: k6 y utilidades.

## Licencia
MIT


---
## 🧪 Postman (Newman) local
```bash
npm i
npm run postman:poc1   # o :poc2, :poc3, :poc4
```

## 🔁 GitHub Actions
- `Postman Smoke (Newman)` → ejecuta colección por POC (input `poc`).
- `POC1 Smoke (Compose + k6)` → levanta infra y corre k6 para POC1.
- `Lint & Build` → flake8.

