# Jaeger en POC3 Security - Guía de Tracing Distribuido

## 📋 Tabla de Contenidos

1. [Introducción a Jaeger en POC3](#introducción-a-jaeger-en-poc3)
2. [Arquitectura de Tracing](#arquitectura-de-tracing)
3. [Configuración de Jaeger](#configuración-de-jaeger)
4. [Instrumentación del POC3](#instrumentación-del-poc3)
5. [Spans y Traces](#spans-y-traces)
6. [Contexto de Tracing](#contexto-de-tracing)
7. [Integración con FastAPI](#integración-con-fastapi)
8. [Métricas de Tracing](#métricas-de-tracing)
9. [Análisis de Performance](#análisis-de-performance)
10. [Troubleshooting](#troubleshooting)
11. [Mejores Prácticas](#mejores-prácticas)

---

## 🎯 Introducción a Jaeger en POC3

Jaeger en el POC3 Security actúa como el **sistema de tracing distribuido**, proporcionando visibilidad completa del flujo de requests a través de todos los componentes del sistema, especialmente útil para analizar la performance de operaciones de seguridad como autenticación JWT y encriptación.

### ¿Qué hace Jaeger en POC3?

1. **Tracing Distribuido**: Seguimiento de requests a través de múltiples servicios
2. **Análisis de Performance**: Identificación de cuellos de botella
3. **Debugging**: Diagnóstico de problemas de latencia
4. **Monitoreo de Dependencias**: Visualización de interacciones entre componentes
5. **Análisis de Flujos**: Comprensión del comportamiento del sistema

### Beneficios para POC3

- **Visibilidad Completa**: Flujo end-to-end de requests de seguridad
- **Análisis de Latencia**: Identificación de operaciones lentas
- **Debugging Eficiente**: Diagnóstico rápido de problemas
- **Optimización**: Mejora de performance basada en datos reales
- **Monitoreo de Dependencias**: Análisis de interacciones entre servicios

---

## 🏗️ Arquitectura de Tracing

### Diagrama de Arquitectura Jaeger

```
┌─────────────────────────────────────────────────────────────┐
│                    POC3 Security                            │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   FastAPI App   │    │   Jaeger Client │                │
│  │   (api.py)      │───▶│   (opentelemetry)│                │
│  │   Port: 8083    │    │   Instrumentation│                │
│  └─────────────────┘    └─────────────────┘                │
│           │                       │                        │
│           ▼                       ▼                        │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   Spans         │    │   Jaeger Agent  │                │
│  │   (Traces)      │◄───│   Port: 6831    │                │
│  │   Generation    │    │   (UDP)         │                │
│  └─────────────────┘    └─────────────────┘                │
│                                   │                        │
│                                   ▼                        │
│                          ┌─────────────────┐                │
│                          │   Jaeger        │                │
│                          │   Collector     │                │
│                          │   Port: 14268   │                │
│                          └─────────────────┘                │
│                                   │                        │
│                                   ▼                        │
│                          ┌─────────────────┐                │
│                          │   Jaeger        │                │
│                          │   Storage       │                │
│                          │   (In-Memory)   │                │
│                          └─────────────────┘                │
│                                   │                        │
│                                   ▼                        │
│                          ┌─────────────────┐                │
│                          │   Jaeger UI     │                │
│                          │   Port: 16686   │                │
│                          └─────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### Componentes del Sistema

1. **POC3 API** - Genera spans y traces
2. **Jaeger Client** - Instrumentación OpenTelemetry
3. **Jaeger Agent** - Recolección de spans via UDP
4. **Jaeger Collector** - Procesamiento y validación
5. **Jaeger Storage** - Almacenamiento de traces
6. **Jaeger UI** - Visualización y análisis

---

## ⚙️ Configuración de Jaeger

### Docker Compose Configuration

```yaml
# docker-compose.yml
jaeger:
  image: jaegertracing/all-in-one:latest
  ports:
    - "16686:16686"  # Jaeger UI
    - "14268:14268"  # Jaeger collector
    - "6831:6831/udp"  # Jaeger agent (UDP)
  environment:
    - COLLECTOR_OTLP_ENABLED=true
    - COLLECTOR_ZIPKIN_HOST_PORT=:9411
  networks:
    - medisupply-network

# Configuración del POC3 con Jaeger
api_poc3:
  build:
    context: .
    dockerfile: Dockerfile.poc3
  ports:
    - "8083:8083"
  environment:
    - JAEGER_AGENT_HOST=jaeger
    - JAEGER_AGENT_PORT=6831
    - JAEGER_SERVICE_NAME=poc3-security
    - JAEGER_SAMPLER_TYPE=const
    - JAEGER_SAMPLER_PARAM=1
  depends_on:
    - jaeger
  networks:
    - medisupply-network
```

### Variables de Entorno

```bash
# Configuración de Jaeger para POC3
JAEGER_AGENT_HOST=jaeger              # Host del agente Jaeger
JAEGER_AGENT_PORT=6831               # Puerto del agente (UDP)
JAEGER_SERVICE_NAME=poc3-security    # Nombre del servicio
JAEGER_SAMPLER_TYPE=const            # Tipo de muestreo
JAEGER_SAMPLER_PARAM=1               # Parámetro de muestreo (100%)
JAEGER_REPORTER_LOG_SPANS=true       # Log de spans
JAEGER_REPORTER_FLUSH_INTERVAL=1000  # Intervalo de flush (ms)
```

### Configuración de Muestreo

```python
# Configuración de muestreo en POC3
JAEGER_CONFIG = {
    'sampler': {
        'type': 'const',
        'param': 1,  # 100% de muestreo para desarrollo
    },
    'reporter': {
        'logSpans': True,
        'agentHost': 'jaeger',
        'agentPort': 6831,
    },
    'service_name': 'poc3-security',
}
```

---

## 🔧 Instrumentación del POC3

### Instalación de Dependencias

```python
# requirements.txt
opentelemetry-api==1.20.0
opentelemetry-sdk==1.20.0
opentelemetry-instrumentation-fastapi==0.41b0
opentelemetry-instrumentation-requests==0.41b0
opentelemetry-exporter-jaeger==1.20.0
opentelemetry-instrumentation-sqlalchemy==0.41b0
```

### Configuración de Instrumentación

```python
# poc3_security/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource

def setup_tracing(app):
    """Configurar tracing con Jaeger para POC3"""
    
    # Configurar resource
    resource = Resource.create({
        "service.name": "poc3-security",
        "service.version": "1.0.0",
        "service.namespace": "medisupply",
    })
    
    # Configurar tracer provider
    trace.set_tracer_provider(TracerProvider(resource=resource))
    tracer = trace.get_tracer(__name__)
    
    # Configurar Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger",
        agent_port=6831,
    )
    
    # Configurar span processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    # Instrumentar FastAPI
    FastAPIInstrumentor.instrument_app(app, tracer_provider=trace.get_tracer_provider())
    
    # Instrumentar requests
    RequestsInstrumentor().instrument()
    
    return tracer

# Configuración de instrumentación automática
def instrument_poc3():
    """Instrumentación automática del POC3"""
    
    # Instrumentar FastAPI
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    
    # Instrumentar componentes
    FastAPIInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument()
```

### Integración con FastAPI

```python
# poc3_security/api.py
from fastapi import FastAPI, Depends, HTTPException
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from poc3_security.tracing import setup_tracing

app = FastAPI(title="POC3 Security API")

# Configurar tracing
tracer = setup_tracing(app)

@app.post("/customers")
async def create_customer(customer_data: dict, current_user: User = Depends(require_mfa_verified)):
    """Crear cliente con tracing distribuido"""
    
    with tracer.start_as_current_span("create_customer") as span:
        try:
            # Agregar atributos al span
            span.set_attribute("customer.email", customer_data.get("email"))
            span.set_attribute("user.role", current_user.role)
            span.set_attribute("operation.type", "create")
            
            # Operación de encriptación
            with tracer.start_as_current_span("encrypt_customer_data") as encrypt_span:
                encrypt_span.set_attribute("encryption.fields", ["email", "phone"])
                encrypted_data = encrypt_customer_data(customer_data)
                encrypt_span.set_attribute("encryption.success", True)
            
            # Operación de base de datos
            with tracer.start_as_current_span("save_customer_db") as db_span:
                db_span.set_attribute("db.operation", "insert")
                db_span.set_attribute("db.table", "customers")
                result = save_customer_to_db(encrypted_data)
                db_span.set_attribute("db.rows_affected", 1)
            
            # Marcar span como exitoso
            span.set_status(Status(StatusCode.OK))
            span.set_attribute("operation.success", True)
            
            return result
            
        except Exception as e:
            # Marcar span como error
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.set_attribute("operation.error", str(e))
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/login")
async def login(login_data: LoginRequest):
    """Login con tracing de autenticación"""
    
    with tracer.start_as_current_span("user_login") as span:
        try:
            span.set_attribute("login.username", login_data.username)
            span.set_attribute("login.method", "password")
            
            # Validación de credenciales
            with tracer.start_as_current_span("validate_credentials") as auth_span:
                auth_span.set_attribute("auth.provider", "local")
                user = authenticate_user(login_data.username, login_data.password)
                auth_span.set_attribute("auth.success", user is not None)
            
            if not user:
                span.set_status(Status(StatusCode.ERROR, "Invalid credentials"))
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Generación de tokens
            with tracer.start_as_current_span("generate_tokens") as token_span:
                token_span.set_attribute("token.type", "jwt")
                token_span.set_attribute("user.role", user.role)
                
                access_token = create_access_token(data={"sub": user.username, "role": user.role})
                refresh_token = create_refresh_token(data={"sub": user.username})
                
                token_span.set_attribute("token.access_created", True)
                token_span.set_attribute("token.refresh_created", True)
            
            # Marcar span como exitoso
            span.set_status(Status(StatusCode.OK))
            span.set_attribute("login.success", True)
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.set_attribute("login.error", str(e))
            raise
```

---

## 📊 Spans y Traces

### Estructura de Spans

#### 1. Span de Request HTTP

```python
# Span principal de request
{
    "traceId": "1234567890abcdef",
    "spanId": "abcdef1234567890",
    "operationName": "POST /customers",
    "startTime": 1640995200000000,
    "duration": 150000000,  # 150ms
    "tags": {
        "http.method": "POST",
        "http.url": "/customers",
        "http.status_code": 200,
        "component": "fastapi",
        "service.name": "poc3-security"
    },
    "logs": [
        {
            "timestamp": 1640995200000000,
            "fields": [
                {"key": "event", "value": "request_start"},
                {"key": "user_id", "value": "admin"}
            ]
        }
    ]
}
```

#### 2. Span de Encriptación

```python
# Span de operación de encriptación
{
    "traceId": "1234567890abcdef",
    "spanId": "fedcba0987654321",
    "parentSpanId": "abcdef1234567890",
    "operationName": "encrypt_customer_data",
    "startTime": 1640995200100000,
    "duration": 50000000,  # 50ms
    "tags": {
        "operation.type": "encryption",
        "encryption.fields": "email,phone",
        "encryption.algorithm": "fernet",
        "encryption.success": True
    }
}
```

#### 3. Span de Base de Datos

```python
# Span de operación de base de datos
{
    "traceId": "1234567890abcdef",
    "spanId": "1122334455667788",
    "parentSpanId": "abcdef1234567890",
    "operationName": "save_customer_db",
    "startTime": 1640995200600000,
    "duration": 80000000,  # 80ms
    "tags": {
        "db.operation": "insert",
        "db.table": "customers",
        "db.rows_affected": 1,
        "db.connection_pool": "active"
    }
}
```

### Traces Completos

#### 1. Trace de Creación de Cliente

```
Trace ID: 1234567890abcdef
├── POST /customers (150ms)
│   ├── validate_jwt_token (5ms)
│   ├── check_mfa_verification (3ms)
│   ├── encrypt_customer_data (50ms)
│   │   ├── encrypt_email (20ms)
│   │   └── encrypt_phone (25ms)
│   └── save_customer_db (80ms)
│       ├── db_connection (10ms)
│       ├── db_insert (60ms)
│       └── db_commit (10ms)
```

#### 2. Trace de Autenticación JWT

```
Trace ID: 2345678901bcdefg
├── POST /auth/login (200ms)
│   ├── validate_credentials (100ms)
│   │   ├── hash_password (30ms)
│   │   └── check_user_exists (70ms)
│   ├── generate_tokens (80ms)
│   │   ├── create_access_token (40ms)
│   │   └── create_refresh_token (35ms)
│   └── log_authentication (20ms)
```

### Atributos de Spans

#### 1. Atributos HTTP

```python
# Atributos estándar HTTP
span.set_attribute("http.method", "POST")
span.set_attribute("http.url", "/customers")
span.set_attribute("http.status_code", 200)
span.set_attribute("http.user_agent", "PostmanRuntime/7.28.4")
span.set_attribute("http.request_size", 1024)
span.set_attribute("http.response_size", 512)
```

#### 2. Atributos de Seguridad

```python
# Atributos específicos de seguridad
span.set_attribute("security.operation", "create_customer")
span.set_attribute("security.user_role", "admin")
span.set_attribute("security.mfa_verified", True)
span.set_attribute("security.jwt_valid", True)
span.set_attribute("security.encryption_used", True)
```

#### 3. Atributos de Base de Datos

```python
# Atributos de base de datos
span.set_attribute("db.operation", "insert")
span.set_attribute("db.table", "customers")
span.set_attribute("db.rows_affected", 1)
span.set_attribute("db.connection_pool_size", 10)
span.set_attribute("db.query_time", 0.08)
```

---

## 🔄 Contexto de Tracing

### Propagación de Contexto

#### 1. Headers de Tracing

```python
# Headers HTTP para propagación de contexto
TRACE_HEADERS = {
    "uber-trace-id": "1234567890abcdef:abcdef1234567890:0:1",
    "uberctx-": "custom-context-data"
}

# Headers W3C Trace Context
W3C_HEADERS = {
    "traceparent": "00-1234567890abcdef-fedcba0987654321-01",
    "tracestate": "poc3=security,version=1.0"
}
```

#### 2. Contexto de Request

```python
# Extraer contexto de request
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

def extract_trace_context(request):
    """Extraer contexto de tracing del request"""
    
    headers = dict(request.headers)
    propagator = TraceContextTextMapPropagator()
    context = propagator.extract(headers)
    
    return context

# Usar contexto en operaciones
def process_with_context(context, operation):
    """Procesar operación con contexto de tracing"""
    
    with trace.set_span_in_context(context):
        with tracer.start_as_current_span(operation) as span:
            # Operación con contexto preservado
            return perform_operation()
```

### Contexto de Usuario

#### 1. Información de Usuario en Spans

```python
# Agregar información de usuario a spans
def add_user_context(span, user):
    """Agregar contexto de usuario al span"""
    
    span.set_attribute("user.id", user.id)
    span.set_attribute("user.username", user.username)
    span.set_attribute("user.role", user.role)
    span.set_attribute("user.mfa_enabled", user.mfa_enabled)
    span.set_attribute("user.last_login", user.last_login.isoformat())
```

#### 2. Contexto de Sesión

```python
# Contexto de sesión JWT
def add_session_context(span, token_data):
    """Agregar contexto de sesión al span"""
    
    span.set_attribute("session.token_type", "jwt")
    span.set_attribute("session.issued_at", token_data.get("iat"))
    span.set_attribute("session.expires_at", token_data.get("exp"))
    span.set_attribute("session.issuer", token_data.get("iss"))
    span.set_attribute("session.audience", token_data.get("aud"))
```

---

## 🚀 Integración con FastAPI

### Middleware de Tracing

```python
# poc3_security/middleware.py
from fastapi import Request, Response
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
import time

class TracingMiddleware:
    """Middleware de tracing para FastAPI"""
    
    def __init__(self, app):
        self.app = app
        self.tracer = trace.get_tracer(__name__)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Crear span para el request
        with self.tracer.start_as_current_span(
            f"{request.method} {request.url.path}"
        ) as span:
            
            # Agregar atributos del request
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.user_agent", request.headers.get("user-agent", ""))
            span.set_attribute("http.content_length", request.headers.get("content-length", 0))
            
            # Agregar información de usuario si está disponible
            if hasattr(request.state, "user"):
                span.set_attribute("user.id", request.state.user.id)
                span.set_attribute("user.role", request.state.user.role)
            
            start_time = time.time()
            
            try:
                # Procesar request
                await self.app(scope, receive, send)
                
                # Marcar span como exitoso
                span.set_status(Status(StatusCode.OK))
                span.set_attribute("http.status_code", 200)
                
            except Exception as e:
                # Marcar span como error
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("http.status_code", 500)
                span.set_attribute("error.message", str(e))
                raise
            
            finally:
                # Agregar duración
                duration = time.time() - start_time
                span.set_attribute("http.duration", duration)
```

### Instrumentación Automática

```python
# poc3_security/instrumentation.py
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

def instrument_all():
    """Instrumentar todos los componentes del POC3"""
    
    # Instrumentar FastAPI
    FastAPIInstrumentor().instrument(
        server_request_hook=server_request_hook,
        client_request_hook=client_request_hook
    )
    
    # Instrumentar requests HTTP
    RequestsInstrumentor().instrument()
    
    # Instrumentar SQLAlchemy
    SQLAlchemyInstrumentor().instrument()
    
    # Instrumentar Psycopg2
    Psycopg2Instrumentor().instrument()

def server_request_hook(span, scope):
    """Hook para requests del servidor"""
    
    if scope["type"] == "http":
        request = Request(scope)
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))

def client_request_hook(span, scope):
    """Hook para requests del cliente"""
    
    span.set_attribute("http.client_request", True)
    span.set_attribute("http.client_url", str(scope.get("url", "")))
```

---

## 📈 Métricas de Tracing

### Métricas de Spans

#### 1. Contadores de Spans

```python
# Métricas de spans generados
spans_created_total = Counter(
    'jaeger_spans_created_total',
    'Total spans created',
    ['operation_name', 'service_name', 'status']
)

# Métricas de traces generados
traces_created_total = Counter(
    'jaeger_traces_created_total',
    'Total traces created',
    ['service_name', 'trace_type']
)
```

#### 2. Métricas de Duración

```python
# Duración de spans
span_duration_seconds = Histogram(
    'jaeger_span_duration_seconds',
    'Span duration in seconds',
    ['operation_name', 'service_name'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

# Duración de traces
trace_duration_seconds = Histogram(
    'jaeger_trace_duration_seconds',
    'Trace duration in seconds',
    ['service_name', 'trace_type'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)
```

### Métricas de Performance

#### 1. Throughput de Spans

```promql
# Spans por segundo
rate(jaeger_spans_created_total[5m])

# Spans por operación
sum by (operation_name) (rate(jaeger_spans_created_total[5m]))

# Spans por servicio
sum by (service_name) (rate(jaeger_spans_created_total[5m]))
```

#### 2. Latencia de Spans

```promql
# Latencia promedio de spans
rate(jaeger_span_duration_seconds_sum[5m]) / rate(jaeger_span_duration_seconds_count[5m])

# Percentil 95 de latencia
histogram_quantile(0.95, rate(jaeger_span_duration_seconds_bucket[5m]))

# Latencia por operación
histogram_quantile(0.95, rate(jaeger_span_duration_seconds_bucket[5m]) by (operation_name))
```

### Métricas de Errores

#### 1. Tasa de Errores

```promql
# Tasa de errores en spans
rate(jaeger_spans_created_total{status="error"}[5m]) / rate(jaeger_spans_created_total[5m])

# Errores por operación
sum by (operation_name) (rate(jaeger_spans_created_total{status="error"}[5m]))

# Errores por servicio
sum by (service_name) (rate(jaeger_spans_created_total{status="error"}[5m]))
```

---

## 🔍 Análisis de Performance

### Identificación de Cuellos de Botella

#### 1. Análisis de Latencia

```python
# Análisis de latencia por operación
def analyze_latency():
    """Analizar latencia de operaciones"""
    
    # Operaciones más lentas
    slow_operations = [
        {"operation": "encrypt_customer_data", "avg_latency": 0.05, "p95_latency": 0.08},
        {"operation": "save_customer_db", "avg_latency": 0.08, "p95_latency": 0.12},
        {"operation": "validate_jwt_token", "avg_latency": 0.003, "p95_latency": 0.005},
    ]
    
    return slow_operations
```

#### 2. Análisis de Dependencias

```python
# Análisis de dependencias
def analyze_dependencies():
    """Analizar dependencias del sistema"""
    
    dependencies = [
        {
            "service": "poc3-security",
            "dependencies": [
                {"service": "postgres", "latency": 0.08, "error_rate": 0.01},
                {"service": "redis", "latency": 0.002, "error_rate": 0.001},
                {"service": "jaeger", "latency": 0.001, "error_rate": 0.0}
            ]
        }
    ]
    
    return dependencies
```

### Análisis de Traces

#### 1. Traces Lentos

```python
# Identificar traces lentos
def find_slow_traces():
    """Encontrar traces con alta latencia"""
    
    slow_traces = [
        {
            "trace_id": "1234567890abcdef",
            "duration": 0.5,  # 500ms
            "operation": "POST /customers",
            "bottlenecks": [
                {"operation": "encrypt_customer_data", "duration": 0.2},
                {"operation": "save_customer_db", "duration": 0.25}
            ]
        }
    ]
    
    return slow_traces
```

#### 2. Traces con Errores

```python
# Identificar traces con errores
def find_error_traces():
    """Encontrar traces con errores"""
    
    error_traces = [
        {
            "trace_id": "2345678901bcdefg",
            "operation": "POST /auth/login",
            "error": "Invalid credentials",
            "error_span": "validate_credentials",
            "duration": 0.1
        }
    ]
    
    return error_traces
```

---

## 🔧 Troubleshooting

### Problemas Comunes

#### 1. Jaeger No Inicia

```bash
# Verificar logs de Jaeger
docker-compose logs jaeger

# Verificar puertos
lsof -i :16686  # Jaeger UI
lsof -i :14268  # Jaeger Collector
lsof -i :6831   # Jaeger Agent

# Verificar configuración
docker-compose exec jaeger jaeger --help
```

#### 2. Spans No Aparecen

```bash
# Verificar que el agente esté recibiendo spans
docker-compose logs jaeger | grep "Received span"

# Verificar configuración de muestreo
curl http://localhost:16686/api/services

# Verificar instrumentación
curl http://localhost:8083/metrics | grep jaeger
```

#### 3. Traces Incompletos

```bash
# Verificar propagación de contexto
curl -H "traceparent: 00-1234567890abcdef-fedcba0987654321-01" \
     http://localhost:8083/customers

# Verificar configuración de contexto
docker-compose exec api_poc3 python -c "from opentelemetry import trace; print(trace.get_tracer_provider())"
```

### Verificación de Estado

#### 1. Health Checks

```bash
# Verificar estado de Jaeger
curl http://localhost:16686/api/services

# Verificar estado del agente
curl http://localhost:14268/api/services

# Verificar métricas de Jaeger
curl http://localhost:16686/metrics
```

#### 2. Verificación de Instrumentación

```bash
# Verificar que la instrumentación esté activa
curl http://localhost:8083/metrics | grep opentelemetry

# Verificar spans generados
curl http://localhost:8083/customers
# Luego verificar en Jaeger UI: http://localhost:16686
```

### Logs de Debugging

```bash
# Logs de Jaeger
docker-compose logs -f jaeger

# Logs del POC3 con tracing
docker-compose logs -f api_poc3 | grep -i trace

# Logs con timestamps
docker-compose logs -t jaeger
```

---

## 📚 Mejores Prácticas

### 1. Configuración de Spans

#### Nomenclatura

```python
# ✅ Bueno: Nombres descriptivos
"create_customer"
"encrypt_customer_data"
"validate_jwt_token"
"save_customer_db"

# ❌ Malo: Nombres genéricos
"operation"
"process"
"handle"
"execute"
```

#### Atributos

```python
# ✅ Bueno: Atributos estructurados
span.set_attribute("user.role", "admin")
span.set_attribute("operation.type", "create")
span.set_attribute("db.table", "customers")

# ❌ Malo: Atributos confusos
span.set_attribute("data", "some_data")
span.set_attribute("info", "additional_info")
span.set_attribute("extra", "more_data")
```

### 2. Configuración de Muestreo

#### Muestreo Apropiado

```python
# ✅ Bueno: Muestreo configurado por ambiente
# Desarrollo: 100% muestreo
JAEGER_SAMPLER_PARAM=1

# Producción: 10% muestreo
JAEGER_SAMPLER_PARAM=0.1

# ❌ Malo: Muestreo fijo
JAEGER_SAMPLER_PARAM=1  # Siempre 100%
```

#### Muestreo Adaptativo

```python
# ✅ Bueno: Muestreo adaptativo
JAEGER_SAMPLER_TYPE=probabilistic
JAEGER_SAMPLER_PARAM=0.1  # 10% de muestreo

# ❌ Malo: Muestreo constante en producción
JAEGER_SAMPLER_TYPE=const
JAEGER_SAMPLER_PARAM=1
```

### 3. Gestión de Contexto

#### Propagación de Contexto

```python
# ✅ Bueno: Propagación explícita
def process_request(request):
    context = extract_trace_context(request)
    with trace.set_span_in_context(context):
        return process_with_context()

# ❌ Malo: Contexto implícito
def process_request(request):
    return process_without_context()
```

#### Contexto de Usuario

```python
# ✅ Bueno: Contexto de usuario estructurado
def add_user_context(span, user):
    span.set_attribute("user.id", user.id)
    span.set_attribute("user.role", user.role)
    span.set_attribute("user.mfa_enabled", user.mfa_enabled)

# ❌ Malo: Contexto de usuario genérico
def add_user_context(span, user):
    span.set_attribute("user", str(user))
```

### 4. Análisis de Traces

#### Consultas Eficientes

```python
# ✅ Bueno: Consultas específicas
# Buscar traces de operaciones específicas
# Filtrar por duración
# Agrupar por usuario

# ❌ Malo: Consultas muy amplias
# Buscar todos los traces
# Sin filtros
# Sin agrupación
```

#### Análisis de Performance

```python
# ✅ Bueno: Análisis estructurado
def analyze_performance():
    return {
        "slow_operations": find_slow_operations(),
        "error_patterns": find_error_patterns(),
        "bottlenecks": identify_bottlenecks()
    }

# ❌ Malo: Análisis ad-hoc
def analyze_performance():
    # Análisis manual sin estructura
    pass
```

---

## 🎯 Métricas Recomendadas para POC3

### 1. Métricas de Tracing

```promql
# SLI (Service Level Indicators)
# Disponibilidad de tracing
rate(jaeger_spans_created_total[5m]) / rate(jaeger_spans_created_total[5m])

# Latencia de spans
histogram_quantile(0.95, rate(jaeger_span_duration_seconds_bucket[5m]))

# Throughput de traces
rate(jaeger_traces_created_total[5m])

# Error rate en spans
rate(jaeger_spans_created_total{status="error"}[5m]) / rate(jaeger_spans_created_total[5m])
```

### 2. Métricas de Performance

```promql
# Operaciones más lentas
topk(5, sum by (operation_name) (rate(jaeger_span_duration_seconds_sum[5m])))

# Dependencias más lentas
topk(5, sum by (service_name) (rate(jaeger_span_duration_seconds_sum[5m])))

# Traces con errores
sum by (operation_name) (rate(jaeger_spans_created_total{status="error"}[5m]))
```

### 3. Métricas de Seguridad

```promql
# Traces de autenticación
rate(jaeger_spans_created_total{operation_name=~".*auth.*"}[5m])

# Traces de encriptación
rate(jaeger_spans_created_total{operation_name=~".*encrypt.*"}[5m])

# Traces de operaciones sensibles
rate(jaeger_spans_created_total{operation_name=~".*customer.*"}[5m])
```

---

## 🎯 Conclusión

Jaeger en el POC3 Security proporciona:

### ✅ **Beneficios Logrados**

1. **Tracing Distribuido**: Visibilidad completa del flujo de requests
2. **Análisis de Performance**: Identificación de cuellos de botella
3. **Debugging Eficiente**: Diagnóstico rápido de problemas
4. **Monitoreo de Dependencias**: Análisis de interacciones entre servicios
5. **Análisis de Seguridad**: Trazabilidad de operaciones sensibles

### 🔧 **Características Técnicas**

- **Instrumentación Automática**: OpenTelemetry con FastAPI
- **Propagación de Contexto**: Headers HTTP y W3C Trace Context
- **Muestreo Configurable**: Adaptativo por ambiente
- **Almacenamiento Eficiente**: In-memory con configuración flexible
- **UI Intuitiva**: Visualización y análisis de traces

### 🚀 **Próximos Pasos**

1. **Implementar más instrumentación** en operaciones críticas
2. **Configurar alertas** basadas en latencia de traces
3. **Optimizar muestreo** para producción
4. **Implementar análisis automático** de traces
5. **Configurar retención** según necesidades de compliance

---

**Última actualización**: $(date)
**Versión del documento**: 1.0.0
**Autor**: Equipo de Desarrollo MediSupply
