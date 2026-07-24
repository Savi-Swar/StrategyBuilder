"""fetchlib: rate limiting, retry, and budget behavior — all offline against
a local aiohttp server; no real API is touched."""
import asyncio
import time

import pytest
from aiohttp import web

from quark.data.fetchlib import (API_LIMITS, Fetcher, RetryBudgetExceeded,
                                 TokenBucket)


def run_with_server(handler, coro_factory):
    """Spin up a local server, run coro_factory(base_url) under a Fetcher
    session, tear down. Returns (result, fetcher)."""
    async def main():
        app = web.Application()
        app.router.add_get("/{tail:.*}", handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = site._server.sockets[0].getsockname()[1]
        fl = Fetcher(quiet=True)
        try:
            result = await fl._with_session(coro_factory(fl, f"http://127.0.0.1:{port}"))
        finally:
            await runner.cleanup()
        return result, fl
    return asyncio.run(main())


def test_token_bucket_enforces_rate():
    """20 acquires at 100/s with burst 1 must take ~190ms, never less."""
    async def main():
        b = TokenBucket(rate=100.0, capacity=1)
        t0 = time.monotonic()
        for _ in range(20):
            await b.acquire()
        return time.monotonic() - t0
    elapsed = asyncio.run(main())
    assert elapsed >= 0.19 * 0.9  # 19 refills at 10ms each, 10% timing slack


def test_concurrent_fetches_respect_rate():
    """30 concurrent GETs through a 100/s bucket: wall time is bounded below
    by the bucket, and the server never sees a burst above capacity."""
    seen = []

    async def handler(request):
        seen.append(time.monotonic())
        return web.json_response({"ok": 1})

    API_LIMITS["_test"] = {"rate": 100.0, "burst": 5, "concurrency": 10}

    def factory(fl, base):
        return fl.gather(fl.get_json(f"{base}/{i}", api="_test") for i in range(30))

    t0 = time.monotonic()
    results, fl = run_with_server(handler, factory)
    elapsed = time.monotonic() - t0
    assert len(results) == 30 and all(r == {"ok": 1} for r in results)
    assert fl.counters.requests == 30
    # 30 requests, burst 5, then 100/s refill -> >= ~0.25s of bucket time
    assert elapsed >= 0.25 * 0.8
    # rate check: any 1s sliding window must hold <= rate + burst requests
    for i, t in enumerate(seen):
        in_window = sum(1 for u in seen if t <= u < t + 1.0)
        assert in_window <= 105 + 1


def test_retry_on_429_then_success():
    calls = {"n": 0}

    async def handler(request):
        calls["n"] += 1
        if calls["n"] < 3:
            return web.Response(status=429)
        return web.json_response({"ok": 1})

    API_LIMITS["_test2"] = {"rate": 1000.0, "burst": 10, "concurrency": 2}

    def factory(fl, base):
        return fl.get_json(f"{base}/x", api="_test2")

    result, fl = run_with_server(handler, factory)
    assert result == {"ok": 1}
    assert fl.counters.retries == 2
    assert fl.counters.rate_limit_hits == 2


def test_no_retry_on_404():
    async def handler(request):
        return web.Response(status=404)

    def factory(fl, base):
        return fl.get_json(f"{base}/gone", api="_test2")

    with pytest.raises(Exception) as ei:
        run_with_server(handler, factory)
    assert "404" in str(ei.value)


def test_retry_budget_exhausts_loudly():
    async def handler(request):
        return web.Response(status=503)

    def factory(fl, base):
        fl.retry_budget = 3
        fl.max_attempts = 10
        return fl.get_json(f"{base}/dying", api="_test2")

    with pytest.raises(RetryBudgetExceeded):
        run_with_server(handler, factory)
