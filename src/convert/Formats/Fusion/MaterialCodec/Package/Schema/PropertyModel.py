from typing import cast as CastValue

from convert.Formats.Fusion.MaterialCodec.Models.PropertySpec import (
    KConnectMode,
    KPropertyKind,
    PropertySpec,
)
from convert.Formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode

# the tag kinds vocabulary must stay centralized so material reconstruction agrees on supported native identities
KTagKinds = {"Distance": "Float"}


# the property model contract needs a shared interpretation so typed appearance properties retain their native identifiers
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
