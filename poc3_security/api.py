
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from common.observability import MetricsMiddleware, metrics_asgi_app
from poc3_security.crypto import encrypt_field, decrypt_field
from poc3_security.auth import (
    authenticate_user, create_access_token, create_refresh_token, 
    get_current_active_user, require_mfa_verified, require_admin_role,
    Token, UserInDB, create_demo_tokens, get_token_info
)
from datetime import timedelta

app = FastAPI(title="POC3 Security with JWT Authentication")
app.add_middleware(MetricsMiddleware)
app.mount("/metrics", metrics_asgi_app())

class Customer(BaseModel):
    name: str
    email: str
    phone: str

class LoginRequest(BaseModel):
    username: str
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# Base de datos simulada de clientes
_db = {}

# Endpoints de autenticación
@app.post("/auth/login", response_model=Token)
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

@app.post("/auth/refresh", response_model=Token)
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

@app.get("/auth/me")
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

@app.get("/auth/demo-tokens")
def get_demo_tokens():
    """
    Obtener tokens de demostración para testing
    """
    return create_demo_tokens()

@app.get("/auth/token-info/{token}")
def get_token_information(token: str):
    """
    Obtener información de un token (para debugging)
    """
    return get_token_info(token)

# Endpoints de clientes (requieren autenticación JWT)
@app.post("/customers")
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

@app.get("/customers/{email}")
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

@app.get("/customers")
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

@app.delete("/customers/{email}")
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

# Endpoint de compatibilidad (mantener para pruebas existentes)
@app.post("/customers-legacy", dependencies=[Depends(require_mfa_verified)])
def create_customer_legacy(c: Customer):
    """
    Endpoint legacy para compatibilidad con pruebas existentes
    """
    enc = {
        "name": c.name,
        "email": encrypt_field(c.email),
        "phone": encrypt_field(c.phone),
    }
    _db[c.email] = enc
    return {"ok": True}

@app.get("/customers-legacy/{email}", dependencies=[Depends(require_mfa_verified)])
def get_customer_legacy(email: str):
    """
    Endpoint legacy para compatibilidad con pruebas existentes
    """
    rec = _db.get(email)
    if not rec:
        raise HTTPException(404, "not found")
    return {
        "name": rec["name"], 
        "email": decrypt_field(rec["email"]), 
        "phone": decrypt_field(rec["phone"])
    }
