import asyncio

from tqdm import tqdm

import logging

logger = logging.getLogger(__name__)


async def run_tasks(tasks, desc="Processing tasks"):
    async def track_task(index, coro):
        try:
            return index, await coro
        except Exception as e:
            logger.error(
                f"Error processing task {index}: {e}",
                exc_info=True,
            )
            return index, e

    wrapped_tasks = [track_task(i, coro) for i, coro in enumerate(tasks)]

    chunk_results_dict = {}
    for finished_task in tqdm(
        asyncio.as_completed(wrapped_tasks),
        total=len(tasks),
        desc=desc,
    ):
        original_index, result_or_exception = await finished_task
        chunk_results_dict[original_index] = result_or_exception

    chunk_results = []
    for chunk_index in range(len(tasks)):
        if chunk_index not in chunk_results_dict:
            chunk_results.append(None)
        else:
            chunk_results.append(chunk_results_dict[chunk_index])
    return chunk_results


def maybe_async(func):
    """Decorator that makes any function callable with await, regardless of sync/async."""

    async def wrapper(*args, **kwargs):
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    return wrapper


async def call_maybe_async(func, *args, **kwargs):
    """Call a function, handling both sync and async cases automatically."""
    if asyncio.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    else:
        return func(*args, **kwargs)
