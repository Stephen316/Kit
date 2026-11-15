from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Values.PathEntity import PathEntity


# node target needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class NodeTarget:
    ExternalRef: PathEntity | None = None
    NodeRef: str | None = None
