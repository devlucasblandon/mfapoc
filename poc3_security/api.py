
from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
from common.observability import MetricsMiddleware, metrics_asgi_app
from poc3_security.crypto import encrypt_field, decrypt_field

app = FastAPI(title="POC3 Security")
app.add_middleware(MetricsMiddleware)
app.mount("/metrics", metrics_asgi_app())

# Nota: Para simplificar el POC se simula validación de JWT y MFA:
def require_mfa(x_mfa: str = Header(default="")):
    if x_mfa != "true":
        raise HTTPException(status_code=401, detail="MFA required")
    return True

class Customer(BaseModel):
    name: str
    email: str
    phone: str

_db = {}

@app.post("/customers", dependencies=[Depends(require_mfa)])
def create_customer(c: Customer):
    enc = {
        "name": c.name,
        "email": encrypt_field(c.email),
        "phone": encrypt_field(c.phone),
    }
    _db[c.email] = enc
    return {"ok": True}

@app.get("/customers/{email}", dependencies=[Depends(require_mfa)])
def get_customer(email: str):
    rec = _db.get(email)
    if not rec: raise HTTPException(404, "not found")
    return {"name": rec["name"], "email": decrypt_field(rec["email"]), "phone": decrypt_field(rec["phone"])}
