import asyncio
from functools import wraps, partial


def get_or_create_eventloop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError as ex:
        if "There is no current event loop in thread" in str(ex):
            asyncio.set_event_loop(asyncio.new_event_loop())
            return asyncio.get_event_loop()
        raise Exception("Unable to create event loop")

def asyncify(func):
    @wraps(func)
    def run(*args, **kwargs):

        loop = get_or_create_eventloop()

        async def run_async(loop, *args, executor=None, **kwargs):
            pfunc = partial(func, *args, **kwargs)
            return await loop.run_in_executor(executor, pfunc)

        return loop.run_until_complete(run_async(loop, *args, **kwargs))

    return run
