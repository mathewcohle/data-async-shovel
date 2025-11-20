"""Worker tasks for the async application."""

import asyncio
import sys
import time

from das.storage import Storage


async def read_data(queue: asyncio.Queue[float]):
    """
    Read entire file and send lines to queue one by one.
    """
    print("[store_data] Prepared to read data", file=sys.stderr)
    try:
        while True:
            data = time.monotonic()
            await queue.put(data)
            # Small delay to simulate processing / slowdown amount of generated data
            await asyncio.sleep(0.2)

    except asyncio.CancelledError:
        print("[read_data] Received signal to cancel, cleaning up...")


async def store_data(storage: Storage, queue: asyncio.Queue[float]):
    """
    Get data from queue and write to storage.
    """
    await storage.ready()
    print("[store_data] Prepared to store data", file=sys.stderr)
    try:
        while True:
            data = await queue.get()

            storage.write(str(data))
            # task is acked only once we know the data accepted to be written
            queue.task_done()
    except asyncio.CancelledError:
        # note that we are not waiting for data in the queue
        # it depends on the particular context but this type of service
        # hopefully reads from a source which can redeliver un-acked messages
        print("[store_data] Received signal to cancel, cleaning up...")
        await storage.close(3)
        print("[store_data] Cleaning up done")
