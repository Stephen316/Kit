# SOLIDWORKS sketch distance display records

The generation-19000 sketch replay now reads each saved distance display through its settings, typed dimension handle, cached lengths, favorite record and return. It follows the same scalar, string and transform readers used by the feature depth display. The sketch-specific handle resolves the owning `sgSketch` object and its saved dimension slot. The two saved cache values agree with the declared parameter within the discovery length tolerance.

All 94 display records replay across six P01, eight P03 and eleven P04 parts. The two independent baseline and YZ controls for each of P01 and P03 still match all 75 display pointer reads per control. The licensed P04 baseline trace also matches all 194 pointer reads between their respective display boundaries. The research replay rejected a typed handle whose slot was changed to the other valid dimension.

Run the pinned evidence commands:

```shell
python re/solidworks/archive/RectangularPlaneEvidence.py --through-operation --include-coincidence
python re/solidworks/archive/SketchEvidence.py --include-coincidence
python re/solidworks/archive/ResolvedEntry.py --through-operation
```

All three reports retain their prior digests. The [region walk](SolidWorksSketchRegionRecords.md) verifies the fields after the displays and the boundary's typed line handles. [Native pointer trace](../../../../re/solidworks/records/P04SketchGeometry.md#native-object-calls-in-the-baseline-a-sketches)
