# Fusion origin coincidence research probe

The probe generates an ordinary 17.75 × 24.125 mm XY rectangle with a separate sketch origin.
It adds a coincidence between the free rectangle corner and the fixed origin.
The research shim adds this relation before the existing author allocates the two driving size dimensions.
The shim stays inside the probe process.

## Reproduce the archive evidence

Use Python 3.14 from a Git checkout with the P01 and P03 discovery capture revision `89c25945f5833ad9c3a1c6c683df510b5702dd54`.
Supply a new output directory for the generated F3D and JSON evidence.

```sh
python re/Fusion/Reconstruction/DimensionAuthoring/ProbeOrigin.py --output ../FusionOriginProbe
```

The generator uses the existing writer and the requested dimensions.
The reader checks the generated record layout and then opens the receipt-pinned controls for independent comparison.
The report records the codec revision, probe hash, archive hash, and exact control inputs.
Fresh identifiers and timestamps can change archive hashes between runs.

## Observed result

The run on codec revision `2eb009eee94e71922a5e5fe5b681c319a400e183` generated 58,744 bytes.
The F3D SHA-256 is `5e324332d0eb2ae0ad0b3a6abf7f654ec4790b4449f78eedfdbac279a7d8ec16`.
The JSON evidence SHA-256 is `ecd613a3aca4cc1eec89e44fa5f0170ce9df06c4c35c9a4172b032ad4fd0928d`.

| Record | Semantic arguments | Ordered subjects and observer slots |
| --- | --- | --- |
| Origin coincidence | Corner, origin | Origin 0, corner 0 |
| Width dimension | Corner, right endpoint | Corner 1, right endpoint 0 |
| Height dimension | Upper endpoint, corner | Corner 2, upper endpoint 0 |

The typed decoder and raw Design records agree on the generated subjects.
The corner belongs to two perimeter lines, and the distinct origin belongs to none.
All six P01 and eight P03 archives exhibit the same anchor ordering and endpoint observer ranks.
The settings observer slots come from each archive's allocation order. [Paired rectangle evidence](../../Research/Readers/Comparison/RectangularPairEvidence.md)

## Native evidence still required

Open the generated archive in a fresh licensed Fusion process between healthy controls.
Record load and rebuild diagnostics, the closed profile, and the five geometric relations.
Verify that the coincidence still reaches both distinct points and that the sketch is fully constrained.
Use `Design.allParameters` to inspect the two driving values. [Native parameter-edit evidence](FusionParamEditAcceptance.md)

Change `proof_width` to 19.25 mm and call `computeAll()`.
Verify the expected width and the original height, anchor and constraints.
Restore the width and repeat with `proof_height` at 26.75 mm.
Restore both original values, rebuild, then save and reopen in a fresh process.
Recheck the two dimensions, all relations, and the original 428.21875 mm² profile.
The current evidence covers archive generation and decoding. Native loadability and editability remain unmeasured.
