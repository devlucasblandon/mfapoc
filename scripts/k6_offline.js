import http from 'k6/http'; import { check } from 'k6';
export let options = { vus: 10, duration: '2m' };
export default function () {
  const key = `idem-${__VU}-${__ITER}`;
  const order = JSON.stringify({ orderId: `O-${__VU}`, lines: [{ sku: "SKU-1", qty: 1 }] });
  let res = http.post('http://localhost:8084/orders', order, { headers: {'Content-Type':'application/json','Idempotency-Key': key }});
  check(res, { 'status 200': r => r.status === 200 });
}
