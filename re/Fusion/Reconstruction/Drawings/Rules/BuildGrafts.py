"""Build object-level graft variants of the A1 control for the drawing rules (route a) and the container probe (route b).

Every L variant starts from Q1NoDataStore, the A1 control without AutoCAD Mechanical objects, unused blocks and the
data-store section, which opened in Fusion 2706.1.17. The header and its four check values stay untouched, so each
variant changes only object records. A native open shows whether Fusion accepts the change.

* L0Base re-emits Q1NoDataStore as the open control of the round.
* L1Lean purges every unused style table entry (layers, line types, text styles, application ids, dimension styles,
  visual styles, materials, multileader, table, multiline, section and detail view styles), then removes the save
  history and Fusion named-object records, the variable dictionary and the fields. Scales stay, because the overall
  viewport annotation-scale record names one (the E1Purged quarantine).
* L2Rules keeps Q1NoDataStore and writes the rule values of Kit's writer into its objects: the overall viewport is
  the paper size, the layout paper fields come from the paper format, and the layout drops its auto-created-layout
  and plot-device extended data.
* L3LeanRules applies both L1Lean and L2Rules.
* L4Core is L3LeanRules without visual, table and multileader styles, the Global material, the dimension
  styles and scales that nothing names, so it keeps only the database core that the header names.
* Z1EmptyDwg keeps the A1 package and empties its embedded DWG member (route b, zero bytes).

The script also checks that the rules reproduce the control values that it leaves alone: the view rep body keys,
the view state captures and the dimension text extents. Its plan goes to Variants/PlanGrafts.json.
Run: python3.14 -I BuildGrafts.py --bundle $TMPDIR/KitFusionDrawings/Variants/P0Control.f3z
"""

import argparse
import io
import json
import re
import struct
import sys
import uuid
import zipfile
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / 'Dwg'))
sys.path.insert(0, str(HERE.parent / 'Authoring'))

import BuildBisect  # noqa: E402
import BuildPruned  # noqa: E402
import BuildPruned2  # noqa: E402
import BuildVariants  # noqa: E402
from PruneDwg import Graph, field, prune, target, with_fields  # noqa: E402

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Notes.TextMetrics import TextExtent  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlacePort import KOverallFlags  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetSizes import SheetSize  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewState import ViewState  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgRecord  # noqa: E402

PLAN = 'PlanGrafts.json'
KEEP_KINDS = tuple(kind for kind in BuildPruned2.PURGE_KINDS if kind != 'SCALE')
DROP_EED = ('FUSDOC_XDATA_AUTO_CREATED_LAYOUT', 'ACAD_PSEXT')


def bundle_parts(path):
    archive = zipfile.ZipFile(io.BytesIO(Path(path).read_bytes()))
    drawing = next(archive.read(name) for name in archive.namelist() if name.endswith('.f2d'))
    source = next(archive.read(name) for name in archive.namelist() if name.endswith('.f3d'))
    return drawing, source


def purged(dwg):
    saved = BuildPruned2.PURGE_KINDS
    BuildPruned2.PURGE_KINDS = KEEP_KINDS
    try:
        return BuildPruned2.purge_all(dwg)
    finally:
        BuildPruned2.PURGE_KINDS = saved


def merged(counts, removed):
    for name, count in removed.items():
        counts[name] = counts.get(name, 0) + count


def lean(dwg):
    graph = Graph(dwg)
    kill = BuildPruned2.nod_items(graph, BuildPruned2.NOD_HISTORY + BuildPruned2.NOD_FUSION)
    kill |= BuildPruned2.kind_items(graph, {'DICTIONARYVAR', 'FIELD', 'FIELDLIST'})
    dwg, counts, _ = prune(dwg, kill)
    counts = dict(counts)
    while True:
        dwg, removed = purged(dwg)
        merged(counts, removed)
        blocks = BuildPruned.unused_blocks(Graph(dwg))
        if not blocks:
            return dwg, counts
        dwg, removed, _ = prune(dwg, blocks)
        merged(counts, removed)


def scale_refs(dwg):
    rows = set()
    for obj in dwg.DwgObjects:
        if obj.ClassKind == 'XRECORD' and isinstance(field(obj.ClassData, 'Items'), DwgRecord):
            rows.update(item.FieldValue for item in field(obj.ClassData, 'Items').RecordFields if item.FieldName == '340' and isinstance(item.FieldValue, int))
    return rows


def core(dwg):
    graph = Graph(dwg)
    header = {ref.RefValue for ref in BuildPruned2.refs_in(dwg.HeaderVars)}
    names = BuildPruned2.entry_names(graph)
    kill = BuildPruned2.kind_items(graph, {'VISUALSTYLE', 'TABLESTYLE', 'MLEADERSTYLE'})
    kill |= {h for h, kind in graph.names.items() if kind == 'MATERIAL' and names.get(h) == 'Global'}
    kill |= {h for h, kind in graph.names.items() if kind == 'SCALE' and h not in scale_refs(dwg)}
    kill |= {h for h, kind in graph.names.items() if kind == 'DIMSTYLE' and h not in header}
    kill -= header
    dwg, removed, _ = prune(dwg, kill)
    return dwg, dict(removed)


def app_names(dwg):
    graph = Graph(dwg)
    return {handle: field(graph.objects[handle].ClassData, 'EntryName', '') for handle, kind in graph.names.items() if kind == 'APPID'}


