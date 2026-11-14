"""Build second-round DWG removal variants for native requirement experiments.

The base is the A1 control without unused blocks, which Fusion opened with every view and the dimension.
Each variant removes one more group of objects, so a native open shows whether Fusion needs that group.
E7StaleBrep changes only the drawing segment, to learn whether a stale tracked body makes Fusion recompute views on open.
"""

import argparse
import hashlib
import json
import sys
from dataclasses import fields, is_dataclass, replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / 'Dwg'))

import BuildPruned  # noqa: E402
import BuildVariants  # noqa: E402
from PruneDwg import Graph, field, prune, refs_in, target  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgRecord  # noqa: E402

from convert.formats.Fusion.DrawingCodec.EmitDrawing import EmitDrawing  # noqa: E402
from convert.formats.Fusion.DrawingCodec.ReadDrawing import ReadDrawing  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile  # noqa: E402

PURGE_KINDS = ('LAYER', 'LTYPE', 'STYLE', 'APPID', 'DIMSTYLE', 'VISUALSTYLE', 'MATERIAL', 'MLEADERSTYLE', 'TABLESTYLE', 'SCALE', 'MLINESTYLE', 'ACDBSECTIONVIEWSTYLE', 'ACDBDETAILVIEWSTYLE')
PURGE_KEEP = ('0', 'Continuous', 'ByLayer', 'ByBlock', 'BYLAYER', 'BYBLOCK', 'Standard', 'Global', 'ACAD')
NOD_HISTORY = ('ACAD_CIP_PREVIOUS_PRODUCT_INFO', 'ACAD_LAST_SAVED_VERSION_INFO', 'ACDB_RECOMPOSE_DATA', 'AMGSNAPSETTINGS', 'AMG', 'AcmDictionary')
NOD_FUSION = ('ACAD_FUSDOC_NOD', 'ACAD_FUSDOC_NOD_VER', 'FUSDOC_NOD_AUTO_CREATED_DRAWING', 'DB_FUSDOC_NOD_', 'AcFusionFieldIds', 'AcFusionFieldsGlobalData', 'AcFusionPimIds')
TRACKED_BREP = 'E4761EB7-1694-472F-BAC0-24B430387180'


def entry_names(graph):
    names = {}
    for handle, kind in graph.names.items():
        obj = graph.objects[handle]
        if kind in ('DICTIONARY', 'ACDBDICTIONARYWDFLT'):
            for entry, ref in zip(field(obj.ClassData, 'Entries', ()), field(obj.ClassData, 'Items', ())):
                names[target(handle, ref)] = field(entry, 'EntryName', '')
        elif field(obj.ClassData, 'EntryName') is not None:
            names[handle] = field(obj.ClassData, 'EntryName')
    return names


def protected(dwg, graph):
    keep = {ref.RefValue for ref in refs_in(dwg.HeaderVars)}
    for obj in dwg.DwgObjects:
        keep.update(eed.AppRef.RefValue for eed in obj.EedBlocks)
    values = {field(graph.objects[h].ClassData, 'VarValue', '') for h, kind in graph.names.items() if kind == 'DICTIONARYVAR'}
    return keep, values


def purgeable(dwg):
    graph = Graph(dwg)
    names = entry_names(graph)
    keep, values = protected(dwg, graph)
    rows = set()
    for handle, kind in graph.names.items():
        name = names.get(handle, '')
        if kind not in PURGE_KINDS or handle in keep or name in PURGE_KEEP or name in values or name.startswith('*'):
            continue
        obj = graph.objects[handle]
        owner = target(handle, field(obj.CommonData, 'Owner'))
        inside = graph.closure({handle})
        callers = {other for other in graph.incoming.get(handle, ()) if other not in inside and other != owner}
        if not callers:
            rows.add(handle)
    return rows


def purge_all(dwg):
    total = {}
    while True:
        rows = purgeable(dwg)
        if not rows:
            return dwg, total
        dwg, removed, _ = prune(dwg, rows)
        for name, count in removed.items():
            total[name] = total.get(name, 0) + count


def nod_items(graph, wanted):
    nod = min(h for h, kind in graph.names.items() if kind == 'DICTIONARY' and target(h, field(graph.objects[h].CommonData, 'Owner')) == 0)
    obj = graph.objects[nod]
    rows = set()
    for entry, ref in zip(field(obj.ClassData, 'Entries', ()), field(obj.ClassData, 'Items', ())):
        name = field(entry, 'EntryName', '')
        if any(name == item or (item.endswith('_') and name.startswith(item)) for item in wanted):
            rows.add(target(nod, ref))
    return rows


def kind_items(graph, kinds):
    return {handle for handle, kind in graph.names.items() if kind in kinds}


