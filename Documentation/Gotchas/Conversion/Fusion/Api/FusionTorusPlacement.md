# A native axial torus capture ignored its requested center

The installed API documents `TemporaryBRepManager.createTorus(center, axis, majorRadius, minorRadius)` as constructing a torus at the supplied center. In Fusion 2706.1.17, the owned capture requesting center `(1.1,-0.7,0.5)` cm and axis `(0,0,1)` returned a torus centered at the origin. The native physical center, bounding box, exported SMT carrier and persisted F3D carrier all agreed on zero. Its body transform was identity. This was a native construction result, not a missing file placement transform.

The same capture using axis `(0,0.6,0.8)` preserved the requested center. This observation is specific to the recorded build and calls; it does not establish a universal API defect or an undocumented format convention.

For the owned axial comparison, construct at the origin and apply an explicit translation with `TemporaryBRepManager.transform`. [The placement control](../../../../../re/Fusion/LocalOracle/RoundCarriers/PlacementCapture.json) then reports center `(1.1,-0.7,0.5)` cm and unchanged volume 22.246088320055406 cm³. Its SMT/F3D carrier stores the translated center directly with an identity body transform.

Use measured native output as the oracle. Do not compare a writer against requested dimensions without checking what the native application actually produced. [The original capture](../../../../../re/Fusion/LocalOracle/RoundCarriers/Capture.json) preserves the discrepancy, and [the field inspection](../../../../../re/Fusion/Reconstruction/RoundCarriers/Evidence.json) records the decoded carrier fields.
