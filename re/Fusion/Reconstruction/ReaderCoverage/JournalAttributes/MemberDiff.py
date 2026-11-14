import io
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ProbeFailures import records


def members(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {info.filename: archive.read(info.filename) for info in archive.infolist() if not info.filename.endswith('/')}


def emitted(path):
    from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
    from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
    data = (ROOT / path).read_bytes()
    return members(data), members(EmitParsed(ReadDocument(data)))


def table(payload, history):
    return [(kind, record.Tokens if record is not None else None) for index, kind, record in records(payload, history)]


if __name__ == '__main__':
    before, after = emitted(sys.argv[1])
    for name in sorted(before):
        if before[name] == after.get(name) or not name.endswith(('.smb', '.smbh')):
            continue
        history = name.endswith('.smbh')
        old, new = table(before[name], history), table(after[name], history)
        print('==', name, len(before[name]), len(after[name]), len(old), len(new))
        print('   head', before[name][:64] == after[name][:64])
        shown = 0
        for index, (left, right) in enumerate(zip(old, new)):
            if left != right and shown < 6:
                print('   ', index, left[0], left[1])
                print('   ', index, right[0], right[1])
                shown += 1
