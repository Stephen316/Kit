from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.ContainerCodec.Model.DocStruct import DocStruct


# doc props needs an explicit state contract so archive members retain their native ownership and reference relationships
@MakeDataClass(frozen=True, slots=True)
class DocProps:
    Structure: DocStruct | None
