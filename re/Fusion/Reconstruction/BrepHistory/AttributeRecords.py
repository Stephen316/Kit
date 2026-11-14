from dataclasses import replace

from BrepCylinder import CountedText, Field, Record, Reference, field
from IdentityModel import DesignIdentity, FeatureTag, SketchLink


def attribute(owner, family, payload, next_attribute=-1, previous_attribute=-1):
    return Record("ATTRIB_CUSTOM-attrib", (
        field("reserved", Reference(-1), "Null attribute profile"),
        field("marker", -1, "Modern attribute marker"),
        field("next_attribute", Reference(next_attribute), "Next newly allocated attribute or null"),
        field("previous_attribute", Reference(previous_attribute), "Previous newly allocated attribute or null"),
        field("owner", Reference(owner), "Newly allocated topology record owning this attribute"),
        field("family", CountedText(family), "Declared attribute family vocabulary"),
        *payload,
    ))


def generic_prefix():
    return (
        field("schema_first", 3, "Observed generic-tag schema version"),
        field("schema_second", 3, "Observed generic-tag schema marker"),
        field("schema_reserved", -1, "Generic-tag null profile"),
        field("repeated_family", CountedText("generic_tag_attrib_def "), "Family vocabulary includes one trailing space"),
        field("group_count", 1, "Exactly one semantic identity group is emitted"),
    )


def generic_feature(owner, identity: FeatureTag):
    payload = (
        *generic_prefix(),
        field("selector", identity.selector, "Explicit source operation topology selector"),
        field("label", CountedText(identity.label), "Explicit source operation topology label; not a kernel pointer"),
        field("group_reserved", 0, "Generic face/edge group profile"),
        field("operation_count", len(identity.operation_ids), "Number of explicit operation identity integers"),
        *(field(f"operation_{index}", operation, "Explicit Design operation identity; not an ASM entity reference") for index, operation in enumerate(identity.operation_ids)),
        field("group_end", 0, "Generic-tag group terminal marker"),
    )
    return attribute(owner, "generic_tag_attrib_def", payload)


def body_attribute(identity: DesignIdentity):
    return attribute(1, "generic_tag_attrib_def", (
        *generic_prefix(),
        field("entity_class", 3, "Body persistent-link group selector"),
        field("operation_id", CountedText(str(identity.operation_id)), "Explicit Design operation identity encoded as decimal text"),
        field("generation_reference", identity.body_generation_reference, "Explicit preserved body-generation linkage; exact cross-namespace meaning remains under investigation"),
        field("group_reserved", 0, "Body group profile"),
        field("group_end", 0, "Body group terminal marker"),
    ), previous_attribute=26)


def sketch_attribute(owner, identity: SketchLink):
    text = f"{identity.primary_id} {identity.secondary_id} {identity.sense} 0 {identity.enum_a} {identity.enum_b}"
    return attribute(owner, "sketch_attrib_def", (
        field("schema_first", 1, "Sketch-link schema marker"),
        field("schema_second", 1, "Sketch-link schema marker"),
        field("payload_form", 3, "Counted six-member ASCII tuple form"),
        field("curve_identity", CountedText(text), "Explicit primary/secondary source sketch identity, sense, zero and enum pair"),
    ))


def attach_attributes(records, identity: DesignIdentity):
    heads = {1: 26, 4: 28, 5: 29, 6: 30, 15: 31, 16: 32, 12: 33, 14: 34}
    allocated = []
    for index, record in enumerate(records):
        fields = list(record.fields)
        if index in heads:
            fields[0] = field("attribute", Reference(heads[index]), "Newly allocated semantic attribute-chain head")
        if index == 1:
            fields[1] = field("body_key", identity.body_key, "Explicit key matched by the containing Design body-map selector")
        allocated.append(replace(record, fields=tuple(fields)))
    timestamp = attribute(1, "Timestamp_attrib_def", (
        field("schema_marker", 1, "Authoring timestamp payload schema"),
        field("unix_microseconds", identity.authoring_unix_microseconds, "Explicit authoring timestamp in microseconds; independent from save time"),
    ), next_attribute=27)
    allocated.extend((
        timestamp, body_attribute(identity), generic_feature(4, identity.side_face),
        generic_feature(5, identity.top_face), generic_feature(6, identity.bottom_face),
        generic_feature(15, identity.top_edge), generic_feature(16, identity.bottom_edge),
        sketch_attribute(12, identity.sketch), sketch_attribute(14, identity.sketch),
    ))
    return allocated
