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
from convert.formats.Fusion.BrepCodec.Journal.Validation.ReadLiveRef import ReadLiveRef
from convert.formats.Fusion.BrepCodec.Journal.Validation.UndoStateMut import UndoStateMut
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import MakeEntityNode
from convert.formats.Fusion.MetaCursor import MetaCursor


def live_tables(path):
    for member, payload in members(path, '.smbh').items():
        model = raw_model(payload)
        records = tuple(MakeEntityNode(value) for value in model.Entities)
        aliases = BuildAliases(model)
        versions = {index: index for index in range(model.ActiveCount)}
        node = model.Stream.ActiveNode
        while node != -1:
            yield 'smbh', {slot: records[revision] for slot, revision in versions.items()}, aliases
            UndoStateMut(model.States[node], versions, aliases)
            node = NextState(model, node)
    for member, payload in members(path, '.smb').items():
        cursor = MetaCursor(payload)
        ReadModelHead(cursor, False)
        records = tuple(MakeEntityNode(value) for value in ReadEntitiesMut(cursor, 'End-of-ASM-data'))
        slots = tuple(range(len(records)))
        yield 'smb', dict(enumerate(records)), slots


# coedge uses per live edge in every saved geometry and every journal state under re/, and the partner ring of edges with more than two uses
def main():
    counts = collections.Counter()
    rings = collections.Counter()
    examples = {}
    unread = 0
    for path in sorted(glob.glob(str(ROOT / 're/**/*.f3d'), recursive=True)):
        try:
            found = list(live_tables(path))
        except Exception:
            unread += 1
            continue
        for kind, table, aliases in found:
            uses = collections.defaultdict(list)
            for slot, record in table.items():
                if record.Name in ('coedge', 'tcoedge-coedge'):
                    uses[ReadLiveRef(record, 6, aliases)].append(slot)
            for slot, record in table.items():
                if record.Name not in ('edge', 'tedge-edge'):
                    continue
                group = uses.get(slot, [])
                counts[(kind, len(group))] += 1
                if len(group) < 3:
                    continue
                order = [group[0]]
                while len(order) < len(group):
                    partner = ReadLiveRef(table[order[-1]], 5, aliases)
                    if partner not in group or partner in order:
                        break
                    order.append(partner)
                closed = len(order) == len(group) and ReadLiveRef(table[order[-1]], 5, aliases) == order[0]
                senses = [table[use].Tokens[7][0] for use in order]
                key = json.dumps({
                    'kind': kind,
                    'uses': len(group),
                    'single_partner_ring': closed,
                    'senses_alternate_along_ring': closed and all(senses[i] != senses[(i + 1) % len(senses)] for i in range(len(senses))),
                    'owner_coedge_is_use': ReadLiveRef(record, 7, aliases) in group,
                    'both_senses': len(set(senses)) == 2,
                }, sort_keys=True)
                rings[key] += 1
                examples.setdefault(key, f'{Path(path).relative_to(ROOT)} {kind} edge {slot}')
    report = {
        'scope': 'Coedge uses per live edge in every .smb and every .smbh journal state under re/, and the partner ring of edges with three or more uses',
        'unread_files': unread,
        'use_counts': [{'kind': kind, 'uses': n, 'edges': count} for (kind, n), count in sorted(counts.items())],
        'rings': [{'count': count, 'example': examples[key], **json.loads(key)} for key, count in rings.most_common()],
    }
    Path(__file__).with_name('UseCycles.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
