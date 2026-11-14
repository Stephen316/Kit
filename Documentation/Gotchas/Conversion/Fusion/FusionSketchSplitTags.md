# Sketch split tags are not constant defaults

## Expectation

The constructor's split ordinal/count pair `(1, 1)` and direction values `0` and `1` describe every persisted sketch tag.

## Actual behavior

The first full production corpus run passed 783 of 804 archive compatibility cases and rejected 21 archives at these restrictive integer guards. Fifteen archives contain 84 split tags, including `(1, 2)`, `(2, 2)`, `(2, 3)`, `(2, 4)`, and `(4, 4)`. Six other archives contain 14 directions equal to `UINT32_MAX`.

Every split pair in the corpus satisfies `1 <= sequence <= total`. Kit reads the pair as a fragment ordinal and a fragment count. Earlier binary inspection suggested that `UINT32_MAX` is a wildcard direction; no black-box experiment confirms that meaning. The maximum observed fragment count is a corpus observation, not a format limit.

## Workaround

Use the dedicated typed sketch-tag callback for the expanded corpus profile. Preserve all seven named fields, accept native direction values `0`, `1`, and `UINT32_MAX`, and validate the ordinal/count relationship jointly. The observed profile still requires version 3, secondary ID zero, and topology role flags zero; nonzero secondary allocation and complete role-bit meanings remain unqualified.

[The split-tag notes](../../../../re/Fusion/Reconstruction/EntityGraph/SketchSplitSemantics.md) describe the fields. [The read-only corpus report](../../../../re/Fusion/Reconstruction/EntityGraph/SketchSplitSamples.json) records all 5,077 tags across 712 archives with no extraction failures. Remote [run 43222880126](https://github.com/TryUniCAD/Kit/actions/runs/43222880126) passed all 807 compatibility cases after the correction, including all 712 corpus files and three malformed split-pair rejection cases. Local automated tests were not run.
