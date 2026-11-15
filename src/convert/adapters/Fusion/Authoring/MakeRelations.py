from interchange.geometry.models.Sketch import ConstraintRef, SketchRelation


# the relations operation needs a consistent construction rule so public document claims remain grounded in native records
def MakeRelations() -> tuple[SketchRelation, ...]:
    Values = [
        SketchRelation(
            f"constraint-{Index}",
            "horizontal" if Index % 2 == 0 else "vertical",
            (ConstraintRef(f"line-{Index}"),),
        )
        for Index in range(4)
    ]
    Values.extend(
        (
            SketchRelation(
                "dimension-width",
                "distance_x",
                (ConstraintRef("point-0"), ConstraintRef("point-1")),
                "width-dimension",
            ),
            SketchRelation(
                "dimension-depth",
                "distance_y",
                (ConstraintRef("point-0"), ConstraintRef("point-3")),
                "depth-dimension",
            ),
        )
    )
    return tuple(Values)
