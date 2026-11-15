# A sketch reference does not establish dimension-driven geometry

A bodyless sketch may have a valid reference feature and literal circle or line
geometry while its document parameter is unrelated to those entities. JSON can
preserve this graph and report native capabilities without establishing that a
dimension change drives geometry. Suppressed or reference dimensions likewise
do not provide an active driving relation.

`kit convert` requires an active driving constraint bound to each
sketch's parameter IDs and a matching SDK authoring/native-state regeneration
contract. The contract prevents unrelated or stale geometry from qualifying by
adding parameter IDs alone. Python 3.14 is required for this validation. Use
`kit decode` or `kit research` for unqualified sketches; constrained SDK rectangle
sketches remain eligible. Solid profiles have the same dimension requirement;
see [the complete model guard](../../../Changes/Commands/ParametricModelGuard.md).
Writer evidence still does not establish measured
target-application edit/rebuild acceptance.

See [the change entry](../../../Changes/Commands/SketchDimensionGuard.md).
