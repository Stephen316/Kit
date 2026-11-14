from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Rectangle.Dimensions.LinkDimGraphMut import (
    LinkDimGraphMut,
)
from convert.formats.Fusion.DocumentCodec.Rectangle.Dimensions.Model.DimensionAxis import (
    DimensionAxis,
)
from convert.formats.Fusion.DocumentCodec.Sketch.SketchRole import SketchRole
from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import ReadSeries


def LinkDimsMut(Author: AuthorState, AxisValues: tuple[DimensionAxis, ...]) -> None:
    Reference = Author.Reference
    Dimensions = [
        Reference(AxisValue.RoleName + "_dimension") for AxisValue in AxisValues
    ]
    Bindings = [Reference(AxisValue.RoleName + "_binding") for AxisValue in AxisValues]
    Author.Change(SketchRole(Author), dimensions=Dimensions)
    ChildNodes = ReadSeries(Author.FindEntity("dc_sketch").FieldValues["childNodes"])
    Author.Change(
        "dc_sketch", dcParameters=Bindings, childNodes=[*ChildNodes, *Bindings]
    )
    Helper = Author.FindEntity("parameter_names")
    Entries = ReadSeries(Helper.FieldValues["parameterMap"])
    for AxisValue in AxisValues:
        for Suffix in ("_user", "_model"):
            RoleName = AxisValue.RoleName + Suffix
            Parameter = Author.FindEntity(RoleName)
            Entries.append(
                {"key": Parameter.FieldValues["userName"], "value": Reference(RoleName)}
            )
            Helper.Subjects.append(RoleName)
    LinkDimGraphMut(Author)
