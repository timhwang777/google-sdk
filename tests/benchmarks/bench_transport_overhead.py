"""Benchmark: SDK transport overhead vs raw httpx.

Measures SDK round-trip time vs raw httpx for 100 requests.
Assertion: SDK overhead < 2x raw httpx time (SC-002).

Run with: uv run python tests/benchmarks/bench_transport_overhead.py
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import google.auth.credentials
import httpx
import respx

from google_sdk._config import SDKConfig
from google_sdk.services.drive.client import _API_BASE, DriveService

FILE_DATA = {
    "id": "file1",
    "name": "test.txt",
    "mimeType": "text/plain",
    "kind": "drive#file",
}

N = 100


def make_creds():
    creds = MagicMock(spec=google.auth.credentials.Credentials)
    creds.valid = True
    creds.token = "fake_token"
    return creds


@respx.mock
def bench_sdk_get_file() -> float:
    """Measure SDK time to call get_file() N times."""
    respx.get(f"{_API_BASE}/files/file1").mock(return_value=httpx.Response(200, json=FILE_DATA))
    svc = DriveService(make_creds(), SDKConfig())

    start = time.perf_counter()
    for _ in range(N):
        svc.get_file("file1")
    elapsed = time.perf_counter() - start
    return elapsed


@respx.mock
def bench_raw_httpx() -> float:
    """Measure raw httpx time to GET the same URL N times.

    Uses per-request httpx.Client to match the SDK's current behavior
    (BaseService creates a new client per request).
    """
    respx.get(f"{_API_BASE}/files/file1").mock(return_value=httpx.Response(200, json=FILE_DATA))

    start = time.perf_counter()
    for _ in range(N):
        with httpx.Client() as client:
            client.get(
                f"{_API_BASE}/files/file1",
                headers={"Authorization": "Bearer fake_token"},
            )
    elapsed = time.perf_counter() - start
    return elapsed


def run_benchmark() -> None:
    raw_time = bench_raw_httpx()
    sdk_time = bench_sdk_get_file()

    overhead_ratio = sdk_time / raw_time if raw_time > 0 else float("inf")

    print(f"Raw httpx ({N} requests): {raw_time * 1000:.1f} ms")
    print(f"SDK DriveService ({N} requests): {sdk_time * 1000:.1f} ms")
    print(f"Overhead ratio: {overhead_ratio:.2f}x")

    assert overhead_ratio < 2.0, (
        f"SDK overhead {overhead_ratio:.2f}x exceeds 2x limit (SC-002). "
        f"Raw: {raw_time * 1000:.1f}ms, SDK: {sdk_time * 1000:.1f}ms"
    )
    print(f"PASS: overhead {overhead_ratio:.2f}x < 2x (SC-002)")


if __name__ == "__main__":
    run_benchmark()
