"""Turn the A3 control's projected views into left, below and back views by Kit's child view rule (route a).

The control's base view looks along the model Z axis and has a child to its right and a child above it. Kit
authors the same base and children (build A) and then another layout (build B). The leaves that differ between A
and B are exactly what the layout decides: view centres, borders, eye points, up vectors, twist angles, view
angles, the parent link of a back view and the child offsets kept in extended data. Each variant copies those
leaves from B into the control's matching objects, with Kit handles mapped to the control's, and keeps every other
leaf the control's own. Where A and B differ, the control's leaf must equal A's, which checks Kit's child rule
against Fusion's right and above children.

* V1LeftBelow: the right child becomes a left child and the above child a below child.
* V2RightBack: the base moves left, and the above child becomes a back view projected right of the right child.
* V3AboveBelow: the right child becomes a below child, so the base has an above and a below child.
* V4KitModel, V5AboveBelowKitModel, V6RightBackKitModel: the base, V3AboveBelow and V2RightBack with Kit's model
  space places for the views (block reference insertions and model viewport targets).
* V7NoEdges, V8AboveBelowNoEdges: the base and V3AboveBelow with every view's stored edge list emptied, as Kit
  writes views. V9AboveBelowNoCurves also removes the drawn curves those edges named.

* V10ActionChanged, V11DependencyChanged, V12ApiFlag, V13AllChanged: V7NoEdges with the view actions, their
  dependencies, or both and the network marked as changed (status 1), or with view flag 0x2000.

BisectRound.py --poke halves and restores the base view scale after open and reads the curves again.

The base is D0Plain from BuildDims.py, so no dimension is tied to view geometry. Each variant goes to
Variants/<label>.f3z with a row in Variants/PlanChildren.json for BisectRound.py.
Run: python3.14 -I BuildChildren.py --bundle $TMPDIR/KitFusionDrawings/Variants/P0Control.f3z
"""
import argparse
import dataclasses
import json
import struct
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
import BuildDims  # noqa: E402
import BuildGrafts  # noqa: E402
import BuildPruned  # noqa: E402
import BuildPruned2  # noqa: E402
import BuildTransplant as T  # noqa: E402
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

PLAN = 'PlanChildren.json'
BASE = (180.46875, 120.609375)
RIGHT = (298.0, 120.609375)
ABOVE = (180.46875, 197.203125)
LAYOUTS = {
    'A': (BASE, (RIGHT, 0), (ABOVE, 0)),
    'V1LeftBelow': (BASE, ((2 * BASE[0] - RIGHT[0], BASE[1]), 0), ((BASE[0], 2 * BASE[1] - ABOVE[1]), 0)),
    'V2RightBack': ((103.75, BASE[1]), ((214.25, BASE[1]), 0), ((324.75, BASE[1]), 1)),
    'V3AboveBelow': (BASE, ((BASE[0], 2 * BASE[1] - ABOVE[1]), 0), (ABOVE, 0)),
}
MODEL_LAYOUTS = {'V4KitModel': 'A', 'V5AboveBelowKitModel': 'V3AboveBelow', 'V6RightBackKitModel': 'V2RightBack'}
EDGELESS = {'V7NoEdges': ('A', False), 'V8AboveBelowNoEdges': ('V3AboveBelow', False),
            'V9AboveBelowNoCurves': ('V3AboveBelow', True)}
STALE = {'V10ActionChanged': ('actions',), 'V11DependencyChanged': ('dependencies',), 'V12ApiFlag': ('flag',),
         'V13AllChanged': ('actions', 'network', 'dependencies')}
KCHANGED = 1
KAPI_FLAG = 0x2000
MODEL_FIELDS = {'ACDBVIEWREPBLOCKREFERENCE': ('Insertion',), 'VIEWPORT': ('ViewTarget', 'UcsOrigin')}
EXPAND = {'ACDBVIEWREP', 'ACDBVIEWREPORIENTATION', 'ACDBVIEWREPORIENTATIONDEF', 'ACDBVIEWREPSOURCEMGR',
          'ACDBVIEWREPFUSIONSOURCE', 'ACDBASSOCACTION', 'ACDBASSOCDEPENDENCY', 'ACDBASSOCVIEWREPACTIONBODY',
          'ACDBASSOCVIEWREPACTIONPARAM', 'ACDBASSOCVIEWREPHATCHMANAGER', 'VIEWPORT', 'DRAWINGVIEW',
          'ACDBVIEWREPBLOCKREFERENCE'}
