import glob
import hashlib
import io
import json
import sys
import traceback
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument


def members(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {info.filename: archive.read(info.filename) for info in archive.infolist() if not info.filename.endswith('/')}


def folders(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return sorted(info.filename for info in archive.infolist() if info.filename.endswith('/'))


def verify(path):
    data = path.read_bytes()
    row = {'file': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest()}
    try:
        model = ReadDocument(data)
        emitted = EmitParsed(model)
        again = ReadDocument(emitted)
        before = members(data)
        after = members(emitted)
        differing = sorted(name for name in before if after.get(name) != before[name])
        canonical = [name for name in differing if name.endswith('.protein')]
        changed = [name for name in differing if not name.endswith('.protein')]
        row.update({
            'model_equal': again == model,
            'member_names_equal': sorted(before) == sorted(after),
            'members': len(before),
            'members_byte_equal': len(before) - len(changed),
            'changed_members': changed,
            'canonicalized_material_packages': canonical,
            'extra_members': sorted(set(after) - set(before)),
            'folders_equal': folders(data) == folders(emitted),
            'forms': len(model.Forms),
            'bodies': len(model.Bodies),
            'snapshots': len(model.Snapshots),
            'emitted_sha256': hashlib.sha256(emitted).hexdigest(),
        })
        row['status'] = 'pass' if row['model_equal'] and not changed and row['member_names_equal'] else 'fail'
    except Exception as error:
        row['status'] = 'error'
        row['error'] = '%s: %s' % (type(error).__name__, error)
        row['traceback'] = traceback.format_exc().replace(str(ROOT), '<repo>')
    return row


def main(pattern):
    rows = [verify(Path(path)) for path in sorted(glob.glob(str(ROOT / pattern)))]
    report = {
        'scope': 'Production ReadDocument and EmitParsed over local Form archives; member-level byte comparison after decompression',
        'material_note': 'Existing production material emission rewrites .protein packages canonically; they are listed separately and excluded from the byte gate',
        'python': sys.version.split()[0],
        'archives': len(rows),
        'passed': sum(row['status'] == 'pass' for row in rows),
        'rows': rows,
    }
    target = BASE / 'RoundTrip.json'
    target.write_text(json.dumps(report, indent=2) + '\n')
    for row in rows:
        print(row['status'], Path(row['file']).name, row.get('error', ''), row.get('changed_members', ''))
    print('passed', report['passed'], 'of', report['archives'])


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 're/Fusion/LocalOracle/TSplineCodec/*.f3d')
