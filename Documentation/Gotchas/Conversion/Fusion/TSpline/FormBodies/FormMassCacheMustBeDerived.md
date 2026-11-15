# A Form mass cache must contain derived measurements

## Expectation

A Form body could omit its derived `MassPropertyCacheValue`, or keep zero placeholders until the first rebuild.
Fusion should calculate its center of mass from the converted BRep on initial load.

## Actual behavior

An empty `cache` collection fails Kit's inherited schema check. The body requires one cache group.
A cache whose vectors and scalars are zero lets Fusion open the body, but `physicalProperties.centerOfMass` initially returns `(0, 0, 0)`.
The native control reports its correct center at the same stage.
`computeAll` repairs the center, so checking only the later stage hides the persisted-cache defect.
The [initial failure](../../../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/InitialMassFailure.json) records 30 center-coordinate differences across 10 cases.

An independently supplied cap declaration causes a related persistence distinction.
Fusion canonicalizes `G0CAPS` and `G2CAPS` to `G1CAPS` when it imports a Form.
This does not remove the need for correct mass fields in Kit's independently written body.

## Workaround

Write one complete cache group from the typed BRep.
Evaluate bicubic points and derivatives on every knot span.
Integrate area, volume, first moments, and second moments with Gaussian quadrature and the divergence theorem.
Keep second moments in the coordinate-origin frame, because the cache stores the center separately.
Do not subtract centroid terms from inertia; `CuboidCache` and `PartCache` use the same origin-based convention.
Open sheets have zero volumetric properties instead of an invented center.
The [Form cache implementation](../../../../../../src/convert/formats/Fusion/DocumentCodec/Form/FormCache.py), [field model](../../../../../../re/Fusion/Reconstruction/FormDocuments/General/CapMassCacheModel.json), and [final native acceptance](../../../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/NativeAcceptance.json) record the derived result.
