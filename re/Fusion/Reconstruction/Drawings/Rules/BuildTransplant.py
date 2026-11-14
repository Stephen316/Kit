"""Graft Kit's generated standard objects into the A3 control (route a) and record the variants.

The control keeps its header, its handles and its view objects. For every table entry, material, multiline
style and view standard that Kit generates, the control object with the same kind and name takes Kit's class
data. Handle links inside that data are mapped by name from Kit's file to the control. The paper and model
layouts take Kit's plot settings fields. Each variant goes to Variants/<label>.f3z with a row in
Variants/PlanTransplant.json, so BisectRound.py can upload and open it.

* T1Tables: L4Core with Kit's layers, line types, text styles, dimension style and active viewport.
* T2Standard: T1Tables plus Kit's materials, multiline style, view standard and layout plot settings.
* T3Sheet: T2Standard plus Kit's border and title block entities, their inserts and the title attributes. The
  control's block entities are removed; Kit's entities take handles freed by the L4Core pruning (below the
  header's handle seed, so the header stays untouched).

Run: python3.14 -I BuildTransplant.py --bundle $TMPDIR/KitFusionDrawings/Variants/P0Control.f3z
"""

import argparse
import json
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / 'Dwg'))
sys.path.insert(0, str(HERE.parent / 'Authoring'))

import BuildBisect  # noqa: E402
import BuildGrafts  # noqa: E402
import BuildPruned  # noqa: E402
import BuildPruned2  # noqa: E402
import BuildVariants  # noqa: E402
import KitSolids  # noqa: E402
from PruneDwg import Graph, field, prune, target, with_fields  # noqa: E402

from convert.formats.Fusion.DrawingCodec.Dwg.Author.AuthorDwg import AuthorDwg  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.DwgDraft import DwgDraft  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.SheetDraft import SheetDraft  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.TitleText import TitleText  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewDraft import ViewDraft  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewSource import ViewSource  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgField, DwgRecord  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile  # noqa: E402

PLAN = 'PlanTransplant.json'
SHEET_BLOCKS = ('ISO_A3_SHEET', 'ISO_TITLEBLOCK')
INSERT_FIELDS = ('Insertion', 'ScaleFlags', 'Rotation', 'Extrusion')
NAME_FIELDS = ('EntryName', 'MaterialName', 'LayoutName', 'StyleName')
TABLE_KINDS = ('LAYER', 'LTYPE', 'STYLE', 'DIMSTYLE', 'VPORT')
STANDARD_KINDS = ('MATERIAL', 'MLINESTYLE', 'ACDBVIEWREPSTANDARD')
PLOT_FIELDS = ('PageName', 'PrinterName', 'PlotFlags', 'LeftMargin', 'BottomMargin', 'RightMargin', 'TopMargin',
               'PaperWidth', 'PaperHeight', 'PaperSize', 'PlotOrigin', 'PaperUnits', 'PlotRotation', 'PlotType',
               'WindowMin', 'WindowMax', 'RealUnits', 'DrawingUnits', 'StyleSheet', 'ScaleType', 'ScaleFactor',
               'ImageOrigin', 'ShadeMode', 'ShadeQuality', 'ShadeDpi', 'LimitMin', 'LimitMax')


def kit_dwg(paper):
    source = ViewSource(0x1C5, '1_Component', '0f0e0d0c-0b0a-4908-8706-050403020100', (-1.0, 0.0, 0.5), (4.0, 2.0, 1.5), Solid=KitSolids.box_solid((-1.0, 0.0, 0.5), (4.0, 2.0, 1.5)))
    views = (ViewDraft((180.0, 120.0), 4.0),)
    sheet = SheetDraft('Kit Sheet', (TitleText('TITLE_1', 'Kit Drawing'),), paper)
    draft = DwgDraft(sheet, 0x2E50, datetime(2026, 11, 13, 12), '11111111-2222-4333-8444-555555555555',
                     '66666666-7777-4888-8999-aaaaaaaaaaaa', views, source, ())
    with KitSolids.no_edges():
        return ReadDwgFile(AuthorDwg(draft))


