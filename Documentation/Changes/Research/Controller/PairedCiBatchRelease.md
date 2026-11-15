# Release a paired discovery CI batch

Use the private A03 store and the original [frozen roster](PendingCiRoster.md). Select the exact protected aggregate and the exact workflow that published the [paired archive receipt](HostedPairedArchiveGate.md). Provide a locally audited Git commit with the same tree as the tested merge. Configure the GitHub credential through `GH_TOKEN` or `GITHUB_TOKEN`.

```sh
python re/automation/CiBatchRelease.py --store /private/ResearchStore \
  --roster /private/Batch.json --roster-sha256 ROSTER_SHA256 \
  --repository TryUniCAD/Kit --pull 94 \
  --aggregate-run AGGREGATE_ID --aggregate-attempt AGGREGATE_ATTEMPT \
  --workflow-run ARCHIVE_ID --workflow-attempt ARCHIVE_ATTEMPT \
  --audited-revision AUDITED_COMMIT
```

The command reads live authenticated GitHub evidence. A successful aggregate and audited archive receipt must name the same repository, pull request, base, head and tested tree. The hosted tree must also equal the parked candidate's head tree. The public save roster must match the immutable local discovery result for every member. An unattributed failure or a superseded observation leaves jobs in `waiting_ci`.

Under one A03 transaction, the coordinator verifies every frozen attempt and input binding before replacing any. Each member uses its own `ci` binding. The same transaction retains the observation and queues the exact successor generation. Repeating an identical applied release is safe. A changed or partially released roster cannot update the remaining members.

The successor [replays stage 11](PairedDiscoveryReplay.md) at the same source revision and checks that only its CI input changed. It completes the archive compatibility scope when the measured replay agrees with the parked result. Native application qualification remains a separate requirement. A member-level remote failure provider and automated isolation are still open.

A hosted A03 scenario covers multi-member replacement, exact replay of the release, a swapped member receipt, and rollback after one member changes. Hosted verification and a live successful release are pending.
