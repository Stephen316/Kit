# Commit-status attribution

A status fixture might appear to need a commit reference. The real response omits that reference. The [status-list API](https://docs.github.com/en/rest/commits/statuses#list-commit-statuses-for-a-reference) selects the commit through the request path. Remove fixture routing metadata before returning statuses. Verify native review status against the commit used in the API request.
