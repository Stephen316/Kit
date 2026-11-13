# Squash queue ancestry

A queued PR head might appear to be an ancestor of its merge-group candidate. With the `SQUASH` merge method, the candidate's only parent is the base commit, and the compare API reports the PR head as `diverged`. Identify the queued PR from the `gh-readonly-queue/<branch>/pr-<number>-<sha>` head ref, and compare trees instead of commit ancestry. See [the repair](../../Changes/SquashQueueReuse.md).
