
import http from 'k6/http'; import { check } from 'k6';
export let options = { rps: 7, duration: '10m' };
export default function () {
  const payload = JSON.stringify({ jobId: `job-${__ITER}`, points: genPoints(30) });
  const res = http.post('http://localhost:8081/routes/solve', payload, { headers: { 'Content-Type': 'application/json' }});
  check(res, { 'status 200': r => r.status === 200 });
}
function genPoints(n){ return Array.from({length:n}, (_,i)=>({id:i, lat:4.6 + Math.random()*0.1, lon:-74.08+Math.random()*0.1})) }
