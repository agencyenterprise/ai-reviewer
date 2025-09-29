import asyncio

from tqdm import tqdm

import logging

logger = logging.getLogger(__name__)


async def run_tasks(tasks, desc="Processing tasks"):
    async def track_task(index, coro):
        try:
            return index, await coro, None
        except Exception as e:
            logger.error(
                f"Error processing task {index}: {e}",
                exc_info=True,
            )
            return index, None, e

    wrapped_tasks = [track_task(i, coro) for i, coro in enumerate(tasks)]

    task_results_dict = {}
    task_errors_dict = {}
    for finished_task in tqdm(
        asyncio.as_completed(wrapped_tasks),
        total=len(tasks),
        desc=desc,
    ):
        original_index, result, error = await finished_task
        task_results_dict[original_index] = result
        task_errors_dict[original_index] = error

    task_results = []
    task_errors = []

    for chunk_index in range(len(tasks)):
        if chunk_index not in task_results_dict:
            task_results.append(None)
            task_errors.append(None)
        else:
            task_results.append(task_results_dict[chunk_index])
            task_errors.append(task_errors_dict[chunk_index])
    return task_results, task_errors


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
