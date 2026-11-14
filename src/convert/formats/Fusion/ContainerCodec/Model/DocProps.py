from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.ContainerCodec.Model.DocStruct import DocStruct


@MakeDataClass(frozen=True, slots=True)
class DocProps:
    Structure: DocStruct | None
