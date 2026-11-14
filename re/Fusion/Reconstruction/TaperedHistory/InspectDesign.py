import collections
import hashlib
import json
import runpy
import sys
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
API = runpy.run_path(str(BASE.parent / 'EntityGraph/DecodeGraph.py'))
STUDY = ROOT / 're/Fusion/Study/extents-f0f33a9a605f'
NAMES = ('BRepHistorySerializer', 'DcExtrudeFeature', 'BodyProgenitor', 'SketchCurveProgenitor', 'SketchCurveRecipe', 'SketchRegionRecipe', 'ProgenitorTable', 'FeatureId', 'SkCircle', 'SkCurve', 'SketchCurve', 'DcSketch', 'Parameter', 'DcProfile', 'DcModel', 'DcExtrudeTool', 'DcBody', 'BRepBody', 'BodyGeometry', 'SkRegion')
EXACT_NAMES = {'MSketchMetaType', 'SketchMetaType', 'Point3DMetaType', 'CircArc3DMetaType', 'ModelDataRefMetaType', 'SketchRegionRefMetaType', 'BodyMetaType', 'ETCachedTopologyMetaType'}


def inspect(source):
    archive = API['TOOLS']['read_archive'](source)
    codec = API['GraphCodec'](archive)
    continuations = collections.defaultdict(set)
    for record in archive['records']:
        if not record['primary']:
            continuations[record['identity']].add(record['class']['identifier'].upper())
    selected_ids = set()
    for record in archive['records']:
        name = codec.schema.get(record['class']['identifier'].upper(), {}).get('name', '')
        if name in EXACT_NAMES or any(item in name for item in NAMES):
            selected_ids.add(record['identity'])
    selected = []
    for record in archive['records']:
        identifier = record['class']['identifier'].upper()
        name = codec.schema.get(identifier, {}).get('name', '')
        if record['identity'] not in selected_ids:
            continue
        reader = API['TOOLS']['Reader'](record['payload'])
        stops = continuations[record['identity']] - ({identifier} if not record['primary'] else set())
        frame = codec.read_frame(reader, record['primary'])
        values = codec.read_groups(reader, codec.groups(identifier, stops))
        if reader.offset != len(reader.data):
            raise ValueError('Incomplete selected Design record ' + str(record['identity']))
        selected.append(dict(entityId=record['identity'], primary=record['primary'], className=name, classId=identifier, frame=frame, groups=values))
    return dict(source=str(source.relative_to(ROOT)), sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(), metadataSha256=archive['metadataSha256'], bulkSha256=archive['bulkSha256'], records=selected)


def main():
    report = dict(schema='FusionTaperedDesignJoins/1', scope='Selected saved Design fields decoded read-only with research schema; no native queries or production codec execution', samples=[inspect(STUDY / name) for name in ('distance_positive.f3d', 'taper.f3d')])
    changes = []
    for before, after in zip(report['samples'][0]['records'], report['samples'][1]['records'], strict=True):
        if (before['entityId'], before['className']) != (after['entityId'], after['className']):
            raise ValueError('Design controls have different selected record layout')
        for old, new in zip(before['groups'], after['groups'], strict=True):
            if old['identifier'] != new['identifier'] or old['fields'].keys() != new['fields'].keys():
                raise ValueError('Design controls have different selected member schema')
            for name, value in old['fields'].items():
                if value != new['fields'][name]:
                    changes.append(dict(entityId=before['entityId'], className=before['className'], group=old['identifier'], field=name, before=value, after=new['fields'][name]))
    report['changes'] = changes
    (BASE / 'ControlledDesign.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps([dict(source=sample['source'], records=len(sample['records']), types=dict(collections.Counter(row['className'] for row in sample['records']))) for sample in report['samples']], indent=2))


if __name__ == '__main__':
    main()
