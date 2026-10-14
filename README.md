
# Automated Timetable Generator

A Python/Flask academic scheduling workspace that imports institutional timetable data, searches for a complete schedule, independently validates faculty/section/room conflicts, and exports CSV. The UI presents the project as a B2B campus-operations SaaS prototype; it does not claim production authentication, multi-tenancy, persistence, or deployment.

## 1. Run on Windows

Install Python 3.10+ and open this folder in VS Code. In **Terminal → New Terminal**, run:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>. The workspace shows a sample schedule immediately. Use **Download template** to prepare data, then import a CSV or `.xlsx` workbook. To stop the local server, press `Ctrl+C` in the terminal.

The weekly grid has days as rows and configured periods as columns, like the supplied timetable example. It scrolls horizontally for long schedules, shows open periods, and stacks concurrent classes in different rooms.

## 2. Input and constraints

### CSV / Excel import

Use one row per class, with these column headers:

| Column | Required | Meaning |
|---|---|---|
| `subject` | Yes | Course/class name |
| `section` | Yes | Student section identifier |
| `faculty` | Yes | Instructor name |
| `rooms` | Yes | Allowed room names, separated by semicolons |
| `available_days` | No | Allowed days, separated by semicolons |
| `available_slots` | No | Allowed periods, separated by semicolons |
| `preferred_days` | No | Soft preferred days, separated by semicolons |

Set the overall teaching days and periods in the import form as comma-separated values. The rooms available to each class are read from its `rooms` cell. Excel files should be `.xlsx`; the importer reads the `Sessions` worksheet when present, otherwise the first worksheet. Uploads are limited to 5 MB and 250 classes to keep the search and import responsive.

### Advanced JSON input

JSON remains available in the advanced editor. Required top-level keys are `days`, `slots`, `rooms`, and `sessions`. Each session needs `subject`, `section`, and `faculty`. Optional `available_days`, `available_slots`, and `available_rooms` restrict placements; `preferred_days` is a **soft preference** that the solver tries to satisfy. This version supports one-slot sessions only.

The solver prevents a faculty member, section, or room from being assigned to two classes in the same day and period. It also respects each class's availability. If no complete schedule is possible, the page does not present a partial result as successful; it reports provable resource-capacity bottlenecks or the constraints to review. The independent validator checks assignments before success is reported.

## 3. Algorithms and data structures

- **Problem decomposition and abstraction:** each class is a session; days, periods, rooms, faculty, and student sections are the scheduling model.
- **Divide-and-conquer:** independent conflict validation recursively splits assignments into halves and checks within-half and cross-half pairs. This is an educational structure with `O(n^2)` time, not a claim of asymptotic speedup.
- **Greedy heuristic:** order highly constrained sessions first and try preferred days first.
- **Backtracking:** recursively assign a placement and undo it when a continuation cannot work.
- **Forward checking:** after each placement, ensure every remaining session has at least one legal candidate.
- **Branch-and-bound:** maximize the number of preferred-day matches using an optimistic upper bound; prune branches that cannot improve the best score.
- **Dynamic programming / memoization:** cache states proven infeasible, keyed by search depth and current occupancy.
- **Functional techniques:** pure conflict, validation, and scoring helpers; immutable dataclasses for input models.
- **Data structures:** tuples and frozen dataclasses for inputs, lists for placements, sets for memoized failed states, and dictionaries for JSON/CSV boundaries.
- **Divide-and-conquer:** the current solver does not split a single problem into independent subproblems. Independent problem instances are used in the benchmark, but that is workload parallelism, not a claim that the solver uses divide-and-conquer.

## 4. Testing and quality checks

Install development tools:

```powershell
python -m pip install -r requirements-dev.txt
```

Run the complete test suite (unit, web integration, and property-based tests):

```powershell
python -m pytest -v
```

Measure branch coverage:

```powershell
coverage run -m pytest
coverage report -m
coverage html
```

Run static checks:

```powershell
ruff check .
mypy scheduler
```

The GitHub Actions workflow runs tests, enforces a coverage threshold, runs Ruff and mypy, and builds the Docker image. The workflow's green status is the evidence that the pipeline passed; a configuration file alone is not proof.

## 5. Performance and concurrency experiment

Run serial measurements:

```powershell
python -m benchmarks.benchmark --sizes 8 20 40 --repeats 3 --workers 1 --output results_serial.csv
```

Run the same independent CPU-bound scheduling cases with processes:

```powershell
python -m benchmarks.benchmark --sizes 8 20 40 --repeats 3 --workers 2 --output results_processes.csv
```

The benchmark records session count, search nodes, solver and measured runtime, peak traced memory, success, and validation violations. Example output files are under `benchmarks/sample_results/`; they were measured in the build environment and are only examples. Compare your results from the same computer. Process startup and serialization overhead may make small cases slower; do not claim multiprocessing is faster unless your measurements show it. Multiprocessing is demonstrated in the benchmark only; the interactive web request uses the normal single-process solver.

## 6. Docker

```powershell
docker build -t timetable-project .
docker run --rm -p 5000:5000 timetable-project
```

Then open <http://127.0.0.1:5000>.

## 7. Defence demonstration checklist

1. State the real-world problem and define faculty, room, and section non-overlap constraints.
2. Explain the input model and constraints, then generate the demo and read the result in the day-by-period grid.
3. Show parallel sessions in separate rooms, empty periods, and the independent no-overlap validation.
4. Submit an impossible faculty-conflict case (two sessions, one day/period, same faculty) and explain the displayed bottleneck; also test room and section infeasibility.
5. Test malformed JSON, malformed session rows, and preferred-day fallback.
6. Export CSV and open it in Excel.
7. Run `python -m pytest -v`, coverage, Ruff, and mypy; record actual outcomes.
8. Run serial and process-pool benchmarks; include the generated CSVs and explain the machine/workload and results.
9. Build/run Docker and inspect the GitHub Actions result if repository CI is configured.
10. Explain the AI usage log honestly, including what you inspected, changed, tested, and still consider limited.

## Limitations and honest claims

This is an educational prototype, not a production university timetabling system. It supports one-slot sessions, has no database/authentication, and does not model holidays, instructor availability, course capacities, lab-specific room requirements, or multi-slot lectures. Backtracking remains exponential in the worst case (roughly `O(m^n)` before pruning, for `n` sessions and up to `m` placements per session); conflict checking adds a linear scan over placed assignments in this implementation. Benchmark results are hardware- and input-dependent. The benchmark demonstrates process-based concurrency over independent jobs, not parallel search inside one timetable.
=======
# automated-timetable-generator
An Automated Timetable Generator that creates optimized academic timetables by assigning subjects, faculty, classrooms, and time slots while minimizing scheduling conflicts and satisfying academic constraints.
