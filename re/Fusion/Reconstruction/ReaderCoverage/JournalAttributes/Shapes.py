import collections
import glob
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ProbeFailures import records


def corpus():
    paths = sorted(set(glob.glob(str(ROOT / 're/**/*.f3d'), recursive=True)) | set(glob.glob(str(ROOT / 'examples/**/*.f3d'), recursive=True)))
    for path in paths:
        try:
            archive = zipfile.ZipFile(path)
        except Exception:
            continue
        for name in archive.namelist():
            if name.endswith('.smbh') or name.endswith('.smb'):
                yield path, name, archive.read(name)


def matching(predicate):
    for path, name, payload in corpus():
        try:
            for index, kind, record in records(payload, name.endswith('.smbh')):
                if record is not None and predicate(kind, record):
                    yield path, name, index, record
        except Exception:
            continue


if __name__ == '__main__':
    target = sys.argv[1]
    family = sys.argv[2] if len(sys.argv) > 2 else None
    shapes = collections.Counter()
    sample = {}
    files = collections.defaultdict(set)
    for path, name, index, record in matching(lambda kind, record: kind == target and (family is None or (len(record.Tokens) > 5 and record.Tokens[5] == (7, family)))):
        shape = tuple(tag for tag, _ in record.Tokens)
        shapes[shape] += 1
        files[shape].add(str(Path(path).relative_to(ROOT)))
        sample.setdefault(shape, []).append(record.Tokens)
    for shape, count in shapes.most_common():
        print(count, 'files', len(files[shape]), shape)
        for tokens in sample[shape][:3]:
            print('    ', tokens)
        print('    e.g.', sorted(files[shape])[:3])
