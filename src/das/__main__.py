"""Entry point for running das as a module: python -m das"""

import argparse
import asyncio
import sys
from pathlib import Path

from das.main import main


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data Async Shovel - Graceful shutdown demo")
    parser.add_argument("output_file", type=Path, help="Output file path")
    parser.add_argument(
        "--buggy",
        action="store_true",
        help="Use buggy signal handler (cancels all tasks immediately)"
    )

    args = parser.parse_args()

    asyncio.run(main(args.output_file, buggy=args.buggy))
