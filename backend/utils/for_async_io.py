import asyncio
import base64
import concurrent
import hashlib
import logging

logger = logging.getLogger(__name__)


def async_run(tasks):
    """
    run a group of tasks async
    Requires the tasks arg to be a list of functools.partial()
    """
    if not tasks:
        return

    # start a new async event loop
    loop = asyncio.get_event_loop()
    # https://github.com/python/asyncio/issues/258
    executor = concurrent.futures.ThreadPoolExecutor(5)
    loop.set_default_executor(executor)

    async_tasks = [asyncio.ensure_future(async_task(task, loop)) for task in tasks]
    # run tasks in parallel
    loop.run_until_complete(asyncio.wait(async_tasks))
    # deal with errors (exceptions, etc)
    for task in async_tasks:
        error = task.exception()
        if error is not None:
            raise error

    executor.shutdown(wait=True)


@asyncio.coroutine
def async_task(params, loop):
    """
    performs an async task
    """
    # get the calling function
    logger.debug('Running {}'.format(params))
    # This executes a task in its own thread (in parallel)
    yield from loop.run_in_executor(None, params)
    logger.debug('Finished running {}'.format(params))
