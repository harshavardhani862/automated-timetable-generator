"""Repeatable solver benchmark with optional process-based concurrency.

Run from the project root: python -m benchmarks.benchmark --sizes 8 20 40 --repeats 3 --workers 2
Independent scheduling problems are used as separate CPU-bound jobs. Process
startup overhead may dominate small examples; compare measurements rather than
assuming multiprocessing is faster.
"""
from __future__ import annotations

import argparse
import csv
import json
import time
import tracemalloc
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from scheduler.engine import generate_timetable
from scheduler.models import parse_problem


def make_problem(size: int) -> dict[str, Any]:
    return {
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "slots": ["09:00", "10:00", "11:00", "12:00"],
        "rooms": ["R101", "R102", "R103"],
        "sessions": [
            {"subject": f"Subject {i + 1}", "section": f"Section {i + 1}",
             "faculty": f"Faculty {i + 1}"}
            for i in range(size)
        ],
    }


def run_case(args: tuple[int, int]) -> dict[str, Any]:
    size, repeat = args
    problem = parse_problem(make_problem(size))
    tracemalloc.start()
    wall_start = time.perf_counter()
    result = generate_timetable(problem)
    elapsed_ms = (time.perf_counter() - wall_start) * 1000
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "sessions": size,
        "repeat": repeat,
        "success": result.success,
        "assignments": len(result.assignments),
        "search_nodes": result.nodes,
        "solver_runtime_ms": round(result.elapsed_ms, 3),
        "measured_runtime_ms": round(elapsed_ms, 3),
        "peak_traced_memory_kb": round(peak_bytes / 1024, 2),
        "validation_violations": len(result.violations),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[8, 20, 40])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--workers", type=int, default=1,
                        help="1=serial; >1=process pool for independent CPU-bound cases")
    parser.add_argument("--output", default="benchmark_results.csv")
    args = parser.parse_args()
    if any(size < 1 for size in args.sizes) or args.repeats < 1 or args.workers < 1:
        parser.error("sizes, repeats, and workers must be positive")
    jobs = [(size, repeat) for size in args.sizes for repeat in range(1, args.repeats + 1)]
    start = time.perf_counter()
    if args.workers == 1:
        results = [run_case(job) for job in jobs]
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            results = list(executor.map(run_case, jobs))
    wall_ms = (time.perf_counter() - start) * 1000
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    print(json.dumps({"workers": args.workers, "jobs": len(jobs),
                      "total_wall_time_ms": round(wall_ms, 3),
                      "csv": str(output), "results": results}, indent=2))


if __name__ == "__main__":
    main()
