# Queue findings from the base

A merge-queue removal might appear to come from the removed PR. The repository CodeQL suites run only on merge-group candidates. A PR merged without a queue run can leave findings on `main`, and every later candidate then fails. Compare each finding path with the PR diff before you repair. Fix base findings, then enroll again. See [the PR #96 removal](../../Changes/DiffBreakdownCodeql.md).
