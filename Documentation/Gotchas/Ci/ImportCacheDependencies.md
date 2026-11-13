# Import cache hides test dependencies

A record of the code that a test runs might appear to list every module that the test depends on.
Python imports each module once in each process and keeps it in `sys.modules`.
A later test that imports the same module runs none of the module's top-level code.
The test can still use constants, classes, and cached values from that module.
Its executed code then does not show the dependency.

Record each `import` statement and `importlib.import_module` call, also when the module is already loaded.
Record which file did each import, and follow those links from each test module.
The [queue test reuse](../../Changes/QueueTestReuse.md) wraps `builtins.__import__` and `importlib.import_module` for this reason.
See [the import system](https://docs.python.org/3/reference/import.html#the-module-cache).
