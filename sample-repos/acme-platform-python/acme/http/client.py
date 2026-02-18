"""
Acme HTTP Client — standard wrapper for all outgoing HTTP calls.

Injects X-Acme-Service and X-Acme-Request-ID headers.
Includes retry with exponential backoff.
"""

import time
import uuid
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class AcmeHTTPClient:
    """Standard Acme HTTP client with retry, tracing, and auth propagation.

    All outgoing HTTP calls MUST use this instead of requests.get/post directly.
    """

    def __init__(
        self,
        service_name: str,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 0.1,
    ):
        self.service_name = service_name
        self.timeout = timeout

        self.session = requests.Session()

        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _prepare_headers(self, headers: Optional[dict] = None) -> dict:
        """Inject Acme standard headers into every request."""
        h = headers or {}
        h["X-Acme-Service"] = self.service_name
        h["X-Acme-Request-ID"] = f"acme-{uuid.uuid4().hex[:16]}"
        return h

    def get(self, url: str, **kwargs) -> requests.Response:
        kwargs["headers"] = self._prepare_headers(kwargs.get("headers"))
        kwargs.setdefault("timeout", self.timeout)
        return self.session.get(url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        kwargs["headers"] = self._prepare_headers(kwargs.get("headers"))
        kwargs.setdefault("timeout", self.timeout)
        return self.session.post(url, **kwargs)

    def put(self, url: str, **kwargs) -> requests.Response:
        kwargs["headers"] = self._prepare_headers(kwargs.get("headers"))
        kwargs.setdefault("timeout", self.timeout)
        return self.session.put(url, **kwargs)

    def delete(self, url: str, **kwargs) -> requests.Response:
        kwargs["headers"] = self._prepare_headers(kwargs.get("headers"))
        kwargs.setdefault("timeout", self.timeout)
        return self.session.delete(url, **kwargs)
