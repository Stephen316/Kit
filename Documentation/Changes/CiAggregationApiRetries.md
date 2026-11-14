# Retry transient API failures during CI aggregation

The existing CI aggregator now configures three retries for requests made through its authenticated GitHub client. A transient API failure can be retried without discarding the aggregation run; persistent failures still fail the job. The default non-retryable status codes remain 400, 401, 403, 404 and 422. Check selection, accepted conclusions, immutable head verification, permissions and the 90-minute job timeout are unchanged.

The change follows two observed failures in PR 92. Runs [43237852382](https://github.com/TryUniCAD/Kit/actions/runs/43237852382) and [43239427853](https://github.com/TryUniCAD/Kit/actions/runs/43239427853) each received HTTP 503 while reading the pull-request head during the wait for other checks. The first run passed on its second attempt without source changes. The second was retried after the same evidenced API failure; that retry also failed while other checks were still running. No automatic recovery is claimed for either attempt.

The pinned action supports bounded request retries with exponential backoff through its documented [`retries` input](https://github.com/actions/github-script#retries). The option retries API requests; it does not convert unsuccessful CI into successful evidence or rerun the checked jobs.

The workflow executes from the trusted base on pull requests. Consequently, this PR's existing aggregate runs do not execute the new option, and a successful manual rerun does not validate automatic retry behavior. Remote workflow policy checks can inspect this configuration; actual automatic recovery remains unverified until the reviewed change reaches a trusted workflow revision. This PR is not authorized to merge.

See [the API retry gotcha](../Gotchas/Ci/AggregationRequestRetries.md) and the existing [trusted-base guidance](../Gotchas/Ci/TrustedBaseAggregation.md).
