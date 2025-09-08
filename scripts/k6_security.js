import http from 'k6/http'; import { check } from 'k6';
export let options = { vus: 5, duration: '1m' };
export default function () {
  const payload = JSON.stringify({ name: "Test", email: `user${__VU}@example.com`, phone: "+57 300 000 0000" });
  const params = { headers: { 'Content-Type': 'application/json', 'x-mfa': 'true' } };
  const res = http.post('http://localhost:8083/customers', payload, params);
  check(res, { '201/200': r => r.status === 200 || r.status === 201 });
}
