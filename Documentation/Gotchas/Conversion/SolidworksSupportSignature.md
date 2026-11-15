# SOLIDWORKS sketch support signatures vary across captures

## Expectation

A generation stamp and an adjacent four-byte tag can appear to identify all principal-plane support records.

## Observed behavior

The existing scanner expects generation 18000 and tag `f6 5a 1a 69`.
The P01/P03/P04 captures use generation 19000 and tag `6c 42 d6 6a`.
The old signatures are absent from the P01/P03 user-sketch spans.
The production reader consequently falls back to stream order for these sketches.
The three YZ variants acquire Front Plane despite independent measurements identifying Right Plane.

See the [native source finding](../../../re/solidworks/records/PrincipalSupportCandidates.md) and [earlier layout](../../../re/solidworks/records/Resolvedfeatures.md).

## Workaround

Keep bounded candidate records and their exact source spans in research evidence.
Resolve the archive class reference and tag domain before changing production support decoding.
Do not replace one capture-specific tag with another.
Do not infer support from the recipe name, geometry, marker order or nearby dimensions.
Native qualification remains unavailable until the complete owner and reference chain is proven.
