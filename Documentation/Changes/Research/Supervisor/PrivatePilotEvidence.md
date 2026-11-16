# Replay private pre-pilot operational evidence

Work from the [controller activity report](OfflinePilotEventReport.md) for a past time window. Write a private JSON manifest with `version` set to `1`, a `window` object, and a `sources` object. Copy `from_unix_seconds`, `until_unix_seconds`, `after_event_id`, `through_event_id`, and `selected_events_sha256` into `window`. Under `sources`, use each supplied source's key and exact file SHA-256. Keep the referenced private files beside the manifest.

| Source key | File | Authority |
| --- | --- | --- |
| `interventions` | `Interventions.json` | `operator_attestation` |
| `agent_activity` | `AgentIntervals.json` | `measured_agent_intervals` |
| `acceptance` | `Acceptances.json` | `independent_acceptance_attestation` |
| `ci_activity` | `CiActivity.json` | `github_actions_job_observations` |

Each source is a JSON object with `version` set to `1`, its exact `authority`, and a `records` array. Use stable ASCII `id` values. Identical records with the same ID count once. Conflicting records and changed pins fail the report.

- An intervention has `id`, Unix `at`, `operator`, private `reason`, and `evidence_sha256`. Keep the source reason and supporting observation with its operator attestation.
- A measured interval has `id`, `agent`, `attempt`, Unix `from`, Unix `until`, and `evidence_sha256`. Use null `until` for an open interval. Closed intervals are clipped to the requested window. Agent seconds sum the merged intervals of each agent. Active wall seconds merge concurrent intervals across agents. Open intervals make the result partial. A window with no interval evidence reports unmeasured.
- An independent acceptance attestation has `id`, Unix `at`, `verifier`, `document_sha256`, `family`, `format_version`, `direction`, `baseline`, and `candidate`. Each comparison side has `status` of `accepted` or `not_accepted` and its own `receipt_sha256`. A gain is an explicit transition to acceptance for the same document and route. Distinct document gains count identical source hashes once across routes. The verifier supplies the underlying evidence under the applicable acceptance gates.

```sh
python3 re/automation/PilotEvidence.py --store /path/to/ResearchStore \
  --manifest /private/path/PilotEvidence.json --manifest-sha256 FULL_SHA256
```

The report verifies the frozen controller window, the supplied file hashes and the record schema. It reports supplied attestations alongside controller activity and marks omitted attestation sources as unmeasured. Retain the independent evidence referenced by the source records. The applicable independent gate verifies the referenced receipts and establishes acceptance. The report emits aggregate counts, time bounds and digests for pre-pilot preparation.

Supply the optional `ci_activity` pin to measure jobs from GitHub Actions API observations. Wrap the API job objects in the same source envelope without changing their fields. For a single attempt, the CLI can collect all jobs for the pinned run and attempt with the following command. [GitHub Actions job endpoints](https://docs.github.com/en/rest/actions/workflow-jobs#list-jobs-for-a-workflow-run-attempt)

```sh
gh api --paginate --slurp \
  'repos/OWNER/REPO/actions/runs/RUN_ID/attempts/ATTEMPT/jobs?per_page=100' \
  --jq '{version:1,authority:"github_actions_job_observations",records:[.[].jobs[]]}' \
  > CiActivity.json
```

The report checks repository, run, job, attempt, and revision identifiers and deduplicates the same job observation. A settled job belongs to the window containing its completion. The report sums each job's observed creation-to-start and start-to-finish intervals and records the sample count for each sum. The creation-to-start interval can include wait for dependencies or scheduling. Overlapping job intervals contribute to the sums independently. Skipped jobs contribute only to conclusion counts. Jobs with missing timing and unfinished jobs that appeared in the window make the evidence partial when at least one job has a recorded execution interval. Preserve the pinned source alongside the report.

The first retrospective replay used attempt 1 of the workflow-quality run for PR head `5605c58f`. It retained eight successful jobs, one failed job and one skipped job. Nine jobs had both timing intervals, totaling 18 creation-to-start job seconds and 3,031 start-to-finish job seconds. The same frozen report replayed byte-for-byte against 19 historical A03 controller events without changing its ledger. This establishes the offline timing measure. [Hosted workflow](https://github.com/TryUniCAD/Kit/actions/runs/43794606581)

The hosted process fixture checks replay after later controller activity, overlapping and open intervals, CI timing coverage, deduplication, distinct document and route counts, and refusal of changed evidence or conflicting record IDs. Hosted verification of the CI timing source is pending.
