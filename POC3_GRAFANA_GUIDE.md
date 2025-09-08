# Grafana en POC3 Security - Guía de Observabilidad

## 📋 Tabla de Contenidos

1. [Introducción a Grafana en POC3](#introducción-a-grafana-en-poc3)
2. [Arquitectura de Observabilidad](#arquitectura-de-observabilidad)
3. [Configuración de Grafana](#configuración-de-grafana)
4. [Dashboards y Métricas](#dashboards-y-métricas)
5. [Métricas del POC3](#métricas-del-poc3)
6. [Configuración de Prometheus](#configuración-de-prometheus)
7. [Monitoreo de JWT](#monitoreo-de-jwt)
8. [Alertas y Notificaciones](#alertas-y-notificaciones)
9. [Uso Práctico](#uso-práctico)
10. [Troubleshooting](#troubleshooting)
11. [Mejores Prácticas](#mejores-prácticas)

---

## 🎯 Introducción a Grafana en POC3

Grafana en el POC3 Security actúa como el **centro de observabilidad** del sistema, proporcionando visualización en tiempo real de métricas, logs y datos de rendimiento. Es la interfaz principal para monitorear la salud y el comportamiento del sistema de seguridad.

### ¿Qué hace Grafana en POC3?

1. **Visualización de Métricas**: Dashboards en tiempo real del rendimiento
2. **Monitoreo de Seguridad**: Métricas de autenticación JWT y acceso
3. **Análisis de Rendimiento**: Latencia, throughput y errores
4. **Alertas Proactivas**: Notificaciones de problemas de seguridad
5. **Análisis Histórico**: Tendencias y patrones de uso

### Beneficios para POC3

- **Visibilidad Completa**: Estado del sistema en tiempo real
- **Detección Temprana**: Identificación de problemas de seguridad
- **Análisis de Rendimiento**: Optimización basada en datos
- **Compliance**: Auditoría y trazabilidad de accesos
- **Debugging**: Diagnóstico rápido de problemas

---

## 🏗️ Arquitectura de Observabilidad

### Diagrama de Observabilidad POC3

```
┌─────────────────────────────────────────────────────────────┐
│                    POC3 Security                            │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   FastAPI App   │    │   Middleware    │                │
│  │   (api.py)      │───▶│   Observability │                │
│  │                 │    │   (metrics.py)  │                │
│  └─────────────────┘    └─────────────────┘                │
│           │                       │                        │
│           ▼                       ▼                        │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   JWT Auth      │    │   Prometheus    │                │
│  │   (auth.py)     │───▶│   Metrics       │                │
│  │                 │    │   Endpoint      │                │
│  └─────────────────┘    └─────────────────┘                │
│           │                       │                        │
│           ▼                       ▼                        │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   Crypto        │    │   Prometheus    │                │
│  │   (crypto.py)   │───▶│   Server        │                │
│  │                 │    │   (9090)        │                │
│  └─────────────────┘    └─────────────────┘                │
│                                   │                        │
│                                   ▼                        │
│                          ┌─────────────────┐                │
│                          │     Grafana     │                │
│                          │   Dashboard     │                │
│                          │    (3000)       │                │
│                          └─────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### Componentes de Observabilidad

1. **POC3 API** - Genera métricas de aplicación
2. **Prometheus** - Recolecta y almacena métricas
3. **Grafana** - Visualiza y analiza métricas
4. **Jaeger** - Trazabilidad distribuida (opcional)

---

## ⚙️ Configuración de Grafana

### Docker Compose Configuration

```yaml
# docker-compose.yml
grafana:
  image: grafana/grafana
  ports: ["3000:3000"]
  volumes:
    - ./observability/grafana/provisioning:/etc/grafana/provisioning:ro
    - ./observability/grafana/dashboards:/var/lib/grafana/dashboards:ro
  environment:
    - GF_AUTH_ANONYMOUS_ENABLED=true
    - GF_USERS_DEFAULT_THEME=light
    - GF_SECURITY_ADMIN_PASSWORD=admin
```

### Configuración de Provisioning

```yaml
# observability/grafana/provisioning/dashboards/dashboards.yml
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
```

### Variables de Entorno

```bash
# Configuración de Grafana
GF_AUTH_ANONYMOUS_ENABLED=true          # Acceso anónimo habilitado
GF_USERS_DEFAULT_THEME=light            # Tema claro por defecto
GF_SECURITY_ADMIN_PASSWORD=admin        # Contraseña de admin
GF_INSTALL_PLUGINS=grafana-piechart-panel  # Plugins adicionales
```

---

## 📊 Dashboards y Métricas

### Dashboard Principal: HTTP Latency

**Archivo**: `observability/grafana/dashboards/http-latency.json`

#### Métricas Principales

1. **Request Rate (RPS)**
   - Métrica: `http_requests_total`
   - Descripción: Número de requests por segundo
   - Panel: Graph con línea de tiempo

2. **Response Time**
   - Métrica: `http_request_duration_seconds`
   - Descripción: Tiempo de respuesta de endpoints
   - Panel: Histograma con percentiles

3. **Error Rate**
   - Métrica: `http_requests_total{status=~"5.."}`
   - Descripción: Porcentaje de errores 5xx
   - Panel: Gauge con umbrales

4. **Active Connections**
   - Métrica: `http_connections_active`
   - Descripción: Conexiones activas
   - Panel: Stat con tendencia

### Dashboard de Seguridad JWT

#### Métricas de Autenticación

1. **Login Success Rate**
   ```promql
   rate(http_requests_total{endpoint="/auth/login",status="200"}[5m]) / 
   rate(http_requests_total{endpoint="/auth/login"}[5m]) * 100
   ```

2. **Token Validation Time**
   ```promql
   histogram_quantile(0.95, 
     rate(http_request_duration_seconds_bucket{endpoint="/auth/me"}[5m])
   )
   ```

3. **Failed Authentication Attempts**
   ```promql
   rate(http_requests_total{endpoint="/auth/login",status="401"}[5m])
   ```

4. **Active Sessions**
   ```promql
   sum(jwt_active_tokens)
   ```

### Dashboard de Rendimiento

#### Métricas de Performance

1. **API Response Time**
   ```promql
   histogram_quantile(0.95, 
     rate(http_request_duration_seconds_bucket[5m])
   )
   ```

2. **Throughput**
   ```promql
   rate(http_requests_total[5m])
   ```

3. **Memory Usage**
   ```promql
   process_resident_memory_bytes
   ```

4. **CPU Usage**
   ```promql
   rate(process_cpu_seconds_total[5m]) * 100
   ```

---

## 📈 Métricas del POC3

### Métricas de Aplicación

#### 1. Métricas HTTP

```python
# En common/observability.py
from prometheus_client import Counter, Histogram, Gauge

# Contadores
http_requests_total = Counter(
    'http_requests_total', 
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Histogramas
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Gauges
http_connections_active = Gauge(
    'http_connections_active',
    'Active HTTP connections'
)
```

#### 2. Métricas de JWT

```python
# Métricas específicas de JWT
jwt_tokens_created_total = Counter(
    'jwt_tokens_created_total',
    'Total JWT tokens created',
    ['token_type', 'user_role']
)

jwt_token_validation_duration_seconds = Histogram(
    'jwt_token_validation_duration_seconds',
    'JWT token validation duration',
    ['validation_result']
)

jwt_active_tokens = Gauge(
    'jwt_active_tokens',
    'Number of active JWT tokens'
)
```

#### 3. Métricas de Seguridad

```python
# Métricas de seguridad
security_events_total = Counter(
    'security_events_total',
    'Total security events',
    ['event_type', 'severity']
)

authentication_attempts_total = Counter(
    'authentication_attempts_total',
    'Total authentication attempts',
    ['result', 'user_role']
)

encryption_operations_total = Counter(
    'encryption_operations_total',
    'Total encryption operations',
    ['operation_type', 'field_type']
)
```

### Métricas del Sistema

#### 1. Métricas de Recursos

```promql
# CPU Usage
rate(process_cpu_seconds_total[5m]) * 100

# Memory Usage
process_resident_memory_bytes / 1024 / 1024  # MB

# Disk Usage
node_filesystem_avail_bytes / node_filesystem_size_bytes * 100
```

#### 2. Métricas de Red

```promql
# Network I/O
rate(node_network_receive_bytes_total[5m])
rate(node_network_transmit_bytes_total[5m])

# Connection Count
node_netstat_Tcp_CurrEstab
```

---

## 🔐 Monitoreo de JWT

### Métricas Específicas de JWT

#### 1. Autenticación

```promql
# Login Success Rate
rate(jwt_tokens_created_total{token_type="access"}[5m])

# Failed Login Attempts
rate(authentication_attempts_total{result="failed"}[5m])

# Token Validation Time
histogram_quantile(0.95, 
  rate(jwt_token_validation_duration_seconds_bucket[5m])
)
```

#### 2. Tokens

```promql
# Active Tokens
jwt_active_tokens

# Token Expiration Rate
rate(jwt_tokens_expired_total[5m])

# Refresh Token Usage
rate(jwt_tokens_created_total{token_type="refresh"}[5m])
```

#### 3. Seguridad

```promql
# Invalid Token Attempts
rate(security_events_total{event_type="invalid_token"}[5m])

# Role Violation Attempts
rate(security_events_total{event_type="role_violation"}[5m])

# MFA Bypass Attempts
rate(security_events_total{event_type="mfa_bypass"}[5m])
```

### Alertas de Seguridad

#### 1. Alertas Críticas

```yaml
# Alerta: Múltiples intentos de login fallidos
- alert: HighFailedLoginAttempts
  expr: rate(authentication_attempts_total{result="failed"}[5m]) > 10
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "High number of failed login attempts"
    description: "{{ $value }} failed login attempts per second"

# Alerta: Tokens inválidos frecuentes
- alert: HighInvalidTokenAttempts
  expr: rate(security_events_total{event_type="invalid_token"}[5m]) > 5
  for: 1m
  labels:
    severity: warning
  annotations:
    summary: "High number of invalid token attempts"
    description: "{{ $value }} invalid token attempts per second"
```

#### 2. Alertas de Rendimiento

```yaml
# Alerta: Alta latencia
- alert: HighLatency
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High API latency"
    description: "95th percentile latency is {{ $value }}s"

# Alerta: Alta tasa de errores
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
  for: 3m
  labels:
    severity: critical
  annotations:
    summary: "High error rate"
    description: "Error rate is {{ $value | humanizePercentage }}"
```

---

## 🚨 Alertas y Notificaciones

### Configuración de Alertas

#### 1. Alertmanager Configuration

```yaml
# observability/alertmanager.yml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@medisupply.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://localhost:5001/'
    send_resolved: true

- name: 'email'
  email_configs:
  - to: 'admin@medisupply.com'
    subject: 'POC3 Security Alert: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
```

#### 2. Reglas de Prometheus

```yaml
# observability/prometheus_rules.yml
groups:
- name: poc3_security
  rules:
  - alert: HighFailedLogins
    expr: rate(authentication_attempts_total{result="failed"}[5m]) > 5
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High failed login rate"
      description: "{{ $value }} failed logins per second"

  - alert: JWTTokenExpired
    expr: jwt_active_tokens < 1
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "No active JWT tokens"
      description: "All JWT tokens have expired"
```

### Notificaciones

#### 1. Slack Integration

```yaml
# Configuración de Slack
receivers:
- name: 'slack'
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    channel: '#poc3-alerts'
    title: 'POC3 Security Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

#### 2. Email Notifications

```yaml
# Configuración de Email
receivers:
- name: 'email'
  email_configs:
  - to: 'security-team@medisupply.com'
    subject: 'POC3 Security Alert'
    body: |
      Alert: {{ .GroupLabels.alertname }}
      Severity: {{ .Labels.severity }}
      {{ range .Alerts }}
      Summary: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
```

---

## 🎯 Uso Práctico

### Acceso a Grafana

#### 1. Iniciar el Sistema

```bash
# Levantar todos los servicios
make poc3

# Verificar que Grafana esté ejecutándose
docker ps | grep grafana
```

#### 2. Acceder a Grafana

```bash
# URL de acceso
http://localhost:3000

# Credenciales por defecto
Usuario: admin
Contraseña: admin
```

#### 3. Navegación Básica

1. **Dashboards**: Panel principal con métricas
2. **Explore**: Consultas ad-hoc de Prometheus
3. **Alerting**: Configuración de alertas
4. **Configuration**: Configuración del sistema

### Consultas Útiles

#### 1. Consultas de Rendimiento

```promql
# Requests por segundo
rate(http_requests_total[5m])

# Latencia promedio
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# Tasa de errores
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])
```

#### 2. Consultas de Seguridad

```promql
# Intentos de login fallidos
rate(authentication_attempts_total{result="failed"}[5m])

# Tokens activos
jwt_active_tokens

# Eventos de seguridad
rate(security_events_total[5m])
```

#### 3. Consultas de Sistema

```promql
# Uso de CPU
rate(process_cpu_seconds_total[5m]) * 100

# Uso de memoria
process_resident_memory_bytes / 1024 / 1024

# Conexiones activas
http_connections_active
```

---

## 🔧 Troubleshooting

### Problemas Comunes

#### 1. Grafana No Inicia

```bash
# Verificar logs
docker-compose logs grafana

# Verificar puerto
lsof -i :3000

# Reiniciar servicio
docker-compose restart grafana
```

#### 2. No Se Ven Métricas

```bash
# Verificar Prometheus
curl http://localhost:9090/metrics

# Verificar endpoint de métricas del POC3
curl http://localhost:8083/metrics

# Verificar configuración de Prometheus
cat observability/prometheus.yml
```

#### 3. Dashboards No Cargar

```bash
# Verificar archivos de dashboard
ls -la observability/grafana/dashboards/

# Verificar permisos
chmod -R 755 observability/grafana/

# Reiniciar Grafana
docker-compose restart grafana
```

### Verificación de Estado

#### 1. Health Checks

```bash
# Verificar Grafana
curl http://localhost:3000/api/health

# Verificar Prometheus
curl http://localhost:9090/-/healthy

# Verificar POC3
curl http://localhost:8083/metrics
```

#### 2. Logs de Debugging

```bash
# Logs de Grafana
docker-compose logs -f grafana

# Logs de Prometheus
docker-compose logs -f prometheus

# Logs del POC3
docker-compose logs -f api_poc3
```

---

## 📚 Mejores Prácticas

### 1. Configuración de Dashboards

#### Organización
- **Dashboards por funcionalidad**: Seguridad, Rendimiento, Sistema
- **Paneles agrupados**: Métricas relacionadas juntas
- **Colores consistentes**: Verde (OK), Amarillo (Warning), Rojo (Critical)

#### Métricas Clave
- **SLI (Service Level Indicators)**: Disponibilidad, Latencia, Throughput
- **SLO (Service Level Objectives)**: Objetivos de servicio
- **SLA (Service Level Agreements)**: Acuerdos de nivel de servicio

### 2. Alertas Efectivas

#### Principios
- **Alertas accionables**: Solo alertar cuando se puede actuar
- **Umbrales apropiados**: Basados en datos históricos
- **Escalación clara**: Niveles de severidad definidos

#### Configuración
```yaml
# Ejemplo de alerta bien configurada
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
  for: 5m  # Evitar alertas espurias
  labels:
    severity: warning
    team: security
  annotations:
    summary: "Error rate above 1%"
    description: "Current error rate: {{ $value | humanizePercentage }}"
    runbook_url: "https://wiki.medisupply.com/runbooks/high-error-rate"
```

### 3. Retención de Datos

#### Configuración de Prometheus
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

# Retención de datos
storage:
  tsdb:
    retention.time: 30d  # 30 días
    retention.size: 10GB  # Máximo 10GB
```

#### Configuración de Grafana
```yaml
# Configuración de retención
[dashboards]
default_home_dashboard_path = /var/lib/grafana/dashboards/home.json

[log]
level = info
```

### 4. Seguridad

#### Configuración Segura
```yaml
# Configuración de seguridad
[security]
admin_user = admin
admin_password = $__env{GF_SECURITY_ADMIN_PASSWORD}
secret_key = $__env{GF_SECURITY_SECRET_KEY}

[auth.anonymous]
enabled = false  # Deshabilitar en producción

[auth.basic]
enabled = true
```

#### Acceso Controlado
- **Usuarios con roles**: Admin, Editor, Viewer
- **Organizaciones**: Separación por equipos
- **Permisos granulares**: Acceso limitado por dashboard

---

## 📊 Métricas Recomendadas para POC3

### 1. Métricas de Negocio

```promql
# Usuarios activos
count(jwt_active_tokens)

# Operaciones de encriptación
rate(encryption_operations_total[5m])

# Accesos a datos sensibles
rate(http_requests_total{endpoint=~"/customers.*"}[5m])
```

### 2. Métricas de Seguridad

```promql
# Intentos de bypass MFA
rate(security_events_total{event_type="mfa_bypass"}[5m])

# Violaciones de roles
rate(security_events_total{event_type="role_violation"}[5m])

# Tokens expirados
rate(jwt_tokens_expired_total[5m])
```

### 3. Métricas de Rendimiento

```promql
# Tiempo de respuesta de autenticación
histogram_quantile(0.95, rate(jwt_token_validation_duration_seconds_bucket[5m]))

# Throughput de API
rate(http_requests_total[5m])

# Latencia de encriptación
histogram_quantile(0.95, rate(encryption_duration_seconds_bucket[5m]))
```

---

## 🎯 Conclusión

Grafana en el POC3 Security proporciona:

### ✅ **Beneficios Logrados**

1. **Visibilidad Completa**: Estado del sistema en tiempo real
2. **Monitoreo de Seguridad**: Detección de amenazas y vulnerabilidades
3. **Análisis de Rendimiento**: Optimización basada en datos
4. **Alertas Proactivas**: Notificación temprana de problemas
5. **Auditoría**: Trazabilidad completa de accesos y operaciones

### 🔧 **Características Técnicas**

- **Dashboards Personalizados**: Métricas específicas del POC3
- **Integración con Prometheus**: Recolección automática de métricas
- **Alertas Configurables**: Notificaciones por email/Slack
- **Análisis Histórico**: Tendencias y patrones de uso
- **Acceso Seguro**: Autenticación y autorización

### 🚀 **Próximos Pasos**

1. **Implementar más dashboards** específicos de seguridad
2. **Configurar alertas avanzadas** con machine learning
3. **Integrar con sistemas externos** (SIEM, ITSM)
4. **Implementar métricas de negocio** personalizadas
5. **Optimizar retención** de datos según necesidades

---

**Última actualización**: $(date)
**Versión del documento**: 1.0.0
**Autor**: Equipo de Desarrollo MediSupply
