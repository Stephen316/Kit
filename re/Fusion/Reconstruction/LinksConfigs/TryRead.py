import io
import sys
import traceback
import zipfile
from pathlib import Path

repository = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repository / 'src'))

from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument


def payloads(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {info.filename: archive.read(info.filename) for info in archive.infolist()}


for name in sys.argv[1:]:
    data = Path(name).read_bytes()
    try:
        model = ReadDocument(data)
        output = EmitParsed(model)
        again = ReadDocument(output)
        source, emitted = payloads(data), payloads(output)
        differ = sorted(key for key in set(source) | set(emitted) if source.get(key) != emitted.get(key))
        print(Path(name).name, 'OK', len(data), len(output), 'model', again == model, 'members', len(source), 'differ', differ)
    except Exception as error:
        frames = traceback.extract_tb(error.__traceback__)
        where = ' <- '.join(f'{Path(f.filename).stem}:{f.lineno}' for f in frames[-4:])
        print(Path(name).name, 'FAIL', type(error).__name__, error, '|', where)
