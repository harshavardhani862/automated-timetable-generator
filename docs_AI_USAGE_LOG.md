# AI-assisted development log (complete this honestly)

Use this file to document your actual development process. Do not claim that a prompt, suggestion, test, or review occurred unless it did.

| Date | Prompt / question | AI suggestion | Accepted or rejected? | Your review / modification | Verification |
|---|---|---|---|---|---|
| YYYY-MM-DD | Describe the prompt you actually used | Summarize suggestion | Accepted/rejected/partial | Explain your reasoning | Commands/tests and outcome |

## Reflection questions
- Which AI-generated code did you inspect line by line?
- What edge case did you discover independently?
- Which tests gave evidence the code works?
- What did you change after a test failed?
- What limitations remain?

## Upgrade work recorded for this ZIP (2026-10-14)

| Date | Prompt / question | AI suggestion | Accepted or rejected? | Your review / modification | Verification |
|---|---|---|---|---|---|
| 2026-10-14 | Update the project to better align with the uploaded Project Defence & Demonstration workflow | Add explicit branch-and-bound scoring for soft preferred-day constraints, expand automated tests and quality tooling, and add a repeatable process-pool benchmark | Partially accepted; implementation is an educational prototype | Review `scheduler/engine.py`, test files, `benchmarks/benchmark.py`, CI configuration, and the limitations in README before submission. The benchmark's multiprocessing applies to independent jobs, not one live timetable search. | Core scheduler unit tests passed in the build environment. Full Flask integration/property tests and third-party quality tools were not run here because the environment could not install packages from the network. Run the full commands in README locally and record the actual results. |

## Weekly grid and conflict-feedback update (2026-10-14)

| Date | Prompt / question | AI suggestion | Accepted or rejected? | Your review / modification | Verification |
|---|---|---|---|---|---|
| 2026-10-14 | Update the project to follow the defence workflow, display the timetable like the supplied day-by-period grid, and handle conflicts | Add a responsive day-by-period grid with parallel room bookings, show resource-capacity explanations for unschedulable cases, handle malformed session rows, and update defence documentation | Accepted with scope kept to the existing solver and Flask app | Reviewed the solver's one-class-per-room/day/period behavior and retained the independent validator. Did not claim unsupported asynchronous scheduling or live-search multiprocessing. The grid uses the user's configured periods rather than hard-coding 20. | Python 3.13.7: `python -m coverage run -m pytest -q` (16 passed), `python -m coverage report --fail-under=70` (89% total), `ruff check .` passed, and `mypy scheduler` passed. Browser-checked a feasible timetable with two concurrent rooms and an infeasible shared-faculty case. Docker build and hosted CI were not run. |

## B2B workspace and spreadsheet import update (2026-10-14)

| Date | Prompt / question | AI suggestion | Accepted or rejected? | Your review / modification | Verification |
|---|---|---|---|---|---|
| 2026-10-14 | Make the project look and work more like a real B2B SaaS website, support schedule-file creation/import, and rename groups to sections | Create a responsive campus-operations workspace, CSV/XLSX intake and a downloadable CSV template; use section as the student-cohort field; enforce per-class room/day/period availability | Accepted with honest prototype scope | Added a single-institution workspace UI but did not invent authentication, tenant isolation, persistence, or claims of production readiness. Spreadsheet values are validated before scheduling; exported CSV text is protected from spreadsheet formula execution. | Python 3.13.7: 21 tests passed; branch coverage report 80% total and above the CI threshold; Ruff and mypy passed. Browser-checked the dashboard at desktop and mobile widths; CSV/XLSX import, section labels, availability, and export are covered by integration tests. Docker and hosted CI were not run. |
