from dataclasses import replace

from BrepCylinder import Reference, build_records, field
from AttributeRecords import generic_feature, sketch_attribute
from IdentityModel import FeatureTag, SketchLink
from PlanarRegion import region_records


def remap_record(record):
    fields = []
    for item in record.fields:
        value = item.value
        if isinstance(value, Reference) and value.index >= 2:
            value = Reference(value.index + 2)
            item = replace(item, value=value, derivation=item.derivation + "; two additional top-level body roots reserve records2 and3")
        fields.append(item)
    return replace(record, fields=tuple(fields))


def build_snapshot(cylinder, circle, feature_tags, sketch):
    source_model = build_records(cylinder)
    double_root, double_records = region_records(circle, 2, 28, True)
    single_root, single_records = region_records(circle, 3, 38, False)
    records = [source_model[0], remap_record(source_model[1]), double_root, single_root]
    records.extend(remap_record(record) for record in source_model[2:])
    records.extend(double_records)
    records.extend(single_records)
    heads = {6: 48, 7: 49, 8: 50, 17: 51, 18: 52, 14: 53, 16: 54, 32: 55, 33: 56, 42: 57, 43: 58}
    for index, attribute in heads.items():
        record = records[index]
        fields = list(record.fields)
        fields[0] = field("attribute", Reference(attribute), "Newly allocated explicit source-link attribute for this entity")
        records[index] = replace(record, fields=tuple(fields))
    if sketch.sense not in (0, 1):
        raise ValueError("Snapshot profile requires a directed source sketch link")
    coedge_link = sketch
    edge_link = replace(sketch, sense=1 - sketch.sense)
    records.extend((
        generic_feature(6, feature_tags["side_face"]),
        generic_feature(7, feature_tags["top_face"]),
        generic_feature(8, feature_tags["bottom_face"]),
        generic_feature(17, feature_tags["top_edge"]),
        generic_feature(18, feature_tags["bottom_edge"]),
        sketch_attribute(14, coedge_link), sketch_attribute(16, coedge_link),
        sketch_attribute(32, coedge_link), sketch_attribute(33, edge_link),
        sketch_attribute(42, coedge_link), sketch_attribute(43, edge_link),
    ))
    return records
