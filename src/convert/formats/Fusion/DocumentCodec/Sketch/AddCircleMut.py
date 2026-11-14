from convert.formats.Fusion.DocumentCodec.Values.MakeAttributes import MakeAttributes
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Sketch.AddSketchMut import AddSketchMut
from convert.formats.Fusion.DocumentCodec.Sketch.AddSketchDcMut import AddSketchDcMut


def AddCircleMut(Author: AuthorState) -> None:
    Generation = Author.Policy.SketchGeneration
    FirstTag = Author.Policy.FirstSketchTag
    AddSketchMut(Author)
    Author.Allocate(
        "circle_center",
        "Point3D",
        ParentRole="circle_sketch",
        NamedPairs=MakeAttributes(EntityGenesis=Generation, pt_tag=FirstTag + 1),
    )
    Author.Allocate("center_uses", "CurveUses", ParentRole="circle_center")
    Author.Allocate(
        "circle",
        "CircArc3D",
        ParentRole="circle_sketch",
        NamedPairs=MakeAttributes(
            EntityGenesis=Generation, crv_primary_id=FirstTag + 2, crv_secondary_id=0
        ),
    )
    AddSketchDcMut(Author)
