"""Rebuild the plain-dimension and no-network probes without dangling handles.

F3PlainDimension and F8NoNetwork removed the rotated-dimension action body but kept the
ACDB_RECOMPOSE_DATA xrecord in the named object dictionary, whose group 330 still names that body.
Fusion's drawing engine crashed on G1FreshHandles, which also carried numbers of absent objects, so
those two uploads are quarantined. These variants also remove that xrecord and its dictionary entry.
Every variant is checked to have no dangling handle before it is planned.
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / 'Dwg'))

import BuildPruned  # noqa: E402
import BuildPruned2  # noqa: E402
import BuildPruned3  # noqa: E402
import BuildVariants  # noqa: E402
from PruneDwg import Graph, field, prune  # noqa: E402

from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile  # noqa: E402

HANDLE_GROUPS = set(range(320, 370)) | set(range(390, 400)) | {480, 481, 1005}


def numeric_handles(record):
    for item in record.RecordFields:
        value = item.FieldValue
        if item.FieldName.isdigit() and int(item.FieldName) in HANDLE_GROUPS and isinstance(value, int):
            yield value
        elif hasattr(value, 'RecordFields'):
            yield from numeric_handles(value)


def recompose_records(graph, dead):
    rows = set()
    for handle, kind in graph.names.items():
        if kind == 'XRECORD':
            items = field(graph.objects[handle].ClassData, 'Items')
            if items is not None and any(value in dead for value in numeric_handles(items)):
                rows.add(handle)
    return rows


def dangling(dwg):
    present = {obj.ObjectHandle for obj in dwg.DwgObjects}
    rows = []
    for obj in dwg.DwgObjects:
        for value in numeric_handles(obj.ClassData):
            if value and value not in present:
                rows.append((hex(obj.ObjectHandle), hex(value)))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--with-dimension', required=True)
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    out = BuildVariants.OUT
    drawing = Path(args.with_dimension).read_bytes()
    source = Path(args.source).read_bytes()
    base = ReadDwgFile(BuildVariants.database(drawing))
    base, _, _ = prune(base, BuildPruned.unused_blocks(Graph(base)))
    graph = Graph(base)
    reps = BuildPruned3.kinds(graph, BuildPruned3.VIEW_REPS)
    dimension = BuildPruned3.actions_with(graph, 'ACDBASSOCROTATEDDIMACTIONBODY')
    kills = {
        'F3bPlainDimension': dimension,
        'F8bNoNetwork': reps | BuildPruned3.kinds(graph, {'ACDBASSOCACTION', 'ACDBASSOCNETWORK'}),
    }
    plan = {'base_objects': len(base.DwgObjects), 'variants': []}
    for label, kill in kills.items():
        dead = graph.closure(kill)
        pruned, removed, _ = prune(base, kill | recompose_records(graph, dead))
        pruned = BuildPruned3.repair_networks(pruned)
        left = dangling(pruned)
        if left:
            raise ValueError(f'{label} still names absent objects: {left[:5]}')
        data = BuildPruned.emit_fresh(pruned)
        bundle = BuildVariants.opaque_bundle(BuildVariants.without_database(drawing, data), source, label)
        plan['variants'].append(BuildPruned2.record(out, label, bundle, data, pruned, dict(removed)))
    (out / 'Plan4.json').write_text(json.dumps(plan, indent=1) + '\n')
    print(json.dumps(plan, indent=1))


if __name__ == '__main__':
    main()
