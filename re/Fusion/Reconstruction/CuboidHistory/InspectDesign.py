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
SOURCE = ROOT / 're/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d'


def main():
    archive = API['TOOLS']['read_archive'](SOURCE)
    codec = API['GraphCodec'](archive)
    continuations = collections.defaultdict(set)
    for record in archive['records']:
        if not record['primary']:
            continuations[record['identity']].add(record['class']['identifier'].upper())
    selected = []
    names = ('BRepHistorySerializer', 'DcExtrudeFeature', 'BodyProgenitor', 'SketchCurveProgenitor', 'SketchCurveRecipe', 'SketchRegionRecipe', 'ProgenitorTable', 'FeatureId', 'SkLine', 'SkCurve', 'SketchCurve', 'DcSketch')
    for record in archive['records']:
        identifier = record['class']['identifier'].upper()
        name = codec.schema.get(identifier, {}).get('name', '')
        if not any(item in name for item in names):
            continue
        reader = API['TOOLS']['Reader'](record['payload'])
        stops = continuations[record['identity']] - ({identifier} if not record['primary'] else set())
        frame = codec.read_frame(reader, record['primary'])
        values = codec.read_groups(reader, codec.groups(identifier, stops))
        if reader.offset != len(reader.data):
            raise ValueError('Incomplete selected Design record ' + str(record['identity']))
        selected.append(dict(entityId=record['identity'], primary=record['primary'], className=name, classId=identifier, frame=frame, groups=values))
    report = dict(schema='FusionControlledCuboidDesignJoins/1', scope='Selected saved Design fields decoded read-only with research schema; no native queries or production codec execution', source=str(SOURCE.relative_to(ROOT)), sourceSha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(), records=selected)
    (BASE / 'ControlledDesign.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps([dict(entityId=record['entityId'], className=record['className'], primary=record['primary']) for record in selected]))


if __name__ == '__main__':
    main()
