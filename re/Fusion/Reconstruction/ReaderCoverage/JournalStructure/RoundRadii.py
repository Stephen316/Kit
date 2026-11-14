import collections
import zipfile
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))

import convert.formats.Fusion.Topology.AsmEdge.AsmTable as TableModule

TableModule.KRecordTokens = 1 << 20
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadModelHead import ReadModelHead
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmName, ReadAsmRecord

KMarks = ('Begin-of-ASM-History-Data', 'End-of-ASM-History-Section', 'End-of-ASM-data')


def records(payload, history):
    cursor = MetaCursor(payload)
    ReadModelHead(cursor, history)
    table = []
    while cursor.Offset < len(payload):
        name = ReadAsmName(cursor)
        if name in KMarks:
            continue
        record = ReadAsmRecord(cursor, name)
        if name not in ('history_stream', 'delta_state'):
            table.append(record)
    return table


def sign(value):
    return 'negative' if value < 0 else ('zero' if value == 0 else 'positive')


# every torus and sphere carrier in every .smb and .smbh under re/, read from raw tokens
def main():
    shapes = collections.Counter()
    examples = {}
    faces = collections.Counter()
    for path in sorted(glob.glob(str(ROOT / 're/**/*.f3d'), recursive=True)):
        archive = zipfile.ZipFile(path)
        for info in archive.infolist():
            if not info.filename.endswith(('.smb', '.smbh')):
                continue
            table = records(archive.read(info.filename), info.filename.endswith('.smbh'))
            users = collections.defaultdict(list)
            for record in table:
                if record.Name == 'face':
                    users[record.Tokens[7][1]].append(record)
            for slot, record in enumerate(table):
                if record.Name == 'torus-surface':
                    major, minor = record.Tokens[5][1], record.Tokens[6][1]
                    key = {'carrier': 'torus', 'major': sign(major), 'minor': sign(minor), 'ring': abs(minor) < major}
                elif record.Name == 'sphere-surface':
                    key = {'carrier': 'sphere', 'radius': sign(record.Tokens[4][1])}
                else:
                    continue
                for face in users.get(slot, ()):
                    faces[json.dumps({**key, 'face_sense_tag': face.Tokens[8][0]})] += 1
                text = json.dumps(key, sort_keys=True)
                shapes[text] += 1
                examples.setdefault(text, f'{Path(path).relative_to(ROOT)} {info.filename.rsplit(".", 1)[-1]} record {slot}: {list(record.Tokens[3:8])}')
    report = {
        'scope': 'Radius signs of every torus-surface and sphere-surface record (live and archived) in every .smb/.smbh under re/',
        'shapes': [{'count': count, 'example': examples[text], **json.loads(text)} for text, count in shapes.most_common()],
        'face_senses': [{'count': count, **json.loads(text)} for text, count in faces.most_common()],
    }
    Path(__file__).with_name('RoundRadii.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
