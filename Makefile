# Simple Makefile for MediSupply POCs
SHELL := /bin/bash

.PHONY: up down logs seed grafana poc1 poc2 poc3 poc4 poc1-build poc2-build poc3-build poc4-build test-poc3-security test-poc3-performance test-poc3-integration

up:
	docker compose up -d postgres redis keycloak prometheus grafana jaeger

down:
	docker compose down -v

logs:
	docker compose logs -f

seed:
	# Ejecuta el schema de POC1
	docker compose exec -T postgres psql -U postgres -d medisupply < poc1_inventory/schema.sql || true

grafana:
	echo "Open Grafana: http://localhost:3000 ; Prometheus: http://localhost:9090 ; Jaeger: http://localhost:16686"

poc1-build:
	docker compose build api_poc1

poc1: up poc1-build
	docker compose --profile poc1 up -d api_poc1
	$(MAKE) seed
	@echo "POC1 running on http://localhost:8080"

poc2-build:
	docker compose build api_poc2

poc2: up poc2-build
	docker compose --profile poc2 up -d api_poc2
	@echo "POC2 running on http://localhost:8081"

poc3-build:
	docker compose build api_poc3

poc3: up poc3-build
	docker compose --profile poc3 up -d api_poc3
	@echo "POC3 running on http://localhost:8083"

poc4-build:
	docker compose build api_poc4

poc4: up poc4-build
	docker compose --profile poc4 up -d api_poc4
	@echo "POC4 running on http://localhost:8084"

# Pruebas de seguridad para POC3
test-poc3-security: poc3
	@echo "Ejecutando pruebas de seguridad avanzadas para POC3..."
	k6 run scripts/k6_security_advanced.js

test-poc3-performance: poc3
	@echo "Ejecutando pruebas de rendimiento para POC3..."
	k6 run scripts/k6_security_performance.js

test-poc3-integration: poc3
	@echo "Ejecutando pruebas de integración para POC3..."
	k6 run scripts/k6_security_integration.js

test-poc3-all: poc3
	@echo "Ejecutando todas las pruebas de POC3..."
	@echo "1. Pruebas de seguridad avanzadas..."
	k6 run scripts/k6_security_advanced.js
	@echo "2. Pruebas de rendimiento..."
	k6 run scripts/k6_security_performance.js
	@echo "3. Pruebas de integración..."
	k6 run scripts/k6_security_integration.js
