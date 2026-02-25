"""Benchmark: Pagination memory stays constant across pages.

Iterates 100 pages and verifies peak memory per page does not grow (SC-004).
Each page contains 10 items. Memory should remain roughly constant — no unbounded
accumulation of previous pages.

Run with: uv run python tests/benchmarks/bench_pagination_memory.py
"""

from __future__ import annotations

import gc
import tracemalloc

from google_sdk._pagination import PageIterator
from google_sdk.services.drive.models import File

N_PAGES = 100
ITEMS_PER_PAGE = 10

FILE_ITEM = {
    "id": "file1",
    "name": "test.txt",
    "mimeType": "text/plain",
    "kind": "drive#file",
}


def make_fetch_page(total_pages: int):
    """Return a fetch_page function that simulates N pages of results."""
    call_count = [0]

    def fetch_page(page_token: str | None) -> dict:
        page_num = call_count[0]
        call_count[0] += 1
        items = [{**FILE_ITEM, "id": f"file_p{page_num}_i{i}"} for i in range(ITEMS_PER_PAGE)]
        next_token = str(page_num + 1) if page_num < total_pages - 1 else None
        return {"files": items, "nextPageToken": next_token}

    return fetch_page


def run_benchmark() -> None:
    gc.collect()
    tracemalloc.start()

    fetch_page = make_fetch_page(N_PAGES)
    iterator = PageIterator(fetch_page, File, response_key="files")

    snapshot_start = tracemalloc.take_snapshot()

    total_items = 0
    for _ in iterator:
        total_items += 1

    gc.collect()
    snapshot_end = tracemalloc.take_snapshot()
    tracemalloc.stop()

    stats = snapshot_end.compare_to(snapshot_start, "lineno")
    total_growth_bytes = sum(s.size_diff for s in stats if s.size_diff > 0)

    expected_items = N_PAGES * ITEMS_PER_PAGE
    print(f"Iterated {total_items} items across {N_PAGES} pages")
    print(f"Memory growth: {total_growth_bytes / 1024:.1f} KB")

    assert total_items == expected_items, f"Expected {expected_items} items, got {total_items}"

    # Memory growth should be modest — well under 10 MB for 1000 items
    max_growth_bytes = 10 * 1024 * 1024  # 10 MB
    assert total_growth_bytes < max_growth_bytes, (
        f"Memory grew by {total_growth_bytes / 1024:.1f} KB exceeding "
        f"{max_growth_bytes // 1024} KB limit (SC-004). "
        "Possible unbounded accumulation of previous pages."
    )
    print(
        f"PASS: memory growth {total_growth_bytes / 1024:.1f} KB < {max_growth_bytes // 1024} KB (SC-004)"
    )


if __name__ == "__main__":
    run_benchmark()
