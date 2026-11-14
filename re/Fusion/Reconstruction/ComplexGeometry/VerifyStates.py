import collections
import json
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.BrepCodec.Journal.EmitStateSmb import EmitStateSmb  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.ComplexEntity import KComplexTypes  # noqa: E402


def classify(path):
    with zipfile.ZipFile(ROOT / path) as archive:
        names = [name for name in archive.namelist() if name.endswith(('.smb', '.smbh'))]
        histories = [name for name in names if name.endswith('.smbh')]
        snapshots = [name for name in names if name.endswith('.smb')]
        if len(histories) != 1 or len(snapshots) != 1:
            return 'not-paired', None
        journal = ReadJournal(archive.read(histories[0]))
        snapshot = ReadGeometry(archive.read(snapshots[0]))
    state = ReadGeometry(EmitStateSmb(journal))
    complex_count = sum(isinstance(value, KComplexTypes) for value in state.Entities)
    archived = len(journal.Entities) - journal.ActiveCount
    if state.Entities == snapshot.Entities:
        return 'valid-equal', dict(complex=complex_count, archived=archived)
    return 'valid-differs-from-snapshot', dict(complex=complex_count, archived=archived, state=len(state.Entities), snapshot=len(snapshot.Entities))


def main():
    verify = json.loads((HERE / 'VerifyComplex.json').read_text())
    paths = sorted({item['path'] for item in verify['members'] if item.get('exact') and item['member'].endswith('.smbh')})
    counts = collections.Counter()
    rows = []
    for path in paths:
        try:
            status, detail = classify(path)
        except ValueError as error:
            status, detail = 'error', str(error)
        counts[status] += 1
        rows.append(dict(path=path, status=status, detail=detail))
        print(status, path, detail, flush=True)
    (HERE / 'VerifyStates.json').write_text(json.dumps(dict(summary=dict(counts), archives=rows), indent=1) + '\n')
    print(dict(counts))


if __name__ == '__main__':
    main()