def staled(value):
    if is_dataclass(value) and not isinstance(value, type):
        if type(value).__name__ == 'EntityGroup' and value.ClassGuid == TRACKED_BREP:
            items = tuple(replace(item, Value=0) if item.FieldName == 'version' else item for item in value.Fields)
            return replace(value, Fields=items)
        changes = {item.name: staled(getattr(value, item.name)) for item in fields(value)}
        return replace(value, **changes)
    if isinstance(value, tuple):
        return tuple(staled(item) for item in value)
    return value


def revised(dwg):
    """Change the body revision GUID that the Fusion view source stores, as if the body had changed."""
    graph = Graph(dwg)
    changed = 0
    objects = []
    for obj in dwg.DwgObjects:
        items = field(obj.ClassData, 'Items') if graph.names[obj.ObjectHandle] == 'XRECORD' else None
        if items is not None and any(item.FieldValue == 'ACAD_ROUNDTRIP_2014_VIEWREP_FUSIONSRC' for item in items.RecordFields):
            values = tuple(replace(item, FieldValue=item.FieldValue ^ 0x5A5A) if item.FieldName == '90' and item.FieldValue > 1 << 20 else item for item in items.RecordFields)
            changed += sum(1 for old, new in zip(items.RecordFields, values) if old != new)
            data = DwgRecord(tuple(replace(item, FieldValue=DwgRecord(values)) if item.FieldName == 'Items' else item for item in obj.ClassData.RecordFields))
            obj = replace(obj, ClassData=data)
        objects.append(obj)
    if changed != 1:
        raise ValueError(f'expected one revision GUID, changed {changed}')
    return replace(dwg, DwgObjects=tuple(objects))


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
    rows = []
    purged, purge_counts = purge_all(base)
    rows.append(('E1Purged', purged, purge_counts))
    for label, kill in (('E2NoNodHistory', nod_items(graph, NOD_HISTORY)), ('E3NoFusionNod', nod_items(graph, NOD_FUSION)), ('E4NoVariables', kind_items(graph, {'DICTIONARYVAR'})), ('E5NoFields', kind_items(graph, {'FIELD', 'FIELDLIST'}))):
        pruned, removed, _ = prune(base, kill)
        rows.append((label, pruned, dict(removed)))
    lean, lean_counts = purge_all(base)
    lean_graph = Graph(lean)
    kill = nod_items(lean_graph, NOD_HISTORY + NOD_FUSION) | kind_items(lean_graph, {'DICTIONARYVAR', 'FIELD', 'FIELDLIST'})
    lean, removed, _ = prune(lean, kill)
    for name, count in removed.items():
        lean_counts[name] = lean_counts.get(name, 0) + count
    lean = BuildPruned.without_sections(lean, BuildPruned.OPTIONAL_SECTIONS)
    rows.append(('E6Lean', lean, lean_counts))
    leaner, removed, _ = prune(lean, BuildPruned.acm_objects(Graph(lean)))
    leaner_counts = dict(lean_counts)
    for name, count in removed.items():
        leaner_counts[name] = leaner_counts.get(name, 0) + count
    rows.append(('E9LeanNoAcm', leaner, leaner_counts))
    curves = BuildPruned.curves_in(Graph(base), '*S', {'LINE', 'CIRCLE', 'ARC'})
    bare, bare_removed, _ = prune(base, curves)
    rows.append(('E8StaleRevision', revised(bare), dict(bare_removed)))
    plan = {'base_objects': len(base.DwgObjects), 'variants': []}
    for label, dwg, removed in rows:
        data = BuildPruned.emit_fresh(dwg)
        bundle = BuildVariants.opaque_bundle(BuildVariants.without_database(drawing, data), source, label)
        plan['variants'].append(record(out, label, bundle, data, dwg, removed))
    removed = bare_removed
    typed = ReadDrawing(BuildVariants.without_database(drawing, BuildPruned.emit_fresh(bare)), BuildVariants.inflate)
    stale = replace(typed, Segments=staled(typed.Segments))
    stale_bytes = EmitDrawing(stale, BuildVariants.compress)
    bundle = BuildVariants.opaque_bundle(stale_bytes, source, 'E7StaleBrep')
    plan['variants'].append(record(out, 'E7StaleBrep', bundle, BuildVariants.database(stale_bytes), bare, dict(removed)))
    (out / 'Plan2.json').write_text(json.dumps(plan, indent=1) + '\n')
    print(json.dumps(plan, indent=1))


def record(out, label, bundle, data, dwg, removed):
    path = out / (label + '.f3z')
    path.write_bytes(bundle)
    return {
        'label': label, 'file': path.name, 'bytes': len(bundle), 'sha256': hashlib.sha256(bundle).hexdigest(),
        'dwg_bytes': len(data), 'dwg_sha256': hashlib.sha256(data).hexdigest(), 'objects': len(dwg.DwgObjects),
        'removed': dict(sorted(removed.items())),
    }


if __name__ == '__main__':
    main()
