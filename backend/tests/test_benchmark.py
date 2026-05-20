"""Benchmark tests — measure and report triage pipeline performance.

Run: pytest tests/test_benchmark.py -v -s
"""
import asyncio
import statistics
import time

import pytest

from app.services.severity_service import compute_severity
from app.services.dispatch_service import select_responder

TRANSCRIPTS = [
    "Massive fire at warehouse in Bhubaneswar, people trapped inside",
    "Person collapsed and not breathing at Delhi metro station",
    "Car accident on Mumbai-Pune expressway, multiple injuries",
    "Gas leak in residential building in Chennai, evacuation underway",
    "Flooding in Odisha, three districts cut off, thousands need food",
    "Cyclone approaching coast near Visakhapatnam, winds 140kmph",
    "Earthquake shaking buildings in Uttarakhand, structures damaged",
    "Stampede at religious gathering near Patna, many injured",
    "Noise complaint from apartment in Bangalore, neighbor playing music",
    "Someone fell and hurt their knee at a park in Jaipur",
    "Bahut badi aag lagi hai yahan pe madad bhejo",
    "Highway pe bada hadsa ho gaya ambulance chahiye",
    "Baadh aa gayi hai pani bahut tez aa raha hai",
    "Building on fire in Kolkata, smoke visible from far away",
    "Chemical spill at factory near Surat, toxic fumes in the air",
    "Landslide blocked road near Shimla, vehicles stranded",
    "Drowning incident at Goa beach, lifeguards called",
    "Riot situation near market in Lucknow, violence reported",
    "Missing child at Hyderabad railway station, parents frantic",
    "Power outage in entire district of Raipur after storm",
]


class TestBenchmark:
    @pytest.mark.asyncio
    async def test_single_triage_latency(self):
        """Single triage should complete in under 5ms."""
        latencies = []
        for transcript in TRANSCRIPTS:
            start = time.perf_counter()
            severity = await compute_severity(transcript, "fear")
            responder = await select_responder("fire", severity)
            elapsed_ms = (time.perf_counter() - start) * 1000
            latencies.append(elapsed_ms)

        avg = statistics.mean(latencies)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        p99 = sorted(latencies)[int(len(latencies) * 0.99)]

        print(f"\n--- Triage Benchmark ({len(TRANSCRIPTS)} scenarios) ---")
        print(f"  Avg:  {avg:.2f}ms")
        print(f"  P95:  {p95:.2f}ms")
        print(f"  P99:  {p99:.2f}ms")
        print(f"  Min:  {min(latencies):.2f}ms")
        print(f"  Max:  {max(latencies):.2f}ms")

        assert avg < 5.0, f"Average latency {avg:.2f}ms exceeds 5ms budget"
        assert p95 < 10.0, f"P95 latency {p95:.2f}ms exceeds 10ms budget"

    @pytest.mark.asyncio
    async def test_throughput_1000_triages(self):
        """1000 triages should complete in under 5 seconds."""
        start = time.perf_counter()
        for i in range(1000):
            transcript = TRANSCRIPTS[i % len(TRANSCRIPTS)]
            severity = await compute_severity(transcript, "fear" if i % 2 == 0 else "neutral")
            _ = await select_responder("fire", severity)
        elapsed = time.perf_counter() - start

        throughput = 1000 / elapsed
        print(f"\n--- Throughput Benchmark ---")
        print(f"  1000 triages in {elapsed:.2f}s")
        print(f"  Throughput: {throughput:.0f} triages/sec")

        assert elapsed < 5.0, f"1000 triages took {elapsed:.2f}s"
        assert throughput > 200, f"Throughput {throughput:.0f}/s below 200/s minimum"

    @pytest.mark.asyncio
    async def test_concurrent_burst(self):
        """50 concurrent triages (simulating burst) should complete in under 2s."""
        async def triage(transcript: str) -> tuple[str, str]:
            severity = await compute_severity(transcript, "fear")
            responder = await select_responder("fire", severity)
            return severity, responder

        start = time.perf_counter()
        tasks = [triage(TRANSCRIPTS[i % len(TRANSCRIPTS)]) for i in range(50)]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

        print(f"\n--- Concurrent Burst Benchmark ---")
        print(f"  50 concurrent triages in {elapsed:.3f}s")

        assert len(results) == 50
        assert elapsed < 2.0
