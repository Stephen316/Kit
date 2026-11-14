from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec


def CheckRectDims(SpecValue: DocumentSpec) -> None:
    if type(SpecValue.ConstrainRectangle) is not bool:
        raise ValueError("Rectangle constraint selection must be Boolean")
    if not SpecValue.ConstrainRectangle:
        return
    if SpecValue.ProfileKind not in ("rectangle", "cuboid"):
        raise ValueError("Rectangle constraints require a rectangle or cuboid profile")
    Names = (SpecValue.ParamName, SpecValue.WidthParamName, SpecValue.DepthParamName)
    Reserved = {"d" + str(Index) for Index in range(1, 8)}
    for NameValue in Names:
        if (
            not isinstance(CastValue(object, NameValue), str)
            or not NameValue
            or len(NameValue) > 1024
            or not NameValue.isascii()
            or not NameValue.isidentifier()
            or NameValue in Reserved
        ):
            raise ValueError("Invalid or reserved dimension parameter name")
    if len(set(Names)) != len(Names):
        raise ValueError("Height, width and depth parameter names must be distinct")
