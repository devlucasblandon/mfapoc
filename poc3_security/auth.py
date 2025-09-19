"""
Módulo de autenticación JWT para POC3 Security
Implementa autenticación basada en JWT con validación de tokens
"""

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

# Esquema de seguridad
security = HTTPBearer()

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

# Base de datos simulada de usuarios
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
    },
    "user2": {
        "username": "user2",
        "email": "user2@medisupply.com",
        "full_name": "Test User 2",
        "hashed_password": "user123",
        "roles": ["user"],
        "is_active": True
    }
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crear token de acceso JWT
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """
    Crear token de refresh JWT
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """
    Verificar y decodificar token JWT
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

def get_user(username: str) -> Optional[UserInDB]:
    """
    Obtener usuario de la base de datos simulada
    """
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return UserInDB(**user_dict)
    return None

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """
    Autenticar usuario con username y password
    """
    user = get_user(username)
    if not user:
        return None
    if user.hashed_password != password:  # En producción usar bcrypt
        return None
    return user

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
    """
    Obtener usuario actual desde el token JWT
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """
    Obtener usuario activo actual
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def require_mfa_verified(current_user: UserInDB = Depends(get_current_active_user)) -> UserInDB:
    """
    Requerir que el usuario tenga MFA verificado
    """
    # En un sistema real, esto verificaría el estado MFA del usuario
    # Para el POC, asumimos que si el usuario está autenticado, MFA está verificado
    return current_user

def require_role(required_role: str):
    """
    Decorator para requerir un rol específico
    """
    def role_checker(current_user: UserInDB = Depends(get_current_active_user)) -> UserInDB:
        if required_role not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return current_user
    return role_checker

def require_admin_role(current_user: UserInDB = Depends(require_role("admin"))) -> UserInDB:
    """
    Requerir rol de administrador
    """
    return current_user

# Funciones de utilidad para el POC
def create_demo_tokens() -> Dict[str, str]:
    """
    Crear tokens de demostración para testing
    """
    # Token para admin
    admin_data = {
        "sub": "admin",
        "username": "admin",
        "roles": ["admin", "user"],
        "mfa_verified": True
    }
    
    # Token para usuario regular
    user_data = {
        "sub": "user1",
        "username": "user1", 
        "roles": ["user"],
        "mfa_verified": True
    }
    
    return {
        "admin_token": create_access_token(admin_data),
        "user_token": create_access_token(user_data),
        "admin_refresh": create_refresh_token(admin_data),
        "user_refresh": create_refresh_token(user_data)
    }

def get_token_info(token: str) -> Dict[str, Any]:
    """
    Obtener información del token sin validar expiración (para debugging)
    """
    try:
        # Decodificar sin verificar expiración
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        return payload
    except jwt.JWTError as e:
        return {"error": str(e)}
