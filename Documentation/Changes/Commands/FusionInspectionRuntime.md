# Fusion inspection runtime

Fusion container stream extraction and native inspection require Python 3.14 or newer.
The CLI rejects these operations on older interpreters before publishing output.
Container inventory and SOLIDWORKS inspection keep their existing Python support.

Install with `uv tool install --python 3.14 .` when these Fusion views are needed.
Python 3.14 provides the ZIP method 93 decoder needed by Zstandard members.
No additional codec dependency is installed.

The remote workflow-quality job covers the refusal through CLI subprocesses on Python 3.11.
The Fusion compatibility job covers successful extraction and native inspection on Python 3.14.
At `bd2812cf`, [workflow-quality run 43649929499](https://github.com/TryUniCAD/Kit/actions/runs/43649929499) passed its Python 3.11 process step.
Python 3.14 success evidence and final-head readiness remain recorded in PR #94 comments.
The first Python 3.14 run exposed invalid directory compression in the new fixture; file members now use method 93 while directories remain stored.
See [the directory-compression gotcha](../../Gotchas/Conversion/Fusion/Archive/ZstandardDirectories.md).
No local tests were run.

See [the command guide](../../Tasks/CommandLine.md) and [the runtime gotcha](../../Gotchas/Conversion/FusionInspectionRuntime.md).
