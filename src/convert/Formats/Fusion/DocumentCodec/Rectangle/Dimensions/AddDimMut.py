from convert.Formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.Formats.Fusion.DocumentCodec.Rectangle.Dimensions.DimensionInfo import (
    DimensionInfo,
)
from convert.Formats.Fusion.DocumentCodec.Rectangle.Dimensions.Model.DimensionAxis import (
    DimensionAxis,
)
from convert.Formats.Fusion.DocumentCodec.Sketch.SketchRole import SketchRole
from convert.Formats.Fusion.DocumentCodec.Values.MakeAttributes import MakeAttributes
from convert.Formats.Fusion.DocumentCodec.Values.ValueShapes import MakeColor


# the dim operation needs a consistent construction rule so model state retains its native feature and ownership relationships
def AddDimMut(Author: AuthorState, AxisValue: DimensionAxis) -> None:
    RoleName = AxisValue.RoleName
    SketchName = SketchRole(Author)
    Author.Allocate(RoleName + "_model", "Parameter", ParentRole="parameters")
    Author.Allocate(
        RoleName + "_binding",
        "DcDoubleParameter",
        ParentRole="nodes",
        Subjects=["dc_sketch"],
    )
    Author.Allocate(RoleName + "_dynamic", "DynamicUpdateData")
    Author.Allocate(
        RoleName + "_dimension",
        "FusionSketchLinearDim",
        ParentRole=SketchName,
        Subjects=["settings", *sorted(AxisValue.PointRoles)],
        NamedPairs=MakeAttributes(EntityGenesis=0),
        Fields=dict(
            LinearDimensionInfo=DimensionInfo(Author, AxisValue),
            RefPositions=[0.0, 1.0],
            constraintType=AxisValue.ConstraintType,
            dcParameter=Author.Reference(RoleName + "_binding"),
            geometries=[
                Author.Reference(PointRole) for PointRole in AxisValue.PointRoles
            ],
            isSick=False,
            ParentNode=Author.Reference(SketchName),
            color=MakeColor(),
            isVisible=False,
        ),
    )
