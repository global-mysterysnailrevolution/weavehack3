from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
import re
from typing import Any

from redis import Redis


@dataclass
class Workspace:
    """External memory workspace stored in Redis or in-memory."""

    redis_url: str | None = None
    namespace: str = "rvla"
    _cache: dict[str, Any] = field(default_factory=dict, repr=False)
    _client: Redis | None = field(default=None, init=False, repr=False)

    def connect(self) -> None:
        if self.redis_url and self._client is None:
            # Clean up Redis URL - handle placeholder format
            clean_url = self.redis_url
            
            # If URL contains placeholders, try to construct proper URL
            # Format: redis://:<PASSWORD>:<PORT>/0
            # Expected: redis://:PASSWORD@HOST:PORT/0
            if '<' in clean_url or '>' in clean_url:
                # Extract password from format: redis://:<PASSWORD>:<PORT>/0
                password_match = re.search(r':<([^>]+)>:', clean_url)
                port_match = re.search(r':<([^>]+)>/', clean_url)
                
                if password_match and port_match:
                    password = password_match.group(1)
                    port = port_match.group(1)
                    # Try to get host from environment or use default from notes
                    host = os.getenv("REDIS_HOST", "redis-17120.c289.us-west-1-2.ec2.cloud.redislabs.com")
                    db = clean_url.split('/')[-1] if '/' in clean_url else '0'
                    clean_url = f"redis://:{password}@{host}:{port}/{db}"
                else:
                    # Fallback: try to extract from example format
                    # redis://:<ZM8yGo4rJf9NxyhPauGMtrgqFlpFuKKOT>:<PORT>/0
                    # Default port from example: 17120
                    if 'PORT' in clean_url:
                        clean_url = clean_url.replace('<PORT>', '17120')
                    # Remove remaining brackets but keep content
                    clean_url = re.sub(r'<([^>]+)>', r'\1', clean_url)
            
            try:
                self._client = Redis.from_url(clean_url, decode_responses=True)
                # Test connection
                self._client.ping()
                print(f"[OK] Connected to Redis")
            except Exception as e:
                print(f"[WARN] Redis connection failed: {e}. Falling back to in-memory storage.")
                self.redis_url = None
                self._client = None

    def _key(self, key: str) -> str:
        return f"{self.namespace}:{key}"

    def set(self, key: str, value: Any) -> None:
        if self.redis_url and self._client is not None:
            self.connect()
            if self._client is not None:  # Check again after connect
                payload = json.dumps(value)
                self._client.set(self._key(key), payload)
                return
        self._cache[key] = value

    def get(self, key: str, default: Any | None = None) -> Any:
        if self.redis_url and self._client is not None:
            self.connect()
            if self._client is not None:  # Check again after connect
                payload = self._client.get(self._key(key))
                if payload is None:
                    return default
                return json.loads(payload)
        return self._cache.get(key, default)

    def append(self, key: str, value: Any) -> list[Any]:
        items = list(self.get(key, []))
        items.append(value)
        self.set(key, items)
        return items


def workspace_from_env() -> Workspace:
    redis_url = os.getenv("REDIS_URL")
    return Workspace(redis_url=redis_url)
