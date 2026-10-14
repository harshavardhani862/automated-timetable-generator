# Project Defence Notes

## Problem statement and decomposition
Manual college timetable planning can create faculty, section, and room clashes. Each class session must be assigned one day, one period, and one eligible room. A valid schedule cannot place the same faculty member, section, or room in two sessions at the same day and time.

## Algorithm selection
1. **Divide-and-conquer validation:** `validate_assignments` recursively splits the assignment list into halves, validates each half, then checks cross-half pairs. It is `O(n^2)` and demonstrates the pattern rather than claiming a performance improvement.
2. **Greedy heuristic:** order sessions by constraint degree and try preferred-day placements first.
3. **Backtracking:** recursively try placements and backtrack when a partial choice prevents completion.
4. **Forward checking:** after each choice, ensure every unassigned session retains a legal placement.
5. **Branch-and-bound:** the objective is the number of scheduled sessions plus one bonus for each satisfied preferred-day soft constraint. An optimistic upper bound assumes every remaining preferred session can satisfy its preference; branches that cannot beat the best complete schedule are pruned.
6. **Memoization / dynamic programming technique:** cache only states proven infeasible, avoiding repeated search of the same occupancy/depth state. Bound-pruned states are not recorded as infeasible.

The solver does not split one timetable into independent subproblems because sessions share room/faculty/section constraints. Divide-and-conquer is used in independent conflict validation. Multiprocessing is used only in the separate benchmark to run independent scheduling cases.

## Data structures and design
- Frozen dataclasses model `ClassSession` and `Problem`.
- Lists hold the current and best assignments; sets hold proven failed states.
- Pure helpers check conflicts, validate assignments, and score schedules.
- Flask is the presentation layer; parsing/models and the scheduling engine are separate modules.
- CSV and XLSX import is isolated in `scheduler/importer.py`; per-session room, day, and period availability flows into solver candidate generation.
- The SaaS-style workspace is a single-process educational prototype, not a production multi-tenant service. It does not include authentication, a database, or persistent institution workspaces.
- The web view lays out days as rows and configured periods as columns. Empty periods remain visible, while simultaneous classes in different rooms are stacked in a cell.
- If no complete schedule exists, capacity checks explain provable faculty/section overloads or total room-period shortages; other unsatisfiable cases receive a general constraint-review message.

## Complexity
Let `n` be the number of sessions and `m` the number of possible placements per session. Backtracking can have exponential worst-case search, commonly described as `O(m^n)` before pruning. Each conflict check scans the current placements, adding up to `O(n)` work per candidate in this simple implementation. Validation checks assignment pairs and is `O(n^2)`. Memoization, forward checking, greedy ordering, and branch-and-bound may reduce actual explored nodes but do not remove the exponential worst case. Do not claim a universal speedup; present measured benchmark output.

## Concurrency, CPU/I/O and GIL
The solver is CPU-bound. Python threads generally do not accelerate CPU-bound Python bytecode under the standard CPython GIL. The benchmark uses `ProcessPoolExecutor` to run independent cases in separate processes. This can use multiple CPU cores, but startup and serialization overhead can dominate small jobs. The website's single timetable request is not parallelized.

## Testing and quality workflow
- Unit tests cover feasible/infeasible schedules, input validation, and conflict validation.
- Flask integration tests cover the workspace, CSV/XLSX import, availability validation, template download, weekly grid, and CSV export.
- Hypothesis property tests generate small cases and check feasibility/validation invariants.
- Coverage, Ruff, and mypy are configured and included in CI. Report only results from commands that actually ran successfully.
- GitHub Actions runs tests, coverage threshold, static checks, and Docker build.

## Performance evaluation template
Run the serial and process-pool benchmark commands in README on the same machine. Compare session count, nodes, runtime, peak traced memory, and violations. Record Python version, OS/CPU, command, and output CSV. Avoid inventing measurements in a report.

| Sessions | Workers | Search nodes | Measured runtime (ms) | Peak traced memory (KB) | Success / violations |
|---:|---:|---:|---:|---:|---|
| 8 | 1 | Fill from CSV | Fill from CSV | Fill from CSV | Fill from CSV |
| 20 | 1 | Fill from CSV | Fill from CSV | Fill from CSV | Fill from CSV |
| 40 | 1 | Fill from CSV | Fill from CSV | Fill from CSV | Fill from CSV |
| 8/20/40 | 2 | Fill from CSV | Fill from CSV | Fill from CSV | Fill from CSV |

## Live demonstration flow
1. Download the CSV template and import a schedule file with subjects, sections, faculty, rooms, and availability.
2. Show the complete schedule in the day-by-period grid. Explain the section, faculty, and room details and identify open periods.
3. Demonstrate parallel room bookings and an infeasible case caused by restricted availability or a shared faculty member.
4. Export a feasible schedule to CSV, then show tests, coverage, static checks, and the process-pool benchmark.

## AI-assisted engineering log
Use `docs_AI_USAGE_LOG.md` to record actual prompts, which suggestions were accepted/rejected, your code review, tests run, and limitations. Do not claim AI-generated code is correct without independent validation.

## Viva questions
1. **Why greedy ordering?** It attempts highly constrained sessions early so conflicts surface sooner.
2. **Why backtracking?** A valid local choice may block later sessions, so choices must be reversible.
3. **What is memoized?** Only states proven infeasible, identified by depth and current occupancy.
4. **What does branch-and-bound optimize?** The number of preferred-day soft constraints satisfied while scheduling every session.
5. **Why use processes for the benchmark?** The workload is CPU-bound and independent cases can run on multiple cores; overhead may outweigh benefits on small examples.
6. **What does the validation message prove?** It verifies the assignments that exist. A successful result must also schedule all requested sessions; zero assignments with zero overlaps is not a successful timetable.
7. **What remains limited?** No persistent database/login, no multi-slot sessions, limited institution-specific rules, and exponential worst-case search.
