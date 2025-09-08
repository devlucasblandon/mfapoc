
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from common import db, cache
from common.observability import MetricsMiddleware, metrics_asgi_app

app = FastAPI(title="POC1 Inventory")
app.add_middleware(MetricsMiddleware)
app.mount("/metrics", metrics_asgi_app())

class InventoryItem(BaseModel):
  sku: str
  lotId: str
  expiresAt: str
  qty: int
  warehouseId: str

@app.get("/health")
def health(): return {"ok": True}

@app.get("/inventory")
def get_inventory(sku: str):
    key = f"inv:{sku}"
    if (v := cache.get(key)): return v
    row = db.fetch_one("""
      SELECT sku, lot_id as "lotId", expires_at as "expiresAt", qty, warehouse_id as "warehouseId"
      FROM inventory WHERE sku=%s LIMIT 1
    """, (sku,))
    if not row: raise HTTPException(status_code=404, detail="SKU not found")
    cache.set(key, row)
    return row
