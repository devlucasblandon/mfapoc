
import json
import redis
from common.config import REDIS_URL, CACHE_TTL_SECONDS

_r = redis.from_url(REDIS_URL, decode_responses=True)

def get(key: str):
    val = _r.get(key)
    return json.loads(val) if val else None

def set(key: str, value, ttl=CACHE_TTL_SECONDS):
    _r.setex(key, ttl, json.dumps(value))

def delete(key: str):
    _r.delete(key)
