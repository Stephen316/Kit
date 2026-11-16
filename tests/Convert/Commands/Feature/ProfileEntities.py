from dataclasses import replace as ReplaceData
from math import tau as KFullTurn

from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import (
    ArcGeometry,
    CircleGeometry,
    LineGeometry,
)
from interchange.geometry.Models.Sketch import SketchEntity
from interchange.geometry.Models.VectorPlane import PlaneVector
from tests.Convert.Commands.Feature.ProfileCases import KProfileCases


# invalid profile contours need actual typed curves rather than untrusted closure metadata
def ProfileEntities(RecordKind: str) -> tuple[SketchEntity, ...]:
    Entities: tuple[SketchEntity, ...]
    if RecordKind in ("CircleZero", "KindMismatch", "MultipleLoops"):
        Entities = (
            SketchEntity(
                "circle",
                (
                    GeometryKind.KLine
                    if RecordKind == "KindMismatch"
                    else GeometryKind.KCircle
                ),
                CircleGeometry(
                    PlaneVector(0.0, 0.0), 0.0 if RecordKind == "CircleZero" else 1.0
                ),
            ),
        )
        if RecordKind == "MultipleLoops":
            Entities += (
                SketchEntity(
                    "second",
                    GeometryKind.KCircle,
                    CircleGeometry(PlaneVector(3.0, 0.0), 1.0),
                ),
            )
        return Entities
    if RecordKind == "UnsupportedArc":
        return (
            SketchEntity(
                "arc",
                GeometryKind.KArcGeometry,
                ArcGeometry(PlaneVector(0.0, 0.0), 1.0, 0.0, KFullTurn),
            ),
        )
    Points = KProfileCases[RecordKind]
    Entities = tuple(
        SketchEntity(
            "edge" + str(Index),
            GeometryKind.KLine,
            LineGeometry(PlaneVector(*Start), PlaneVector(*Finish)),
        )
        for Index, (Start, Finish) in enumerate(zip(Points, Points[1:]))
    )
    if RecordKind == "Disconnected":
        Entities = (
            *Entities[:-1],
            ReplaceData(
                Entities[-1],
                geometry=LineGeometry(PlaneVector(0.0, 3.0), PlaneVector(0.0, 0.0)),
            ),
        )
    return Entities
