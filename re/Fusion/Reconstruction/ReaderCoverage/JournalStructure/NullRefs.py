import collections
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).parent))

import convert.formats.Fusion.BrepCodec.Journal.Reading.ReadBoardMut as BoardModule
import convert.formats.Fusion.Topology.AsmEdge.AsmTable as StatesModule

BoardModule.KBoardChanges = 1 << 20
StatesModule.KRecordTokens = 1 << 20
from Journals import members, raw_model
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntitiesMut import ReadEntitiesMut
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadModelHead import ReadModelHead
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import MakeEntityNode
from convert.formats.Fusion.MetaCursor import MetaCursor


def tables(path):
    for member, payload in members(path, '.smbh').items():
        model = raw_model(payload)
        yield member, tuple(MakeEntityNode(value) for value in model.Entities)
    for member, payload in members(path, '.smb').items():
        cursor = MetaCursor(payload)
        ReadModelHead(cursor, False)
        yield member, tuple(MakeEntityNode(value) for value in ReadEntitiesMut(cursor, 'End-of-ASM-data'))


def ref(records, value):
    return records[value].Name if 0 <= value < len(records) else None


# every edge without a curve or coedge and every body without a lump, with the records around it
def main():
    shapes = collections.Counter()
    examples = {}
    unread = collections.Counter()
    for path in sorted(glob.glob(str(ROOT / 're/**/*.f3d'), recursive=True)):
        try:
            found = list(tables(path))
        except Exception as error:
            unread[f'{type(error).__name__}: {error}'] += 1
            continue
        for member, records in found:
            kind = member.rsplit('.', 1)[-1]
            for slot, record in enumerate(records):
                tokens = record.Tokens
                if record.Name in ('edge', 'tedge-edge') and tokens[8][1] == -1:
                    coedge = records[tokens[7][1]] if tokens[7][1] != -1 else None
                    loop = records[coedge.Tokens[8][1]] if coedge and coedge.Tokens[8][1] != -1 else None
                    face = records[loop.Tokens[5][1]] if loop and loop.Tokens[5][1] != -1 else None
                    vertex = records[tokens[3][1]]
                    key = {
                        'shape': 'edge without curve',
                        'kind': kind,
                        'same_vertex': tokens[3][1] == tokens[5][1],
                        'params': [tokens[4][1], tokens[6][1]],
                        'sense': tokens[9][0],
                        'convexity': tokens[10][1],
                        'coedge_partner_is_self': coedge is not None and coedge.Tokens[5][1] == tokens[7][1],
                        'coedge_pcurve': None if coedge is None else ref(records, coedge.Tokens[10][1]),
                        'face_surface': None if face is None else ref(records, face.Tokens[7][1]),
                        'vertex_edge_is_self': vertex.Tokens[3][1] == slot,
                    }
                elif record.Name in ('edge', 'tedge-edge') and tokens[7][1] == -1:
                    key = {
                        'shape': 'edge without coedge',
                        'kind': kind,
                        'curve': ref(records, tokens[8][1]),
                        'referenced_by': sorted({other.Name for other in records if any(tag == 12 and value == slot for tag, value in other.Tokens)}),
                    }
                elif record.Name == 'body' and tokens[3][1] == -1:
                    key = {
                        'shape': 'body without lump',
                        'kind': kind,
                        'wire': tokens[4][1],
                        'transform': tokens[5][1],
                    }
                else:
                    continue
                text = json.dumps(key, sort_keys=True)
                shapes[text] += 1
                examples.setdefault(text, f'{Path(path).relative_to(ROOT)} {kind} slot {slot}')
    report = {
        'scope': 'Every entity record (live and archived) in every .smbh and .smb under re/ whose curve, coedge or lump reference is -1',
        'unread': dict(unread.most_common()),
        'shapes': [{'count': count, 'example': examples[text], **json.loads(text)} for text, count in shapes.most_common()],
    }
    Path(__file__).with_name('NullRefs.json').write_text(json.dumps(report, indent=1) + '\n')
    for row in report['shapes']:
        print(row)
    print(sum(unread.values()), 'unread')


if __name__ == '__main__':
    main()
