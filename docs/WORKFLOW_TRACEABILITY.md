# Defence Workflow Traceability

This checklist maps the submitted project to the uploaded Project Defence & Demonstration brief. It distinguishes code that is present from checks that must be run by the student before claiming completion.

| Brief area | Project evidence | Status / remaining action |
|---|---|---|
| Real-world problem, decomposition, abstraction | `README.md`, `scheduler/models.py`, `scheduler/engine.py` | Implemented; explain the modeled constraints. |
| Greedy, backtracking, branch-and-bound | `scheduler/engine.py` | Implemented; explain MRV/degree ordering, reversible choices, and the preference-score upper bound. |
| Divide-and-conquer | `validate_assignments` in `scheduler/engine.py` | Implemented in pairwise validation. It remains O(n²); it is a teaching demonstration, not a performance improvement. |
| Dynamic programming | `failed_states` cache in `scheduler/engine.py` | Memoization of proven-infeasible search states. Explain why bound-pruned states are not cached as impossible. |
| Complexity analysis | `docs/DEFENCE_NOTES.md` | Worst-case and validation complexity are documented; understand them for the viva. |
| Python data structures and Pythonic design | `scheduler/models.py`, `scheduler/engine.py` | Dataclasses, tuples, lists, sets, comprehensions, and type annotations are used. |
| Visible weekly timetable and conflict handling | `app.py`, `scheduler/engine.py`, `scheduler/models.py` | Days render as rows and configured periods as horizontally scrollable columns. Empty periods are visible; concurrent classes in different rooms are stacked. The solver rejects conflicting placements, the independent validator checks assignments, and unschedulable inputs show provable resource-capacity bottlenecks or a general constraint explanation. |
| SaaS-style campus workspace and spreadsheet intake | `templates/index.html`, `static/app.css`, `static/app.js`, `scheduler/importer.py` | Responsive institution workspace supports CSV and XLSX imports, downloadable template, configurable teaching days/periods, per-session room/day/period availability, and schedule export. This remains a single-process prototype without auth, database, or tenant isolation. |
| OOP and functional programming | `scheduler/models.py`, `scheduler/engine.py` | Immutable data models and pure helper functions are present. Inheritance/generic programming are not materially needed in this small design; do not claim them as implemented. |
| Concurrency and GIL | `benchmarks/benchmark.py` | `ProcessPoolExecutor` runs independent CPU-bound benchmark jobs. The web solver itself is not parallelized. Compare serial and process results; overhead may dominate small workloads. |
| Unit/integration/property tests | `tests/test_scheduler.py`, `tests/test_app.py`, `tests/test_properties.py` | Test code included. Install `requirements-dev.txt` and run `python -m pytest -v`; property tests require Hypothesis. |
| Coverage, typing, linting, CI | `pyproject.toml`, `.github/workflows/tests.yml` | Configured; run locally or inspect a successful GitHub Actions run. Configuration alone is not proof of a passing check. |
| Containerisation | `Dockerfile` | Included; verify with `docker build -t timetable-project .`. |
| AI-assisted development and review | `docs_AI_USAGE_LOG.md` | Log includes the upgrade work and notes verification limits. Add your own actual review notes before submission. |
| Performance evaluation | `benchmarks/benchmark.py` | Repeatable serial/process-pool experiment records runtime, nodes, memory, and violations. Save and discuss your own machine's CSV results. |
| Live demonstration and technical defence | `app.py`, `README.md`, `docs/DEFENCE_NOTES.md` | Demonstrate the week grid, a feasible timetable, parallel rooms, each conflict type, invalid input, CSV export, tests, benchmarks, and Docker/CI evidence. |

## Definition of “complete” for submission

Do not mark the workflow fully complete until the student has run the test and quality commands, captured actual coverage/type/lint/CI outputs, built the container, generated benchmark CSVs on the target machine, and prepared to explain the algorithm choices and limitations. Some techniques (for example inheritance, asynchronous web handling, or multiprocessing inside one search) are not implemented because they are not necessary to the current problem formulation; confirm with the evaluator whether they are mandatory rather than claiming them by implication.
