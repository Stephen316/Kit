from convert.formats.Fusion.TSplineCodec.Model.CompoundGrip import CompoundGrip
from convert.formats.Fusion.TSplineCodec.Model.GripMapping import GripMapping
from convert.formats.Fusion.TSplineCodec.Model.GripOwner import GripOwner
from convert.formats.Fusion.TSplineCodec.Reading.ReadCompound import ReadCompound
from convert.formats.Fusion.TSplineCodec.Wire.TextCursor import TextCursor
from convert.formats.Fusion.TSplineCodec.Wire.ReadInteger import ReadInteger


def ReadMapping(Cursor: TextCursor) -> GripMapping | None:
    if not Cursor.HasKind("0m"):
        return None
    if Cursor.ReadFields("0m", 1) != ("odd-grip-map",):
        raise ValueError("Unsupported TSM grip map declaration")
    Owners: list[GripOwner] = []
    Compounds: list[CompoundGrip] = []
    while Cursor.HasKind("0m"):
        Fields = Cursor.ReadFields("0m")
        if len(Fields) == 2 and Fields[0] in ("gvp", "gv") and not Compounds:
            Owners.append(GripOwner(ReadInteger(Fields[1]), Fields[0] == "gvp"))
        elif Fields and Fields[0] == "cg":
            Compounds.append(ReadCompound(Fields[1:]))
        else:
            raise ValueError("Unsupported TSM grip map record")
    return GripMapping(tuple(Owners), tuple(Compounds))
