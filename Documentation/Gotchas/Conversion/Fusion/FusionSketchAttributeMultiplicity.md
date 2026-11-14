# One sketch identity can have multiple topology attributes

## Expectation

A particular serialized sketch-link string occurs once in a body history, so its bytes uniquely identify the attribute to edit.

## Actual behavior

The qualified cylinder history contains two separately owned sketch attributes with the same six-field string. Both refer to the same source sketch curve through distinct topology owners. The malformed-range integration fixture initially assumed a single occurrence and failed its setup assertion in remote run `43227394158` before reaching the reader.

## Workaround

Treat attributes as owned graph entities. Do not deduplicate them by equal sketch-link text or use global text uniqueness as an identity rule. The controlled malformed-range fixture checks the known multiplicity of two and corrupts exactly one occurrence; complete history reading must reject the malformed owned attribute.

The production writer already emits both owners explicitly in `BrepCodec/Attributes/HistoryAttributes.py`. The correction preserves that topology and updates the fixture rather than removing an attribute. The [ASCII attribute model](../../../Changes/Fusion/FusionSketchAttributeSemantics.md) records the field semantics.
