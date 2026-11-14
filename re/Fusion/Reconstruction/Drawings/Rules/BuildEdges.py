"""Graft view edges onto the A3 control and plan the oracle and acceptance rounds for stored view edges.

The base is D0Plain from BuildDims.py, laid out by BuildChildren.py. Each variant takes Kit's child layout leaves,
empties every view's stored edge list as BuildChildren.edgeless does, sets the view style and then, for the
acceptance variants, writes the edges Kit computes for each view (see ViewEdgeNotes.md).

* E1HiddenA: layout A (right and above children), no stored edges, base view with hidden edges (ViewLongB 1).
  After a poke the export holds Fusion's own edges for the control in hidden style.
* T16<Style><Layout>: the layout's views with the edges Kit computes from the control design's solid (read in
  stored order by SmbSolid.py), in visible or hidden style. Kit's edge entities take handles freed by the
  pruning and join each view's inner block; each view's edge list and style become Kit's. Layout A is the
  training layout (the control and E1); LeftBelow, RightBack and AboveBelow are held-out directions.

Run: python3.14 -I BuildEdges.py --bundle $TMPDIR/KitFusionDrawings/Variants/P0Control.f3z [--only E1HiddenA]
Each variant goes to Variants/<label>.f3z with a row in Variants/PlanEdges.json.
"""
import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / 'Dwg'))
sys.path.insert(0, str(HERE.parent / 'Authoring'))
sys.path.insert(0, str(HERE.parents[4] / 'src'))

import BuildBisect  # noqa: E402
import BuildChildren as C  # noqa: E402
import BuildDims  # noqa: E402
import BuildGrafts  # noqa: E402
import BuildPruned  # noqa: E402
import BuildPruned2  # noqa: E402
import BuildTransplant as T  # noqa: E402
import BuildVariants  # noqa: E402
import SmbSolid  # noqa: E402
from PruneDwg import Graph, field, target, with_fields  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef  # noqa: E402

PLAN = 'PlanEdges.json'
KBASE_LONG_A = 11
VARIANTS = {
    'E1HiddenA': {'layout': 'A', 'style': 1, 'edges': False},
}
for _name, _layout in (('A', 'A'), ('LeftBelow', 'V1LeftBelow'), ('RightBack', 'V2RightBack'), ('AboveBelow', 'V3AboveBelow')):
    VARIANTS['T16Visible' + _name] = {'layout': _layout, 'style': 2, 'edges': True}
    VARIANTS['T16Hidden' + _name] = {'layout': _layout, 'style': 1, 'edges': True}


def styled(dwg, style):
    graph = Graph(dwg)
    rows = {obj.ObjectHandle: obj for obj in dwg.DwgObjects}
    for handle, kind in graph.names.items():
        if kind == 'ACDBVIEWREP' and field(rows[handle].ClassData, 'ViewLongA') == KBASE_LONG_A:
            rows[handle] = replace(rows[handle], ClassData=with_fields(rows[handle].ClassData, ViewLongB=style))
    return replace(dwg, DwgObjects=tuple(rows[h] for h in sorted(rows)))


def view_block(graph, rep):
    ref = target(rep, field(graph.objects[rep].ClassData, 'BlockRef'))
    return target(ref, field(graph.objects[ref].ClassData, 'BlockHeader'))


