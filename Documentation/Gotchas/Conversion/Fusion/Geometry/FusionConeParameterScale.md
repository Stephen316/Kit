# Fusion cone parameter scale is not the upper radius

An ASM `cone-surface` stores an ellipse followed by sine, cosine, a dimensional parameter scale, sense and optional parameter limits. Interpreting the third scalar as the top radius appears plausible for a cylinder because the values coincide, but produces the wrong parameterization for a taper.

Kit reads the first surface parameter as longitudinal motion and the second as the angular direction. For a circular forward cone with positive cosine, axial motion is then `u * scale * cosine` and radial growth is `u * scale * sine`. The geometric radius at height `z` is `baseRadius + z * sine / cosine`. Kit-authored frustums built on this reading passed Fusion's volume, area, centroid and bounds checks. The upper radius is determined by the trimming topology and height, not a second radius field on the surface record.

The independent writer chooses the native-compatible scale `baseRadius` and computes signed sine and positive cosine from the requested radius difference and height. The writer generates the two circular boundary carriers separately. In SMB, both the major vector and scale are dimensional and convert from millimetres to centimetres; sine and cosine do not scale. SMT keeps millimetres.

The controlled 7-degree taper source stores base radius 1 cm, scale 1 cm and upper rim radius 1.2087337535349378 cm at height 1.7 cm. Exact source hashes and field-level evidence are in [ConeEvidence.json](../../../../../re/Fusion/Reconstruction/FrustumModel/ConeEvidence.json), with the [equations and topology](../../../../../re/Fusion/Reconstruction/FrustumModel/FrustumModel.md). [Native acceptance](../../../../../re/Fusion/LocalOracle/Frustums/NativeAcceptance.json) records the frustum measurements.
