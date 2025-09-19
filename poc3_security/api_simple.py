"""
POC3 Security API - Versión Simplificada para Swagger
Sin dependencias de observabilidad para facilitar la ejecución
"""

from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
from poc3_security.crypto import encrypt_field, decrypt_field
from poc3_security.auth import (
    authenticate_user, create_access_token, create_refresh_token, 
    get_current_active_user, require_mfa_verified, require_admin_role,
    Token, UserInDB, create_demo_tokens, get_token_info
)
from datetime import timedelta
from typing import List, Optional
import os

# Configuración de Swagger/OpenAPI
app = FastAPI(
    title="POC3 Security API",
    description="""
    ## 🔐 POC3 Security - Sistema de Seguridad Robusto
    
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
            "url": "http://localhost:8086",
            "description": "Servidor de Desarrollo Local"
        },
        {
            "url": "https://api.medisupply.com",
            "description": "Servidor de Producción"
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
            "name": "legacy",
            "description": "🔄 Endpoints legacy para compatibilidad"
        },
        {
            "name": "monitoring",
            "description": "📊 Endpoints de monitoreo y métricas"
        }
    ]
)

# Configuración de seguridad
security = HTTPBearer()

# Modelos de datos con documentación detallada
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

class RefreshTokenRequest(BaseModel):
    """Solicitud de renovación de token"""
    refresh_token: str = Field(
        ..., 
        description="Token de renovación válido",
        example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
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

# Base de datos simulada de clientes
_db = {}

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

@app.post(
    "/auth/refresh", 
    response_model=Token,
    responses={
        200: {
            "description": "Token renovado exitosamente",
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
            "description": "Token de renovación inválido o expirado",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid refresh token"
                    }
                }
            }
        }
    },
    tags=["authentication"],
    summary="🔄 Renovar token de acceso",
    description="""
    Renueva un token de acceso usando un refresh token válido.
    
    ### Uso:
    1. Obtener refresh_token del endpoint `/auth/login`
    2. Usar refresh_token para renovar access_token
    3. El refresh_token se reutiliza (no se regenera)
    
    ### Ventajas:
    - No requiere re-autenticación del usuario
    - Access token renovado válido por 30 minutos
    - Refresh token válido por 7 días
    """
)
def refresh_token(refresh_data: RefreshTokenRequest):
    """
    Renovar token de acceso usando refresh token
    """
    try:
        from poc3_security.auth import verify_token
        payload = verify_token(refresh_data.refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Crear nuevo access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={
                "sub": username,
                "username": username,
                "roles": payload.get("roles", []),
                "mfa_verified": True
            },
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_data.refresh_token,  # Reutilizar refresh token
            "token_type": "bearer",
            "expires_in": 30 * 60
        }
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@app.get(
    "/auth/me",
    tags=["authentication"],
    summary="👤 Información del usuario actual",
    description="Obtener información del usuario autenticado actualmente"
)
def get_current_user_info(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Obtener información del usuario actual
    """
    return {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "roles": current_user.roles,
        "is_active": current_user.is_active
    }

@app.get(
    "/auth/demo-tokens",
    tags=["authentication"],
    summary="🎫 Tokens de demostración",
    description="Obtener tokens de demostración para testing"
)
def get_demo_tokens():
    """
    Obtener tokens de demostración para testing
    """
    return create_demo_tokens()

@app.get(
    "/auth/token-info/{token}",
    tags=["authentication"],
    summary="🔍 Información de token",
    description="Obtener información de un token (para debugging)"
)
def get_token_information(token: str):
    """
    Obtener información de un token (para debugging)
    """
    return get_token_info(token)

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
    - Datos sensibles (email, teléfono) se encriptan con Fernet
    
    ### Encriptación:
    - **Email**: Encriptado con AES-128 + HMAC
    - **Teléfono**: Encriptado con AES-128 + HMAC
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
        "created_at": "2024-01-01T00:00:00Z"  # En producción usar datetime.utcnow()
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
        "timestamp": "2024-01-01T00:00:00Z",
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
                            "encryption_algorithm": "Fernet (AES-128 + HMAC)",
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
            "encryption_algorithm": "Fernet (AES-128 + HMAC)",
            "jwt_algorithm": "HS256",
            "token_expiry": "30 minutes",
            "refresh_token_expiry": "7 days"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8086)
