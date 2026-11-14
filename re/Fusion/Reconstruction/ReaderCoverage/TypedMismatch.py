import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))

import convert.formats.Fusion.BrepCodec.Frustum.ReadFrustumHist as FrustumModule
import convert.formats.Fusion.BrepCodec.Prism.ReadPrismHist as PrismModule
import convert.formats.Fusion.BrepCodec.ReadHistory as HistoryModule
import convert.formats.Fusion.BrepCodec.ReadSnapshot as SnapshotModule
from convert.formats.Fusion.DocumentCodec.Reading.PickBodyView import PickBodyView
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal

found = []


def check(expected, actual, mapping):
    for ordinal, wanted in enumerate(expected):
        stored = actual.Records[mapping[ordinal]]
        for index, (left, right) in enumerate(zip(wanted.Tokens, stored.Tokens)):
            if left[0] != 12 and left != right:
                found.append((ordinal, wanted.Name, index, left, right))


for module in (FrustumModule, PrismModule, HistoryModule, SnapshotModule):
    module.CheckTopology = check

readers = {'.smbh': {'cylinder': HistoryModule.ReadHistory, 'frustum': FrustumModule.ReadFrustumHist, 'prism': PrismModule.ReadPrismHist}}

for name in sys.argv[1:]:
    archive = zipfile.ZipFile(name)
    for member in archive.namelist():
        payload = archive.read(member)
        if member.endswith('.smbh'):
            view = PickBodyView(ReadJournal(payload))
            reader = readers['.smbh'].get(view)
        elif member.endswith('.smb'):
            view = 'snapshot'
            reader = SnapshotModule.ReadSnapshot
        else:
            continue
        if reader is None:
            continue
        found.clear()
        try:
            reader(payload)
            status = 'ok'
        except Exception as error:
            status = f'{type(error).__name__}: {error}'
        if found or status != 'ok':
            print(Path(name).parent.name + '/' + Path(name).name, member[-12:], view, status)
            for row in found:
                print('   ', row)
