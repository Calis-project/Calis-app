from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

import httpx

from .base import ProviderError


T = TypeVar("T")


def with_retries(
    operation: Callable[[], T],
    *,
    attempts: int = 3,
    retry_statuses: tuple[int, ...] = (429, 500, 502, 503, 504),
) -> T:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return operation()
        except httpx.HTTPStatusError as error:
            last_error = error
            if error.response.status_code not in retry_statuses:
                raise ProviderError(_http_error_message(error)) from error
            if attempt + 1 < attempts:
                retry_after = error.response.headers.get("retry-after")
                delay = float(retry_after) if retry_after else 0.75 * (2**attempt)
                time.sleep(min(delay, 8.0))
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            last_error = error
            if attempt + 1 < attempts:
                time.sleep(0.75 * (2**attempt))
    if isinstance(last_error, httpx.HTTPStatusError):
        raise ProviderError(_http_error_message(last_error)) from last_error
    raise ProviderError(f"Provider request failed: {last_error}") from last_error


def _http_error_message(error: httpx.HTTPStatusError) -> str:
    try:
        body = error.response.json()
        detail = (
            body.get("error", {}).get("message")
            if isinstance(body.get("error"), dict)
            else body.get("error")
        )
    except ValueError:
        detail = error.response.text[:500]
    return (
        f"Provider returned HTTP {error.response.status_code}: "
        f"{detail or 'unknown error'}"
    )

