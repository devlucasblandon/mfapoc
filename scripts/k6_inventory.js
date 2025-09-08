
import http from 'k6/http'; import { check, Trend } from 'k6';
export let options = { vus: 30, duration: '3m' };
let t = new Trend('inventory_latency');
export default function () {
  const sku = `SKU-${__VU % 100}`;
  const res = http.get(`http://localhost:8080/inventory?sku=${sku}`);
  t.add(res.timings.duration);
  check(res, { 'status == 200': r => r.status === 200 });
}
