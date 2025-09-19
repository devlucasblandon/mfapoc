# Guía de Implementación JWT - POC3 Security

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Arquitectura de la Implementación](#arquitectura-de-la-implementación)
3. [Análisis del Código](#análisis-del-código)
4. [Flujo de Implementación](#flujo-de-implementación)
5. [Configuración y Variables](#configuración-y-variables)
6. [Estructura de Datos](#estructura-de-datos)
7. [Funciones Principales](#funciones-principales)
8. [Integración con FastAPI](#integración-con-fastapi)
9. [Manejo de Errores](#manejo-de-errores)
10. [Testing de la Implementación](#testing-de-la-implementación)
11. [Consideraciones de Seguridad](#consideraciones-de-seguridad)
12. [Optimizaciones y Mejoras](#optimizaciones-y-mejoras)

---

## 🎯 Introducción

Este documento explica en detalle la implementación de JWT (JSON Web Tokens) en el POC3 Security. La implementación incluye autenticación basada en tokens, control de roles, y integración completa con FastAPI.

### Objetivos de la Implementación

- **Autenticación Stateless**: Sin almacenamiento de sesiones en servidor
- **Control de Acceso**: Sistema de roles granular
- **Seguridad**: Tokens firmados y con expiración
- **Escalabilidad**: Fácil distribución en múltiples servidores
- **Compatibilidad**: Integración con FastAPI y middleware existente

---

## 🏗️ Arquitectura de la Implementación

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                    POC3 Security JWT                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   FastAPI App   │    │   JWT Service   │                │
│  │   (api.py)      │◄──►│   (auth.py)     │                │
│  └─────────────────┘    └─────────────────┘                │
│           │                       │                        │
│           ▼                       ▼                        │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   Endpoints     │    │   Token Utils   │                │
│  │   Protected     │    │   - create_*    │                │
│  │   - /customers  │    │   - verify_*    │                │
│  │   - /auth/*     │    │   - validate_*  │                │
│  └─────────────────┘    └─────────────────┘                │
│           │                       │                        │
│           ▼                       ▼                        │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   Middleware    │    │   User DB       │                │
│  │   - HTTPBearer  │    │   (Simulated)   │                │
│  │   - Dependencies│    │   - fake_users  │                │
│  └─────────────────┘    └─────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### Componentes Principales

1. **`poc3_security/auth.py`** - Módulo principal de JWT
2. **`poc3_security/api.py`** - Endpoints que usan JWT
3. **`requirements.txt`** - Dependencias JWT
4. **Middleware FastAPI** - Integración automática

---

## 🔍 Análisis del Código

### Estructura del Módulo `auth.py`

```python
# Imports y configuración
import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# Configuración de JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
```

#### Explicación de la Configuración

- **SECRET_KEY**: Clave secreta para firmar tokens (debe ser única por entorno)
- **ALGORITHM**: Algoritmo de firma (HS256 es seguro y eficiente)
- **ACCESS_TOKEN_EXPIRE_MINUTES**: Tiempo de vida del token de acceso
- **REFRESH_TOKEN_EXPIRE_DAYS**: Tiempo de vida del refresh token

### Modelos de Datos

```python
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None
    roles: list = []
    mfa_verified: bool = False

class User(BaseModel):
    username: str
    email: str
    full_name: str
    roles: list = []
    is_active: bool = True

class UserInDB(User):
    hashed_password: str
```

#### Explicación de los Modelos

- **Token**: Estructura de respuesta para login/refresh
- **TokenData**: Datos extraídos del token JWT
- **User**: Modelo público del usuario
- **UserInDB**: Modelo interno con contraseña hasheada

---

## 🔄 Flujo de Implementación

### 1. Proceso de Login

```python
@app.post("/auth/login", response_model=Token)
def login(login_data: LoginRequest):
    # 1. Autenticar usuario
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect credentials")
    
    # 2. Crear access token
    access_token = create_access_token(
        data={
            "sub": user.username,
            "username": user.username,
            "roles": user.roles,
            "mfa_verified": True
        },
        expires_delta=timedelta(minutes=30)
    )
    
    # 3. Crear refresh token
    refresh_token = create_refresh_token(
        data={
            "sub": user.username,
            "username": user.username,
            "roles": user.roles
        }
    )
    
    # 4. Retornar tokens
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 30 * 60
    }
```

### 2. Proceso de Validación de Token

```python
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # 1. Extraer token del header
    token = credentials.credentials
    
    # 2. Verificar y decodificar token
    payload = verify_token(token)
    
    # 3. Extraer username
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # 4. Obtener usuario de la base de datos
    user = get_user(username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
```

### 3. Proceso de Refresh Token

```python
@app.post("/auth/refresh", response_model=Token)
def refresh_token(refresh_data: RefreshTokenRequest):
    # 1. Verificar refresh token
    payload = verify_token(refresh_data.refresh_token)
    
    # 2. Validar tipo de token
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    
    # 3. Crear nuevo access token
    access_token = create_access_token(
        data={
            "sub": payload.get("sub"),
            "username": payload.get("username"),
            "roles": payload.get("roles", []),
            "mfa_verified": True
        },
        expires_delta=timedelta(minutes=30)
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_data.refresh_token,
        "token_type": "bearer",
        "expires_in": 30 * 60
    }
```

---

## ⚙️ Configuración y Variables

### Variables de Entorno

```bash
# Archivo .env (recomendado para desarrollo)
JWT_SECRET_KEY=your-super-secret-key-change-in-production
CRYPTO_KEY_FILE=.devkey

# Para producción
JWT_SECRET_KEY=$(openssl rand -base64 32)
```

### Configuración de Tokens

```python
# Configuración en auth.py
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-key")
ALGORITHM = "HS256"  # HMAC con SHA-256
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutos
REFRESH_TOKEN_EXPIRE_DAYS = 7     # 7 días
```

### Configuración de Seguridad

```python
# Esquema de seguridad HTTPBearer
security = HTTPBearer()

# Headers requeridos
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}
```

---

## 📊 Estructura de Datos

### Payload del Access Token

```json
{
    "sub": "admin",                    // Subject (username)
    "username": "admin",               // Username
    "roles": ["admin", "user"],        // Roles del usuario
    "mfa_verified": true,              // MFA verificado
    "type": "access",                  // Tipo de token
    "exp": 1735728000,                 // Expiración (timestamp)
    "iat": 1735726200                  // Emitido en (timestamp)
}
```

### Payload del Refresh Token

```json
{
    "sub": "admin",                    // Subject (username)
    "username": "admin",               // Username
    "roles": ["admin", "user"],        // Roles del usuario
    "type": "refresh",                 // Tipo de token
    "exp": 1736332800,                 // Expiración (7 días)
    "iat": 1735726200                  // Emitido en (timestamp)
}
```

### Base de Datos de Usuarios

```python
fake_users_db = {
    "admin": {
        "username": "admin",
        "email": "admin@medisupply.com",
        "full_name": "Administrator",
        "hashed_password": "admin123",  # En producción usar bcrypt
        "roles": ["admin", "user"],
        "is_active": True
    },
    "user1": {
        "username": "user1",
        "email": "user1@medisupply.com",
        "full_name": "Test User 1",
        "hashed_password": "user123",
        "roles": ["user"],
        "is_active": True
    }
}
```

---

## 🔧 Funciones Principales

### 1. Creación de Tokens

```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crear token de acceso JWT
    
    Args:
        data: Datos a incluir en el token
        expires_delta: Tiempo de expiración personalizado
    
    Returns:
        Token JWT firmado
    """
    to_encode = data.copy()
    
    # Calcular expiración
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Agregar metadatos
    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    
    # Firmar y codificar
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

### 2. Verificación de Tokens

```python
def verify_token(token: str) -> Dict[str, Any]:
    """
    Verificar y decodificar token JWT
    
    Args:
        token: Token JWT a verificar
    
    Returns:
        Payload decodificado del token
    
    Raises:
        HTTPException: Si el token es inválido o expirado
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

### 3. Autenticación de Usuarios

```python
def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """
    Autenticar usuario con username y password
    
    Args:
        username: Nombre de usuario
        password: Contraseña
    
    Returns:
        Usuario autenticado o None si falla
    """
    user = get_user(username)
    if not user:
        return None
    if user.hashed_password != password:  # En producción usar bcrypt
        return None
    return user
```

### 4. Control de Roles

```python
def require_role(required_role: str):
    """
    Decorator para requerir un rol específico
    
    Args:
        required_role: Rol requerido
    
    Returns:
        Dependency que valida el rol
    """
    def role_checker(current_user: UserInDB = Depends(get_current_active_user)) -> UserInDB:
        if required_role not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return current_user
    return role_checker
```

---

## 🚀 Integración con FastAPI

### 1. Dependencies

```python
# Dependency para obtener usuario actual
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
    # Implementación de validación de token
    pass

# Dependency para usuario activo
def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Dependency para MFA verificado
def require_mfa_verified(current_user: UserInDB = Depends(get_current_active_user)) -> UserInDB:
    return current_user
```

### 2. Uso en Endpoints

```python
# Endpoint protegido básico
@app.get("/customers/{email}")
def get_customer(
    email: str, 
    current_user: UserInDB = Depends(require_mfa_verified)
):
    # Lógica del endpoint
    pass

# Endpoint con rol específico
@app.delete("/customers/{email}")
def delete_customer(
    email: str,
    current_user: UserInDB = Depends(require_admin_role)
):
    # Solo usuarios admin pueden acceder
    pass
```

### 3. Middleware HTTPBearer

```python
# Configuración del esquema de seguridad
security = HTTPBearer()

# Uso automático en dependencies
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # FastAPI automáticamente extrae el token del header Authorization
    token = credentials.credentials
    # Procesar token...
```

---

## ⚠️ Manejo de Errores

### Tipos de Errores JWT

```python
# 1. Token expirado
except jwt.ExpiredSignatureError:
    raise HTTPException(
        status_code=401,
        detail="Token has expired",
        headers={"WWW-Authenticate": "Bearer"}
    )

# 2. Token inválido
except jwt.JWTError:
    raise HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

# 3. Usuario no encontrado
if user is None:
    raise HTTPException(
        status_code=401,
        detail="User not found",
        headers={"WWW-Authenticate": "Bearer"}
    )

# 4. Rol insuficiente
if required_role not in current_user.roles:
    raise HTTPException(
        status_code=403,
        detail=f"Role '{required_role}' required"
    )
```

### Códigos de Estado HTTP

- **200 OK**: Operación exitosa
- **401 Unauthorized**: Token inválido, expirado o faltante
- **403 Forbidden**: Rol insuficiente
- **404 Not Found**: Usuario o recurso no encontrado
- **422 Unprocessable Entity**: Datos de entrada inválidos

---

## 🧪 Testing de la Implementación

### Pruebas Unitarias

```python
# Ejemplo de prueba unitaria
def test_create_access_token():
    data = {"sub": "testuser", "roles": ["user"]}
    token = create_access_token(data)
    
    # Verificar que el token se crea correctamente
    assert token is not None
    assert isinstance(token, str)
    
    # Verificar que se puede decodificar
    payload = verify_token(token)
    assert payload["sub"] == "testuser"
    assert payload["roles"] == ["user"]
```

### Pruebas de Integración

```python
# Ejemplo de prueba de integración
def test_login_flow():
    # 1. Login
    response = client.post("/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    
    # 2. Extraer token
    token_data = response.json()
    access_token = token_data["access_token"]
    
    # 3. Usar token para acceder a recurso protegido
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/customers", headers=headers)
    assert response.status_code == 200
```

### Pruebas de Seguridad

```python
# Ejemplo de prueba de seguridad
def test_invalid_token():
    headers = {"Authorization": "Bearer invalid-token"}
    response = client.get("/customers", headers=headers)
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]
```

---

## 🔒 Consideraciones de Seguridad

### 1. Gestión de Claves

```python
# ❌ Malo: Clave hardcodeada
SECRET_KEY = "my-secret-key"

# ✅ Bueno: Clave desde variable de entorno
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-key")

# ✅ Mejor: Generar clave segura
SECRET_KEY = os.getenv("JWT_SECRET_KEY") or secrets.token_urlsafe(32)
```

### 2. Validación de Tokens

```python
# Validación estricta de algoritmos
payload = jwt.decode(
    token, 
    SECRET_KEY, 
    algorithms=[ALGORITHM]  # Solo permitir algoritmo específico
)

# Verificación de expiración automática
# jwt.decode() verifica automáticamente la expiración
```

### 3. Manejo de Errores Seguro

```python
# No exponer información sensible en errores
except jwt.JWTError:
    raise HTTPException(
        status_code=401,
        detail="Could not validate credentials",  # Mensaje genérico
        headers={"WWW-Authenticate": "Bearer"}
    )
```

### 4. Headers de Seguridad

```python
# Incluir headers de autenticación
headers = {
    "WWW-Authenticate": "Bearer",
    "Content-Type": "application/json"
}
```

---

## 🚀 Optimizaciones y Mejoras

### 1. Caché de Usuarios

```python
# Implementar caché para usuarios frecuentes
from functools import lru_cache

@lru_cache(maxsize=100)
def get_user_cached(username: str) -> Optional[UserInDB]:
    return get_user(username)
```

### 2. Rate Limiting

```python
# Implementar rate limiting para login
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/login")
@limiter.limit("5/minute")  # Máximo 5 intentos por minuto
def login(request: Request, login_data: LoginRequest):
    # Lógica de login
    pass
```

### 3. Blacklist de Tokens

```python
# Implementar blacklist para tokens revocados
token_blacklist = set()

def is_token_blacklisted(token: str) -> bool:
    return token in token_blacklist

def revoke_token(token: str):
    token_blacklist.add(token)
```

### 4. Logging de Seguridad

```python
import logging

security_logger = logging.getLogger("security")

def log_auth_attempt(username: str, success: bool, ip: str):
    if success:
        security_logger.info(f"Successful login: {username} from {ip}")
    else:
        security_logger.warning(f"Failed login attempt: {username} from {ip}")
```

---

## 📚 Referencias y Recursos

### Documentación Oficial
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io/) - Herramientas y debugger

### Estándares
- [RFC 7519 - JSON Web Token (JWT)](https://tools.ietf.org/html/rfc7519)
- [RFC 7515 - JSON Web Signature (JWS)](https://tools.ietf.org/html/rfc7515)
- [RFC 7516 - JSON Web Encryption (JWE)](https://tools.ietf.org/html/rfc7516)

### Mejores Prácticas
- [OWASP JWT Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [Auth0 JWT Best Practices](https://auth0.com/blog/a-look-at-the-latest-draft-for-jwt-bcp/)

### Herramientas de Testing
- [Postman JWT Testing](https://learning.postman.com/docs/sending-requests/authorization/#bearer-token)
- [K6 JWT Testing](https://k6.io/docs/examples/jwt-authentication/)

---

## 🎯 Conclusión

La implementación de JWT en el POC3 Security proporciona:

### ✅ **Beneficios Logrados**

1. **Autenticación Stateless**: Sin necesidad de almacenar sesiones
2. **Escalabilidad**: Fácil distribución en múltiples servidores
3. **Seguridad**: Tokens firmados con expiración automática
4. **Flexibilidad**: Sistema de roles granular
5. **Integración**: Compatible con FastAPI y middleware existente

### 🔧 **Características Técnicas**

- **Algoritmo**: HMAC-SHA256 para firma
- **Expiración**: 30 minutos para access tokens, 7 días para refresh tokens
- **Roles**: Sistema de roles (admin, user) con control granular
- **MFA**: Integración de multi-factor authentication
- **Compatibilidad**: Endpoints legacy mantenidos

### 🚀 **Próximos Pasos**

1. **Implementar bcrypt** para hash de contraseñas
2. **Agregar rate limiting** para endpoints de autenticación
3. **Implementar blacklist** de tokens revocados
4. **Agregar logging** de seguridad
5. **Optimizar caché** de usuarios

---

**Última actualización**: $(date)
**Versión del documento**: 1.0.0
**Autor**: Equipo de Desarrollo MediSupply
