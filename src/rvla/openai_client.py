"""Centralized OpenAI client initialization with compatibility fixes."""

import os
from typing import Any
from openai import OpenAI
import httpx


def get_openai_client() -> OpenAI:
    """Get OpenAI client with compatibility fixes for httpx/proxies issues."""
    try:
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except TypeError as e:
        if "proxies" in str(e):
            # Workaround for httpx compatibility issue
            # Create httpx client explicitly without proxies parameter
            http_client = httpx.Client()
            return OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                http_client=http_client
            )
        else:
            raise
