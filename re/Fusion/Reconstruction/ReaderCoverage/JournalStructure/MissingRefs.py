import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).parent))

from Journals import members, raw_model
from Scope import scope
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntitiesMut import ReadEntitiesMut
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadModelHead import ReadModelHead
from convert.formats.Fusion.BrepCodec.Journal.Validation.BuildAliases import BuildAliases
from convert.formats.Fusion.BrepCodec.Journal.Validation.HasVertedge import HasVertedge
from convert.formats.Fusion.BrepCodec.Journal.Validation.NextState import NextState
from convert.formats.Fusion.BrepCodec.Journal.Validation.RequiredRefs import KRequiredRefs
from convert.formats.Fusion.BrepCodec.Journal.Validation.ResolveSlot import ResolveSlot
from convert.formats.Fusion.BrepCodec.Journal.Validation.UndoStateMut import UndoStateMut
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import MakeEntityNode
from convert.formats.Fusion.MetaCursor import MetaCursor


# every live record whose required reference slot is -1, with the owning chain around it
def missing(records, versions, aliases):
    found = []
    for slot, revision in versions.items():
        record = records[revision]
        for index, (tag, value) in enumerate(record.Tokens):
            if tag != 12 or value != -1:
                continue
            if index not in KRequiredRefs.get(record.Name, ()):
                continue
            if index == 3 and HasVertedge(records, versions, aliases, record):
                continue
            found.append({'slot': slot, 'name': record.Name, 'index': index, 'tokens': [list(token) for token in record.Tokens[:12]]})
    return found


def journal(payload):
    model = raw_model(payload)
    aliases = BuildAliases(model)
    records = tuple(MakeEntityNode(value) for value in model.Entities)
    versions = {index: index for index in range(model.ActiveCount)}
    current = model.Stream.ActiveNode
    rows = []
    while current != -1:
        state = model.States[current]
        for row in missing(records, versions, aliases):
            row['state_id'] = state.StateId
            rows.append(row)
        UndoStateMut(state, versions, aliases)
        current = NextState(model, current)
    return rows


def geometry(payload):
    cursor = MetaCursor(payload)
    ReadModelHead(cursor, False)
    entities = ReadEntitiesMut(cursor, 'End-of-ASM-data')
    records = tuple(MakeEntityNode(value) for value in entities)
    slots = tuple(range(len(records)))
    return missing(records, {index: index for index in slots}, slots)


def main():
    report = {}
    kinds = collections.Counter()
    for name, cause in sorted(scope(sys.argv[1]).items()):
        if cause != 'Missing required Fusion topology reference':
            continue
        path = ROOT / name
        entry = {}
        for member, payload in members(path, '.smbh').items():
            try:
                entry[member] = journal(payload)
            except Exception as error:
                entry[member] = f'{type(error).__name__}: {error}'
        for member, payload in members(path, '.smb').items():
            try:
                entry[member] = geometry(payload)
            except Exception as error:
                entry[member] = f'{type(error).__name__}: {error}'
        for member, rows in entry.items():
            if isinstance(rows, list):
                for row in rows:
                    kinds[(member.rsplit('.', 1)[-1], row['name'], row['index'])] += 1
        report[name] = {member: rows for member, rows in entry.items() if rows}
    out = {'kinds': {' '.join(map(str, key)): value for key, value in kinds.most_common()}, 'files': report}
    Path(__file__).with_name('MissingRefs.json').write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps(out['kinds'], indent=1))


if __name__ == '__main__':
    main()
