# setup-uv cache in the merge queue

The `astral-sh/setup-uv` cache might appear to save the queue's Python 3.14 environment.
Its default `save-cache: auto` does not save a cache in a `merge_group` run.
A merge-group run can only restore caches from its own ref and from `main`.
The action computes its cache key before a later `uv sync --python 3.14` step runs.
Other `main` workflows sync Python 3.11 under the same key.
The saved cache can then lack the Python 3.14 packages and the Python 3.14 install.

Save the queue cache from a `main` push workflow.
Give that workflow and the queue jobs the same `cache-suffix` and `cache-python: true`.
See [the setup-uv inputs](https://github.com/astral-sh/setup-uv/blob/v10.3.3/action.yml),
the [merge-queue cache scope](QueueCacheScope.md), and [the queue build cache](../../Changes/QueueTestReuse.md).
