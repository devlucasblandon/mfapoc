# 🔍 Cómo Ver Swagger del POC 3

## 📋 Resumen

Te explico cómo ver la documentación Swagger del POC 3 Security con todas las mejoras implementadas.

## 🚀 Métodos para Ver Swagger

### **Método 1: Usando Docker (Recomendado)**

```bash
# 1. Ir al directorio del proyecto
cd /Users/lucasblandon/PROYECTOFINAL/POCsemana6local/medisupply-pocs-with-postman-k6-ci-newman

# 2. Levantar el POC 3 con Docker
docker-compose --profile poc3 up -d api_poc3

# 3. Verificar que esté ejecutándose
docker ps | grep poc3

# 4. Acceder a Swagger
open http://localhost:8083/docs
```

### **Método 2: Ejecución Local (Si Docker no funciona)**

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar POC 3
uvicorn poc3_security.api:app --reload --port 8083

# 3. Acceder a Swagger
open http://localhost:8083/docs
```

### **Método 3: Versión Simplificada (Sin Observabilidad)**

```bash
# 1. Ejecutar versión simplificada
uvicorn poc3_security.api_simple:app --port 8086

# 2. Acceder a Swagger
open http://localhost:8086/docs
```

## 🌐 URLs de Swagger

### **Swagger UI (Interfaz Interactiva)**
```
http://localhost:8083/docs
```

### **ReDoc (Documentación Alternativa)**
```
http://localhost:8083/redoc
```

### **Esquema OpenAPI (JSON)**
```
http://localhost:8083/openapi.json
```

## 🔧 Solución de Problemas

### **Error: Puerto ocupado**
```bash
# Verificar qué está usando el puerto
lsof -i :8083

# Matar proceso si es necesario
kill -9 <PID>

# Usar puerto diferente
uvicorn poc3_security.api:app --port 8084
```

### **Error: Módulo no encontrado**
```bash
# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación
python -c "import poc3_security.api; print('OK')"
```

### **Error: Dependencias de observabilidad**
```bash
# Usar versión simplificada
uvicorn poc3_security.api_simple:app --port 8086
```

## 🎯 Características de Swagger Implementadas

### **1. Documentación Completa**
- ✅ Descripción detallada de la API
- ✅ Información de contacto del equipo
- ✅ Licencia MIT
- ✅ Servidores de desarrollo y producción

### **2. Sistema de Tags Organizado**
- 🔐 **authentication** - Endpoints de autenticación JWT
- 👥 **customers** - Gestión de clientes con encriptación
- 🔄 **legacy** - Endpoints de compatibilidad
- 📊 **monitoring** - Health checks y métricas

### **3. Modelos Pydantic Mejorados**
- ✅ Validaciones de entrada (email, teléfono, longitud)
- ✅ Ejemplos de request/response
- ✅ Documentación detallada de cada campo
- ✅ Modelos de respuesta específicos

### **4. Endpoints Documentados**
- ✅ **Login** con usuarios de prueba y ejemplos
- ✅ **Refresh Token** para renovación de tokens
- ✅ **Customers** CRUD con encriptación
- ✅ **Health Check** para estado de la API
- ✅ **API Info** con información detallada

## 🧪 Cómo Probar la API desde Swagger

### **Paso 1: Obtener Token de Autenticación**
1. Ir a `/auth/login`
2. Usar credenciales:
   - **Username**: `admin`
   - **Password**: `admin123`
3. Hacer clic en "Execute"
4. Copiar el `access_token` de la respuesta

### **Paso 2: Autorizar en Swagger**
1. Hacer clic en el botón "Authorize" (🔒) en la parte superior
2. Pegar el token: `Bearer <access_token>`
3. Hacer clic en "Authorize"

### **Paso 3: Probar Endpoints de Clientes**
1. Ir a `/customers` (POST)
2. Usar el ejemplo de request:
   ```json
   {
     "name": "Alice Johnson",
     "email": "alice@example.com",
     "phone": "+57-300-123-4567"
   }
   ```
3. Hacer clic en "Execute"

### **Paso 4: Verificar Resultados**
1. Ir a `/customers` (GET) para listar clientes
2. Ir a `/customers/{email}` (GET) para obtener un cliente específico

## 📊 Endpoints Disponibles

### **🔐 Autenticación**
- `POST /auth/login` - Autenticar usuario
- `POST /auth/refresh` - Renovar token
- `GET /auth/me` - Información del usuario actual
- `GET /auth/demo-tokens` - Tokens de demostración
- `GET /auth/token-info/{token}` - Información de token

### **👥 Clientes**
- `POST /customers` - Crear cliente
- `GET /customers` - Listar clientes
- `GET /customers/{email}` - Obtener cliente
- `DELETE /customers/{email}` - Eliminar cliente (solo admin)

### **📊 Monitoreo**
- `GET /health` - Health check
- `GET /info` - Información de la API

## 🔑 Usuarios de Prueba

| Usuario | Contraseña | Roles | Descripción |
|---------|------------|-------|-------------|
| `admin` | `admin123` | admin, user | Acceso completo |
| `user1` | `user123` | user | Acceso limitado |
| `user2` | `user123` | user | Acceso limitado |

## 🛡️ Características de Seguridad

### **Encriptación**
- **Algoritmo**: Fernet (AES-128 + HMAC)
- **Campos Encriptados**: email, phone
- **Campos Planos**: name

### **Autenticación JWT**
- **Algoritmo**: HS256
- **Access Token**: 30 minutos
- **Refresh Token**: 7 días

### **Control de Roles**
- **Admin**: Acceso completo + eliminación
- **User**: Solo lectura y creación

## 📱 Acceso Móvil

También puedes acceder a Swagger desde tu dispositivo móvil:

```
http://<tu-ip-local>:8083/docs
```

Ejemplo:
```
http://192.168.1.100:8083/docs
```

## 🎉 ¡Listo!

Una vez que tengas el POC 3 ejecutándose, podrás:

1. **Ver la documentación completa** en Swagger UI
2. **Probar todos los endpoints** directamente desde el navegador
3. **Autenticarte con JWT** usando el botón Authorize
4. **Crear y gestionar clientes** con datos encriptados
5. **Explorar la API** con ejemplos interactivos

---

**¿Necesitas ayuda?** Si tienes algún problema, revisa la sección de "Solución de Problemas" o ejecuta los comandos de verificación.
