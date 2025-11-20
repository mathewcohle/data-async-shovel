import asyncio
import sys
from pathlib import Path
import time

from aiofile import async_open
from aiofile.utils import FileIOWrapperBase


class PendingWritesError(Exception):
    """Raised when writes are still pending after timeout."""

    pass


_WRITE_TIME_SEC = 1


class Storage:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._temp_path = path.with_suffix(".part")
        self._write_tasks = []
        self._file: FileIOWrapperBase | None = None

    async def ready(self) -> None:
        """Open the file for async writing. Must be called before write()."""
        if self._file is not None:
            raise RuntimeError("Storage already initialized")
        self._file = await async_open(self._temp_path, "a")

    def write(self, data: str) -> None:
        """
        Queue data for async writing.
        """
        if self._file is None:
            raise RuntimeError(
                "Storage not ready - call `await storage.ready()` before writing"
            )
        # use this opportunity to clean up done tasks to prevent memory leak
        self._write_tasks = [t for t in self._write_tasks if not t.done()]
        self._write_tasks.append(asyncio.create_task(self._write_line(data)))

    async def _write_line(self, data: str) -> None:
        """Write a single line to file with simulated I/O delay."""
        assert self._file is not None
        # simulate processing so there are pending tasks when `close` is called, like
        # pretend the network round trip taking place
        await asyncio.sleep(_WRITE_TIME_SEC)
        await self._file.write(f"{data}\n")

    async def close(self, timeout: float) -> None:
        """
        Wait for all pending writes to complete and close the file.

        Args:
            timeout: Maximum time to wait for pending writes (seconds)

        Raises:
            PendingWritesError: If writes don't complete within timeout
        """
        # NOTE: This implementation is intentionally verbose for demonstration purposes.
        # We explicitly check task states to show what happens when tasks are cancelled.
        # In production code, the symptoms of cancelling all event loop tasks are often
        # more subtle - tasks silently fail without clear error messages, making the
        # root cause harder to diagnose.
        assert timeout > _WRITE_TIME_SEC, (
            "Use bigger timeout as otherwise all tasks are already done"
        )
        if self._file is None:
            print(
                "[Storage] Cleanup called on uninitialized storage (no-op)",
                file=sys.stderr,
            )
            return

        print(
            f"[Storage] Waiting for {len(self._write_tasks)} pending writes...",
            file=sys.stderr,
        )

        def all_completed_successfully() -> bool:
            return all(
                t.done() and not t.cancelled() and t.exception() is None
                for t in self._write_tasks
            )

        start = time.monotonic()
        while not all_completed_successfully():
            if (time.monotonic() - start) > timeout:
                raise PendingWritesError(f"Writes still pending after {timeout}s")

            # Don't block the event loop
            await asyncio.sleep(0.1)

        await self._file.close()
        # Rename temp file to final path (atomic operation)
        self._temp_path.rename(self._path)
        print("[Storage] Writes successfully finished", file=sys.stderr)
