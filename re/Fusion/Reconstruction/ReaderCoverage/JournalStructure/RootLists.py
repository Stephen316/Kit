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
from convert.formats.Fusion.BrepCodec.Journal.Validation.BuildAliases import BuildAliases
from convert.formats.Fusion.BrepCodec.Journal.Validation.NextState import NextState
from convert.formats.Fusion.BrepCodec.Journal.Validation.UndoStateMut import UndoStateMut
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import MakeEntityNode
from convert.formats.Fusion.MetaCursor import MetaCursor


# top-level entity kinds: a body, a face without a shell, an edge without a coedge
def top_level(record):
    if record.Name == 'body':
        return 'empty body' if record.Tokens[3][1] == -1 and record.Tokens[4][1] == -1 else 'body'
    if record.Name == 'face' and record.Tokens[5][1] == -1:
        return 'free face'
    if record.Name in ('edge', 'tedge-edge') and record.Tokens[7][1] == -1:
        return 'free edge'
    return None


def describe(records, versions, roots):
    lead = [top_level(records[versions[slot]]) if slot in versions else 'absent' for slot in range(1, roots)]
    rest = collections.Counter()
    for slot, revision in versions.items():
        if slot >= roots:
            kind = top_level(records[revision])
            if kind:
                rest[kind] += 1
    return lead, dict(rest)


def main():
    current = collections.Counter()
    history = collections.Counter()
    examples = {}
    unread = 0
    for path in sorted(glob.glob(str(ROOT / 're/**/*.f3d'), recursive=True)):
        name = str(Path(path).relative_to(ROOT))
        try:
            for member, payload in members(path, '.smbh').items():
                model = raw_model(payload)
                roots = model.Header.RootCount
                records = tuple(MakeEntityNode(value) for value in model.Entities)
                versions = {index: index for index in range(model.ActiveCount)}
                aliases = BuildAliases(model)
                node = model.Stream.ActiveNode
                first = True
                while node != -1:
                    lead, rest = describe(records, versions, roots)
                    key = json.dumps({'kind': 'smbh', 'lead': sorted(collections.Counter(lead).items(), key=str), 'outside_lead': sorted(rest.items())})
                    (current if first else history)[key] += 1
                    examples.setdefault(key, name)
                    first = False
                    UndoStateMut(model.States[node], versions, aliases)
                    node = NextState(model, node)
            for member, payload in members(path, '.smb').items():
                cursor = MetaCursor(payload)
                header, _ = ReadModelHead(cursor, False)
                records = tuple(MakeEntityNode(value) for value in ReadEntitiesMut(cursor, 'End-of-ASM-data'))
                lead, rest = describe(records, {index: index for index in range(len(records))}, header.RootCount)
                key = json.dumps({'kind': 'smb', 'lead': sorted(collections.Counter(lead).items(), key=str), 'outside_lead': sorted(rest.items())})
                current[key] += 1
                examples.setdefault(key, name)
        except Exception:
            unread += 1
    def rows(counter):
        return [{'count': count, 'example': examples[key], **json.loads(key)} for key, count in counter.most_common()]
    report = {
        'scope': 'Top-level entities (body, face without shell, edge without coedge) in slots 1..RootCount-1 versus elsewhere, for the saved state of every .smb/.smbh and for every older journal state',
        'unread_files': unread,
        'current': rows(current),
        'history': rows(history),
    }
    Path(__file__).with_name('RootLists.json').write_text(json.dumps(report, indent=1) + '\n')
    print('current')
    for row in report['current']:
        print(' ', row)
    print('history')
    for row in report['history']:
        print(' ', row)
    print(unread, 'unread')


if __name__ == '__main__':
    main()
