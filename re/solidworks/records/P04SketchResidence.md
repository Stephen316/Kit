# P04 sketch records in the configuration stream

## Evidence

The remote discovery census for PR head `6cec3b3a7d2bc71413abb62f94255fb1d96d3ad2` ran on checkout `dc3c652d472eabe4620dce6bb7a16e8d95c92c42`. Census JSON SHA-256 is `897912d6c8d9898b57a3820ac9c8ab0cecb64684cb20db5aa23e8efdeaddbfbc`. Both P04 baseline A sketches have zero parsed markers. Their resolved-stream spans are 5,549–6,399 for `RectangleSketch` and 9,419–13,007 for `CutSketch`.

Read-only container inventory used [P04 baseline A](../../automation/PairedCaptures/P04/solidworks-c1986308375a/P04-solidworks-baseline-a.SLDPRT), Git blob `a195dde7efc466d8660e083a4e191bfef32bd1ce`, SHA-256 `c1986308375aaf68ebac6f8de61e70a47b9b33535c94271bab2e4bd00504c59d`. The input identity and application evidence are in the [capture receipt](../../automation/PairedCaptures/P04/solidworks-c1986308375a/receipt.json). No CAD process, reader test or P05 inputs were used in this inventory.

## Observations

- The 16,256-byte `Contents/Config-0-ResolvedFeatures` stream contains one `ff ff 1f 00 03` marker at 4,840, before both measured sketch spans. Neither span contains an accepted marker prefix. The existing sketch decode reads only the resolved feature span.
- The 42,879-byte `Contents/Config-0` stream has 20 of the existing 2026 marker prefix and SHA-256 `e40cdd1e562a9e501a0a29ac252745d5c5cac6a7265ef924ccef4f5d078b34ab`. Its two ten-marker groups begin at 3,800 and 12,937. The first is preceded by an `sgSketch` class definition at 3,772 with a point count of 5. The second is preceded by a class-reference candidate at 12,921 and the same count. Track class-map ownership before accepting the second token as an `sgSketch` reference.
- Using the established point tag at marker +56 or +64 and two little-endian doubles in metres, the first group's rectangle corners are `(15,6)`–`(25,14)` mm in XY. The second group's corners are `(0,0)`–`(40,20)` mm. On the width-44 edit, the groups move to `(17,6)`–`(27,14)` and `(0,0)`–`(44,20)` mm. On the cut-width-12 edit, the first reaches `(14,6)`–`(26,14)` while the second stays unchanged. On YZ both groups use their native local coordinates `(-Z,+Y)`. The local marker indices repeat across groups.
- Name-framed dimension scalar records immediately following the first group carry IDs 36, 37, 39 and 40 for `cut_width_mm`, `cut_height_mm`, `cut_left_mm`, and `cut_bottom_mm`. The second group precedes IDs 27 and 28 for `width_mm` and `height_mm`. IDs and names remain stable after reopen and across the tested shape and plane edits. The KeyWords XML explicitly lists these dimension names under feature 35 `CutSketch` and feature 26 `RectangleSketch`, respectively. The XML does not carry the observed dimension scalar IDs.

## Remaining ownership

Configuration-stream storage and coordinate correlation are directly observed. Ownership of those `sgSketch` objects by the resolved features remains unverified. The marker groups appear in reverse timeline order under relation-handle context, so neither marker order nor nearby matching dimensions provide a sufficient owner key for production. The [equation record findings](Equations.md#the-two-reference-chains) also leave the `moSkDimHandleValG2_c` handle unresolved.

Trace the `moSkDimHandleValG2_c` and `sgSketch` object references in the baseline and one width edit, recording stream class-map IDs and enclosing spans. Resolve the dimension handles to the sketch owner and verify that map on the YZ and cut-width variants before wiring configuration-stream marker recovery. Preserve native provenance by recording the configuration stream for geometry and the resolved stream for feature and face references. The resolved lane already labels `CutSketch` face-supported. Its producer and persistent face identity need a separate source-backed link.
