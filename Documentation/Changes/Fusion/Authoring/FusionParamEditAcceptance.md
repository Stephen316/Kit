# Parameter edit in a Fusion-saved design

## Problem

Kit could author a design from a `DocumentSpec` and Fusion accepted it, but nothing recorded whether
Kit could change a parameter in a design Fusion had already saved. Authoring and editing are different
paths: an edit has to rewrite the design segment in place and keep every other record intact.

## Change

The edit path is now measured natively.

`BuildParamEdit.py` reads a Fusion-saved F3D, rewrites one parameter record in the design segment, and
writes the result beside an untouched control.
`OpenParam.py` uploads both, opens each in Fusion, and reports every parameter Fusion sees.

The rewrite uses the same record rebuild the parameter tests use: read the bulk spans, replace the
numeric record for the chosen parameter, and re-emit the segment.

## Recorded verification

Source: `re/Fusion/Study/advanced-627f7fe095f4/advanced.f3d`, parameter `d1`.

| Role    | `d1`        | `d2`        | `d3`                 |
| ------- | ----------- | ----------- | -------------------- |
| control | `30.00 mm`  | `35.00 mm`  | `56.309932474 deg`   |
| edited  | `45.00 mm`  | `35.00 mm`  | `56.309932474 deg`   |

Fusion 2706.1.17 opened both and reported the edited value on the edited file, with the other two
parameters unchanged. The run asserts the edited expression and fails if Fusion reports anything else.

An identity rewrite of the same file leaves all 29 zip entries byte-identical, so the edit changes the
parameter record and nothing else.

## Behavior

| Step                        | Result                                        |
| --------------------------- | --------------------------------------------- |
| Kit reads the parameters    | `d1`, `d2`, `d3` with their expressions       |
| Kit rewrites `d1`           | `30.00 mm` to `45.00 mm`                      |
| Fusion opens the control    | `d1` `30.00 mm`                               |
| Fusion opens the edited file | `d1` `45.00 mm`, `d2` and `d3` unchanged     |

## Geometry rebuild

A second run uses a design with bodies: `re/Fusion/Study/bodymodes-405fbd002680/mirror_xy.f3d`, with
`d1` at `20 mm` and two bodies of `24.0 cm³` each.

| State                        | `d1`        | Volumes cm³    |
| ---------------------------- | ----------- | -------------- |
| control                      | `20 mm`     | `[24.0, 24.0]` |
| edited, as opened            | `40.00 mm`  | `[24.0, 24.0]` |
| edited, after `computeAll()` | `40.00 mm`  | `[48.0, 48.0]` |

The volume doubles with the dimension, so the edited parameter drives the feature.
Fusion does not rebuild the cached BRep on open, which is recorded in the
[cached BRep gotcha](../../../Gotchas/Conversion/Fusion/Api/FusionCachedBrepRecompute.md).

## Reader cross-check

The same file was read by Kit and by Fusion, and the expressions compared:

| Parameter | Kit reads   | Fusion reports |
| --------- | ----------- | -------------- |
| `d1`      | `20 mm`     | `20 mm`        |
| `d2`      | `0.0 deg`   | `0.0 deg`      |
| `d3`      | `2`         | not listed     |
| `d4`      | `0.01 mm`   | not listed     |

Every parameter Fusion exposes is read by Kit with the same expression.
Kit also reads two records that Fusion does not list as parameters: a pattern count and a mirror
stitch tolerance.
Those are feature inputs stored in the same record stream, so Kit's read is a superset of
`Design.allParameters` and not a different set.

## Limits

The edit changes one parameter. A formula that references another parameter is untested.

A run that reads geometry from an edited design must call `Design.computeAll()` first, or it will
compare stale volumes.
