
import os

POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/medisupply")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
OTLP_ENDPOINT = os.getenv("OTLP_ENDPOINT", "http://localhost:4318")
JWT_ISSUER = os.getenv("JWT_ISSUER", "http://localhost:8082/realms/master")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "account")
JWT_ALGO = "RS256"
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "60"))
