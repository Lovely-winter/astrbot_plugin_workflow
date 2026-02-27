"""
Async retry decorator with exponential backoff.
"""
from __future__ import annotations

import asyncio
import functools
import logging
from typing import Callable, Iterable, Type, TypeVar, Awaitable, Optional

T = TypeVar("T")


def async_retry(
	max_retries: int = 3,
	delay: float = 1.0,
	exceptions: Iterable[Type[BaseException]] = (Exception,),
	backoff: float = 2.0,
	max_delay: Optional[float] = None,
	logger: Optional[logging.Logger] = None
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
	"""
	Retry an async function on specified exceptions.

	Args:
		max_retries: Max number of retries after the first failure.
		delay: Initial delay in seconds before retry.
		exceptions: Exception types that should trigger retry.
		backoff: Exponential backoff multiplier.
		max_delay: Max delay between retries.
		logger: Optional logger for retry warnings.
	"""
	if max_retries < 0:
		max_retries = 0
	if delay < 0:
		delay = 0.0
	if backoff < 1.0:
		backoff = 1.0

	log = logger or logging.getLogger(__name__)
	exc_tuple = tuple(exceptions)

	def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
		@functools.wraps(func)
		async def wrapper(*args, **kwargs) -> T:
			attempt = 0
			current_delay = delay
			while True:
				try:
					return await func(*args, **kwargs)
				except exc_tuple as exc:  # type: ignore[arg-type]
					if attempt >= max_retries:
						raise
					attempt += 1
					log.warning(
						"Retrying %s after error: %s (attempt %s/%s)",
						func.__name__,
						exc,
						attempt,
						max_retries
					)
					if current_delay > 0:
						await asyncio.sleep(current_delay)
					current_delay *= backoff
					if max_delay is not None:
						current_delay = min(current_delay, max_delay)

		return wrapper

	return decorator