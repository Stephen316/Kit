import collections
import concurrent.futures
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))


def classify(name):
    from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
    from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
    data = (ROOT / name).read_bytes()
    model = ReadDocument(data)
    emitted = EmitParsed(model)
    before = zipfile.ZipFile(io.BytesIO(data))
    after = zipfile.ZipFile(io.BytesIO(emitted))
    prefix = 'FusionAssetName[Active]/'
    rows = []
    for body in model.Bodies:
        member = prefix + body.PartName
        rows.append(('smbh', type(body.History).__name__, before.read(member) == after.read(member)))
    for snap in model.Snapshots:
        member = prefix + snap.Name
        rows.append(('smb', type(snap.Snapshot).__name__, before.read(member) == after.read(member)))
    for mesh in model.Meshes:
        member = prefix + mesh.Name if hasattr(mesh, 'Name') else None
        if member:
            rows.append(('paramesh', type(mesh).__name__, before.read(member) == after.read(member)))
    return name, rows


if __name__ == '__main__':
    report = json.loads(Path(sys.argv[1]).read_text())
    names = [row['file'] for row in report['rows'] if row['status'] == 'pass' and row['file'].endswith('.f3d')]
    counts = collections.Counter()
    samples = collections.defaultdict(list)
    with concurrent.futures.ProcessPoolExecutor(max_workers=10) as pool:
        for name, rows in pool.map(classify, names, chunksize=4):
            for row in rows:
                counts[row] += 1
                if not row[2]:
                    samples[row].append(name)
    for key in sorted(counts):
        print(key, counts[key], samples.get(key, [])[:3])
