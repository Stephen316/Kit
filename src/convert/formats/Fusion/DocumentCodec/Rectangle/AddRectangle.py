from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Rectangle.RectangleRoles import (
    KCornerRoles,
    KLineRoles,
)
from convert.formats.Fusion.DocumentCodec.Sketch.AddSketchDcMut import AddSketchDcMut
from convert.formats.Fusion.DocumentCodec.Sketch.AddSketchMut import AddSketchMut
from convert.formats.Fusion.DocumentCodec.Sketch.SketchRole import SketchRole
from convert.formats.Fusion.DocumentCodec.Values.MakeAttributes import MakeAttributes


def AddRectangle(Author: AuthorState) -> None:
    AddSketchMut(Author)
    Generation = Author.Policy.SketchGeneration
    FirstTag = Author.Policy.FirstSketchTag
    ParentRole = SketchRole(Author)
    for Index, RoleName in enumerate(KCornerRoles):
        Author.Allocate(
            RoleName,
            "Point3D",
            ParentRole=ParentRole,
            NamedPairs=MakeAttributes(
                EntityGenesis=Generation, pt_tag=FirstTag + Index + 1
            ),
        )
        Author.Allocate(RoleName + "_uses", "CurveUses", ParentRole=RoleName)
    for Index, RoleName in enumerate(KLineRoles):
        Author.Allocate(
            RoleName,
            "Line3D",
            ParentRole=ParentRole,
            NamedPairs=MakeAttributes(
                EntityGenesis=Generation,
                crv_primary_id=FirstTag + Index + 5,
                crv_secondary_id=0,
            ),
        )
    AddSketchDcMut(Author)
