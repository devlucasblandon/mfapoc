
from fastapi import FastAPI, Header, HTTPException, Response
from pydantic import BaseModel
from hashlib import sha256
from common.observability import MetricsMiddleware, metrics_asgi_app

app = FastAPI(title="POC4 Offline API")
app.add_middleware(MetricsMiddleware)
app.mount("/metrics", metrics_asgi_app())

class OrderLine(BaseModel):
    sku: str
    qty: int

class Order(BaseModel):
    orderId: str
    lines: list[OrderLine]

_store = {}

@app.post("/orders")
def create_order(order: Order, idempotency_key: str = Header(default="")):
    if not idempotency_key:
        raise HTTPException(400, "Missing Idempotency-Key")
    if idempotency_key in _store:
        return _store[idempotency_key]
    etag = sha256((order.orderId + str(order.lines)).encode()).hexdigest()
    resp = {"orderId": order.orderId, "status": "created", "etag": etag}
    _store[idempotency_key] = resp
    return resp

@app.put("/orders/{order_id}")
def update_order(order_id: str, order: Order, if_match: str | None = Header(default=None)):
    new_etag = sha256((order.orderId + str(order.lines)).encode()).hexdigest()
    if if_match and if_match != new_etag:
        raise HTTPException(412, "ETag mismatch")
    return {"orderId": order.orderId, "status": "updated", "etag": new_etag}
