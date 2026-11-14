import collections
import io
import struct
import sys
import traceback
import zipfile
from math import isfinite
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE))
sys.setrecursionlimit(20000)

from ExampleRecords import documents
import convert.formats.Fusion.Topology.AsmEdge.AsmTable as Table
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
import convert.formats.Fusion.BrepCodec.Journal.ReadJournal as JournalModule
import convert.formats.Fusion.BrepCodec.Journal.Reading.ReadModelHead as Head
import convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntitiesMut as Entities

WIDTH = [8]
STATS = []
LONGEST = [0]
STEP = ['read']
HEADS = collections.Counter()
original = Table.ReadAsmToken


def token(cursor):
    if WIDTH[0] == 8:
        return original(cursor)
    tag = cursor.TakeBytes(1)[0]
    if tag in (4, 12, 21, 23):
        return tag, struct.unpack('<i', cursor.TakeBytes(4))[0]
    if tag == 18:
        size = struct.unpack('<i', cursor.TakeBytes(4))[0]
        return tag, cursor.TakeBytes(size)
    cursor.Offset -= 1
    return original(cursor)


def record(cursor, name, *rest):
    start = len(TOKENS)
    found = RECORD(cursor, name)
    LONGEST[0] = max(LONGEST[0], len(found.Tokens))
    return found


TOKENS = []
RECORD = Table.ReadAsmRecord


def patch():
    Table.KRecordTokens = 1 << 22
    import convert.formats.Fusion.BrepCodec.Journal.Reading.ReadStatesMut as States
    States.ReadAsmRecord = record
    for name, module in list(sys.modules.items()):
        if name.startswith('convert.') and getattr(module, 'ReadAsmToken', None) is original:
            module.ReadAsmToken = token
    source = Head.ReadModelHead

    def head(cursor, history):
        data = cursor.DataValue
        if data[cursor.Offset:cursor.Offset + 15] != b'ASM BinaryFile4':
            WIDTH[0] = 8
            return source(cursor, history)
        WIDTH[0] = 4
        cursor.TakeBytes(15)
        version, stored, roots, flags = struct.unpack('<4i', cursor.TakeBytes(16))
        strings = [token(cursor)[1] for _ in range(3)]
        numbers = [token(cursor)[1] for _ in range(3)]
        header = Head.BrepHeader(version, roots, flags, *numbers)
        HEADS[(header, stored)] += 1
        return header, Head.GeometryStamp(*strings)

    Head.ReadModelHead = head
    JournalModule.ReadModelHead = head


def journal(payload):
    module = JournalModule
    cursor = module.MetaCursor(payload)
    header, stamp = module.ReadModelHead(cursor, True)
    active = entities(cursor, 'Begin-of-ASM-History-Data')
    stream = module.ReadStreamNode(module.ReadAsmRecord(cursor, module.ReadAsmName(cursor)))
    states = module.ReadStatesMut(cursor)
    archived = entities(cursor, 'End-of-ASM-data')
    if cursor.Offset != len(payload):
        raise ValueError('Trailing Fusion journal bytes')
    model = module.JournalModel(header, stamp, len(active), active + archived, stream, states)
    STATS.append((len(payload), len(model.Entities), len(states), header.RootCount))
    check(model)
    module.WalkStates(model)


def entities(cursor, end):
    found = []
    while (name := Table.ReadAsmName(cursor)) != end:
        found.append(Entities.ReadEntityNode(record(cursor, name)))
    return tuple(found)


def check(model):
    from convert.formats.Fusion.BrepCodec.Journal.Validation import CheckJournal as source
    if source.CountRoots(model.Entities[: model.ActiveCount]) != model.Header.RootCount - 1:
        raise ValueError('Fusion journal active bodies disagree with its root count')
    for name in ('CheckStream', 'CheckStates', 'CheckAllocTags'):
        STEP[0] = name
        getattr(source, name)(model)
    STEP[0] = 'CheckNode'
    for entity in model.Entities:
        source.CheckNode(entity)
    STEP[0] = 'CheckSubtypes'
    source.CheckSubtypes(model.Entities)
    STEP[0] = 'CheckComplex'
    source.CheckComplex(model.Entities)
    STEP[0] = 'States'
    for state in model.States:
        source.EmitWireRecord(source.MakeStateNode(state))
    STEP[0] = 'walk'


def main():
    import convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntitiesMut  # noqa
    patch()
    causes = collections.Counter()
    for name, data in documents():
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for member in archive.namelist():
                if not member.endswith('.smbh'):
                    continue
                payload = archive.read(member)
                try:
                    STEP[0] = 'read'
                    journal(payload)
                    causes[('pass',)] += 1
                except Exception as error:
                    frames = traceback.extract_tb(error.__traceback__)
                    where = ' <- '.join(f'{Path(f.filename).stem}:{f.lineno}' for f in reversed(frames[-3:]))
                    causes[(STEP[0], str(error)[:60], where)] += 1
    print('max bytes, entities, states, roots', [max(row[index] for row in STATS) for index in range(4)], 'longest record', LONGEST[0])
    for key, count in causes.most_common(20):
        print(count, *key)


if __name__ == '__main__':
    main()
