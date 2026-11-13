# Free-plan runner limits

A workflow might appear able to select a larger GitHub-hosted runner with more CPUs.
The TryUniCAD organization uses the GitHub Free plan.
The `GET /orgs/TryUniCAD/actions/hosted-runners` request returns HTTP 404.
The message is `GitHub hosted runners are not supported for this organization`.
A job with a larger-runner label waits for a runner that does not exist.
Larger runners are billed for each minute, also in public repositories.

Public repositories get 4-CPU `ubuntu-24.04` and `ubuntu-24.04-arm` runners at no cost.
Use all CPUs of these runners before you add jobs.

The Free plan also allows at most 20 concurrent jobs.
In run [43371286350](https://github.com/TryUniCAD/Kit/actions/runs/43371286350), 3 merge-group runs started within 30 seconds.
Its shard jobs waited 2.6 to 3.4 minutes for a runner.
Each additional queue job increases this wait.
See [Actions limits](https://docs.github.com/en/actions/reference/limits),
[larger runners](https://docs.github.com/en/actions/concepts/runners/larger-runners),
and [the parallel test shards](../../Changes/ParallelTestShards.md).
