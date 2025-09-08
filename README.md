
# MediSupply POCs with Comprehensive Testing Suite

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=FastAPI)](https://fastapi.tiangolo.com/)
[![Postman](https://img.shields.io/badge/Postman-FF6C37?style=flat&logo=postman&logoColor=white)](https://www.postman.com/)
[![K6](https://img.shields.io/badge/k6-7D64FF?style=flat&logo=k6&logoColor=white)](https://k6.io/)

Proyecto completo de **4 POCs** con suite de pruebas exhaustiva, observabilidad y automatización CI/CD:

- **POC 1**: Inventario (p95 ≤ 2s) con PostgreSQL + Redis + FastAPI
- **POC 2**: Motor de rutas (≤ 3s por lote) con OR-Tools + Redis Streams  
- **POC 3**: Seguridad (MFA + encriptación) con Keycloak + cifrado de campos
- **POC 4**: Pedidos offline-first (API idempotente + outbox + sync worker)

## ✨ Características Principales

- 🧪 **Suite de Pruebas Completa**: Postman, K6, Newman, pruebas de regresión
- 🔒 **Seguridad Avanzada**: Encriptación, MFA, pruebas de vulnerabilidades
- 📊 **Observabilidad**: Prometheus, Grafana, Jaeger para monitoreo completo
- 🚀 **CI/CD**: GitHub Actions con pruebas automatizadas
- 🐳 **Containerización**: Docker Compose para desarrollo local
- 📚 **Documentación**: Guías completas de testing y contribución

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

## 🧪 Testing Suite

### Pruebas de Postman
```bash
# Ejecutar todas las pruebas de Postman
npm run postman:poc1   # POC1: Inventario
npm run postman:poc2   # POC2: Routing  
npm run postman:poc3   # POC3: Seguridad
npm run postman:poc4   # POC4: Offline

# Pruebas de carga
./scripts/postman_poc3_load.sh
```

### Pruebas de K6
```bash
# Pruebas de rendimiento
make test-poc3-performance

# Pruebas de seguridad avanzadas  
make test-poc3-security

# Pruebas de integración
make test-poc3-integration

# Todas las pruebas
make test-poc3-all
```

### Pruebas de Regresión
```bash
# Suite completa de regresión
./scripts/poc3_regression_test.sh
```

### Documentación de Testing
- 📖 [Guía Completa de Pruebas POC3](POC3_TESTING_GUIDE.md)
- 📋 [Guía de Contribución](CONTRIBUTING.md)

## 🔁 GitHub Actions
- `Postman Smoke (Newman)` → ejecuta colección por POC (input `poc`).
- `POC1 Smoke (Compose + k6)` → levanta infra y corre k6 para POC1.
- `Lint & Build` → flake8.

