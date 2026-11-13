# Concurrency queue lint

A workflow copied from another repository can use `queue: max` in its `concurrency` block.
The pinned actionlint 1.7.12 rejects that key with `unexpected key "queue" for "concurrency" section`.
The workflow quality check then fails.
Use a concurrency group with `cancel-in-progress: false`.
GitHub then keeps one pending run, and a newer pending run replaces it.
Make the workflow tolerate a skipped intermediate run.
See the [actionlint issue](https://github.com/rhysd/actionlint/issues/657) and [diff breakdown reports](../../Changes/DiffBreakdownReports.md).
