# Run CLI process coverage independently of archive compatibility

The Fusion compatibility workflow runs `tests/Convert/Commands` through the required
`CLI conversion and inspection compatibility` report. Its current
[parallel groups](CliProcessGroups.md) preserve every case. The existing
`Fusion archive compatibility` job retains every codec/API case. Each suite
executes once, on Ubuntu 24.04 runners with 10-minute timeouts, locked
Python 3.14 environment, and native schema provenance check.

Both jobs are registered in the CI allowlist for pull requests and merge groups.
Existing checks, test cases, timeout limits, and acceptance gates remain enabled.
The additional runner separates scheduling and installation cost from the test
budgets instead of increasing the archive timeout.

The earlier combined compatibility step took 8 minutes 15 seconds in
[run 43655420515](https://github.com/TryUniCAD/Kit/actions/runs/43655420515).
The expanded CLI-only step took 269.30 seconds in
[job 132657682013](https://github.com/TryUniCAD/Kit/actions/runs/43663480845/job/132657682013),
with 341 passes and 12 invalid negative fixtures rejected before their intended
CLI boundary. The fixture repair and additional coverage require independent
budgets. See [the suite-budget gotcha](../../Gotchas/Ci/Commands/CommandSuiteBudget.md).

Workflow source, formatting, and policy registration were checked. Accepted-head
execution evidence is recorded in the CLI PR. No local tests ran; green pull
request checks do not establish merge-group or target-application acceptance.
