# Guía de Pruebas para POC3 Security

Esta guía describe todas las pruebas disponibles para el POC3 Security, incluyendo las pruebas originales y las nuevas pruebas avanzadas que se han creado.

## 📋 Índice

- [Pruebas Existentes](#pruebas-existentes)
- [Nuevas Pruebas de Postman](#nuevas-pruebas-de-postman)
- [Pruebas de Rendimiento con K6](#pruebas-de-rendimiento-con-k6)
- [Pruebas de Seguridad Avanzadas](#pruebas-de-seguridad-avanzadas)
- [Pruebas de Integración](#pruebas-de-integración)
- [Pruebas de Regresión](#pruebas-de-regresión)
- [Comandos de Ejecución](#comandos-de-ejecución)
- [Interpretación de Resultados](#interpretación-de-resultados)

## 🔧 Pruebas Existentes

### Colección Original de Postman
- **Archivo**: `postman/POC3_Security.postman_collection.json`
- **Pruebas**: 2 pruebas básicas
  - Crear cliente con MFA
  - Leer cliente con MFA

## 🆕 Nuevas Pruebas de Postman

### Colección Expandida
- **Archivo**: `postman/POC3_Security.postman_collection.json` (actualizado)
- **Total de pruebas**: 20 pruebas

#### Categorías de Pruebas:

1. **Pruebas Negativas (6 pruebas)**
   - Crear cliente sin MFA (Error 401)
   - Crear cliente con MFA falso (Error 401)
   - Leer cliente sin MFA (Error 401)
   - Leer cliente no existente (Error 404)
   - Crear cliente con datos inválidos (Error 422)
   - Crear cliente con campos faltantes (Error 422)

2. **Pruebas de Casos Límite (4 pruebas)**
   - Crear cliente con caracteres especiales
   - Leer cliente con caracteres especiales
   - Crear cliente con datos largos
   - Crear cliente con datos sensibles

3. **Pruebas de Actualización (2 pruebas)**
   - Crear cliente duplicado (sobrescribir)
   - Verificar actualización

4. **Pruebas de Seguridad (4 pruebas)**
   - Headers maliciosos
   - Método HTTP no permitido (PUT)
   - Método HTTP no permitido (DELETE)
   - Content-Type incorrecto

5. **Pruebas de Validación (4 pruebas)**
   - JSON malformado
   - Headers de seguridad
   - Validación de entrada
   - Manejo de errores

## 🚀 Pruebas de Rendimiento con K6

### 1. Pruebas de Rendimiento Básicas
- **Archivo**: `scripts/k6_security_performance.js`
- **Objetivo**: Medir rendimiento de encriptación/desencriptación
- **Métricas**:
  - Tiempo de encriptación
  - Tiempo de desencriptación
  - Tiempo de validación MFA
  - Tasa de éxito de encriptación

### 2. Pruebas de Seguridad Avanzadas
- **Archivo**: `scripts/k6_security_advanced.js`
- **Objetivo**: Probar vulnerabilidades de seguridad
- **Categorías**:
  - Bypass de MFA
  - Headers maliciosos
  - Inyección de código
  - Caracteres especiales problemáticos
  - Datos extremadamente largos
  - Acceso no autorizado
  - Métodos HTTP no permitidos

### 3. Pruebas de Integración
- **Archivo**: `scripts/k6_security_integration.js`
- **Objetivo**: Probar flujos completos end-to-end
- **Escenarios**:
  - Flujo básico de creación y lectura
  - Flujo de actualización
  - Consistencia de encriptación
  - Manejo de errores
  - Datos sensibles
  - Concurrencia

## 🔒 Pruebas de Regresión

### Script de Regresión Automatizado
- **Archivo**: `scripts/poc3_regression_test.sh`
- **Objetivo**: Verificar que todas las funcionalidades funcionen después de cambios
- **Categorías**:
  - Funcionalidad básica
  - Seguridad
  - Validación de datos
  - Encriptación
  - Casos límite
  - Métodos HTTP
  - Rendimiento básico

## 📊 Comandos de Ejecución

### Comandos Makefile

```bash
# Ejecutar POC3
make poc3

# Pruebas de seguridad avanzadas
make test-poc3-security

# Pruebas de rendimiento
make test-poc3-performance

# Pruebas de integración
make test-poc3-integration

# Todas las pruebas
make test-poc3-all
```

### Comandos Directos

```bash
# Pruebas de Postman con Newman
newman run postman/POC3_Security.postman_collection.json \
  --environment postman/environment.medisupply.local.json

# Pruebas de carga con Postman
./scripts/postman_poc3_load.sh

# Pruebas de regresión
./scripts/poc3_regression_test.sh

# Pruebas de K6 individuales
k6 run scripts/k6_security_advanced.js
k6 run scripts/k6_security_performance.js
k6 run scripts/k6_security_integration.js
```

## 📈 Interpretación de Resultados

### Métricas de K6

#### Pruebas de Rendimiento
- **encryption_success_rate**: Debe ser > 99%
- **encryption_time**: 95% de las encriptaciones < 100ms
- **decryption_time**: 95% de las desencriptaciones < 100ms
- **mfa_validation_time**: 95% de las validaciones MFA < 50ms

#### Pruebas de Seguridad
- **security_violations**: Máximo 10 violaciones
- **mfa_bypass_attempts**: Máximo 5 intentos de bypass
- **injection_attempts**: Máximo 3 intentos de inyección
- **unauthorized_access**: Máximo 5 accesos no autorizados

#### Pruebas de Integración
- **integration_success_rate**: Debe ser > 95%
- **encryption_consistency_checks**: Mínimo 10 verificaciones
- **data_integrity_checks**: Mínimo 10 verificaciones
- **end_to_end_time**: 95% de flujos completos < 1s

### Códigos de Salida

- **0**: Todas las pruebas pasaron
- **1**: Algunas pruebas fallaron
- **2**: Error de configuración o dependencias

## 🛠️ Configuración Requerida

### Dependencias
- Docker y Docker Compose
- Node.js (para Newman y K6)
- Newman: `npm install -g newman`
- K6: [Instalación de K6](https://k6.io/docs/getting-started/installation/)

### Servicios Requeridos
- PostgreSQL (puerto 5432)
- Redis (puerto 6379)
- Keycloak (puerto 8082)
- Prometheus (puerto 9090)
- Grafana (puerto 3000)
- Jaeger (puerto 16686)

## 📝 Notas Importantes

1. **Datos de Prueba**: Las pruebas crean datos de prueba que pueden persistir entre ejecuciones
2. **Puertos**: Asegúrate de que los puertos requeridos estén disponibles
3. **MFA**: Todas las pruebas de creación y lectura requieren el header `x-mfa: true`
4. **Encriptación**: Los campos `email` y `phone` se encriptan automáticamente
5. **Limpieza**: En un entorno de producción, implementa limpieza de datos de prueba

## 🔍 Troubleshooting

### Problemas Comunes

1. **Puerto 8083 ocupado**
   ```bash
   # Verificar qué proceso usa el puerto
   lsof -i :8083
   # Detener POC3
   make down
   # Reiniciar
   make poc3
   ```

2. **Newman no encontrado**
   ```bash
   npm install -g newman
   ```

3. **K6 no encontrado**
   ```bash
   # macOS
   brew install k6
   # Linux
   sudo apt-get install k6
   ```

4. **Errores de MFA**
   - Verificar que el header `x-mfa: true` esté presente
   - Verificar que el valor sea exactamente "true" (no "TRUE" o "True")

## 📚 Recursos Adicionales

- [Documentación de K6](https://k6.io/docs/)
- [Documentación de Newman](https://learning.postman.com/docs/running-collections/using-newman-cli/command-line-integration-with-newman/)
- [Documentación de FastAPI](https://fastapi.tiangolo.com/)
- [Documentación de Cryptography](https://cryptography.io/en/latest/)

---

**Última actualización**: $(date)
**Versión**: 1.0.0
