# A reversed pcurve runs on the negated edge range

## Expectation

A coedge pcurve maps the edge parameter to the surface. Its knot range looks equal to the edge range for both coedge senses.

## Actual behavior

The sense of a pcurve is the coedge `Reversed` flag compared with the pcurve `Reversed` flag. When the two flags differ, the pcurve runs on the negated edge range. An edge range (a, b) then gives the pcurve range (-b, -a).

The 113 byte-exact corpus members give these inline `exp_par_cur` ranges.

| Pcurve sense | Equal to the edge range | Negated edge range | Symmetric range, both match | Other range |
| --- | --- | --- | --- | --- |
| Same flags | 668 | 0 | 52 | 33 |
| Different flags | 0 | 574 | 60 | 1 |

The referenced pcurve forms encode the same sense in their sign. Forms 1 and 2 occur with the same flags only, 250 times. Forms -1 and -2 occur with different flags only, 114 times.

## Workaround

Give `NurbsUse.Pcurve` in the direction and range of its edge. `CreateNurbsBody` applies `NegateCurve` to a reversed use. Apply `NegateCurve` again when you read the pcurve of a reversed coedge back into edge parameters. Do not compare a pcurve range with its edge range before you apply the sense.

## Evidence

Fusion 2706.1.17 accepted the closed `AuthoredPillow` solid with 12 reversed uses. Its volume relative error was 3.18e-8.

- [Pcurve survey](../../../../../re/Fusion/Reconstruction/ComplexGeometry/SurveyPcurves.json)
- [Native acceptance](../../../../../re/Fusion/LocalOracle/ComplexGeometry/NativeAcceptance.json)
- [Complex geometry change entry](../../../../Changes/Fusion/Geometry/FusionComplexGeometry.md)
