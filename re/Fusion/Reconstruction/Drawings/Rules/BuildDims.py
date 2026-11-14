"""Graft Kit's dimensions of each kind into the A3 control (route a) and record the variants.

The base is T2Standard: L4Core with Kit's tables and standard objects. Its one dimension loses its associative
action, as in F3bPlainDimension, so it can change kind. Each variant then swaps that dimension for the one Kit
writes for a kind: the dimension object keeps the control's handle and takes Kit's type, fields and extended
data, and its anonymous block takes Kit's lines, arrows, text and points on handles freed by L4Core.

* D0Plain: the base with the plain control dimension.
* D1Vertical, D2Aligned, D3Radius, D4Diameter: Kit's dimension of that kind.
* D5Short: an aligned dimension too short for its arrows and text, so both go outside.
* D6OnLine: D5Short with its dimension line through the points, so it has no extension lines.
* D7Split: an aligned dimension with room for its arrows but not its text, which goes past the second arrow.
* D8Flank: a vertical dimension with room for its text but not its arrows, which point in from outside.

Each variant goes to Variants/<label>.f3z with a row in Variants/PlanDims.json for BisectRound.py.
Run: python3.14 -I BuildDims.py --bundle $TMPDIR/KitFusionDrawings/Variants/P0Control.f3z
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
import BuildPruned3  # noqa: E402
import BuildPruned4  # noqa: E402
import BuildTransplant as T  # noqa: E402
import BuildVariants  # noqa: E402
import KitSolids  # noqa: E402
from PruneDwg import Graph, field, prune, target, with_fields  # noqa: E402

from convert.formats.Fusion.DrawingCodec.Dwg.Author.AuthorDwg import AuthorDwg  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.DimensionDraft import DimensionDraft  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.DwgDraft import DwgDraft  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.SheetDraft import SheetDraft  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.TitleText import TitleText  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewDraft import ViewDraft  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewSource import ViewSource  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile  # noqa: E402

PLAN = 'PlanDims.json'
DIMENSIONS = {
    'D1Vertical': DimensionDraft((350.0, 210.0), (350.0, 250.0), 330.0, 1.0, 'Vertical'),
    'D2Aligned': DimensionDraft((300.0, 220.0), (330.0, 250.0), 10.0, 1.0, 'Aligned'),
    'D3Radius': DimensionDraft((360.0, 150.0), (370.0, 150.0), 8.0, 1.0, 'Radius'),
    'D4Diameter': DimensionDraft((340.0, 150.0), (360.0, 150.0), 8.0, 1.0, 'Diameter'),
    'D5Short': DimensionDraft((300.0, 220.0), (305.0, 225.0), 10.0, 2.0, 'Aligned'),
    'D6OnLine': DimensionDraft((300.0, 220.0), (305.0, 225.0), 0.0, 2.0, 'Aligned'),
    'D7Split': DimensionDraft((300.0, 220.0), (307.5, 227.5), 10.0, 3.0, 'Aligned'),
    'D8Flank': DimensionDraft((350.0, 210.0), (350.0, 217.5), 330.0, 0.75, 'Vertical'),
}


def kit_with(paper, dimension):
    source = ViewSource(0x1C5, '1_Component', '0f0e0d0c-0b0a-4908-8706-050403020100', (-1.0, 0.0, 0.5), (4.0, 2.0, 1.5), Solid=KitSolids.box_solid((-1.0, 0.0, 0.5), (4.0, 2.0, 1.5)))
    views = (ViewDraft((180.0, 120.0), 4.0),)
    sheet = SheetDraft('Kit Sheet', (TitleText('TITLE_1', 'Kit Drawing'),), paper)
    dims = () if dimension is None else (dimension,)
    draft = DwgDraft(sheet, 0x2E50, datetime(2026, 11, 13, 12), '11111111-2222-4333-8444-555555555555',
                     '66666666-7777-4888-8999-aaaaaaaaaaaa', views, source, dims)
    with KitSolids.no_edges():
        return ReadDwgFile(AuthorDwg(draft))


def dimension_of(graph):
    rows = [handle for handle, obj in graph.objects.items() if obj.ClassKind.startswith('DIMENSION')]
    if len(rows) != 1:
        raise RuntimeError(f'expected one dimension, found {len(rows)}')
    return rows[0]


def plain(dwg):
    graph = Graph(dwg)
    kill = BuildPruned3.actions_with(graph, 'ACDBASSOCROTATEDDIMACTIONBODY')
    dead = graph.closure(kill)
    dwg, removed, _ = prune(dwg, kill | BuildPruned4.recompose_records(graph, dead))
    dwg = BuildPruned3.repair_networks(dwg)
    graph = Graph(dwg)
    handle = dimension_of(graph)
    xdic = field(graph.objects[handle].CommonData, 'Xdic')
    if xdic is not None and field(graph.objects[handle].CommonData, 'NoXdic') == 0:
        dwg, more, _ = prune(dwg, {target(handle, xdic)})
        removed.update(more)
    return dwg, dict(removed)


def mapped_eed(obj, home, kit_keys, control_handles, misses):
    rows = []
    for block in obj.EedBlocks:
        app = T.mapped(block.AppRef, obj.ObjectHandle, home, kit_keys, control_handles, misses)
        rows.append(replace(block, AppRef=app))
    return tuple(rows)


def swap(control, kit):
    graph, kit_graph = Graph(control), Graph(kit)
    home, source = dimension_of(graph), dimension_of(kit_graph)
    block = target(home, field(graph.objects[home].ClassData, 'DimBlock'))
    kit_block = target(source, field(kit_graph.objects[source].ClassData, 'DimBlock'))
    control, removed, _ = prune(control, set(T.owned_by(graph, block)))
    kit_keys = dict(T.keys_of(kit))
    control_handles = {key: handle for handle, key in T.keys_of(control).items()}
    kit_keys[kit_block], control_handles[('dimblock',)] = ('dimblock',), block
    kit_keys[source], control_handles[('dimension',)] = ('dimension',), home
    pool, misses, adds = T.free_pool(control), [], []
    entities = T.owned_by(kit_graph, kit_block)
    for entity in entities:
        kit_keys[entity] = ('kit', entity)
        control_handles[('kit', entity)] = pool.pop(0)
    for entity in entities:
        item = T.moved(kit_graph.objects[entity], control_handles[('kit', entity)], kit_keys, control_handles, misses)
        adds.append(replace(item, EedBlocks=mapped_eed(kit_graph.objects[entity], item.ObjectHandle, kit_keys, control_handles, misses)))
    rows = {obj.ObjectHandle: obj for obj in control.DwgObjects}
    owned = T.mapped(field(kit_graph.objects[kit_block].ClassData, 'Owned'), kit_block, block, kit_keys, control_handles, misses)
    rows[block] = replace(rows[block], ClassData=with_fields(rows[block].ClassData, Owned=owned, OwnedCount=len(owned)))
    item = T.moved(kit_graph.objects[source], home, kit_keys, control_handles, misses)
    rows[home] = replace(item, EedBlocks=mapped_eed(kit_graph.objects[source], home, kit_keys, control_handles, misses))
    objects = tuple(sorted((*rows.values(), *adds), key=lambda obj: obj.ObjectHandle))
    note = {'kind': kit_graph.objects[source].ClassKind, 'removed': dict(removed), 'added': len(entities),
            'unmapped_links': sorted(set(misses))}
    return replace(control, DwgObjects=objects), note


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
    base, _, _ = T.transplant(core_dwg, kit_with(args.paper, None), T.TABLE_KINDS + T.STANDARD_KINDS, True)
    base, removed = plain(base)
    plan = {'paper': args.paper, 'variants': [], 'transplants': {'D0Plain': {'plain_removed': removed}}}
    builds = [('D0Plain', base)]
    for label, dimension in DIMENSIONS.items():
        dwg, note = swap(base, kit_with(args.paper, dimension))
        plan['transplants'][label] = note
        builds.append((label, dwg))
    for label, dwg in builds:
        data = BuildPruned.emit_fresh(dwg)
        bundle = BuildVariants.opaque_bundle(BuildVariants.without_database(drawing, data), source, label)
        plan['variants'].append(BuildPruned2.record(out, label, bundle, data, dwg, {}))
    (out / PLAN).write_text(json.dumps(plan, indent=1, default=str) + '\n')
    print(json.dumps({label: {k: v for k, v in row.items() if k != 'removed'} for label, row in plan['transplants'].items()}))


if __name__ == '__main__':
    main()
