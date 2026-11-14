from math import pi as KPiValue

from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Sketch.LinkSketchMut import LinkSketchMut
from convert.formats.Fusion.DocumentCodec.Values.ValueShapes import MakePoint


def LinkCircleMut(Author: AuthorState) -> None:
    Reference = Author.Reference
    Author.Change("circle_center", curveUses=Reference("center_uses"))
    Author.Change("center_uses", geometries=[Reference("circle")])
    ArcFields = dict(
        center=MakePoint(),
        normal=MakePoint(0.0, 0.0, 1.0),
        refVec=MakePoint(1.0),
        radius=Author.SpecValue.RadiusMm / 10.0,
        startAngle=0.0,
        endAngle=2.0 * KPiValue,
    )
    Author.Change("circle", arcCurve=ArcFields, rCenterPoint=Reference("circle_center"))
    LinkSketchMut(Author)