SEEDS = ('ACDBVIEWREP', 'VIEWPORT', 'DRAWINGVIEW', 'ACDBVIEWREPORIENTATION', 'ACDBASSOCVIEWREPACTIONBODY',
         'ACDBVIEWREPBLOCKREFERENCE', 'XRECORD')
STATE = (4 + 18, 4 + 90)
PARTS = ('EedBlocks', 'CommonData', 'ClassData', 'HandleRefs')


def kit(layout, paper, solid=None, hidden=False):
    """Kit's build of a layout. Without a solid the views carry no edges, as the leaf grafts need; with one they
    carry the edges Kit computes from it, in visible or hidden style."""
    shape = solid if solid is not None else KitSolids.box_solid((0.0, 0.0, 0.0), (4.0, 2.0, 1.0))
    source = ViewSource(0x1C5, '1_Component', '0f0e0d0c-0b0a-4908-8706-050403020100', (0.0, 0.0, 0.0), (4.0, 2.0, 1.0), Solid=shape)
    base, first, second = LAYOUTS[layout]
    views = (ViewDraft(base, 4.0, ShowHidden=hidden), ViewDraft(first[0], 4.0, Parent=first[1], ShowHidden=hidden),
             ViewDraft(second[0], 4.0, Parent=second[1], ShowHidden=hidden))
    sheet = SheetDraft('Kit Sheet', (TitleText('TITLE_1', 'Kit Drawing'),), paper)
    draft = DwgDraft(sheet, 0x2E50, datetime(2026, 11, 13, 12), '11111111-2222-4333-8444-555555555555',
                     '66666666-7777-4888-8999-aaaaaaaaaaaa', views, source, ())
    if solid is not None:
        return ReadDwgFile(AuthorDwg(draft))
    with KitSolids.no_edges():
        return ReadDwgFile(AuthorDwg(draft))


def refs(value, own, path=''):
    if isinstance(value, DwgHandleRef):
        if not (value.RefValue == 0 and value.RefCode in (2, 3, 4, 5)):
            yield path, target(own, value)
    elif isinstance(value, DwgRecord):
        for index, item in enumerate(value.RecordFields):
            yield from refs(item.FieldValue, own, f'{path}/{index}:{item.FieldName}')
    elif isinstance(value, tuple):
        for index, item in enumerate(value):
            yield from refs(item, own, f'{path}[{index}]')
    elif dataclasses.is_dataclass(value):
        for name in (f.name for f in dataclasses.fields(value)):
            yield from refs(getattr(value, name), own, f'{path}.{name}')


def all_refs(obj):
    return dict(item for part in PARTS for item in refs(getattr(obj, part), obj.ObjectHandle, part))


def seeded(graph, kind):
    rows = sorted(h for h, n in graph.names.items() if n == kind)
    if kind == 'XRECORD':
        rows = [h for h in rows if 'ACDBIMPVIEWREP' in repr(graph.objects[h].ClassData)[:400]]
    return rows


def pairs(kit_graph, graph):
    pair, conflicts = {}, []
    for kind in SEEDS:
        mine, theirs = seeded(kit_graph, kind), seeded(graph, kind)
        if len(mine) != len(theirs):
            raise RuntimeError(f'{kind}: Kit has {len(mine)}, the control {len(theirs)}')
        pair.update(zip(mine, theirs))
    queue = list(pair)
    while queue:
        kit_handle = queue.pop()
        if kit_graph.names[kit_handle] not in EXPAND:
            continue
        mine, theirs = all_refs(kit_graph.objects[kit_handle]), all_refs(graph.objects[pair[kit_handle]])
        for path, kit_hit in mine.items():
            hit = theirs.get(path)
            if hit is None or kit_hit not in kit_graph.names or hit not in graph.names:
                continue
            if kit_graph.names[kit_hit] != graph.names[hit]:
                continue
            if kit_hit in pair:
                if pair[kit_hit] != hit:
                    conflicts.append((kit_graph.names[kit_handle], path, hex(kit_hit), hex(pair[kit_hit]), hex(hit)))
                continue
            pair[kit_hit] = hit
            queue.append(kit_hit)
    return pair, conflicts


