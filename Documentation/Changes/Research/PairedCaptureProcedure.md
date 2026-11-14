# Paired capture procedure and first Fusion capture

## Behavior

A02c now has a [capture procedure](../../Reference/Research/PairedCaptures.md) for the five paired recipes.
It defines the file set, the shared rules and a P01 checklist with a measurement form for SOLIDWORKS.

[`GenerateFusion.py`](../../../re/automation/PairedCaptures/P01/GenerateFusion.py) authors P01 through the Fusion API from the recipe.
It does not use a Kit reader, writer or source archive.
It measures the pinned Fusion control archive before and after the capture.
It creates and closes only its own documents.

The first Fusion run is in `re/automation/PairedCaptures/P01/fusion-5dc3245eb59c/`.
It contains six native files, `measurements.json` and `receipt.json`.

## Usage and limits

Follow the capture procedure for each recipe and application.
Run the Fusion script from the Fusion text command field with `Python.RunScript`.
Sketch entity coordinates are in sketch space.
The measurements record each sketch frame, so world coordinates can be derived.
The two Fusion baseline saves are separated by a document close and archive reopen in one process, not an application restart.
P01 has no SOLIDWORKS capture yet, and P02–P05 have no captures.
A capture does not qualify a reader, a writer or a conversion by itself.

## Verification

Fusion 2706.1.17 ran the committed script with zero recorded errors.
The script hash in `measurements.json` matches the committed script.
The receipt hash matches `measurements.json`, and all six native file hashes match their files.
The control archive measured one body and 30,000 mm³ before and after the capture.
The baseline, its fresh reopen and its unchanged rebuild each measured 800 mm², a fully constrained healthy sketch and the recipe constraints.
The `width_mm` = 41 edit measured 820 mm², and the `height_mm` = 23 edit measured 920 mm².
Each edit measured the same area after a fresh reopen, and each restore measured 800 mm².
The inch-units and YZ variants measured 800 mm² after a fresh reopen.
The YZ sketch frame maps its corners to world (0, 0, 0), (0, 40, 0), (0, 40, 20) and (0, 0, 20) mm.
No local tests ran.
Independent qualification of these captures remains A02d work.
