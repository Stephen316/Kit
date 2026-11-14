import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.MetaIndex import SegmentKind

PROBE = ROOT / 're/Fusion/LocalOracle/ActSlack/Probe.json'


def act_segment(path):
    model = ReadDocument((ROOT / path).read_bytes())
    rows = [segment for segment in model.Segments if segment.Metadata.Header.Segment is SegmentKind.KAct]
    if len(rows) != 1:
        raise ValueError('expected one ACT segment')
    return rows[0]


def describe(path):
    segment = act_segment(path)
    final = segment.Records[-1]
    return segment, {
        'file': path,
        'records': len(segment.Records),
        'final_object': final.ObjectId,
        'final_type_code': final.TypeCode,
        'slack_bytes': len(segment.BulkSlack),
        'slack_sha256': hashlib.sha256(segment.BulkSlack).hexdigest() if segment.BulkSlack else None,
        'slack_zero': not any(segment.BulkSlack),
    }


def main():
    probe = json.loads(PROBE.read_text())
    cases = []
    for case in probe['cases']:
        described = [describe(save['file']) for save in case['saves']]
        first = described[0][0]
        rows = [row for _, row in described]
        for segment, row in described[1:]:
            row['records_equal_first'] = segment.Records == first.Records
            row['slack_equal_first'] = segment.BulkSlack == first.BulkSlack
            row['final_fields_equal_first'] = (segment.Records[-1].Frame, segment.Records[-1].Groups) == (first.Records[-1].Frame, first.Records[-1].Groups)
        cases.append({'name': case['name'], 'saves': rows})
    report = {
        'scope': 'Unchanged documents saved repeatedly by local Fusion; compares decoded ACT records and the bytes after the final record',
        'fusion_version': probe['fusion_version'],
        'python': sys.version.split()[0],
        'cases': cases,
    }
    (BASE / 'Saves.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
