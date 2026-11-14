from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Values.PathEntity import PathEntity


@MakeDataClass(frozen=True, slots=True)
class NodeTarget:
    ExternalRef: PathEntity | None = None
    NodeRef: str | None = None
