import collections
import hashlib
import json
import lzma
import runpy
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
TOKEN = runpy.run_path(str(BASE.parent / 'BrepTokens.py'))


def field(records, identity, index, tag):
    item = records[identity]['fields'][index]
    if item['tag'] != tag:
        raise ValueError('Unexpected field tag')
    return item['value']


def chain(records, first, kind, next_slot):
    values = []
    while first != -1:
        if first in values or not 0 <= first < len(records) or records[first]['name'] != kind:
            raise ValueError('Invalid ownership chain')
        values.append(first)
        first = field(records, first, next_slot, 12)
    return values


def body_summary(records, body):
    lumps = chain(records, field(records, body, 3, 12), 'lump', 3)
    shells = [shell for lump in lumps for shell in chain(records, field(records, lump, 4, 12), 'shell', 3)]
    faces = [face for shell in shells for face in chain(records, field(records, shell, 5, 12), 'face', 3)]
    loops = [loop for face in faces for loop in chain(records, field(records, face, 4, 12), 'loop', 3)]
    edges, vertices, uses = set(), set(), set()
    rings = []
    for loop in loops:
        first = field(records, loop, 4, 12)
        current, ring = first, []
        while True:
            if current in uses or records[current]['name'] != 'coedge':
                raise ValueError('Invalid coedge ring')
            uses.add(current)
            ring.append(current)
            edges.add(field(records, current, 6, 12))
            current = field(records, current, 3, 12)
            if current == first:
                break
        rings.append(len(ring))
    for edge in edges:
        vertices.update((field(records, edge, 3, 12), field(records, edge, 5, 12)))
    surfaces = collections.Counter(records[field(records, face, 7, 12)]['name'] for face in faces)
    curves = collections.Counter(records[field(records, edge, 8, 12)]['name'] for edge in edges)
    points = [field(records, field(records, vertex, 5, 12), 3, 19) for vertex in sorted(vertices)]
    corners = False
    bounds = None
    if points:
        lower = [min(point[axis] for point in points) for axis in range(3)]
        upper = [max(point[axis] for point in points) for axis in range(3)]
        bounds = [lower, upper]
        corner_codes = {tuple(0 if abs(point[axis] - lower[axis]) < 1e-9 else 1 if abs(point[axis] - upper[axis]) < 1e-9 else -1 for axis in range(3)) for point in points}
        corners = len(corner_codes) == 8 and all(-1 not in code for code in corner_codes) and all(b > a for a, b in zip(lower, upper))
    box = len(lumps) == len(shells) == 1 and len(faces) == len(loops) == 6 and len(edges) == 12 and len(vertices) == 8 and rings == [4] * 6 and surfaces == {'plane-surface': 6} and curves == {'straight-curve': 12} and corners
    planar = bool(faces) and set(surfaces) == {'plane-surface'} and set(curves) <= {'straight-curve'}
    return {'bodyOrdinal': body, 'bodyKey': field(records, body, 1, 4), 'transformRef': field(records, body, 5, 12), 'lumps': len(lumps), 'shells': len(shells), 'faces': len(faces), 'loops': len(loops), 'coedges': len(uses), 'edges': len(edges), 'vertices': len(vertices), 'ringLengths': rings, 'surfaces': dict(surfaces), 'curves': dict(curves), 'boundsCm': bounds, 'planarLinearCandidate': planar, 'axisAlignedBoxCandidate': box}


def inspect(data):
    parsed = TOKEN['read_stream'](data)
    initial = []
    for record in parsed['records']:
        if record['boundary_marker'] or record['name'] == 'End-of-ASM-data':
            break
        initial.append(record)
    names = collections.Counter(record['name'] for record in initial)
    attrs = collections.Counter(record['fields'][5]['value'] for record in initial if record['name'] == 'ATTRIB_CUSTOM-attrib' and len(record['fields']) > 5)
    body_rows = []
    for index, record in enumerate(initial):
        if record['name'] == 'body':
            try:
                body_rows.append(body_summary(initial, index))
            except (ValueError, IndexError, KeyError, TypeError) as error:
                body_rows.append({'bodyOrdinal': index, 'topologyUnresolved': repr(error)})
    shape = tuple(sorted((name, count) for name, count in names.items() if not name.endswith('attrib')))
    return {'header': {key: value for key, value in parsed['header'].items() if key != 'tagged_values'}, 'initialRecordCount': len(initial), 'allRecordCount': len(parsed['records']), 'recordTypes': dict(names), 'attributeTypes': dict(attrs), 'historyRecordTypes': dict(collections.Counter(record['name'] for record in parsed['records'][len(initial):])), 'bodies': body_rows, 'signature': str(shape)}


