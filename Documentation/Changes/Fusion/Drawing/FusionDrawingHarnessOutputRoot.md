# Fusion drawing harness output root

## Problem

The native drawing harness wrote every round into `%TMPDIR%/KitFusionDrawings`.
Two problems followed from that fixed location.

A research round that built variants elsewhere could not point the runner at its
own `Variants` directory, so rounds overwrote each other's plan files and round
summaries.

The Fusion-side upload script also ignored any chosen root. The runner held plan
files under a custom root while the script that runs inside Fusion looked in the
temporary directory, so the two halves of a round could disagree about which
variant set they were exercising.

## Change

`BisectRound.py` now resolves its `Variants` directory from `KIT_DRAWING_OUT`,
falling back to `%TMPDIR%/KitFusionDrawings` when the variable is unset.

`RunGuarded.mjs` forwards `KIT_DRAWING_OUT` into the generated dispatch script, so
the Python code it runs inside Fusion observes the same root as the driving
process.

`BeginUploads.py` additionally reads the `PlanArbitrary.json`,
`PlanZeroChecksum.json`, and `PlanIsolate.json` plan files that later rounds write.

| File                                                          | Change                                                        |
| ------------------------------------------------------------- | ------------------------------------------------------------- |
| `re/Fusion/Reconstruction/Drawings/Native/BisectRound.py`      | `Variants` root from `KIT_DRAWING_OUT` with the old default   |
| `re/Fusion/Reconstruction/Drawings/Native/RunGuarded.mjs`      | Export `KIT_DRAWING_OUT` into the dispatched Python script     |
| `re/Fusion/Reconstruction/Drawings/Native/BeginUploads.py`     | Read three more plan files                                    |

## Limits

This is research harness plumbing in `re/`. It does not change any reader,
writer, or product behavior, and it makes no claim about drawing output.

The variable only selects where a round reads and writes its own plan files,
round summaries, and uploaded archives. It does not change how Fusion opens a
variant or how a round judges the result.

A round that sets the variable must set it for every process in the round,
because the runner and the in-Fusion script both read it.

## Recorded verification

Rounds were run with `KIT_DRAWING_OUT` pointing at a scratch directory outside
`%TMPDIR%`, and the runner read and wrote `Variants/BisectC15TP.json` and
`Variants/BisectC16TP.json` under that directory while uploading the matching
variants.

The upload summary for those rounds recorded the expected plan labels and a
completed upload state, which shows the in-Fusion script read the same root.

No local tests ran. Remote PR CI covers the changed files.
