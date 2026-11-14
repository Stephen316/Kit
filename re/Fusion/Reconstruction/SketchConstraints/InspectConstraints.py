import hashlib
import json
import lzma
from pathlib import Path
import runpy
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
API = runpy.run_path(str(BASE.parent / 'SketchDimensions/InspectDimensions.py'))
CAPTURES = ROOT / 're/Fusion/LocalOracle/RectangleConstraints'
API['inspect'].__globals__['CAPTURES'] = CAPTURES
STAGES = ('Baseline', 'Orientation1', 'Orientation2', 'Orientation3', 'Orientation4', 'FixedAnchor', 'WidthDimension', 'WidthDepthDimensions', 'EditedDimensions')


def digest(value):
    return hashlib.sha256(value).hexdigest()


def main():
    graphs = [API['inspect'](name) for name in STAGES]
    deltas = [API['compare'](a, b) for a, b in zip(graphs, graphs[1:])]
    report = {
        'schema': 'FusionSketchConstraintDifferential/1',
        'scope': 'Read-only native corpus analysis using the research decoder; no product execution, local tests or native calls',
        'captureSha256': digest((CAPTURES / 'Capture.json').read_bytes()),
        'scriptSha256': digest((CAPTURES.parent / 'CaptureRectangleConstraints.py').read_bytes()),
        'graphs': graphs, 'deltas': deltas,
    }
    raw = (json.dumps(report, indent=2, allow_nan=False) + '\n').encode()
    packed = lzma.compress(raw, preset=9)
    (BASE / 'ConstraintGraphs.json.xz').write_bytes(packed)
    summary = {key: value for key, value in report.items() if key not in ('graphs', 'deltas')}
    summary.update({
        'artifact': 'ConstraintGraphs.json.xz', 'artifactSha256': digest(packed), 'uncompressedSha256': digest(raw),
        'stages': [{'stage': graph['stage'], 'source': graph['source'], 'sourceSha256': graph['sourceSha256'], 'recordCount': len(graph['records']), 'primaryCount': sum(row['primary'] for row in graph['records']), 'payloadBytes': sum(row['payloadBytes'] for row in graph['records'])} for graph in graphs],
        'deltas': [{'before': delta['beforeStage'], 'after': delta['afterStage'], 'added': [{key: row[key] for key in ('entityId', 'primary', 'className', 'classId', 'schemaVersion')} for row in delta['addedRecords']], 'removed': [{key: row[key] for key in ('entityId', 'primary', 'className')} for row in delta['removedRecords']], 'changed': [{key: row[key] for key in ('entityId', 'primary', 'className')} for row in delta['changedRecords']]} for delta in deltas],
    })
    (BASE / 'ConstraintSummary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'stages': summary['stages'], 'added': [{'after': row['after'], 'classes': [r['className'] for r in row['added']]} for row in summary['deltas']]}))


if __name__ == '__main__':
    main()