class Patch:
    def __init__(self, pair):
        self.pair, self.misses, self.checks, self.leaves = pair, [], [], 0

    def moved(self, value, own, home):
        if isinstance(value, DwgHandleRef):
            if value.RefValue == 0 and value.RefCode in (2, 3, 4, 5):
                return value
            hit = self.pair.get(target(own, value))
            if hit is None:
                self.misses.append(hex(target(own, value)))
                return value
            return T.encoded(value.RefCode, home, hit)
        if isinstance(value, DwgRecord):
            return DwgRecord(tuple(DwgField(f.FieldName, self.moved(f.FieldValue, own, home)) for f in value.RecordFields))
        if isinstance(value, tuple):
            return tuple(self.moved(item, own, home) for item in value)
        if dataclasses.is_dataclass(value):
            return replace(value, **{f.name: self.moved(getattr(value, f.name), own, home) for f in dataclasses.fields(value)})
        return value

    def apply(self, mine, first, second, own, home, path):
        if repr(first) == repr(second):
            return mine
        if isinstance(first, DwgHandleRef):
            expected = self.moved(first, own, home)
            if not isinstance(mine, DwgHandleRef) or target(home, mine) != target(home, expected):
                self.checks.append({'leaf': path, 'control': brief(mine), 'kit_a': brief(expected)})
            self.leaves += 1
            return self.moved(second, own, home)
        same_record = isinstance(first, DwgRecord) and isinstance(second, DwgRecord) and isinstance(mine, DwgRecord)
        if same_record and [f.FieldName for f in first.RecordFields] == [f.FieldName for f in second.RecordFields] == [f.FieldName for f in mine.RecordFields]:
            return DwgRecord(tuple(DwgField(m.FieldName, self.apply(m.FieldValue, a.FieldValue, b.FieldValue, own, home, f'{path}/{m.FieldName}'))
                                   for m, a, b in zip(mine.RecordFields, first.RecordFields, second.RecordFields)))
        same_tuple = all(isinstance(v, tuple) for v in (mine, first, second)) and len(mine) == len(first) == len(second)
        if same_tuple and not all(isinstance(v, float) for v in first):
            return tuple(self.apply(m, a, b, own, home, f'{path}[{i}]') for i, (m, a, b) in enumerate(zip(mine, first, second)))
        if dataclasses.is_dataclass(first) and type(first) is type(second) is type(mine):
            return replace(mine, **{f.name: self.apply(getattr(mine, f.name), getattr(first, f.name), getattr(second, f.name), own, home, f'{path}.{f.name}')
                                    for f in dataclasses.fields(first)})
        expected = self.moved(first, own, home)
        if not close(expected, mine):
            self.checks.append({'leaf': path, 'control': brief(mine), 'kit_a': brief(expected)})
        self.leaves += 1
        return self.moved(second, own, home)


def close(one, two):
    if isinstance(one, float) and isinstance(two, float):
        return abs(one - two) <= 1e-6
    if isinstance(one, tuple) and isinstance(two, tuple) and len(one) == len(two):
        return all(close(a, b) for a, b in zip(one, two))
    return repr(one) == repr(two)


def brief(value):
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, tuple) and all(isinstance(v, float) for v in value):
        return [round(v, 6) for v in value]
    return repr(value)[:80]


def items_of(record):
    return field(record, 'Items').RecordFields


def triples(items):
    data = bytes(int(item.FieldValue) for item in items[STATE[0]:STATE[1]])
    return [round(v, 9) for v in struct.unpack('<9d', data)]


