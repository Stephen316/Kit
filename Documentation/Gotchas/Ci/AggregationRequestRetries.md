# Polling does not automatically retry failed GitHub requests

The CI aggregator polls while other checks are pending, but a failed API call can terminate the whole run before the next poll. The GitHub script action defaults to zero retries. Two PR 92 aggregate runs failed on a transient HTTP 503 from the pull-request endpoint while their underlying checks continued normally.

Configure bounded retries on the action's authenticated client to retry the read request. Keep authentication and validation failures non-retryable and retain the original head checks and CI acceptance rules. Retrying a failed aggregate manually is separate evidence and does not prove that automatic retry logic ran.

The pull-request workflow uses trusted base code. So a proposed retry setting on the PR will not affect that PR's aggregate until the setting exists in the trusted revision. [The change entry](../../Changes/CiAggregationApiRetries.md) links the observed runs and documents that verification boundary.
