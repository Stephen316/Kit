# Breaking change label event concurrency

Opening and editing a PR can start separate label runs on the same commit.
The shared concurrency group let the edit displace the opening run in [PR #78](https://github.com/TryUniCAD/Kit/actions/runs/43175011024/job/131037021398).
Disabling cancellation of running jobs still leaves a one-job pending limit.
Use a separate concurrency group for each event type and read current PR metadata before applying the label.
See [breaking change label checks](../../Changes/BreakingChangeLabelChecks.md).