def state(mine, first, second, patch):
    rows, one, two = items_of(mine), items_of(first), items_of(second)
    if not len(rows) == len(one) == len(two) or any(repr(x) != repr(y) for x, y in zip(one[:STATE[0]], two[:STATE[0]])):
        raise RuntimeError('view state records differ in shape')
    if any(repr(x) != repr(y) for x, y in zip(one[STATE[1]:], two[STATE[1]:])):
        raise RuntimeError('view state records differ outside the target, eye and up triples')
    if triples(rows) != triples(one):
        patch.checks.append({'leaf': 'XRECORD view state', 'control': triples(rows), 'kit_a': triples(one)})
    patch.leaves += 1
    items = (*rows[:STATE[0]], *two[STATE[0]:STATE[1]], *rows[STATE[1]:])
    fields = tuple(DwgField(f.FieldName, DwgRecord(items) if f.FieldName == 'Items' else f.FieldValue) for f in mine.RecordFields)
    return DwgRecord(fields)


def kit_model(dwg, kit_dwg):
    graph, kit_graph = Graph(dwg), Graph(kit_dwg)
    pair, _ = pairs(kit_graph, graph)
    rows, moved = {obj.ObjectHandle: obj for obj in dwg.DwgObjects}, []
    for kit_handle, home in pair.items():
        names = MODEL_FIELDS.get(kit_graph.names[kit_handle], ())
        values = {name: field(kit_graph.objects[kit_handle].ClassData, name) for name in names}
        values = {name: value for name, value in values.items() if repr(value) != repr(field(rows[home].ClassData, name))}
        if values:
            rows[home] = replace(rows[home], ClassData=with_fields(rows[home].ClassData, **values))
            moved.append([kit_graph.names[kit_handle], sorted(values)])
    return replace(dwg, DwgObjects=tuple(rows[h] for h in sorted(rows))), moved


def edgeless(dwg, drop_curves):
    graph = Graph(dwg)
    rows, curves = {obj.ObjectHandle: obj for obj in dwg.DwgObjects}, set()
    for handle, kind in graph.names.items():
        if kind != 'ACDBVIEWREP' or graph.objects[handle].ClassKind != 'ACDBVIEWREP':
            continue
        data = graph.objects[handle].ClassData
        bodies = field(data, 'Bodies')
        curves.update(target(handle, field(edge, 'EdgeEntity')) for body in bodies for edge in field(body, 'Edges'))
        bodies = tuple(with_fields(body, EdgeCount=0, Edges=()) for body in bodies)
        rows[handle] = replace(rows[handle], ClassData=with_fields(data, Bodies=bodies))
    dwg, removed = replace(dwg, DwgObjects=tuple(rows[h] for h in sorted(rows))), {}
    if drop_curves:
        dwg, removed, _ = prune(dwg, curves)
    return dwg, {'edges': len(curves), 'removed': dict(removed)}


def stale(dwg, parts):
    graph = Graph(dwg)
    rows, changed = {obj.ObjectHandle: obj for obj in dwg.DwgObjects}, []

    def mark(handle, **values):
        rows[handle] = replace(rows[handle], ClassData=with_fields(rows[handle].ClassData, **values))
        changed.append(graph.names[handle])

    for handle, kind in graph.names.items():
        data = graph.objects[handle].ClassData
        if kind == 'ACDBVIEWREP' and 'flag' in parts:
            mark(handle, ViewFlags=field(data, 'ViewFlags') | KAPI_FLAG)
        if kind != 'ACDBASSOCACTION' or graph.names.get(target(handle, field(data, 'ActionBody'))) != 'ACDBASSOCVIEWREPACTIONBODY':
            continue
        if 'actions' in parts:
            mark(handle, GeometryStatus=KCHANGED)
        if 'network' in parts:
            network = target(handle, field(data, 'OwningNetwork'))
            if field(rows[network].ClassData, 'GeometryStatus') != KCHANGED:
                mark(network, GeometryStatus=KCHANGED)
        if 'dependencies' in parts:
            for item in field(data, 'Dependencies'):
                mark(target(handle, field(item, 'Dependency')), DependencyStatus=KCHANGED)
    return replace(dwg, DwgObjects=tuple(rows[h] for h in sorted(rows))), sorted(changed)


