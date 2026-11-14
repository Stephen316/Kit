from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Values.PathEntity import PathEntity


@MakeDataClass(frozen=True, slots=True)
class NodePath:
    Entries: tuple[PathEntity, ...]
