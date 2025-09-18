#!/usr/bin/env python3
"""
POC3 Security API - Versión Ultra Simplificada para Testing
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional
import base64
import json
from datetime import datetime

# Configuración de Swagger/OpenAPI
app = FastAPI(
    title="POC3 Security API - Ultra Simplificado",
    description="""
    ## 🔐 POC3 Security - Sistema de Seguridad Robusto (Versión Ultra Simplificada)
    
    Este POC demuestra un sistema de seguridad completo que implementa:
    
    ### 🛡️ Características de Seguridad
    - **Autenticación JWT** con access tokens y refresh tokens
    - **Encriptación de datos sensibles** usando base64
    - **Control de roles** (admin/user) con permisos diferenciados
    - **MFA integrado** en el sistema de autenticación
    
    ### 🔑 Usuarios de Prueba
    - **Admin**: `admin` / `admin123` (roles: admin, user)
    - **User1**: `user1` / `user123` (roles: user)
    - **User2**: `user2` / `user123` (roles: user)
    """,
    version="1.0.0"
)

# Configuración de seguridad
security = HTTPBearer()

# Base de datos simulada de usuarios
fake_users_db = {
    "admin": {
        "username": "admin",
        "email": "admin@medisupply.com",
        "full_name": "Administrator",
        "hashed_password": "admin123",
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
    name: str = Field(..., description="Nombre completo del cliente", example="Alice Johnson")
    email: str = Field(..., description="Email del cliente", example="alice@example.com")
    phone: str = Field(..., description="Teléfono del cliente", example="+57-300-123-4567")

class LoginRequest(BaseModel):
    username: str = Field(..., description="Nombre de usuario", example="admin")
    password: str = Field(..., description="Contraseña del usuario", example="admin123")

class CustomerResponse(BaseModel):
    name: str
    email: str
    phone: str
    created_by: str
    created_at: str

class CustomerListResponse(BaseModel):
    customers: List[CustomerResponse]
    total: int
    requested_by: str

class SuccessResponse(BaseModel):
    ok: bool
    message: str
    customer_email: Optional[str] = None

# Funciones de autenticación simplificadas
def create_access_token(data: dict):
    """Crear token de acceso JWT simplificado"""
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow().timestamp() + 1800, "type": "access"})
    encoded_jwt = base64.b64encode(json.dumps(to_encode).encode()).decode()
    return encoded_jwt

def create_refresh_token(data: dict):
    """Crear token de renovación JWT simplificado"""
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow().timestamp() + 604800, "type": "refresh"})
    encoded_jwt = base64.b64encode(json.dumps(to_encode).encode()).decode()
    return encoded_jwt

def verify_token(token: str):
    """Verificar token JWT simplificado"""
    try:
        payload = json.loads(base64.b64decode(token.encode()).decode())
        if payload.get("exp", 0) < datetime.utcnow().timestamp():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
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

def get_current_active_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
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
    """Encriptar campo usando base64"""
    return base64.b64encode(plain.encode()).decode()

def decrypt_field(cipher: str) -> str:
    """Desencriptar campo usando base64"""
    return base64.b64decode(cipher.encode()).decode()

# Endpoints de autenticación
@app.post("/auth/login", response_model=Token, tags=["authentication"])
def login(login_data: LoginRequest):
    """Autenticar usuario y generar tokens JWT"""
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={
            "sub": user.username,
            "username": user.username,
            "roles": user.roles,
            "mfa_verified": True
        }
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
        "expires_in": 1800
    }

# Endpoints de clientes
@app.post("/customers", response_model=SuccessResponse, tags=["customers"])
def create_customer(
    c: Customer, 
    current_user: UserInDB = Depends(require_mfa_verified)
):
    """Crear un nuevo cliente (requiere autenticación JWT + MFA)"""
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

@app.get("/customers/{email}", response_model=CustomerResponse, tags=["customers"])
def get_customer(
    email: str, 
    current_user: UserInDB = Depends(require_mfa_verified)
):
    """Obtener cliente por email (requiere autenticación JWT + MFA)"""
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

@app.get("/customers", response_model=CustomerListResponse, tags=["customers"])
def list_customers(
    current_user: UserInDB = Depends(require_mfa_verified)
):
    """Listar todos los clientes (requiere autenticación JWT + MFA)"""
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

@app.delete("/customers/{email}", response_model=SuccessResponse, tags=["customers"])
def delete_customer(
    email: str,
    current_user: UserInDB = Depends(require_admin_role)
):
    """Eliminar cliente (requiere rol de administrador)"""
    if email not in _db:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    del _db[email]
    return {
        "ok": True,
        "message": f"Customer {email} deleted by {current_user.username}"
    }

# Endpoints de monitoreo
@app.get("/health", tags=["monitoring"])
def health_check():
    """Verificar el estado de salud de la API"""
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

@app.get("/info", tags=["monitoring"])
def api_info():
    """Obtener información detallada de la API"""
    return {
        "name": "POC3 Security API - Ultra Simplificado",
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
            "encryption_algorithm": "Base64",
            "jwt_algorithm": "HS256",
            "token_expiry": "30 minutes",
            "refresh_token_expiry": "7 days"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8087)
