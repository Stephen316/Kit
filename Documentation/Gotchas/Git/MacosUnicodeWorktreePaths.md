# macOS Unicode worktree paths

A new worktree might appear to contain untracked CAD fixtures.
Some tracked paths in [the V8 fixture directory](../../../examples/Single%20Turbo%20Dual%20Overhead%20Cam%20V8%20-%20KDP%20-%202024/) use decomposed Unicode.
Git on macOS can report the composed form as untracked when `core.precomposeunicode` is enabled.

Inspect those paths with a command-specific setting:

```sh
git -c core.precomposeunicode=false status --short -- examples
```

Stage only intended paths.
Do not delete or re-add the fixtures to clear the status output.