def keys_of(dwg):
    graph = Graph(dwg)
    keys = {}
    for handle, kind in graph.names.items():
        if handle <= 0xF:
            keys[handle] = ('fixed', handle)
            continue
        data = graph.objects[handle].ClassData
        name = next((field(data, name) for name in NAME_FIELDS if field(data, name) is not None), None)
        if kind == 'ACDBVIEWREPSTANDARD':
            name = 'standard'
        if name is not None:
            keys[handle] = (kind, str(name).upper() if kind == 'MLINESTYLE' else name)
    return keys


def encoded(code, own, hit):
    if code in (2, 3, 4, 5):
        return DwgHandleRef(code, hit)
    if hit == own + 1:
        return DwgHandleRef(6, 0)
    if hit == own - 1:
        return DwgHandleRef(8, 0)
    return DwgHandleRef(0xA, hit - own) if hit > own else DwgHandleRef(0xC, own - hit)


def mapped(value, own, home, kit_keys, control_handles, misses):
    if isinstance(value, DwgHandleRef):
        if value.RefValue == 0 and value.RefCode in (2, 3, 4, 5):
            return value
        key = kit_keys.get(target(own, value))
        hit = control_handles.get(key)
        if hit is None:
            misses.append(str(key))
            return DwgHandleRef(value.RefCode if value.RefCode in (2, 3, 4, 5) else 5, 0)
        return encoded(value.RefCode, home, hit)
    if isinstance(value, DwgRecord):
        return DwgRecord(tuple(DwgField(item.FieldName, mapped(item.FieldValue, own, home, kit_keys, control_handles, misses)) for item in value.RecordFields))
    if isinstance(value, tuple):
        return tuple(mapped(item, own, home, kit_keys, control_handles, misses) for item in value)
    return value


def transplant(control, kit, kinds, plot):
    kit_keys = keys_of(kit)
    control_keys = keys_of(control)
    control_handles = {key: handle for handle, key in control_keys.items()}
    kit_objects = {kit_keys[obj.ObjectHandle]: obj for obj in kit.DwgObjects if obj.ObjectHandle in kit_keys}
    rows, changed, misses = [], [], []
    for obj in control.DwgObjects:
        key = control_keys.get(obj.ObjectHandle)
        source = kit_objects.get(key)
        if source is not None and key[0] in kinds:
            data = mapped(source.ClassData, source.ObjectHandle, obj.ObjectHandle, kit_keys, control_handles, misses)
            obj = replace(obj, ClassData=data)
            changed.append(list(map(str, key)))
        elif plot and obj.ClassKind == 'LAYOUT':
            name = 'Model' if field(obj.ClassData, 'LayoutName') == 'Model' else None
            pick = kit_objects.get(('LAYOUT', 'Model')) if name else next(
                (o for k, o in kit_objects.items() if k[0] == 'LAYOUT' and k[1] != 'Model'), None)
            if pick is not None:
                values = {name: field(pick.ClassData, name) for name in PLOT_FIELDS}
                obj = replace(obj, ClassData=with_fields(obj.ClassData, **values))
                changed.append(['LAYOUT', field(obj.ClassData, 'LayoutName'), 'plot fields'])
        rows.append(obj)
    return replace(control, DwgObjects=tuple(rows)), changed, sorted(set(misses))


def block_handles(graph, name):
    return next(handle for handle, kind in graph.names.items() if kind == 'BLOCK_HEADER' and field(graph.objects[handle].ClassData, 'EntryName') == name)


def owned_by(graph, handle, name='Owned'):
    return [target(handle, ref) for ref in field(graph.objects[handle].ClassData, name) or ()]


def insert_of(graph, block):
    return next(handle for handle, kind in graph.names.items() if kind == 'INSERT' and target(handle, field(graph.objects[handle].ClassData, 'BlockHeader')) == block)


def free_pool(dwg):
    seed = field(dwg.HeaderVars, 'HandSeed').RefValue
    used = {obj.ObjectHandle for obj in dwg.DwgObjects}
    return [handle for handle in range(0x10, seed) if handle not in used]


def moved(obj, home, kit_keys, control_handles, misses):
    own = obj.ObjectHandle
    common = mapped(obj.CommonData, own, home, kit_keys, control_handles, misses)
    data = mapped(obj.ClassData, own, home, kit_keys, control_handles, misses)
    tail = mapped(obj.HandleRefs, own, home, kit_keys, control_handles, misses)
    return replace(obj, ObjectHandle=home, CommonData=common, ClassData=data, HandleRefs=tail)


