"""Write the stored view edge round report (E1, T16) and the offline held-out comparison.

Inputs, all outside git under $TMPDIR/KitFusionDrawings:
* Variants/PlanEdges.json and Variants/<label>.f3z from BuildEdges.py;
* Variants/Edges<tag>.json from Native/EdgeRound.py (open and update curves and boxes, export digest);
* Exports/<label>.dwg, the DWG Fusion exported after the poke (it keeps Fusion's own edge lists).

For each graft the report compares, view by view, Kit's edge rows and drawn entities in the graft with the rows
Fusion wrote in its export after the update. Entity handles are left out; every other row field, the entity kind,
its layer and its data are compared, floats to 1e-5.

--held <drawing.f2d> <kit.dwg> adds a held-out design compared the same way: a Fusion-saved drawing of another
design and the DWG Kit authors for the same view directions.

Run: python3.14 -I ReportEdges.py [--held boxa.f2d boxakit.dwg]
"""
import argparse
import io
import json
import os
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / 'Dwg'))
sys.path.insert(0, str(HERE.parents[4] / 'src'))

import BuildVariants  # noqa: E402
from PruneDwg import field, target  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgRecord  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile  # noqa: E402

ROOT = Path(os.environ['TMPDIR']) / 'KitFusionDrawings'
OUT = HERE / 'GraftRoundT16.json'
HELD_OUT = ('LeftBelow', 'RightBack', 'AboveBelow')


def load(path):
    data = Path(path).read_bytes()
    if str(path).endswith('.dwg'):
        return ReadDwgFile(data)
    if str(path).endswith('.f3z'):
        archive = zipfile.ZipFile(io.BytesIO(data))
        data = next(archive.read(name) for name in archive.namelist() if name.endswith('.f2d'))
    return ReadDwgFile(BuildVariants.database(data))


def plain(value):
    if isinstance(value, DwgHandleRef):
        return None
    if isinstance(value, DwgRecord):
        return {item.FieldName: plain(item.FieldValue) for item in value.RecordFields}
    if isinstance(value, tuple):
        return [plain(item) for item in value]
    if isinstance(value, float):
        rounded = round(value, 5)
        return 0.0 if rounded == 0 else rounded
    if isinstance(value, bytes):
        return value.hex()
    return value


def views(path):
    rows = {obj.ObjectHandle: obj for obj in load(path).DwgObjects}
    layers = {handle: field(obj.ClassData, 'EntryName') for handle, obj in rows.items() if obj.ClassKind == 'LAYER'}
    found = []
    for handle, obj in sorted(rows.items()):
        if obj.ClassKind != 'ACDBVIEWREP':
            continue
        edges = []
        for body in field(obj.ClassData, 'Bodies'):
            for edge in field(body, 'Edges'):
                entity = rows[target(handle, field(edge, 'EdgeEntity'))]
                data = plain(entity.ClassData)
                if data.get('UnitExtrusion') == 0 and data.get('Extrusion') == [0.0, 0.0, 1.0]:
                    data['UnitExtrusion'] = 1
                    data.pop('Extrusion')
                if entity.ClassKind == 'LINE':
                    data.pop('Extrusion', None)
                row = {key: value for key, value in plain(edge).items() if key != 'EdgeEntity'}
                edges.append([row, entity.ClassKind, layers.get(target(entity.ObjectHandle, field(entity.CommonData, 'Layer'))), data])
        found.append({'style': [field(obj.ClassData, 'ViewLongA'), field(obj.ClassData, 'ViewLongB')], 'edges': edges})
    return found


def compare(kit_path, fusion_path):
    kit, fusion = views(kit_path), views(fusion_path)
    out = []
    for kit_view, fusion_view in zip(kit, fusion):
        ids = [row[0]['EdgeId'] for row in kit_view['edges']]
        out.append({
            'style': kit_view['style'], 'fusion_style': fusion_view['style'],
            'rows': len(kit_view['edges']), 'fusion_rows': len(fusion_view['edges']),
            'same': kit_view['edges'] == fusion_view['edges'],
            'ids': [hex(value) if value > 0xFFFF else value for value in ids],
            'hidden': sum(1 for row in kit_view['edges'] if row[0]['EdgeFlagA'] == 0),
            'kinds': sorted({row[1] for row in kit_view['edges']}),
        })
    return {'views': len(kit), 'fusion_views': len(fusion), 'per_view': out}


def round_rows(tag):
    data = json.loads((ROOT / 'Variants' / f'Edges{tag}.json').read_text())
    rows = {}
    for row in data['rows']:
        result = row.get('result') or {}
        export = result.get('export') or {}
        rows[row['label']] = {
            'run': row['run'], 'open_seconds': result.get('open_seconds'), 'modified_after_open': result.get('modified_after_open'),
            'open_curves': result.get('open_curves'), 'update_curves': result.get('update_curves'),
            'open_boxes': result.get('open_boxes'), 'update_boxes': result.get('update_boxes'),
            'open_equals_update': result.get('open_curves') == result.get('update_curves') and result.get('open_boxes') == result.get('update_boxes'),
            'export_sha256': export.get('sha256'),
        }
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--held', nargs=2, default=None)
    args = parser.parse_args()
    plan = json.loads((ROOT / 'Variants' / 'PlanEdges.json').read_text())
    grafts = {row['label']: {'sha256': row['sha256'], 'dwg_sha256': row['dwg_sha256'], 'objects': row['objects'],
                             **{key: plan['notes'][row['label']][key] for key in ('layout', 'style', 'kit_edges')}}
              for row in plan['variants']}
    report = {
        'fusion_version': '2706.1.17',
        'route': 'object-level grafts on the A3 control (D0Plain base, BuildEdges.py); every stored edge removed; '
                 'E1 leaves the views empty, T16 writes the edges Kit computes from the control design solid',
        'run': 'Native/EdgeRound.py: upload, open, read curves and boxes, halve the base scale and restore it, read again, export DWG',
        'held_out_directions': ['T16Visible' + name for name in HELD_OUT] + ['T16Hidden' + name for name in HELD_OUT],
        'grafts': grafts,
        'rounds': {'E1': round_rows('E1'), 'T16': round_rows('T16')},
        'export_compare': {},
    }
    for label in grafts:
        if label.startswith('T16'):
            report['export_compare'][label] = compare(ROOT / 'Variants' / f'{label}.f3z', ROOT / 'Exports' / f'{label}.dwg')
    if args.held:
        report['held_out_design'] = {
            'design': 'BoxA, 25 x 25 x 5 mm box, Fusion-saved drawing: base view sight +Z, up +X, one projected view sight +Y',
            'compare': compare(args.held[1], args.held[0]),
        }
    OUT.write_text(json.dumps(report, indent=1) + '\n')
    same = {label: all(view['same'] for view in item['per_view']) for label, item in report['export_compare'].items()}
    print(json.dumps(same))
    if args.held:
        print('held', all(view['same'] for view in report['held_out_design']['compare']['per_view']))


if __name__ == '__main__':
    main()
