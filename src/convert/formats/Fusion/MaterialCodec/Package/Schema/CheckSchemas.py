from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode
from convert.formats.Fusion.MaterialCodec.Package.PackageLimits import (
    KMaxSchemas,
    KMaxSchemaNodes,
    KMaxXmlDepth,
)
from convert.formats.Fusion.MaterialCodec.Package.Schema.CheckNode import CheckNode


def CheckSchemas(Values: tuple[SchemaNode, ...]) -> None:
    if not 0 < len(Values) <= KMaxSchemas or any(
        Value.TagName != "AssetSchema" for Value in Values
    ):
        raise ValueError("Invalid material schema count or root")
    Pending = [(Value, 0) for Value in Values]
    Count = 0
    while Pending:
        Value, Depth = Pending.pop()
        Count += 1
        if Count > KMaxSchemaNodes or Depth > KMaxXmlDepth:
            raise ValueError("Material schema exceeds node or nesting limits")
        CheckNode(Value)
        Pending.extend((Child, Depth + 1) for Child in Value.Children)
