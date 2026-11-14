import collections
import concurrent.futures
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE))


def shapes(name):
    import convert.formats.Fusion.BrepCodec.Journal.Round.ReadTorusNode as Module
    from convert.formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode
    from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
    seen = []
    check = Module.CheckRoundNode

    def spy(value):
        if isinstance(value, TorusNode):
            seen.append((value.MajorRadiusCm, value.MinorRadiusCm))
        check(value)

    Module.CheckRoundNode = spy
    data = (ROOT / name).read_bytes()
    payloads = [data]
    if name.endswith('.f3z'):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            payloads = [archive.read(item) for item in archive.namelist() if item.endswith('.f3d')]
    error = None
    for payload in payloads:
        try:
            ReadDocument(payload)
        except Exception as caught:
            error = str(caught)[:80]
    return name, seen, error


def kind(major, minor):
    if abs(minor) < major:
        return 'ring, minor positive' if minor > 0 else 'ring, minor negative'
    if abs(minor) == major:
        return 'horn'
    return 'apple, minor positive' if minor > 0 else 'lemon, minor negative'


def main():
    from Sweep import tracked
    names = tracked()
    rows = collections.Counter()
    files = collections.defaultdict(set)
    with concurrent.futures.ProcessPoolExecutor(max_workers=10) as pool:
        for name, seen, error in pool.map(shapes, names, chunksize=4):
            for major, minor in seen:
                label = kind(major, minor)
                rows[label] += 1
                files[label].add(name)
    report = {
        'scope': 'Torus carriers that the journal reader decodes in every tracked Fusion file',
        'records': dict(rows),
        'files': {label: len(value) for label, value in files.items()},
        'apple_or_lemon_files': sorted(files['apple, minor positive'] | files['lemon, minor negative']),
    }
    (BASE / 'TorusCensus.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
