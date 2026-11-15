# A parameter edit does not rebuild the cached brep

## Expectation

Changing a parameter in a design file changes the geometry, so a body's volume follows the new value
as soon as Fusion opens the file.

## Actual behavior

The body is stored as a cached BRep snapshot. Fusion opens the file, reports the new parameter, and
keeps the cached geometry until something asks for a recompute.

A design with `d1` at `20 mm` and two bodies of `24.0 cm³` each was edited to `40 mm`:

| State                        | `d1`        | Volumes cm³   |
| ---------------------------- | ----------- | ------------- |
| control                      | `20 mm`     | `[24.0, 24.0]` |
| edited, as opened            | `40.00 mm`  | `[24.0, 24.0]` |
| edited, after `computeAll()` | `40.00 mm`  | `[48.0, 48.0]` |

The volume doubles with the dimension, so the parameter is driving the feature; the geometry was
simply not rebuilt on open.

## Workaround

Call `Design.computeAll()` after opening an edited design, then read the geometry.
`computeAll()` returned `True` and the volumes changed from `24.0` to `48.0` cm³.

Do not conclude that a parameter edit failed because the volume did not move. Check the parameter
expression first, then recompute.

## Evidence

The run is recorded in the
[parameter edit change entry](../../../../Changes/Fusion/Authoring/FusionParamEditAcceptance.md).
The source is `re/Fusion/Study/bodymodes-405fbd002680/mirror_xy.f3d` and the edit is `d1` from
`20 mm` to `40 mm`.
