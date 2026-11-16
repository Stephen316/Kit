# Observe the terminal CI aggregate for a frozen batch

Use the [pending roster](PendingCiRoster.md) with its payload SHA-256 and the exact GitHub aggregate run and attempt. Set `GH_TOKEN` or `GITHUB_TOKEN` through the authorized read-only credential source.

```sh
python3 re/automation/CiBatchTerminal.py --repository TryUniCAD/Kit --pull 94 \
  --run RUN_ID --run-attempt 1 --roster /private/path/Batch.json \
  --roster-sha256 ROSTER_PAYLOAD_SHA256
```

The roster names the PR head. The observer reads the protected `PullRequest.yml` aggregate and its matching terminal `CI Agg` job, then verifies the GitHub artifact digest, the receipt's repository and PR provenance, and the live head tree and tested merge parents. The report identifies the tested merge commit and tree when the aggregate's artifact verifies. The bearer credential goes to the GitHub API request. Archive redirects use HTTPS and carry the signed download link.

The observer reads the current PR, run attempt and latest aggregate again after evidence verification. A competing head, base, run or rerun reports `superseded`. An active aggregate reports `pending`. A failed aggregate provides terminal evidence for the head without a tested merge attestation. A startup failure with an empty attempt job list also checks the exact Actions suite and its empty check-run list. It reports the suite ID and leaves member attribution unavailable. Any candidate-level outcome requires its own stage 11 and hosted result evidence. The command reads public CI metadata and its authenticated artifact under the selected repository's authority.

The hosted process fixture supplies a fixed GitHub response transcript through the standalone entry point. It covers immutable artifact verification, competing revisions and runs, unattributed failure, changed roster bytes and inconsistent merge ancestry. The protected aggregate recorded startup failure with zero attempt jobs and zero check runs at PR head `90bdd0e8`. GitHub identified the exact Actions suite `118885792340`. [Hosted aggregate](https://github.com/TryUniCAD/Kit/actions/runs/43915295801)

Hosted verification of the observer remains pending. [GitHub workflow run and artifact API](https://docs.github.com/en/rest/actions/workflow-runs), [GitHub artifact API](https://docs.github.com/en/rest/actions/artifacts)
