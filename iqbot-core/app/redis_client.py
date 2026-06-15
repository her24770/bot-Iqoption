"""Cliente Redis compartido (estado del bot, cache de config, rate limit, logs)."""
import redis

from app.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
