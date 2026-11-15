# Bind pending CI candidate fingerprints

A downstream research job can select the exact fingerprint object of a candidate with a settled `waiting_ci` attempt. Include the candidate in `depends_on` and use this input selector.

```json
{
  "depends_on": ["candidate:paired"],
  "inputs": {
    "candidate": {"dependency": "candidate:paired", "candidate_fingerprint": true}
  }
}
```

The input gives the job the candidate snapshot as an immutable JSON object. The downstream receipt binds that fingerprint and the selected candidate's receipt and result hashes. Controller status and settlement events include `waiting_ci_inputs` for work based on a pending candidate, even when its own execution completed. The pre-pilot report counts these completions explicitly. Other jobs wait for that provisional work to be rerun with verified prerequisites before using its result. Dependency result and artifact selectors still require a completed prerequisite.

When a CI binding changes, the controller invalidates dependent snapshots, revokes stale leases and discards previously accepted results based on the old fingerprint. Once the new candidate completes, the affected jobs become eligible again. If it is rejected, jobs that depend on it wait for evidence.

The hosted controller scenario exercises the fingerprint input, provisional completion, stale lease refusal, rejection and eligibility after an accepted replacement. Hosted verification is pending. Applying an authenticated member verdict remains a separate integration step.
