# Fusion sketch-owned dimension research probe

The probe generates a 40 × 20 mm XY rectangle with the explicit corner-to-origin coincidence.
Its complete parameter inventory consists of the sketch-owned driving dimensions `width_mm` and `height_mm`.
Each model parameter stores a literal length expression and binds directly to the corresponding sketch dimension.
The allocation changes occur inside the research probe process.

## Reproduce the archive evidence

Use Python 3.14 from a Git checkout containing discovery revision `89c25945f5833ad9c3a1c6c683df510b5702dd54`.
Supply a new output directory.

```sh
python re/Fusion/Reconstruction/DimensionAuthoring/ProbeOwnedDims.py --output ../FusionOwnedDimensionProbe
```

The command writes `OwnedRectangle.f3d` and `OwnedRectangleEvidence.json`.
It generates the archive before reading the six receipt-pinned P01 controls.
The report records the codec revision, both probe hashes, and the generated and control archive hashes.
Fresh identifiers and timestamps can change archive hashes between runs.

## Recorded archive comparison

The archive at codec revision `e9097e8f47249012118ce3d2b2c4c6ab7f442302` has 57,976 bytes.
Its SHA-256 is `4054963f82329aecdd85d3566e0ca1ade7c67d51e88f908b4fb1162fc9dfd49d`.
The JSON evidence SHA-256 is `436aacdf2cae8287a81aafd7104c402af923b45879152b0463d0c08cbc4d1edb`.

| Model parameter | P01 baseline A parameter, binding, dimension | Generated parameter, binding, dimension |
| --- | --- | --- |
| `width_mm` with `40 mm` | 258, 259, 257 | 1125, 1126, 1128 |
| `height_mm` with `20 mm` | 265, 266, 264 | 1129, 1130, 1132 |

The six P01 archives and the generated archive share ProductVersion `2706.1.17` and the same Design metadata version words.
Each bound numeric parameter has 11 zero expression metadata bytes and matching cached values in its binding.
The two baseline edit captures independently change the stored width to 41 mm and height to 23 mm.
The name table contains the two model parameter references in every file.
The saved table entry order varies across P01 controls, while its subjects remain parameter table, width, height.

The paired reads check the dimension-to-binding and binding-to-parameter joins.
The generated graph also connects both bindings to the anchored sketch, its child inventory, and their update nodes.
The generated dimension settings subjects use the authoring allocation. [Origin coincidence probe](FusionOriginCoincidenceProbe.md)

## Native evidence still required

Open the generated archive in a fresh licensed Fusion process between two healthy controls.
Use `Design.allParameters` to verify the two direct model parameters and check their owning sketch dimensions.
Record the closed profile, origin coincidence, fully constrained state, and 800 mm² initial area. [Parameter-edit evidence](FusionParamEditAcceptance.md)

Set `width_mm.expression` to `41 mm` and call `computeAll()`.
Verify an 820 mm² profile, the original height, and the same coincidence.
Restore `40 mm` and recompute.
Set `height_mm.expression` to `23 mm` and recompute.
Verify a 920 mm² profile, the original width, and the same coincidence.
Restore `20 mm`, recompute, save, and reopen in a fresh process.
Verify the original area, both driving values, and the preserved constraint inventory.
Native loadability and editability remain unmeasured for this research archive.
