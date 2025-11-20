"""Main application module handling top-level logic and shutdown."""

import asyncio
import signal
import sys
from pathlib import Path
from typing import Any, Coroutine, Sequence

from das.storage import PendingWritesError, Storage
from das.task import read_data, store_data


async def main(output_file: Path, buggy: bool = False):
    """Main application entry point."""
    mode = "BUGGY" if buggy else "GRACEFUL"
    print(f"[main] Starting application in {mode} mode...", file=sys.stderr)
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    storage = Storage(output_file)

    prepared_tasks = [
        read_data(queue),
        store_data(storage, queue),
    ]

    if buggy:
        await buggy_runner(prepared_tasks)
    else:
        await graceful_runner(prepared_tasks)

    print("[main] Application exited gracefully")


async def buggy_runner(
    prepared_tasks: Sequence[Coroutine[Any, Any, None]],
) -> None:
    """
    Buggy runner that demonstrates improper signal handling.

    BUG: Calls asyncio.all_tasks() in the signal handler, which attempts
    to cancel ALL tasks in the event loop, not just the application tasks.
    This can lead to race conditions and improper cleanup.
    """
    loop = asyncio.get_running_loop()

    def handle_signal(sig: signal.Signals) -> None:
        print(
            f"[main] Received signal {sig}, cancelling ALL tasks (BUGGY!)",
            file=sys.stderr,
        )
        # BUG: This cancels ALL tasks in the event loop, including internal ones
        tasks = asyncio.all_tasks(loop)
        for task in tasks:
            task.cancel()

    # Register signal handlers
    for sig in (signal.SIGTERM,):
        print(f"[main] Registered BUGGY signal handler for {sig}", file=sys.stderr)
        loop.add_signal_handler(sig, lambda s=sig: handle_signal(s))

    # try/except-print just to better illustrate what will happen
    try:
        async with asyncio.TaskGroup() as tg:
            for t in prepared_tasks:
                tg.create_task(t)
    except* Exception as e:
        if isinstance(e, ExceptionGroup) and len(e.exceptions) == 1:
            if not isinstance(e.exceptions[0], PendingWritesError):
                raise e
            print(
                "[main] Application termination failed, the stored data can be corrupted"
            )
            sys.exit(1)

    print("[main] This is never reached")


async def graceful_runner(
    prepared_tasks: Sequence[Coroutine[Any, Any, None]],
) -> None:
    """Run tasks concurrently and terminate on SIGTERM.

    Registers signal handlers for graceful shutdown. On signal receipt, cancels
    all running tasks.

    Example:
        tasks = [
            worker_task(queue, logger),
            monitor_task(metrics, logger),
            heartbeat_task(queue, wrap_fn, logger),
        ]
        await graceful_runner(tasks)
    """
    loop = asyncio.get_event_loop()
    event = asyncio.Event()

    def handle_signal(sig: signal.Signals, event: asyncio.Event) -> None:
        print(
            f"[main] Received signal {sig}, shutting down gracefully", file=sys.stderr
        )
        event.set()

    for sig in (signal.SIGTERM,):
        print(f"[main] Registred signal handler for {sig}")
        loop.add_signal_handler(sig, lambda s=sig, e=event: handle_signal(s, e))

    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(t) for t in prepared_tasks]

        await event.wait()
        for t in tasks:
            t.cancel()

    print("[main] Shutdown done", file=sys.stderr)
