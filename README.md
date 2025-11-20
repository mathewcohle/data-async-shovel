# Data Async Shovel

A demonstration of graceful `SIGTERM` handling in Python asyncio applications to prevent accidental data loss.

Accompanying code to blog post [Just Gracefully Shutdown](https://matcohle.me/just-gracefully-shutdown).

## Overview

This application implements a simple data processing pipeline using two `asyncio` tasks that communicate via a queue:

- **`read_data`**: Generates timestamped data and places it in a queue
- **`store_data`**: Reads from the queue and writes data to an output file

The key feature is **graceful shutdown handling** that ensures the application handles `SIGTERM` signals gracefully.

## The Problem

When processing data asynchronously, a naive shutdown can cause:

- Loss of data handovered to `Storage` but not yet written
- Incomplete writes to output files
- Corrupted state if file handles aren't properly closed

## Solution

This project demonstrates two approaches:

- **Graceful mode** (`graceful_runner`) 

Properly coordinates shutdown between tasks using an `asyncio.Event`. When `SIGTERM` is received, it cancels only the application tasks and waits for pending writes to complete. Creates `data/out.txt` on successful completion.

- **Buggy mode** (`buggy_runner`)

Incorrectly uses `asyncio.all_tasks()` to cancel ALL event loop tasks immediately, including internal asyncio tasks. This causes the storage cleanup to fail, leaving an incomplete `data/out.txt.part` file.

Take a close look at the implementation in `src/das/main.py` and the cleanup logic in `src/das/storage.py`.

## Usage

Run `make run-graceful` or `make run-buggy` in one terminal window, then execute `make stop` from another terminal.

The Makefile will display the contents of the `data/` directory after each run to show the difference:
- **Graceful shutdown**: Complete `out.txt` file (all pending writes finished)
- **Buggy shutdown**: Incomplete `out.part` file (demonstrating data loss)