def ruled(dwg, paper_name):
    paper = SheetSize(paper_name)
    graph = Graph(dwg)
    apps = app_names(dwg)
    layouts = [h for h, kind in graph.names.items() if kind == 'LAYOUT' and field(graph.objects[h].ClassData, 'LayoutName') != 'Model']
    if len(layouts) != 1:
        raise ValueError(f'expected one paper layout, found {len(layouts)}')
    layout = graph.objects[layouts[0]]
    overall = target(layout.ObjectHandle, field(layout.ClassData, 'LastViewport'))
    changes = {'layout': {}, 'overall': {}, 'eed_dropped': []}
    rows = []
    for obj in dwg.DwgObjects:
        if obj.ObjectHandle == layout.ObjectHandle:
            values = {
                'PaperWidth': paper.PaperWidth, 'PaperHeight': paper.PaperHeight, 'PaperSize': paper.MediaName,
                'WindowMin': (0.0, 0.0), 'WindowMax': (0.0, 0.0), 'LimitMin': (0.0, 0.0),
                'LimitMax': (paper.PaperWidth, paper.PaperHeight),
            }
            changes['layout'] = {name: [field(obj.ClassData, name), value] for name, value in values.items()}
            kept = tuple(block for block in obj.EedBlocks if apps.get(target(0, block.AppRef)) not in DROP_EED)
            changes['eed_dropped'] = [apps.get(target(0, block.AppRef)) for block in obj.EedBlocks if block not in kept]
            obj = replace(obj, ClassData=with_fields(obj.ClassData, **values), EedBlocks=kept)
        elif obj.ObjectHandle == overall:
            center = (paper.PaperWidth / 2, paper.PaperHeight / 2)
            values = {'Center': (*center, 0.0), 'Width': paper.PaperWidth, 'Height': paper.PaperHeight, 'ViewHeight': paper.PaperHeight, 'ViewCenter': center}
            changes['overall'] = {name: [field(obj.ClassData, name), value] for name, value in values.items()}
            changes['overall']['StatusFlags'] = [field(obj.ClassData, 'StatusFlags'), KOverallFlags]
            obj = replace(obj, ClassData=with_fields(obj.ClassData, **values))
        rows.append(obj)
    return replace(dwg, DwgObjects=tuple(rows)), changes


def state_checks(dwg):
    rows = []
    for obj in dwg.DwgObjects:
        if obj.ClassKind != 'XRECORD' or not isinstance(field(obj.ClassData, 'Items'), DwgRecord):
            continue
        pairs = [(item.FieldName, item.FieldValue) for item in field(obj.ClassData, 'Items').RecordFields]
        if not pairs or pairs[0][1] != 'ACAD_ROUNDTRIP_2016_ACDBIMPVIEWREP':
            continue
        blob = bytes(value for name, value in pairs[4:] if name == '70')
        target_point, eye, up = (struct.unpack_from('<3d', blob, at) for at in (18, 42, 66))
        offset = 91
        bodies = []
        for index in range(blob[90]):
            offset += 8 + (1 if index == 0 else 2) + 8
            guid = str(uuid.UUID(bytes_le=blob[offset:offset + 16]))
            lower = struct.unpack_from('<3d', blob, offset + 16)
            upper = struct.unpack_from('<3d', blob, offset + 40)
            bodies.append((guid, lower, upper))
            offset += 16 + 48 + 5
        rows.append({'handle': hex(obj.ObjectHandle), 'bytes': len(blob), 'bodies': blob[90], 'equal': ViewState(target_point, eye, up, tuple(bodies)) == blob})
    return rows


def text_checks(dwg):
    rows = []
    for obj in dwg.DwgObjects:
        if obj.ClassKind != 'MTEXT':
            continue
        data = obj.ClassData
        raw = field(data, 'TextValue', '')
        text = re.sub(r'\\[A-Za-z][^;]*;|[{}]', '', raw).replace('%%c', 'Ø').replace('%%d', '°').replace('%%p', '±')
        height = field(data, 'TextHeight')
        want_height, want_width = TextExtent(text, height)
        got_height, got_width = field(data, 'ExtentHeight'), field(data, 'ExtentWidth')
        rows.append({'text': raw, 'height': height, 'equal': abs(got_height - want_height) < 1e-6 and abs(got_width - want_width) < 1e-6})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--paper', default='A3 Landscape')
    args = parser.parse_args()
    out = BuildVariants.OUT
    drawing, source = bundle_parts(args.bundle)
    q1, _ = BuildBisect.bases(drawing)
    lean_dwg, lean_counts = lean(q1)
    rules_dwg, changes = ruled(q1, args.paper)
    both_dwg, _ = ruled(lean_dwg, args.paper)
    core_dwg, core_counts = core(both_dwg)
    merged(core_counts, lean_counts)
    plan = {'paper': args.paper, 'base_objects': len(q1.DwgObjects), 'changes': changes, 'variants': []}
    plan['checks'] = {'view_states': state_checks(q1), 'texts': text_checks(q1)}
    for label, dwg, removed in (('L0Base', q1, {}), ('L1Lean', lean_dwg, lean_counts), ('L2Rules', rules_dwg, {}), ('L3LeanRules', both_dwg, lean_counts), ('L4Core', core_dwg, core_counts)):
        data = BuildPruned.emit_fresh(dwg)
        bundle = BuildVariants.opaque_bundle(BuildVariants.without_database(drawing, data), source, label)
        plan['variants'].append(BuildPruned2.record(out, label, bundle, data, dwg, removed))
    empty = BuildVariants.opaque_bundle(BuildVariants.without_database(drawing, b''), source, 'Z1EmptyDwg')
    plan['variants'].append(BuildPruned2.record(out, 'Z1EmptyDwg', empty, b'', q1, {}))
    (out / PLAN).write_text(json.dumps(plan, indent=1, default=str) + '\n')
    print(json.dumps({'changes': changes, 'checks': plan['checks'], 'variants': [(row['label'], row['objects'], row['dwg_bytes']) for row in plan['variants']]}, indent=1, default=str))


if __name__ == '__main__':
    main()
