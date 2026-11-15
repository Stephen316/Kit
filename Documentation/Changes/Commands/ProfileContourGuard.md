# Validate supported creator contours before conversion

`kit convert` no longer treats declared closed-profile entity IDs as geometric proof.
Each creator sketch must contain one unambiguous supported outer profile.
The guard indexes sketch entities once, rejects duplicate identities or repeated members, and requires declared member kinds to match their geometry classes.
Construction members remain unsupported.

The supported contours are one complete circle or an ordered simple ring of three or four straight sides.
Circle checks reuse the SDK's analytic B-rep curve validator for finite centers and positive finite radii.
Line checks reuse `ReadPrismRing` and `MeasureRing` for finite nonzero segments, source-order connectivity, closure, distinct vertices, simplicity, and positive finite measures.
No body or CAD application is constructed for this check.

The existing SDK simplicity check compares edge pairs.
Restricting this boundary to at most four sides bounds that work per profile; entity indexing and member traversal remain linear in the total input size.
Arcs, splines, mixed curves, longer rings, and multiple loops remain inspection-only until their contour contract and bounded validation are supported.
Supported authoring and native Fusion circle and rectangle profiles retain their existing path.
Contour validation does not establish evaluated body geometry, losslessness, native loadability, or parametric acceptance.

Process cases retain a typed Fusion body and valid feature bindings while replacing the sketch with a one-line declaration, open or disconnected chains, zero-length or collinear sides, a crossed loop, a repeated member, a zero-radius circle, mismatched kind tags, and unsupported arc, longer-ring, or multiple-loop profiles.
Every case validates the neutral source and checks root/nested conversion refusal, missing/existing destination preservation, source preservation, and inspection.
Existing Fusion and resolved-assembly positives remain required.

No local tests, decoding, or CAD applications ran.
Anchored Black and Prettier formatting passed.
Pyright reported zero errors, mypy reported no issues, and steering compliance passed for all six changed Python files.
Pyright also reported three unsupported settings already present in the repository configuration.
Source inspection found no archive or Python 3.14 compression import in the new math/model dependency path; Python 3.11 startup evidence remains a remote CI requirement.
Tracked-tree path policy and staged whitespace checks passed; new runtime evidence remains pending remote CI.

See [command usage](../../Tasks/CommandLine.md) and [the closed-profile tag gotcha](../../Gotchas/Conversion/Commands/ClosedProfileTagsAreNotClosure.md).
