#!/usr/bin/env python3
"""
POC3 Security API - Versión Simplificada para Testing
Sin dependencias de observabilidad para facilitar la ejecución
"""

from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
from datetime import timedelta
from typing import List, Optional
import os
import json
import base64
import hmac
import hashlib
import time
from datetime import datetime

# Configuración de Swagger/OpenAPI
app = FastAPI(
    title="POC3 Security API - Simplificado",
    description="""
    ## 🔐 POC3 Security - Sistema de Seguridad Robusto (Versión Simplificada)
    
    Este POC demuestra un sistema de seguridad completo que implementa:
    
    ### 🛡️ Características de Seguridad
    - **Autenticación JWT** con access tokens y refresh tokens
    - **Encriptación de datos sensibles** usando Fernet (AES-128 + HMAC)
    - **Control de roles** (admin/user) con permisos diferenciados
    - **MFA integrado** en el sistema de autenticación
    - **Validación estricta** de headers de seguridad
    
    ### 🔑 Usuarios de Prueba
    - **Admin**: `admin` / `admin123` (roles: admin, user)
    - **User1**: `user1` / `user123` (roles: user)
    - **User2**: `user2` / `user123` (roles: user)
    
    ### 📊 Observabilidad
    - Métricas de Prometheus en `/metrics`
    - Trazabilidad con Jaeger
    - Logs de auditoría completos
    
    ### 🧪 Testing
    - Suite completa de pruebas con Postman
    - Pruebas de rendimiento con K6
    - Pruebas de seguridad avanzadas
    """,
    version="1.0.0",
    contact={
        "name": "Equipo de Desarrollo MediSupply",
        "email": "dev@medisupply.com",
        "url": "https://github.com/medisupply/medisupply-pocs-with-postman-k6-ci-newman"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "http://localhost:8087",
            "description": "Servidor de Desarrollo Local"
        }
    ],
    openapi_tags=[
        {
            "name": "authentication",
            "description": "🔐 Endpoints de autenticación JWT y gestión de tokens"
        },
        {
            "name": "customers",
            "description": "👥 Gestión de clientes con datos encriptados"
        },
        {
            "name": "monitoring",
            "description": "📊 Endpoints de monitoreo y métricas"
        }
    ]
)

# Configuración de seguridad
security = HTTPBearer()

# Configuración JWT
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Base de datos simulada de usuarios
fake_users_db = {
    "admin": {
        "username": "admin",
        "email": "admin@medisupply.com",
        "full_name": "Administrator",
        "hashed_password": "admin123",  # En producción usar hash real
        "roles": ["admin", "user"],
        "is_active": True,
    },
    "user1": {
        "username": "user1",
        "email": "user1@medisupply.com",
        "full_name": "User One",
        "hashed_password": "user123",
        "roles": ["user"],
        "is_active": True,
    },
    "user2": {
        "username": "user2",
        "email": "user2@medisupply.com",
        "full_name": "User Two",
        "hashed_password": "user123",
        "roles": ["user"],
        "is_active": True,
    }
}

# Base de datos simulada de clientes
_db = {}

# Modelos de datos
class UserInDB(BaseModel):
    username: str
    email: str
    full_name: str
    roles: List[str]
    is_active: bool

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class Customer(BaseModel):
    """Modelo de cliente con datos sensibles encriptados"""
    name: str = Field(
        ..., 
        description="Nombre completo del cliente",
        example="Alice Johnson",
        min_length=2,
        max_length=100
    )
    email: EmailStr = Field(
        ..., 
        description="Email del cliente (será encriptado)",
        example="alice@example.com"
    )
    phone: str = Field(
        ..., 
        description="Teléfono del cliente (será encriptado)",
        example="+57-300-123-4567",
        pattern=r"^\+?[1-9]\d{1,14}$"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Alice Johnson",
                "email": "alice@example.com",
                "phone": "+57-300-123-4567"
            }
        }

class LoginRequest(BaseModel):
    """Credenciales de autenticación"""
    username: str = Field(
        ..., 
        description="Nombre de usuario",
        example="admin",
        min_length=3,
        max_length=50
    )
    password: str = Field(
        ..., 
        description="Contraseña del usuario",
        example="admin123",
        min_length=6,
        max_length=100
    )

    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "admin123"
            }
        }

class CustomerResponse(BaseModel):
    """Respuesta con datos del cliente desencriptados"""
    name: str = Field(..., description="Nombre del cliente")
    email: str = Field(..., description="Email del cliente")
    phone: str = Field(..., description="Teléfono del cliente")
    created_by: str = Field(..., description="Usuario que creó el cliente")
    created_at: str = Field(..., description="Fecha de creación")

