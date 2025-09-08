
CREATE TABLE IF NOT EXISTS inventory(
  sku TEXT PRIMARY KEY,
  lot_id TEXT NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  qty INT NOT NULL,
  warehouse_id TEXT NOT NULL
);

INSERT INTO inventory (sku, lot_id, expires_at, qty, warehouse_id) VALUES
('SKU-1','L-001','2026-01-01',100,'W-BOG-01')
ON CONFLICT (sku) DO NOTHING;
