# Explicit UTF-8 archive controller consumption

The archive gate now decodes both streams from `Controller.py` as strict UTF-8.
Use `InferenceArchiveGate.py` with its existing arguments; no new option is required.
The controller already emits UTF-8, so locale decoding could corrupt the artifact paths returned to `GateStore.result`.
For example, a Windows legacy decoder could change a path containing `é` before the gate opened the artifact.

The generic `invoke` function retains its existing default decoding for every other child script.
The caller inventory found that `Adapters.py` already selects UTF-8, while `LinuxOomGuest.py` discards controller stdout and inherits stderr without decoding either stream.
`ResearchTools.py` selects a directly executed CLI, and `FusionLifecycleRegistration.py` lists the controller source for policy hashes rather than invoking it.
No controller metadata cap, canonical payload, object digest, transaction, exit code or acknowledgement guarantee changes.

The new process coverage loads the actual archive gate and runs real controller commands against an isolated Unicode store path.
It exercises claim acknowledgement, a usable lease, Unicode argument refusal, genuine output refusal, one completed attempt and artifact opening through `GateStore.result`.
It also checks the unchanged canonical result digest and exact artifact bytes.
On POSIX, the child starts with a UTF-8 filesystem locale and disabled Python UTF-8 mode, then selects the C character locale before invoking the consumer.
This gives the consumer a verified non-UTF-8 default decoder without corrupting filesystem arguments at interpreter startup.
On Windows, the process retains the native ANSI decoder; a host configured with UTF-8 ANSI does not establish legacy-decoder coverage.

Python documents that [subprocess text mode uses its selected encoding or the text wrapper default](https://docs.python.org/3.13/library/subprocess.html#subprocess.run), and that [locale encoding depends on the platform and current character locale](https://docs.python.org/3.13/library/locale.html#locale.getencoding).
The implementation and process coverage received static checks only locally.
Hosted process execution remains required; this repair establishes no CAD or native acceptance.

The first hosted archive run reached 418 passing cases, but the consumer case stopped before its transport assertions because importing the real archive gate required `numpy` through `InferenceRunner.py` and `InferenceSearch.py`.
The archive environment selects the optional `dev` extra and disables default dependency groups.
The existing `numpy` declaration belongs to the separate `dev` dependency group.
The consumer case now lives at `tests/Research/Inference/ControllerUtfEightConsumerTests.py` and is selected by the existing deterministic inference job, which already supplies both the extra and the group.
Its assertions, real subprocess boundaries and the job's existing selectors remain intact.
The complete merge-queue test plan still includes the moved case.
After reading each shard's actual planned node IDs, the queue selects the existing `dev` dependency group only for shards containing `tests/Research/Inference/` cases.
Their conditional frozen sync retains the optional `dev` extra, disabled default groups, Python 3.14 and bytecode compilation.
Initial plan and shard syncs, test trackers, reuse rules, gate names and timeouts remain unchanged.
The complete candidate plan includes the relocated node path; dependency selection neither filters nor rewrites its planned IDs.
The [dependency selection gotcha](../../../Gotchas/Ci/Dependencies/OptionalDevIsNotDependencyGroup.md) records the distinction and observed limitation.
