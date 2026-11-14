import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(HERE))

from ProbeFailures import entities
from Shapes import corpus

from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntityNode import ReadEntityNode
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import MakeEntityNode

KKINDS = ('int64_attrib-name_attrib-gen-attrib', 'name_attrib-gen-attrib', 'no_merge_attribute-st-attrib', 'wire')
KNESTED = ((7, 'generic_tag_attrib_def'), (4, 3), (4, 3), (4, -1), (7, 'generic_tag_attrib_def '), (4, 1), (4, 0), (7, ''))


def label(table, value):
    return 'null' if value == -1 else table[value].Name


def gather():
    groups = collections.defaultdict(lambda: {'records': 0, 'files': set(), 'shapes': collections.Counter(), 'owners': collections.defaultdict(collections.Counter), 'values': collections.Counter(), 'typed_roundtrip': 0})
    for path, name, payload in corpus():
        try:
            table = entities(payload, name.endswith('.smbh'))
        except Exception:
            continue
        relative = str(Path(path).relative_to(ROOT))
        for index, record in enumerate(table):
            tokens = record.Tokens
            key = None
            values = None
            if record.Name in KKINDS:
                key = record.Name
                if record.Name.endswith('gen-attrib'):
                    values = (tuple(value for _, value in tokens[5:9]), tokens[9][1], tokens[10][1] if len(tokens) > 10 else None)
                elif record.Name == 'wire':
                    values = (tokens[6], tokens[7])
            elif record.Name == 'ATTRIB_CUSTOM-attrib' and tokens[5] == (7, 'FDM_feature_attrib_def'):
                key = 'FDM_feature_attrib_def'
                values = tuple(value for _, value in tokens[8:14]) + ((tokens[17][1],) if len(tokens) > 17 else ())
            elif record.Name == 'ATTRIB_CUSTOM-attrib' and tokens[5:13] == KNESTED:
                key = 'nested generic tag child'
                parent = table[tokens[4][1]]
                values = ('operation', tokens[15][1], 'parent owner', label(table, parent.Tokens[4][1]), 'parent points back', parent.Tokens[0] == (12, index))
            elif record.Name == 'ATTRIB_CUSTOM-attrib' and tokens[0] != (12, -1):
                key = 'generic tag parent with nested child'
                values = ('owner', label(table, tokens[4][1]))
            elif record.Name == 'shell' and tokens[6] != (12, -1):
                key = 'shell with wire'
                values = ('first face', label(table, tokens[5][1]), 'wire', label(table, tokens[6][1]))
            if key is None:
                continue
            group = groups[key]
            group['records'] += 1
            group['files'].add(relative)
            group['shapes'][str(tuple(tag for tag, _ in tokens))] += 1
            group['values'][str(values)] += 1
            for slot, (tag, value) in enumerate(tokens):
                if tag == 12 and slot != 1:
                    group['owners'][slot][label(table, value)] += 1
            if MakeEntityNode(ReadEntityNode(record)) == record:
                group['typed_roundtrip'] += 1
    result = {}
    for key, group in sorted(groups.items()):
        result[key] = {
            'records': group['records'],
            'files': len(group['files']),
            'typed_roundtrip_equal': group['typed_roundtrip'],
            'shapes': dict(group['shapes']),
            'values': dict(group['values'].most_common()),
            'pointer_targets': {str(slot): dict(counter) for slot, counter in sorted(group['owners'].items())},
            'examples': sorted(group['files'])[:4],
        }
    return result


def provenance():
    folder = ROOT / 're/Fusion/LocalOracle/FormDocuments/Cache'
    preparation = json.loads((folder / 'Preparation.json').read_text())
    probe = json.loads((folder / 'Probe.json').read_text())
    rows = []
    for row in preparation['rows']:
        if row['variant'] != 'SurfNone':
            continue
        opened = next(item for item in probe['rows'] if item['file'] == row['file'])
        rows.append({
            'file': row['file'],
            'prepared_from': row['source'],
            'preparation_scope': preparation['scope'],
            'fusion_open_status': opened['status'],
            'fusion_open_error': opened['traceback'].strip().splitlines()[-1],
            'classification': 'Kit-made mutation of a Fusion-saved source; Fusion refuses to open it',
        })
    return rows


if __name__ == '__main__':
    report = {
        'scope': 'Saved Fusion journal records behind qualified-field, attribute-family and entity-kind failures; corpus is every .smb and .smbh member under re and examples',
        'records': gather(),
        'kit_made_out_of_scope': provenance(),
    }
    if len(sys.argv) > 1:
        report['census'] = json.loads(Path(sys.argv[1]).read_text())
    (HERE / 'Evidence.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({key: (value['records'], value['files'], value['typed_roundtrip_equal']) for key, value in report['records'].items()}, indent=1))
