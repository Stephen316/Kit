from convert.Formats.Fusion.GeometryCodec.EncodeSmtValue import EncodeSmtValue
from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.Formats.Fusion.GeometryCodec.HeaderStrings import HeaderStrings
from convert.Formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody
from convert.Formats.Fusion.GeometryCodec.Prism.CuboidRecords import CuboidRecords


# the cuboid smt operation needs a consistent construction rule so geometric values retain their native record boundaries
def EmitCuboidSmt(Model: CuboidBody, Stamp: GeometryStamp) -> bytes:
    Lines = ["23200 0 2 2", HeaderStrings(Stamp), "1 1e-6 1e-10"]
    for Record in CuboidRecords(Model):
        Fields = " ".join(EncodeSmtValue(Value) for Value in Record.Fields)
        Lines.append(f"{Record.NameValue} {Fields} #")
    Lines.append("End-of-ASM-data")
    return ("\n".join(Lines) + "\n").encode("utf-8")
