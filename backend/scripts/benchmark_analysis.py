"""Measure repeated parcel analyses without HTTP or server startup overhead."""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.spatial_analysis_service import SpatialAnalysisService


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=25)
    args = parser.parse_args()
    if args.runs < 2:
        parser.error("--runs must be at least 2")

    service = SpatialAnalysisService()
    durations = []
    buffers = {"wetlands": 50.0, "buildings": 20.0, "floodzones": 0.0}
    constraints = list(buffers)

    for _ in range(args.runs):
        started = time.perf_counter()
        service.analyze("parcel", constraints, buffers)
        durations.append((time.perf_counter() - started) * 1000)

    ordered = sorted(durations)
    p95_index = min(len(ordered) - 1, int(len(ordered) * 0.95))
    print(f"runs={args.runs}")
    print(f"median_ms={statistics.median(durations):.1f}")
    print(f"p95_ms={ordered[p95_index]:.1f}")
    print(f"max_ms={max(durations):.1f}")


if __name__ == "__main__":
    main()
