from redis import Redis

from app.core.config import settings

redis_client = Redis.from_url(settings.redis_uri, decode_responses=True) if settings.redis_uri else None
