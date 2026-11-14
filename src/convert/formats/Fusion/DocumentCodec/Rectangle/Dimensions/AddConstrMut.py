from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Rectangle.RectangleRoles import KLineRoles
from convert.formats.Fusion.DocumentCodec.Sketch.SketchRole import SketchRole
from convert.formats.Fusion.DocumentCodec.Values.MakeAttributes import MakeAttributes


def AddConstrMut(Author: AuthorState) -> None:
    Reference = Author.Reference
    SketchName = SketchRole(Author)
    Roles: list[str] = []
    for Index, LineName in enumerate(KLineRoles):
        RoleName = LineName + "_constraint"
        Roles.append(RoleName)
        Author.Allocate(
            RoleName,
            "SketchGeomConstraint",
            Subjects=[LineName],
            NamedPairs=MakeAttributes(EntityGenesis=Author.Policy.SketchGeneration),
            Fields=dict(
                ParentNode=Reference(SketchName),
                constraintType=64 if Index % 2 == 0 else 128,
                geometries=[Reference(LineName)],
                isVisible=False,
            ),
        )
    Author.Change(SketchName, constraints=[Reference(RoleName) for RoleName in Roles])
    Author.Change("corner_a", isFixed=True)
