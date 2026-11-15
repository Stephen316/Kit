# Run CLI process coverage in two required parallel groups

The CLI compatibility workflow now runs core commands and qualification cases on
separate Ubuntu 24.04 runners. Core collects `tests/convert/Commands` while
excluding its Feature, Metadata, and Sketch directories. Qualification collects
those three directories explicitly. Every existing process case remains in
exactly one group; new directories join Core by default.

Each group retains the pinned Python environment, native schema check, pytest
worker settings, and ten-minute timeout. Matrix fail-fast is disabled so one
failure does not cancel the other group's evidence. The existing
`CLI conversion and inspection compatibility` report now requires both groups to
succeed, and both new group reports are required in the PR/merge-group allowlist.
The separate archive suite and heavy merge-queue acceptance remain unchanged.

Run `43709549223` reached only 83 percent of 775 CLI cases before cancellation.
GitHub's job timing records ten minutes eighteen seconds including cancellation
cleanup; archive coverage passed 2,959 cases with three skips in 514.38 seconds.
The extra CLI runner adds environment setup cost while splitting test execution;
no timeout or coverage gate is relaxed. Static workflow, formatting, and policy
checks validate this repair locally. No local tests or collection ran. Exact-head
group totals and full CI results are recorded in PR #119.
The [aggregation fixture correction](CliMatrixReportFixtures.md) supplies the
expanded report names in the repository's process simulations.

See [the CLI job timeout](../../Gotchas/Ci/Commands/CliQualificationOutgrowsSingleJob.md).
