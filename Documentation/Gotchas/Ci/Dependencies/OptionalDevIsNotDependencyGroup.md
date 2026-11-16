# Optional dev is separate from dependency group dev

Selecting `--extra dev` does not select the same-named `dev` dependency group.
The optional dependencies under `[project.optional-dependencies].dev` and the development dependencies under `[dependency-groups].dev` have separate selectors.
In this repository, the extra supplies pytest and its plugins; the group supplies `numpy` and other development tools.
Using `--no-default-groups --extra dev` therefore does not provide `numpy`.

At PR head `e4fd0ef0cec2f6582375495efd3228fdc79424db`, the hosted archive run passed 418 cases and stopped the real controller consumer case before its transport assertions.
The import chain was `InferenceArchiveGate.py` → `InferenceRunner.py` → `InferenceSearch.py:16`, where importing `numpy` failed.
The [operator report](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6929185774) identifies the actual missing dependency.
This failure did not establish a transport verdict.

Keep archive cases in their existing narrow environment.
Run the real inference consumer case through the existing deterministic inference job, whose command already selects both `--extra dev` and `--group dev`.
The case now lives under `tests/Research/Inference/` and remains selected explicitly by that job and recursively by the complete merge-queue test plan.
The queue preserves its initial narrow syncs and reads each shard's actual planned node IDs.
Only a shard containing a node under `tests/Research/Inference/` performs an additional frozen sync with the existing `dev` group before test execution.
That sync retains `--no-default-groups`, `--extra dev`, Python 3.14 and bytecode compilation.
The complete candidate plan includes the relocated node path; dependency selection neither filters nor rewrites its planned IDs.
Trackers, reuse rules, job names and timeouts remain unchanged.
Do not infer dependency availability from a shared name or from another step's environment.
No dependency declarations, test assertions or gate names changed for the relocation.

The relocation received static checks only locally; the relocated process case still requires hosted execution.
See the [consumer change entry](../../../Changes/Research/Controller/ControllerUtfEightConsumers.md) and uv's [dependency groups](https://docs.astral.sh/uv/concepts/projects/dependencies/#dependency-groups) and [optional dependency selection](https://docs.astral.sh/uv/concepts/projects/sync/#syncing-optional-dependencies) documentation.
