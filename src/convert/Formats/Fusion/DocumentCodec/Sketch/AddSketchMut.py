from convert.Formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.Formats.Fusion.DocumentCodec.Sketch.SketchRole import SketchRole
from convert.Formats.Fusion.DocumentCodec.Values.MakeAttributes import MakeAttributes


# the sketch operation needs a consistent construction rule so model state retains its native feature and ownership relationships
def AddSketchMut(Author: AuthorState) -> None:
    RoleName = SketchRole(Author)
    Generation = Author.Policy.SketchGeneration
    Author.Allocate(
        RoleName,
        "MSketch",
        ParentRole="sketches",
        NamedPairs=MakeAttributes(EntityGenesis=Generation),
    )
    Author.Allocate("sketches_root", "SketchesRoot", RootName="SketchesRoot")
    Author.Allocate("sketch_coordinates", "CoordinateSystem", ParentRole="component")
    Author.Allocate(
        "sketch_origin",
        "Point3D",
        ParentRole=RoleName,
        Fields={
            "isFixed": True,
            "isFullyConstrained": True,
            "isOrigin": True,
            "isVisible": False,
        },
        NamedPairs=MakeAttributes(
            EntityGenesis=Generation, pt_tag=Author.Policy.FirstSketchTag
        ),
    )
    Author.Allocate("origin_uses", "CurveUses", ParentRole="sketch_origin")
