# Cached bytecode and checkout timestamps

Cached `.pyc` files might appear to be valid for the same source files in a later job.
By default, a `.pyc` file stores the modification time and size of its source file.
`actions/checkout` writes each source file again, so each file gets a new modification time.
Python then compiles every cached file again and does not use the cache.

Compile the cached bytecode with `python -m compileall --invalidation-mode checked-hash`.
Python then compares a hash of the source file and ignores the modification time.
Python compiles only the changed files again.
See [cached bytecode invalidation](https://docs.python.org/3/reference/import.html#cached-bytecode-invalidation)
and [the queue build cache](../../Changes/QueueTestReuse.md).
