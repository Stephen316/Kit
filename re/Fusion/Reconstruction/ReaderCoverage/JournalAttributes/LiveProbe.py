import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))

import convert.formats.Fusion.BrepCodec.Journal.Validation.CheckLiveRefs as LiveModule
import convert.formats.Fusion.BrepCodec.Journal.Validation.WalkStates as WalkModule
from convert.formats.Fusion.BrepCodec.Journal.Validation.ResolveSlot import ResolveSlot

original = LiveModule.CheckLiveRefs
walk = {'state': 0}


def explain(records, versions, aliases):
    for slot, revision in sorted(versions.items()):
        record = records[revision]
        rules = LiveModule.KEntityRefRules[record.Name]
        for index, (tag, value) in enumerate(record.Tokens):
            if tag != 12:
                continue
            if value == -1:
                if index in LiveModule.KRequiredRefs.get(record.Name, ()):
                    print('   null required', 'slot', slot, 'revision', revision, record.Name, 'index', index, record.Tokens[:12])
                continue
            target = ResolveSlot(aliases, value)
            if target not in versions:
                print('   absent', 'slot', slot, 'revision', revision, record.Name, 'index', index, 'target', target)
            elif index in rules and records[versions[target]].Name not in rules[index]:
                print('   class', 'slot', slot, record.Name, 'index', index, '->', records[versions[target]].Name)


def patched(records, versions, aliases, root_count):
    walk['state'] += 1
    try:
        original(records, versions, aliases, root_count)
    except ValueError as error:
        print('state walk step', walk['state'], 'error', error)
        explain(records, versions, aliases)
        uses = {}
        for slot, revision in versions.items():
            record = records[revision]
            if record.Name in ('coedge', 'tcoedge-coedge'):
                uses.setdefault(ResolveSlot(aliases, record.Tokens[6][1]), []).append(slot)
        for edge, slots in uses.items():
            if len(slots) > 2:
                print('   edge', edge, records[versions[edge]].Name, 'uses', slots, [records[versions[slot]].Tokens[8] for slot in slots])
        raise


WalkModule.CheckLiveRefs = patched

from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal

for name in zipfile.ZipFile(ROOT / sys.argv[1]).namelist():
    if name.endswith('.smbh'):
        walk['state'] = 0
        print('==', name)
        try:
            ReadJournal(zipfile.ZipFile(ROOT / sys.argv[1]).read(name))
            print('   ok')
        except ValueError as error:
            print('   failed', error)
