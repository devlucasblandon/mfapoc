
from prometheus_client import Histogram, Counter, Gauge, make_asgi_app
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
import time

REQUEST_LATENCY = Histogram("http_request_duration_seconds", "Latency", ["method","route","status"])
REQUEST_COUNT = Counter("http_requests_total", "Requests", ["method","route","status"])

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        dur = time.time() - start
        route = request.url.path
        REQUEST_LATENCY.labels(request.method, route, str(response.status_code)).observe(dur)
        REQUEST_COUNT.labels(request.method, route, str(response.status_code)).inc()
        return response

def metrics_asgi_app():
    return make_asgi_app()
