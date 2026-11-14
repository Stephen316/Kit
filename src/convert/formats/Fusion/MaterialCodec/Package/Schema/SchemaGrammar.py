from convert.formats.Fusion.MaterialCodec.Package.Schema.NumberAttributes import (
    KNumberAttrs,
)
from convert.formats.Fusion.MaterialCodec.Package.Schema.TextAttributes import (
    KTextAttrs,
)

KSchemaAttrs = {
    "AssetSchema": (),
    "UID": ("val",),
    "Base": ("val",),
    "type": ("val",),
    **KTextAttrs,
    "Uuid": ("id", "val", "label", "definitionIteratorData", "public"),
    "Boolean": ("id", "val", "label", "definitionIteratorData", "public"),
    "Integer": ("id", "val", "label", "public", "readonly"),
    **KNumberAttrs,
    "Color": ("id", "label", "valA", "valB", "valG", "valR", "allowconnectedassets"),
    "Choice": ("id", "val", "label"),
    "ChoiceValue": ("id", "val", "label"),
    "Reference": ("id", "val", "label", "type", "allowconnectedassets"),
    "ui": ("id", "val", "public", "readonly"),
    "implementation": ("id", "val", "public", "readonly"),
    "Bounds": (
        "minimum",
        "maximum",
        "minimumisinclusive",
        "maximumisinclusive",
        "incrementsize",
        "percentage",
    ),
}
KSchemaChildren = {
    "AssetSchema": (
        "UID",
        "Base",
        "type",
        "String",
        "URL",
        "Uuid",
        "Boolean",
        "Integer",
        "Float",
        "Color",
        "Choice",
        "Reference",
        "ui",
        "implementation",
        "Distance",
        "TextureURI",
        "PropertyAlias",
    ),
    "Float": ("Bounds",),
    "Distance": ("Bounds",),
    "Integer": ("Bounds",),
    "Choice": ("ChoiceValue",),
}
