import collections
import io
import json
import re
import struct
import sys
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from PackageCensus import designs, tracked

WORLD = 'OGS.BlobFolder/OGS/DefaultScene/world'
ENVIRONMENT = 'RiverRubicon'.encode('utf-16le')
CLASS = re.compile(rb'([\x04-\x60])\x00\x00\x00((?:[A-Za-z0-9_<>]\x00){4,96})')


def versions(world):
    end = world.find(ENVIRONMENT)
    if end < 4:
        return None
    end -= 4
    for start in range(max(0, end - 4096), end):
        count = struct.unpack_from('<I', world, start)[0]
        if not 0 < count <= 64:
            continue
        position = start + 4
        found = []
        try:
            for _ in range(count):
                length = struct.unpack_from('<I', world, position)[0]
                if not 0 < length <= 64:
                    raise ValueError
                name = world[position + 4:position + 4 + 2 * length].decode('utf-16le')
                if not name.isidentifier():
                    raise ValueError
                position += 4 + 2 * length
                found.append((name, struct.unpack_from('<I', world, position)[0]))
                position += 4
        except (ValueError, struct.error, UnicodeError):
            continue
        if position == end:
            return found
    return None


def names(world):
    found = collections.Counter()
    for match in CLASS.finditer(world):
        if match.group(1)[0] * 2 != len(match.group(2)):
            continue
        text = match.group(2).decode('utf-16le')
        if text.endswith(('Attribute', 'Node', 'Mark', 'Qualifier', 'Buffer', 'Format', 'Mesh', 'World', 'List')):
            found[text] += 1
    return dict(found)


def census(name):
    rows = []
    for label, data in designs(name):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                members = {info.filename.split('/', 1)[-1]: info for info in archive.infolist()}
                if WORLD not in members:
                    rows.append({'document': label, 'world': False})
                    continue
                world = archive.read(members[WORLD])
                streams = {key.rsplit('/', 1)[-1]: members[key].file_size for key in members if '/DefaultScene/' in key and '_mesh_' in key}
                rows.append({'document': label, 'world': True, 'versions': versions(world), 'classes': names(world), 'streams': streams})
        except Exception as error:
            rows.append({'document': label, 'error': f'{type(error).__name__}: {error}'[:160]})
    return rows


def main():
    with ProcessPoolExecutor(max_workers=10) as pool:
        rows = [row for group in pool.map(census, tracked()) for row in group]
    lists = collections.Counter()
    places = collections.defaultdict(list)
    classes = collections.Counter()
    users = collections.defaultdict(list)
    for row in rows:
        if not row.get('world'):
            continue
        key = ' '.join(f'{name}={version}' for name, version in sorted(row['versions'] or []))
        lists[key] += 1
        places[key].append(row['document'])
        for name in row['classes']:
            classes[name] += 1
            users[name].append(row['document'])
    rare = {key: places[key][:12] for key, count in lists.items() if count <= 12}
    report = {
        'documents': len(rows),
        'with_world': sum(1 for row in rows if row.get('world')),
        'errors': [row for row in rows if 'error' in row],
        'version_lists': dict(lists.most_common()),
        'rare_version_lists': rare,
        'classes': dict(classes.most_common()),
        'rare_class_users': {name: users[name][:12] for name, count in classes.items() if count <= 12},
    }
    (BASE / 'GraphicsCensus.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({key: report[key] for key in ('documents', 'with_world', 'errors')}))
    print(json.dumps(report['version_lists'], indent=1)[:3000])


if __name__ == '__main__':
    main()