def with_edges(dwg, kit_dwg):
    """Give each control view Kit's edge list, style and drawn edge entities."""
    graph, kit_graph = Graph(dwg), Graph(kit_dwg)
    pair, _ = C.pairs(kit_graph, graph)
    kit_keys, control_handles = dict(T.keys_of(kit_dwg)), {key: handle for handle, key in T.keys_of(dwg).items()}
    pool, rows, adds, misses, counts = T.free_pool(dwg), {obj.ObjectHandle: obj for obj in dwg.DwgObjects}, [], [], []
    for kit_rep in C.seeded(kit_graph, 'ACDBVIEWREP'):
        rep = pair[kit_rep]
        kit_block, block = view_block(kit_graph, kit_rep), view_block(graph, rep)
        kit_keys[kit_block], control_handles[('home', kit_block)] = ('home', kit_block), block
        entities = T.owned_by(kit_graph, kit_block)
        for entity in entities:
            kit_keys[entity], control_handles[('kit', entity)] = ('kit', entity), pool.pop(0)
        for entity in entities:
            adds.append(T.moved(kit_graph.objects[entity], control_handles[('kit', entity)], kit_keys, control_handles, misses))
        owned = tuple(field(rows[block].ClassData, 'Owned') or ()) + tuple(DwgHandleRef(3, control_handles[('kit', e)]) for e in entities)
        rows[block] = replace(rows[block], ClassData=with_fields(rows[block].ClassData, Owned=owned, OwnedCount=len(owned)))
        kit_data, data = kit_graph.objects[kit_rep].ClassData, rows[rep].ClassData
        edges = T.mapped(field(field(kit_data, 'Bodies')[0], 'Edges'), kit_rep, rep, kit_keys, control_handles, misses)
        bodies = field(data, 'Bodies')
        bodies = (with_fields(bodies[0], EdgeCount=len(edges), Edges=edges), *bodies[1:])
        rows[rep] = replace(rows[rep], ClassData=with_fields(data, Bodies=bodies, ViewLongB=field(kit_data, 'ViewLongB')))
        counts.append(len(edges))
    objects = tuple(sorted((*rows.values(), *adds), key=lambda obj: obj.ObjectHandle))
    return replace(dwg, DwgObjects=objects), {'edges': counts, 'unmapped': sorted(set(misses))}


def control_base(bundle, paper):
    drawing, source = BuildGrafts.bundle_parts(bundle)
    q1, _ = BuildBisect.bases(drawing)
    lean_dwg, _ = BuildGrafts.lean(q1)
    both_dwg, _ = BuildGrafts.ruled(lean_dwg, paper)
    core_dwg, _ = BuildGrafts.core(both_dwg)
    base, _, _ = T.transplant(core_dwg, BuildDims.kit_with(paper, None), T.TABLE_KINDS + T.STANDARD_KINDS, True)
    base, _ = BuildDims.plain(base)
    return drawing, source, base


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--paper', default='A3 Landscape')
    parser.add_argument('--only', nargs='*', default=[])
    args = parser.parse_args()
    out = BuildVariants.OUT
    drawing, source, base = control_base(args.bundle, args.paper)
    solid = SmbSolid.design_solid(source)
    first = C.kit('A', args.paper)
    path = out / PLAN
    plan = json.loads(path.read_text()) if path.exists() else {'paper': args.paper, 'variants': [], 'notes': {}}
    for label, spec in VARIANTS.items():
        if args.only and label not in args.only:
            continue
        dwg, note = C.graft(base, first, C.kit(spec['layout'], args.paper))
        if note['unpaired'] or note['unmapped'] or note['conflicts']:
            raise RuntimeError(label + ' ' + json.dumps(note)[:800])
        dwg, note['edgeless'] = C.edgeless(dwg, True)
        dwg = styled(dwg, spec['style'])
        if spec['edges']:
            dwg, note['kit_edges'] = with_edges(dwg, C.kit(spec['layout'], args.paper, solid, spec['style'] == 1))
            if note['kit_edges']['unmapped']:
                raise RuntimeError(label + ' ' + json.dumps(note['kit_edges']))
        data = BuildPruned.emit_fresh(dwg)
        bundle = BuildVariants.opaque_bundle(BuildVariants.without_database(drawing, data), source, label)
        row = BuildPruned2.record(out, label, bundle, data, dwg, {})
        plan['variants'] = [item for item in plan['variants'] if item['label'] != label] + [row]
        plan['notes'][label] = {'layout': spec['layout'], 'style': spec['style'], 'edgeless': note['edgeless'], 'leaves': note['leaves'],
                                'kit_edges': note.get('kit_edges')}
    path.write_text(json.dumps(plan, indent=1, default=str) + '\n')
    print(json.dumps(plan['notes'])[:1500])


if __name__ == '__main__':
    main()
