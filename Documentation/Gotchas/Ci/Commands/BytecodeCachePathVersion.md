# Bytecode cache save and restore paths must match

Keeping the same Actions cache key does not make caches interchangeable when their configured path lists differ.
Adding the developer source root to the warmer and test planner left the shard restore step on the previous three-path version, so newly warmed caches could not match.

Keep all save and restore lists identical, including order: SDK sources, developer CLI sources, tools, and tests.
Compile the same four roots before saving.
See [the review finding](https://github.com/TryUniCAD/Kit/pull/119#discussion_r4578452316).
