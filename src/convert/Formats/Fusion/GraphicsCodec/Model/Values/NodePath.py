from dataclasses import dataclass as MakeDataClass
from convert.Formats.Fusion.GraphicsCodec.Model.Values.PathEntity import PathEntity


# node path needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class NodePath:
    Entries: tuple[PathEntity, ...]
