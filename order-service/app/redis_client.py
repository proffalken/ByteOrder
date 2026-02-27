import redis as redis_lib
from app.config import settings

_client = None


def get_redis() -> redis_lib.Redis:
    global _client
    if _client is None:
        _client = redis_lib.from_url(settings.redis_url, decode_responses=False)
    return _client
