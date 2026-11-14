# Paired capture procedure and Fusion captures

## Behavior

A02c has a [capture procedure](../../Reference/Research/PairedCaptures.md) for the five paired recipes.
It defines the file set and the shared rules.
It has a SOLIDWORKS checklist for each recipe and a measurement form.

Each recipe folder under `re/automation/PairedCaptures/` has a `GenerateFusion.py` that authors the recipe through the Fusion API.
P01 has its own complete script.
P02–P05 use the shared [`FusionCapture.py`](../../../re/automation/PairedCaptures/FusionCapture.py).
The scripts do not use a Kit reader, writer or source archive.
Each script measures the pinned Fusion control archive before and after the capture.
It creates and closes only its own documents.

The optional [`KitCaptureRunner`](../../../re/automation/PairedCaptures/Runner/KitCaptureRunner/KitCaptureRunner.py) Fusion add-in runs queued capture scripts one at a time.
It runs only `GenerateFusion.py` files inside one configured folder.
It works on Windows and macOS, and it starts the next queued job as soon as the last one finishes.
Its `runner.json` reports the job count, failures, busy time and utilization.
It does not start automatically.

The SOLIDWORKS captures are described in [their own entry](SolidWorksPairedCaptures.md).

## Usage and limits

Follow the capture procedure for each recipe and application.
Run a Fusion script from the text command field with `Python.RunScript`, or queue it for the runner add-in.
The two Fusion baseline saves are separated by a document close and archive reopen in one process, not an application restart.
P01 records sketch coordinates in sketch space with the sketch frame.
P02–P05 record curve endpoints in world coordinates.
Analytic comparisons are labelled separately and never replace a measurement.
A capture does not qualify a reader, a writer or a conversion by itself.

Two Fusion behaviors affect capture scripts.
See [negative extent expressions](../../Gotchas/Conversion/Fusion/Api/FusionNegativeExtentExpression.md) and [face sketch reference planes](../../Gotchas/Conversion/Fusion/Api/FusionFaceSketchReferencePlane.md).

## Verification

Fusion 2706.1.17 ran each committed script with zero recorded errors.
Each `measurements.json` records the hash of the script and shared code that produced it.
P02, P03 and P05 used shared code at `d22d3600`, and P04 used it at `5c960b19`.
Every receipt hash and native file hash matches.
The control archive measured one body and 30,000 mm³ before and after every capture.

| Recipe | Baseline reading                            | Edits and variants                                                                 |
| ------ | ------------------------------------------- | ---------------------------------------------------------------------------------- |
| P01    | 800 mm², fully constrained                  | 820 and 920 mm² edits, inch and YZ variants at 800 mm²                             |
| P02    | 78.539816 mm² (25π), fully constrained      | 201.061930 mm² (64π) edit, inch and YZ variants at 25π                             |
| P03    | 8000 mm³, center (20, 10, 5) mm             | Three edits matched; YZ center (5, 20, 10); reversed boss center (20, 10, −5)      |
| P04    | 7680 mm³, center (20, 10, 4.875) mm         | Six edits matched; YZ center (4.875, 20, 10); through-all cut 7200 mm³             |
| P05    | 1206.371579 mm³ (384π), center (0, 0, 6) mm | Four edits matched; the 90° sweep center (2.759, 2.759, 6) turns from +X toward +Y |

Each edit measured the same value after a fresh reopen, and each restore measured the baseline value.
Every reading has a healthy feature tree and fully constrained sketches.
Two failed first runs of P04 were discarded before commit, and the scripts were repaired.
The Windows runner changes compile, but no Windows Fusion run has used them yet.
No local tests ran.
Independent qualification of these captures remains A02d work.

Commits `0b8dfbba` and `777a8ac7` published this entry and the capture procedure as empty files.
The cause was a formatting command that opened each file for writing before it read the file.
This revision restores both files from their last complete text.