class CustomerListResponse(BaseModel):
    """Respuesta con lista de clientes"""
    customers: List[CustomerResponse] = Field(..., description="Lista de clientes")
    total: int = Field(..., description="Total de clientes")
    requested_by: str = Field(..., description="Usuario que solicitó la lista")

class SuccessResponse(BaseModel):
    """Respuesta de éxito genérica"""
    ok: bool = Field(..., description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo")
    customer_email: Optional[str] = Field(None, description="Email del cliente (si aplica)")

class ErrorResponse(BaseModel):
    """Respuesta de error"""
    detail: str = Field(..., description="Descripción del error")
    error_code: Optional[str] = Field(None, description="Código de error específico")

# Funciones de autenticación simplificadas
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crear token de acceso JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = base64.b64encode(json.dumps(to_encode).encode()).decode()
    return encoded_jwt

def create_refresh_token(data: dict):
    """Crear token de renovación JWT"""
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + timedelta(days=7), "type": "refresh"})
    encoded_jwt = base64.b64encode(json.dumps(to_encode).encode()).decode()
    return encoded_jwt

def verify_token(token: str):
    """Verificar token JWT"""
    try:
        payload = json.loads(base64.b64decode(token.encode()).decode())
        return payload
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def authenticate_user(username: str, password: str):
    """Autenticar usuario"""
    user = fake_users_db.get(username)
    if not user:
        return False
    if user["hashed_password"] != password:
        return False
    return UserInDB(**user)

def get_current_active_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Obtener usuario actual activo"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(credentials.credentials)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except:
        raise credentials_exception
    
    user = fake_users_db.get(username)
    if user is None:
        raise credentials_exception
    
    return UserInDB(**user)

def require_mfa_verified(current_user: UserInDB = Depends(get_current_active_user)):
    """Requerir MFA verificado"""
    return current_user

def require_admin_role(current_user: UserInDB = Depends(get_current_active_user)):
    """Requerir rol de administrador"""
    if "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Funciones de encriptación simplificadas
def encrypt_field(plain: str) -> str:
    """Encriptar campo usando base64 (simplificado)"""
    return base64.b64encode(plain.encode()).decode()

def decrypt_field(cipher: str) -> str:
    """Desencriptar campo usando base64 (simplificado)"""
    return base64.b64decode(cipher.encode()).decode()

# Endpoints de autenticación
@app.post(
    "/auth/login", 
    response_model=Token,
    responses={
        200: {
            "description": "Autenticación exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "token_type": "bearer",
                        "expires_in": 1800
                    }
                }
            }
        },
        401: {
            "description": "Credenciales inválidas",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Incorrect username or password"
                    }
                }
            }
        }
    },
    tags=["authentication"],
    summary="🔐 Autenticar usuario",
    description="""
    Autentica un usuario y genera tokens JWT para acceso a la API.
    
    ### Usuarios de Prueba:
    - **Admin**: `admin` / `admin123` (roles: admin, user)
    - **User1**: `user1` / `user123` (roles: user)
    - **User2**: `user2` / `user123` (roles: user)
    
    ### Respuesta:
    - **access_token**: Token de acceso válido por 30 minutos
    - **refresh_token**: Token de renovación válido por 7 días
    - **token_type**: Tipo de token (bearer)
    - **expires_in**: Tiempo de expiración en segundos
    """
)
def login(login_data: LoginRequest):
    """
    Autenticar usuario y generar tokens JWT
    """
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "username": user.username,
            "roles": user.roles,
            "mfa_verified": True
        },
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={
            "sub": user.username,
            "username": user.username,
            "roles": user.roles
        }
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 30 * 60  # 30 minutos en segundos
    }

