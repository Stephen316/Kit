import collections
import concurrent.futures
import hashlib
import io
import json
import sys
import traceback
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))


def members(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {info.filename: archive.read(info.filename) for info in archive.infolist() if not info.filename.endswith('/')}


def where(error):
    frames = traceback.extract_tb(error.__traceback__)
    return ' <- '.join(f'{Path(f.filename).stem}:{f.lineno}' for f in reversed(frames[-6:]))


def document(data):
    from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
    from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
    row = {}
    try:
        model = ReadDocument(data)
    except Exception as error:
        return {'status': 'read', 'error': f'{type(error).__name__}: {error}', 'where': where(error)}
    try:
        emitted = EmitParsed(model)
        again = ReadDocument(emitted)
    except Exception as error:
        return {'status': 'emit', 'error': f'{type(error).__name__}: {error}', 'where': where(error)}
    before, after = members(data), members(emitted)
    differing = sorted(name for name in set(before) | set(after) if before.get(name) != after.get(name))
    row.update({
        'model_equal': again == model,
        'members': len(before),
        'differing': differing,
        'emitted_sha256': hashlib.sha256(emitted).hexdigest(),
    })
    row['status'] = 'pass' if row['model_equal'] else 'model'
    return row


def verify(path):
    data = path.read_bytes()
    row = {'file': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    if path.suffix.lower() == '.f3z':
        from convert.formats.Fusion.BundleCodec.EmitBundle import EmitBundle
        from convert.formats.Fusion.BundleCodec.ReadBundle import ReadBundle
        try:
            bundle = ReadBundle(data)
            again = ReadBundle(EmitBundle(bundle))
            row['bundle_equal'] = again == bundle
        except Exception as error:
            row.update({'status': 'read', 'error': f'{type(error).__name__}: {error}', 'where': where(error)})
            return row
        children = []
        for entry in bundle.Documents:
            if entry.FileName.lower().endswith('.f3d'):
                child = document(entry.DataValue)
                child['member'] = entry.FileName
                children.append(child)
        row['children'] = children
        bad = [child for child in children if child['status'] != 'pass']
        row['status'] = 'pass' if not bad and row['bundle_equal'] else (bad[0]['status'] if bad else 'model')
        if bad:
            row['error'] = bad[0].get('error', 'model')
        return row
    row.update(document(data))
    return row


def collect(patterns):
    found = []
    for pattern in patterns:
        found.extend(path for path in ROOT.glob(pattern) if path.is_file())
    return sorted(set(found))


def classify(error):
    text = error.split(': ', 1)[-1]
    return text if len(text) < 90 else text[:90]


def main():
    scope = sys.argv[1] if len(sys.argv) > 1 else 'all'
    target = Path(sys.argv[2]) if len(sys.argv) > 2 else BASE / f'Census-{scope}.json'
    if scope == 'vendor':
        paths = collect(['re/Fusion/LocalOracle/**/vendor_*.f3d'])
    elif scope == 'all':
        paths = collect(['re/**/*.f3d', 're/**/*.f3z', 'examples/**/*.f3d', 'examples/**/*.f3z', 're/**/*.F3D', 'examples/**/*.F3D'])
    else:
        paths = collect(scope.split(','))
    with concurrent.futures.ProcessPoolExecutor(max_workers=10) as pool:
        rows = list(pool.map(verify, paths, chunksize=2))
    counts = collections.Counter(row['status'] for row in rows)
    causes = collections.Counter(classify(row['error']) for row in rows if 'error' in row)
    report = {'scope': scope, 'python': sys.version.split()[0], 'files': len(rows), 'counts': dict(counts), 'causes': dict(causes.most_common()), 'rows': rows}
    target.write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({'files': len(rows), 'counts': dict(counts)}, indent=1))
    for cause, count in causes.most_common():
        print(count, cause)


if __name__ == '__main__':
    main()
