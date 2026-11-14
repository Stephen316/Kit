import collections
import io
import json
import re
import subprocess
import sys
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
PART = re.compile(r".*/ProteinAssets\.BlobParts/ProteinAsset\.[A-Fa-f0-9-]{36}\.protein")
LINK = re.compile(rb'<link name="([^"]*)"')
HEX = re.compile(r'[0-9A-Fa-f]{8}-[0-9A-Fa-f-]{27}')
FIELD = re.compile(rb'<(\w+) name="([^"]*)"')
DEPTH = re.compile(r'[^/]+')


def tracked():
    output = subprocess.run(['git', 'ls-files', '-z', '*.f3d', '*.f3z'], cwd=ROOT, capture_output=True, check=True).stdout
    return sorted(name.decode() for name in output.split(b'\0') if name)


def designs(name):
    data = (ROOT / name).read_bytes()
    if name.endswith('.f3z'):
        with zipfile.ZipFile(io.BytesIO(data)) as outer:
            for index, info in enumerate(outer.infolist()):
                if info.filename.lower().endswith('.f3d'):
                    yield f'{name} zip {index}', outer.read(info)
    else:
        yield name, data


def links(inner, member):
    return [item.decode() for item in LINK.findall(inner.read(member))]


def layout(inner, prefix):
    rows = []
    for info in inner.infolist():
        rows.append({
            'name': HEX.sub('<uuid>', info.filename.replace(prefix, '<asset>/', 1)),
            'method': info.compress_type,
            'size': info.file_size,
            'flags': info.flag_bits,
            'extra': len(info.extra),
        })
    return rows


def role(name, prefix):
    if name == 'core.xml':
        return 'root'
    rest = name[len(prefix):]
    parts = rest.split('/')
    if parts[0] == 'core.xml':
        return 'asset'
    if parts[0] == 'Resources':
        return f'Resources depth {len(parts) - 2}'
    return parts[0]


def cores(inner, prefix):
    found = {}
    for name in inner.namelist():
        if name.endswith('core.xml'):
            fields = [item[1].decode() for item in FIELD.findall(inner.read(name)) if item[0] not in (b'node', b'group', b'root')]
            found.setdefault(role(name, prefix), set()).add(','.join(fields))
    return {key: sorted(value) for key, value in found.items()}


def order(inner, prefix):
    kinds = []
    for name in inner.namelist():
        tail = name.rsplit('/', 1)[-1]
        kind = tail if tail in ('core.xml', 'cnx.xml', '[Content_Types].xml', 'autodesk-design-package.xml') else 'data'
        if not kinds or kinds[-1] != kind:
            kinds.append(kind)
    return '>'.join(kinds)


def package(payload):
    with zipfile.ZipFile(io.BytesIO(payload)) as inner:
        top = links(inner, 'cnx.xml')
        prefix = top[0] + '/'
        folders = links(inner, prefix + 'cnx.xml')
        row = {'folders': folders, 'members': len(inner.namelist()), 'cores': cores(inner, prefix), 'order': order(inner, prefix)}
        if 'Resources' in folders:
            row['layout'] = layout(inner, prefix)
        return row


def census(name):
    rows = []
    try:
        for label, data in designs(name):
            with zipfile.ZipFile(io.BytesIO(data)) as outer:
                for info in outer.infolist():
                    if PART.fullmatch(info.filename):
                        rows.append({'document': label, **package(outer.read(info))})
    except Exception as error:
        rows.append({'document': name, 'error': f'{type(error).__name__}: {error}'[:160]})
    return rows


def main():
    with ProcessPoolExecutor(max_workers=10) as pool:
        rows = [row for group in pool.map(census, tracked()) for row in group]
    sets = collections.Counter(','.join(row.get('folders', ['error'])) for row in rows)
    found = [row for row in rows if 'layout' in row]
    shapes = collections.Counter()
    for row in rows:
        for key, value in row.get('cores', {}).items():
            for item in value:
                shapes[f'{key}: {item}'] += 1
    orders = collections.Counter(row.get('order') for row in rows)
    places = collections.defaultdict(collections.Counter)
    for row in rows:
        data = ','.join(row.get('cores', {}).get('AssetData', []))
        places[f"{row.get('order')} | AssetData {data}"]['/'.join(row['document'].split('/')[:4])] += 1
    report = {
        'packages': len(rows),
        'documents': len({row['document'] for row in rows}),
        'folder_sets': dict(sets),
        'errors': [row for row in rows if 'error' in row],
        'core_fields': dict(shapes.most_common()),
        'member_orders': dict(orders.most_common()),
        'order_places': {key: dict(value.most_common()) for key, value in places.items()},
        'resource_packages': [{key: value for key, value in row.items() if key != 'cores'} | {'cores': row['cores']} for row in found],
    }
    (BASE / 'PackageCensus.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'resource_packages'}, indent=1)[:2000])
    print('resource packages', [(row['document'], row['members']) for row in found])


if __name__ == '__main__':
    main()
