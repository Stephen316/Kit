# xdist load chunks group slow tests

A slowest-first test order might appear to spread slow tests across all pytest-xdist workers.
The xdist 3.8.0 `load` scheduler sends consecutive tests to each worker at the start.
The first chunk is a quarter of the worker's share, with a minimum of 2 tests.
For 1,700 tests on 4 workers, the first worker gets the 106 slowest tests.
A small `--maxschedchunk` value does not remove the minimum of 2 tests.
The `worksteal` scheduler gives each worker a consecutive quarter of the tests.
It steals only from the end of a worker's queue.

Use `--dist load --maxschedchunk 1`.
Then each worker holds the test that runs and the next test.
Order the tests so that a fast test follows each slow test.
See [the scheduler source](https://github.com/pytest-dev/pytest-xdist/blob/v3.8.0/src/xdist/scheduler/load.py)
and [the parallel test shards](../../Changes/ParallelTestShards.md).
