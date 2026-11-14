from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Rectangle.RectangleRoles import (
    KCornerRoles,
    KLineRoles,
)
from convert.formats.Fusion.DocumentCodec.Sketch.LinkSketchMut import LinkSketchMut
from convert.formats.Fusion.DocumentCodec.Values.ValueShapes import MakePoint


def LinkRectangle(Author: AuthorState) -> None:
    Reference = Author.Reference
    Width, Depth = Author.SpecValue.WidthMm / 10.0, Author.SpecValue.DepthMm / 10.0
    Corners = ((0.0, 0.0), (Width, 0.0), (Width, Depth), (0.0, Depth))
    Directions = ((1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0))
    for Index, RoleName in enumerate(KCornerRoles):
        Author.Change(
            RoleName,
            point=MakePoint(*Corners[Index]),
            curveUses=Reference(RoleName + "_uses"),
        )
        Author.Change(
            RoleName + "_uses",
            geometries=[
                Reference(LineName)
                for EdgeIndex, LineName in enumerate(KLineRoles)
                if Index in (EdgeIndex, (EdgeIndex + 1) % 4)
            ],
        )
    for Index, RoleName in enumerate(KLineRoles):
        Start, Finish = Corners[Index], Corners[(Index + 1) % 4]
        Author.Change(
            RoleName,
            lineCurve=dict(
                startPoint=MakePoint(*Start),
                displacement=MakePoint(Finish[0] - Start[0], Finish[1] - Start[1]),
            ),
            lineDirection=MakePoint(*Directions[Index]),
            planeNormal=MakePoint(0.0, 0.0, -1.0),
            rStartPoint=Reference(KCornerRoles[Index]),
            rEndPoint=Reference(KCornerRoles[(Index + 1) % 4]),
        )
    LinkSketchMut(Author)
