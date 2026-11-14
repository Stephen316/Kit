from typing import cast as CastValue

from convert.formats.Fusion.MaterialCodec.Models.PropertySpec import (
    KConnectMode,
    KPropertyKind,
    PropertySpec,
)
from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode

KTagKinds = {"Distance": "Float"}


def PropertyModel(Value: SchemaNode) -> PropertySpec:
    Attributes = dict(Value.Attributes)
    return PropertySpec(
        Attributes["id"],
        CastValue(KPropertyKind, KTagKinds.get(Value.TagName, Value.TagName)),
        Attributes.get("definitionIteratorData") == "true",
        Attributes.get("readonly") == "true",
        Attributes.get("allowmultiplevalues") == "true",
        Attributes.get("unit"),
        CastValue(KConnectMode, Attributes.get("allowconnectedassets", "none")),
    )