def main():
    inventory_path = BASE.parent / 'CorpusInventory.json'
    inventory = json.loads(inventory_path.read_text())
    cache, members, errors = {}, [], []
    for index, entry in enumerate(inventory['files']):
        with zipfile.ZipFile(ROOT / entry['path']) as archive:
            for name in archive.namelist():
                if not name.lower().endswith(('.smb', '.smbh')):
                    continue
                payload = archive.read(name)
                digest = hashlib.sha256(payload).hexdigest()
                if digest not in cache:
                    try:
                        cache[digest] = inspect(payload)
                    except Exception as error:
                        cache[digest] = {'unresolved': repr(error)}
                result = {'path': entry['path'], 'member': name, 'sha256': digest, 'size': len(payload), 'extension': Path(name).suffix}
                members.append(result)
                if 'unresolved' in cache[digest]:
                    errors.append({**result, 'error': cache[digest]['unresolved']})
        if index % 100 == 0:
            print(json.dumps({'archivesProcessed': index + 1, 'members': len(members), 'uniqueBlobs': len(cache)}), flush=True)
    record_counts, attrs, shapes = collections.Counter(), collections.Counter(), collections.Counter()
    body_counts, body_examples = collections.Counter(), {}
    for member in members:
        result = cache[member['sha256']]
        if 'unresolved' in result:
            continue
        record_counts.update(result['recordTypes'])
        attrs.update(result['attributeTypes'])
        shapes[result['signature']] += 1
        for body in result['bodies']:
            for key in ('axisAlignedBoxCandidate', 'planarLinearCandidate', 'topologyUnresolved'):
                if body.get(key):
                    body_counts[key] += 1
                    body_examples.setdefault(key, {**member, 'body': body})
    detailed = {'schema': 'FusionBrepCorpusInventory/1', 'scope': 'Structural token and ownership inspection, not complete semantic decoding or vendor acceptance; blob bodies include selection caches and historical/current model state', 'inventorySha256': hashlib.sha256(inventory_path.read_bytes()).hexdigest(), 'members': members, 'uniqueBlobs': cache}
    raw = (json.dumps(detailed, separators=(',', ':')) + '\n').encode()
    packed = lzma.compress(raw)
    (BASE / 'Inventory.json.xz').write_bytes(packed)
    summary = {'schema': detailed['schema'], 'scope': detailed['scope'], 'archives': len(inventory['files']), 'archivesWithBrep': len({item['path'] for item in members}), 'members': len(members), 'uniqueBlobCount': len(cache), 'extensions': dict(collections.Counter(member['extension'] for member in members)), 'parseFailures': errors, 'recordTypeCountsIncludingRepeatedBlobs': dict(record_counts.most_common()), 'attributeTypeCountsIncludingRepeatedBlobs': dict(attrs.most_common()), 'bodyCandidateCountsIncludingRepeatedBlobs': dict(body_counts), 'bodyExamples': body_examples, 'mostCommonInitialShapes': [{'signature': shape, 'members': count} for shape, count in shapes.most_common(12)], 'detailArchive': 'Inventory.json.xz', 'uncompressedSha256': hashlib.sha256(raw).hexdigest(), 'compressedSha256': hashlib.sha256(packed).hexdigest()}
    (BASE / 'Summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({key: value for key, value in summary.items() if key not in ('parseFailures', 'bodyExamples', 'mostCommonInitialShapes')}), flush=True)


if __name__ == '__main__':
    main()