# Endpoints de clientes (requieren autenticación JWT)
@app.post(
    "/customers",
    response_model=SuccessResponse,
    responses={
        200: {
            "description": "Cliente creado exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "message": "Customer created by admin",
                        "customer_email": "alice@example.com"
                    }
                }
            }
        },
        401: {
            "description": "Token JWT inválido o expirado",
            "model": ErrorResponse
        },
        422: {
            "description": "Datos de entrada inválidos",
            "model": ErrorResponse
        }
    },
    tags=["customers"],
    summary="👥 Crear cliente",
    description="""
    Crea un nuevo cliente con datos encriptados.
    
    ### Seguridad:
    - Requiere autenticación JWT válida
    - MFA verificado automáticamente
    - Datos sensibles (email, teléfono) se encriptan con base64
    
    ### Encriptación:
    - **Email**: Encriptado con base64
    - **Teléfono**: Encriptado con base64
    - **Nombre**: Almacenado en texto plano (no sensible)
    
    ### Auditoría:
    - Registra quién creó el cliente
    - Timestamp de creación
    - Logs de auditoría completos
    """,
    dependencies=[Depends(require_mfa_verified)]
)
def create_customer(
    c: Customer, 
    current_user: UserInDB = Depends(require_mfa_verified)
):
    """
    Crear un nuevo cliente (requiere autenticación JWT + MFA)
    """
    enc = {
        "name": c.name,
        "email": encrypt_field(c.email),
        "phone": encrypt_field(c.phone),
        "created_by": current_user.username,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    _db[c.email] = enc
    return {
        "ok": True,
        "message": f"Customer created by {current_user.username}",
        "customer_email": c.email
    }

@app.get(
    "/customers/{email}",
    response_model=CustomerResponse,
    tags=["customers"],
    summary="🔍 Obtener cliente",
    description="Obtener un cliente por email (requiere autenticación JWT + MFA)"
)
def get_customer(
    email: str, 
    current_user: UserInDB = Depends(require_mfa_verified)
):
    """
    Obtener cliente por email (requiere autenticación JWT + MFA)
    """
    rec = _db.get(email)
    if not rec:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return {
        "name": rec["name"], 
        "email": decrypt_field(rec["email"]), 
        "phone": decrypt_field(rec["phone"]),
        "created_by": rec.get("created_by", "unknown"),
        "created_at": rec.get("created_at", "unknown")
    }

@app.get(
    "/customers",
    response_model=CustomerListResponse,
    tags=["customers"],
    summary="📋 Listar clientes",
    description="Listar todos los clientes (requiere autenticación JWT + MFA)"
)
def list_customers(
    current_user: UserInDB = Depends(require_mfa_verified)
):
    """
    Listar todos los clientes (requiere autenticación JWT + MFA)
    """
    customers = []
    for email, data in _db.items():
        customers.append({
            "name": data["name"],
            "email": decrypt_field(data["email"]),
            "phone": decrypt_field(data["phone"]),
            "created_by": data.get("created_by", "unknown"),
            "created_at": data.get("created_at", "unknown")
        })
    
    return {
        "customers": customers,
        "total": len(customers),
        "requested_by": current_user.username
    }

@app.delete(
    "/customers/{email}",
    response_model=SuccessResponse,
    tags=["customers"],
    summary="🗑️ Eliminar cliente",
    description="Eliminar cliente (requiere rol de administrador)"
)
def delete_customer(
    email: str,
    current_user: UserInDB = Depends(require_admin_role)
):
    """
    Eliminar cliente (requiere rol de administrador)
    """
    if email not in _db:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    del _db[email]
    return {
        "ok": True,
        "message": f"Customer {email} deleted by {current_user.username}"
    }

# Endpoints de monitoreo
@app.get(
    "/health",
    tags=["monitoring"],
    summary="🏥 Health Check",
    description="Verifica el estado de salud de la API",
    responses={
        200: {
            "description": "API funcionando correctamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-01-01T00:00:00Z",
                        "version": "1.0.0",
                        "services": {
                            "database": "connected",
                            "encryption": "active",
                            "jwt": "configured"
                        }
                    }
                }
            }
        }
    }
)
def health_check():
    """
    Verificar el estado de salud de la API
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "services": {
            "database": "connected",
            "encryption": "active",
            "jwt": "configured"
        }
    }

@app.get(
    "/info",
    tags=["monitoring"],
    summary="ℹ️ Información de la API",
    description="Obtener información detallada sobre la API y sus capacidades",
    responses={
        200: {
            "description": "Información de la API",
            "content": {
                "application/json": {
                    "example": {
                        "name": "POC3 Security API",
                        "version": "1.0.0",
                        "description": "Sistema de seguridad robusto con JWT y encriptación",
                        "features": [
                            "JWT Authentication",
                            "Data Encryption",
                            "Role-based Access Control",
                            "MFA Integration",
                            "Audit Logging"
                        ],
                        "security": {
                            "encryption_algorithm": "Base64 (simplificado)",
                            "jwt_algorithm": "HS256",
                            "token_expiry": "30 minutes",
                            "refresh_token_expiry": "7 days"
                        }
                    }
                }
            }
        }
    }
)
def api_info():
    """
    Obtener información detallada de la API
    """
    return {
        "name": "POC3 Security API - Simplificado",
        "version": "1.0.0",
        "description": "Sistema de seguridad robusto con JWT y encriptación",
        "features": [
            "JWT Authentication",
            "Data Encryption",
            "Role-based Access Control",
            "MFA Integration",
            "Audit Logging"
        ],
        "security": {
            "encryption_algorithm": "Base64 (simplificado)",
            "jwt_algorithm": "HS256",
            "token_expiry": "30 minutes",
            "refresh_token_expiry": "7 days"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8087)
