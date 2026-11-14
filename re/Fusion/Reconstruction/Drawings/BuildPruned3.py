"""Build third-round DWG removal variants that probe which view, dimension and sheet objects Fusion needs.

The base is the A1 control without unused blocks. Each variant removes one family of objects:
view representations, the associative view actions, the associative dimension action, the title block,
the sheet border, the centre mark, or the whole associative network. F7ZeroHeaderTail keeps every object
and writes the header section without the trailing bits that follow its handle stream.
"""

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / 'Dwg'))

import BuildPruned  # noqa: E402
import BuildPruned2  # noqa: E402
import BuildVariants  # noqa: E402
from PruneDwg import Graph, field, prune, target, with_fields  # noqa: E402

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgField, DwgRecord  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile  # noqa: E402

VIEW_REPS = {'ACDBVIEWREP', 'ACDBASSOCEXTERNALPERSSUBENTIDHOLDER', 'ACDBASSOCPROJECTEDENTITYPERSSUBENTIDHOLDER'}


def actions_with(graph, body_kind):
    rows = set()
    for handle, kind in graph.names.items():
        if kind == 'ACDBASSOCACTION':
            body = field(graph.objects[handle].ClassData, 'ActionBody')
            if body is not None and body.RefValue and graph.names.get(target(handle, body)) == body_kind:
                rows.add(handle)
    return rows


def kinds(graph, wanted):
    return {handle for handle, kind in graph.names.items() if kind in wanted}


def insert_of(graph, block_name):
    rows = set()
    for handle, kind in graph.names.items():
        if kind == 'BLOCK_HEADER' and field(graph.objects[handle].ClassData, 'EntryName') == block_name:
            rows.add(handle)
            for other, other_kind in graph.names.items():
                if other_kind == 'INSERT' and target(other, field(graph.objects[other].ClassData, 'BlockHeader')) == handle:
                    rows.add(other)
    return rows


def center_mark(graph):
    rows = actions_with(graph, 'AcDbCenterMarkActionBody')
    for handle, kind in graph.names.items():
        if kind == 'BLOCK_HEADER' and field(graph.objects[handle].ClassData, 'EntryName') == '*U':
            rows |= insert_of_handle(graph, handle) | {handle}
    return rows


def insert_of_handle(graph, block):
    return {other for other, kind in graph.names.items() if kind == 'INSERT' and target(other, field(graph.objects[other].ClassData, 'BlockHeader')) == block}


def repair_networks(dwg):
    graph = Graph(dwg)
    objects = []
    for obj in dwg.DwgObjects:
        if graph.names[obj.ObjectHandle] == 'ACDBASSOCNETWORK':
            entries = field(obj.ClassData, 'Actions', ())
            alive = tuple(entry for entry in entries if field(entry, 'Action').RefValue)
            if len(alive) != len(entries):
                obj = replace(obj, ClassData=with_fields(obj.ClassData, Actions=alive, ActionCount=len(alive)))
        objects.append(obj)
    return replace(dwg, DwgObjects=tuple(objects))


def zero_tail(dwg):
    values = []
    for name, record in dwg.SectionVars:
        if name == 'AcDb:Header':
            record = DwgRecord(tuple(DwgField(item.FieldName, 0 if item.FieldName in ('TailWidth', 'TailBits') else item.FieldValue) for item in record.RecordFields))
        values.append((name, record))
    return replace(dwg, SectionVars=tuple(values))


def kit_app_info(dwg):
    """Replace the Autodesk product and trusted-file entries with a Kit product entry, as an authored file would carry."""
    product = dwg.AppInfo.AppEntries[0]
    text = '<ProductInformation name ="Kit" build_version="1" registry_version="26.0" install_id_string="Kit" registry_localeID="1033"/>'
    info = replace(dwg.AppInfo, AppEntries=(replace(product, TextValue=text),))
    summary = replace(dwg.Summary, LastSavedBy='')
    trimmed = BuildPruned.without_sections(dwg, ('AcDb:AppInfoHistory',))
    return replace(trimmed, AppInfo=info, Summary=summary)


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
    reps = kinds(graph, VIEW_REPS)
    view_actions = actions_with(graph, 'ACDBASSOCVIEWREPACTIONBODY')
    kills = {
        'F1NoViewReps': reps,
        'F2NoViewActions': reps | view_actions,
        'F3PlainDimension': actions_with(graph, 'ACDBASSOCROTATEDDIMACTIONBODY'),
        'F4NoTitleBlock': insert_of(graph, 'ISO_TITLEBLOCK'),
        'F5NoBorder': insert_of(graph, 'ISO_A3_SHEET'),
        'F6NoCenterMark': center_mark(graph),
        'F8NoNetwork': reps | kinds(graph, {'ACDBASSOCACTION', 'ACDBASSOCNETWORK'}),
    }
    plan = {'base_objects': len(base.DwgObjects), 'variants': []}
    rows = []
    for label, kill in kills.items():
        pruned, removed, nulled = prune(base, kill)
        rows.append((label, repair_networks(pruned), dict(removed)))
    rows.append(('F7ZeroHeaderTail', zero_tail(base), {}))
    rows.append(('F9KitAppInfo', kit_app_info(base), {}))
    for label, dwg, removed in rows:
        data = BuildPruned.emit_fresh(dwg)
        bundle = BuildVariants.opaque_bundle(BuildVariants.without_database(drawing, data), source, label)
        plan['variants'].append(BuildPruned2.record(out, label, bundle, data, dwg, removed))
    (out / 'Plan3.json').write_text(json.dumps(plan, indent=1) + '\n')
    print(json.dumps(plan, indent=1))


if __name__ == '__main__':
    main()