def graft(control, first, second):
    graph, kit_graph = Graph(control), Graph(first)
    pair, conflicts = pairs(kit_graph, graph)
    patch = Patch(pair)
    one = {obj.ObjectHandle: obj for obj in first.DwgObjects}
    two = {obj.ObjectHandle: obj for obj in second.DwgObjects}
    if sorted(one) != sorted(two):
        raise RuntimeError('Kit builds A and B differ in handles')
    rows, touched, unpaired = {obj.ObjectHandle: obj for obj in control.DwgObjects}, [], []
    for handle in sorted(one):
        a, b = one[handle], two[handle]
        if all(repr(getattr(a, part)) == repr(getattr(b, part)) for part in PARTS):
            continue
        home = pair.get(handle)
        if home is None:
            unpaired.append(f'{a.ClassKind}@{handle:#x}')
            continue
        mine = rows[home]
        if a.ClassKind == 'XRECORD':
            rows[home] = replace(mine, ClassData=state(mine.ClassData, a.ClassData, b.ClassData, patch))
            touched.append(a.ClassKind)
            continue
        values = {part: patch.apply(getattr(mine, part), getattr(a, part), getattr(b, part), handle, home, f'{a.ClassKind}.{part}')
                  for part in PARTS}
        rows[home] = replace(mine, **values)
        touched.append(a.ClassKind)
    note = {'paired': len(pair), 'conflicts': conflicts, 'unpaired': unpaired, 'objects': len(touched),
            'kinds': sorted(set(touched)), 'leaves': patch.leaves, 'control_differs_from_kit_a': patch.checks,
            'unmapped': sorted(set(patch.misses))}
    return replace(control, DwgObjects=tuple(rows[h] for h in sorted(rows))), note


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--paper', default='A3 Landscape')
    args = parser.parse_args()
    out = BuildVariants.OUT
    drawing, source = BuildGrafts.bundle_parts(args.bundle)
    q1, _ = BuildBisect.bases(drawing)
    lean_dwg, _ = BuildGrafts.lean(q1)
    both_dwg, _ = BuildGrafts.ruled(lean_dwg, args.paper)
    core_dwg, _ = BuildGrafts.core(both_dwg)
    base, _, _ = T.transplant(core_dwg, BuildDims.kit_with(args.paper, None), T.TABLE_KINDS + T.STANDARD_KINDS, True)
    base, _ = BuildDims.plain(base)
    first = kit('A', args.paper)
    plan = {'paper': args.paper, 'variants': [], 'transplants': {}}
    for label in (*LAYOUTS, *MODEL_LAYOUTS, *EDGELESS, *STALE):
        if label == 'A':
            continue
        layout = 'A' if label in STALE else MODEL_LAYOUTS.get(label, EDGELESS.get(label, (label,))[0])
        second = kit(layout, args.paper)
        dwg, note = graft(base, first, second)
        if label in MODEL_LAYOUTS:
            dwg, note['kit_model'] = kit_model(dwg, second)
        if label in EDGELESS or label in STALE:
            dwg, note['edgeless'] = edgeless(dwg, EDGELESS.get(label, ('A', False))[1])
        if label in STALE:
            dwg, note['stale'] = stale(dwg, STALE[label])
        plan['transplants'][label] = note
        if note['unpaired'] or note['unmapped'] or note['conflicts']:
            print(label, json.dumps(note)[:1500])
            continue
        data = BuildPruned.emit_fresh(dwg)
        bundle = BuildVariants.opaque_bundle(BuildVariants.without_database(drawing, data), source, label)
        plan['variants'].append(BuildPruned2.record(out, label, bundle, data, dwg, {}))
    (out / PLAN).write_text(json.dumps(plan, indent=1, default=str) + '\n')
    print(json.dumps({label: {k: v for k, v in row.items() if k != 'control_differs_from_kit_a'} | {'checks': len(row['control_differs_from_kit_a'])}
                      for label, row in plan['transplants'].items()}))


if __name__ == '__main__':
    main()
