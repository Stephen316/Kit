from convert.Formats.Fusion.DocumentCodec.Defaults.MakeNumeric import MakeNumeric
from convert.Formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.Formats.Fusion.DocumentCodec.Rectangle.Dimensions.AddConstrMut import (
    AddConstrMut,
)
from convert.Formats.Fusion.DocumentCodec.Rectangle.Dimensions.AddDimMut import (
    AddDimMut,
)
from convert.Formats.Fusion.DocumentCodec.Rectangle.Dimensions.BindDimMut import (
    BindDimMut,
)
from convert.Formats.Fusion.DocumentCodec.Rectangle.Dimensions.LinkDimsMut import (
    LinkDimsMut,
)
from convert.Formats.Fusion.DocumentCodec.Rectangle.Dimensions.MakeDimAxes import (
    MakeDimAxes,
)
from convert.Formats.Fusion.DocumentCodec.Values.ReadObjects import ReadInteger


# the constrain contract needs a shared interpretation so model state retains its native feature and ownership relationships
def ConstrainMut(Author: AuthorState) -> None:
    AddConstrMut(Author)
    AxisValues = MakeDimAxes(Author.SpecValue)
    Watermark = ReadInteger(
        Author.FindEntity("parameters").FieldValues["highWaterMark"]
    )
    RuntimeId = ReadInteger(Author.FindEntity("fragment").FieldValues["nextParamId"])
    for Index, AxisValue in enumerate(AxisValues):
        Parameter = MakeNumeric(
            AxisValue.ParamName, AxisValue.LengthMm, "", Author.Policy.ParamBirthday
        )
        Parameter["creationIndex"] = Watermark + Index + 1
        Author.Allocate(
            AxisValue.RoleName + "_user",
            "Parameter",
            ParentRole="parameters",
            Fields=Parameter,
        )
    for Index, AxisValue in enumerate(AxisValues):
        AddDimMut(Author, AxisValue)
        BindDimMut(Author, AxisValue, Watermark + 3 + Index, RuntimeId + 1 + Index)
    Author.Change("parameters", highWaterMark=Watermark + 4)
    Author.Change("fragment", nextParamId=RuntimeId + 2)
    LinkDimsMut(Author, AxisValues)