def sheet_blocks(control, kit, names):
    kit_graph, kit_keys = Graph(kit), dict(keys_of(kit))
    graph = Graph(control)
    dead = set()
    pairs = [name if isinstance(name, tuple) else (name, name) for name in names]
    for name, _ in pairs:
        dead |= set(owned_by(graph, block_handles(graph, name)))
    control, removed, _ = prune(control, dead)
    graph = Graph(control)
    control_handles = {key: handle for handle, key in keys_of(control).items()}
    pool, adds, misses, notes = free_pool(control), [], [], {}
    for name, kit_name in pairs:
        entities = owned_by(kit_graph, block_handles(kit_graph, kit_name))
        for entity in entities:
            kit_keys[entity] = ('kit', entity)
            control_handles[('kit', entity)] = pool.pop(0)
        notes[name] = {'removed': len(dead), 'added': len(entities)}
    rows = {obj.ObjectHandle: obj for obj in control.DwgObjects}
    for name, kit_name in pairs:
        home, source = block_handles(graph, name), block_handles(kit_graph, kit_name)
        for entity in owned_by(kit_graph, source):
            adds.append(moved(kit_graph.objects[entity], control_handles[('kit', entity)], kit_keys, control_handles, misses))
        owned = mapped(field(kit_graph.objects[source].ClassData, 'Owned'), source, home, kit_keys, control_handles, misses)
        rows[home] = replace(rows[home], ClassData=with_fields(rows[home].ClassData, Owned=owned, OwnedCount=len(owned)))
        here, there = insert_of(graph, home), insert_of(kit_graph, source)
        values = {key: field(kit_graph.objects[there].ClassData, key) for key in INSERT_FIELDS}
        rows[here] = replace(rows[here], ClassData=with_fields(rows[here].ClassData, **values))
        tags = {field(kit_graph.objects[h].ClassData, 'Tag'): h for h in owned_by(kit_graph, there, 'Attribs')}
        for attrib in owned_by(graph, here, 'Attribs'):
            twin = tags.get(field(rows[attrib].ClassData, 'Tag'))
            if twin is not None:
                data = mapped(kit_graph.objects[twin].ClassData, twin, attrib, kit_keys, control_handles, misses)
                rows[attrib] = replace(rows[attrib], ClassData=data)
                notes[name]['attribs'] = notes[name].get('attribs', 0) + 1
    objects = tuple(sorted((*rows.values(), *adds), key=lambda obj: obj.ObjectHandle))
    return replace(control, DwgObjects=objects), {'blocks': notes, 'removed': dict(removed), 'unmapped_links': sorted(set(misses))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--paper', default='A3 Landscape')
    args = parser.parse_args()
    out = BuildVariants.OUT
    drawing, source = BuildGrafts.bundle_parts(args.bundle)
    q1, _ = BuildBisect.bases(drawing)
    lean_dwg, lean_counts = BuildGrafts.lean(q1)
    both_dwg, _ = BuildGrafts.ruled(lean_dwg, args.paper)
    core_dwg, core_counts = BuildGrafts.core(both_dwg)
    kit = kit_dwg(args.paper)
    plan = {'paper': args.paper, 'variants': [], 'transplants': {}}
    for label, kinds, plot, blocks in (('T1Tables', TABLE_KINDS, False, ()), ('T2Standard', TABLE_KINDS + STANDARD_KINDS, True, ()),
                                       ('T3Sheet', TABLE_KINDS + STANDARD_KINDS, True, SHEET_BLOCKS)):
        dwg, changed, misses = transplant(core_dwg, kit, kinds, plot)
        plan['transplants'][label] = {'changed': changed, 'unmapped_links': misses}
        if blocks:
            dwg, notes = sheet_blocks(dwg, kit, blocks)
            plan['transplants'][label]['sheet_blocks'] = notes
        data = BuildPruned.emit_fresh(dwg)
        bundle = BuildVariants.opaque_bundle(BuildVariants.without_database(drawing, data), source, label)
        plan['variants'].append(BuildPruned2.record(out, label, bundle, data, dwg, {}))
    (out / PLAN).write_text(json.dumps(plan, indent=1, default=str) + '\n')
    print(json.dumps({label: {'changed': len(row['changed']), 'unmapped': row['unmapped_links']} for label, row in plan['transplants'].items()}))


if __name__ == '__main__':
    main()
