"""Focused sketch payload replays, reciprocal topology and legacy dictionaries."""

import argparse
from collections import Counter
import copy
import json
from pathlib import Path

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags
from decode_basics import decode_basics
from decode_brep import decode_topology
from decode_sketch_attributes import decode_sketch_attribute
from fusion_archive import read_members

ROOT = Path(__file__).resolve().parent
FILES = ['advanced-627f7fe095f4/advanced.f3d'] + ['loftbrepends-e07e3859ed20/'+name+'.f3d' for name in
         ('edge_start_free', 'face_end_free', 'edge_end_tangent_weight1_5', 'edge_end_smooth_weight1_25', 'edge_both_tangent')]
INVENTORY = {'archives': 559, 'blobs': 959, 'initial_sketch_attributes': 17175,
             'owner_counts': {'coedge': 13172, 'edge': 3969, 'vertex': 34},
             'observed_payloads': 'Every record10 tokens, schema integer[1,1,3], six space-separated text fields; ASCII-decimal grammar and actual payload replay independently checked in focused sample',
             'observed_headers': 'Every record pointer0=-1, integer1=-1; no relaxed header variant needed',
             'provenance': 'Read-only initial ASM record census of committed fusion-class-catalog.json file list; no whole-model reader run; 4.98 seconds. Focused payload/owner checks below are independently repeatable.'}


def owner_chain(record, parsed):
    records = parsed['records']; limit = next((r['index'] for r in records if r['record_kind'] == 'marker'), len(records))
    assert all(r['index'] == index and r['section'] == 'geometry' for index, r in enumerate(records[:limit]))
    def pointer(token, nullable=False):
        assert token['kind'] == 'pointer' and token['tag'] == 12
        value = token['value']
        assert type(value) is int and (nullable and value == -1 or 0 <= value < limit)
        return value
    owner_id = pointer(record['tokens'][4]); owner = records[owner_id]
    assert owner['name'] in ('coedge', 'edge', 'vertex')
    current = pointer(owner['tokens'][0], True); previous = -1; chain = []
    while current != -1:
        assert current not in chain and len(chain) < 128
        chain.append(current); attribute = records[current]; t = attribute['tokens']
        assert attribute['name'] == 'ATTRIB_CUSTOM-attrib'
        assert pointer(t[0], True) == -1 and t[1]['kind'] == 'integer' and t[1]['value'] == -1
        assert pointer(t[3], True) == previous and pointer(t[4]) == owner_id
        previous, current = current, pointer(t[2], True)
    assert record['index'] in chain
    return owner_id, chain


def typed_source(owner_id, nodes):
    owner = nodes[owner_id]; kind = owner['kind']; result = {'owner_kind': kind, 'owner_index': owner_id}
    if kind == 'coedge':
        edge = nodes[owner['edge_index']]
        nxt, prev = nodes[owner['next_coedge_index']], nodes[owner['previous_coedge_index']]
        assert edge['kind'] == 'edge' and nxt['previous_coedge_index'] == owner_id and prev['next_coedge_index'] == owner_id
        result.update(edge_index=edge['index'], next_coedge_index=nxt['index'], previous_coedge_index=prev['index'])
    elif kind == 'edge':
        edge = owner
        first = edge['first_coedge_index']
        if first is not None:
            assert nodes[first]['kind'] == 'coedge' and nodes[first]['edge_index'] == owner_id
        result['first_coedge_index'] = first
    else:
        edge = nodes[owner['first_edge_index']]
        assert edge['kind'] == 'edge' and owner_id in (edge['start_vertex_index'], edge['end_vertex_index'])
        point = nodes[owner['point_index']]; assert point['kind'] == 'point'
        result.update(first_edge_index=edge['index'], point_index=point['index'], raw_point=point['raw_origin'])
    curve_id = edge['curve_index']; curve = nodes[curve_id]
    assert curve['kind'].endswith('-curve')
    result.update(curve_index=curve_id, curve_kind=curve['kind'], edge_vertex_indices=[edge['start_vertex_index'], edge['end_vertex_index']])
    if kind == 'edge':
        result['raw_endpoint_positions'] = [nodes[nodes[v]['point_index']]['raw_origin'] for v in result['edge_vertex_indices']]
    return result


def validate(zstd_library):
    report = {'scope': 'Focused six-archive replay and reciprocal topology checks; saved census17175 attributes only inventories framing, not a full-main audit',
              'integration': {'function': 'decode_sketch_attributes.decode_sketch_attribute(record)',
                              'caller': 'Shared generic reader retains initial prefix/index checks, typed COEDGE/EDGE/VERTEX owner and reciprocal chain, then compares payload_hex against original blob. Existing dictionary shape/text preserved exactly.',
                              'validation_command': '/usr/bin/python3 validate_sketch_attributes.py'},
              'inventory': INVENTORY, 'files': [], 'representatives': [], 'saved_API_contexts': [], 'guards': [],
              'limitations': ['Six decimal substrings remain opaque strings, not native sketch/entity IDs or interpreted flags.',
                              'Typed topology ownership establishes source-cache provenance only; it does not establish native sketch identity, current/final visibility, or selected source closure.',
                              'Pure payload helper intentionally does not validate owner/header/initial scope; the production caller owns those checks.',
                              'Saved API sketch names and native sketches are independent context controls, not attribute text-to-sketch mappings.',
                              'No solver, geometry regeneration, live capture or global history-pointer conversion is performed.']}
    counts = Counter(); legacy_count = 0; candidates = []; contexts = {}
    for relative in FILES:
        local = Counter(); members = read_members(ROOT/relative, zstd_library)
        for member, raw in members.items():
            if not member.endswith(('.smb', '.smbh')): continue
            parsed = inspect_asm(raw); assert parsed['complete_token_stream']
            shared = decode_asm_generic_tags(raw, parsed, allow_fpm_tracking=True)
            recognized = {r['attribute_record_index']: r for r in shared['ignored_validated_other_definition_attributes']}
            topology = decode_topology(parsed); nodes = {n['index']: n for n in topology['nodes']}
            seen = set()
            for record in parsed['records']:
                t = record['tokens']
                if record['section'] != 'geometry' or record['name'] != 'ATTRIB_CUSTOM-attrib' or len(t) < 6 or t[5]['value'] != 'sketch_attrib_def': continue
                payload = decode_sketch_attribute(record)
                assert bytes.fromhex(payload['payload_hex']) == raw[payload['payload_offset']:payload['payload_end_offset']]
                owner, chain = owner_chain(record, parsed); kind = parsed['records'][owner]['name']
                source = typed_source(owner, nodes)
                expected = {'attribute_record_index': record['index'], 'definition_name': 'sketch_attrib_def',
                            'owner_record_index': owner, 'owner_kind': kind, 'uninterpreted_text': t[9]['value']}
                assert recognized[record['index']] == expected
                assert not any(r['attribute_record_index'] == record['index'] for r in shared['unresolved'])
                counts[kind] += 1; local[kind] += 1; legacy_count += kind == 'coedge'
                candidates.append((raw, parsed, record))
                if kind not in seen:
                    seen.add(kind)
                    report['representatives'].append({'file': relative, 'member': member, 'record_index': record['index'],
                        'expected_payload': payload, 'expected_shared_dictionary': expected,
                        'reciprocal_attribute_chain': chain, 'typed_source': source,
                        'body_graph_memberships': [g['body_index'] for g in topology['body_graphs'] if owner in g.get(kind+'_indices', [])]})
        report['files'].append({'file': relative, 'validated_owner_counts': dict(local)})
    # Independent native/API contexts deliberately do not use any sketch text field.
    for relative in [FILES[0], FILES[-1]]:
        model = decode_basics(ROOT/relative, zstd_library); features = model['streams'][0]['features']
        sketches = [f for f in features if f['kind'] == 'Sketch']
        truth = json.loads((ROOT/Path(relative).parent/'ground_truth.json').read_text())
        if 'sketches' in truth:
            names = [s['name'] for s in truth['sketches']]
            assert set(names) <= {s['name'] for s in sketches}
        else:
            sample = next(s for s in truth['samples'] if s['file'] == Path(relative).name)
            names = [s['sketch_name'] for s in sample['source_entities_before_loft'] if 'sketch_name' in s]
            assert set(names) <= {s['name'] for s in sketches}
        report['saved_API_contexts'].append({'file': relative, 'saved_API_sketch_names': names,
            'native_sketches': [{'name': s['name'], 'sketch_object_id': s['sketch_object_id'],
                                 'entity_object_ids': [g['object_id'] for g in s.get('geometry', [])]} for s in sketches],
            'source_identity_scope': 'Native entity-to-sketch references decoded independently by sketch reader; no mapping from attribute text numbers'})
    raw, parsed, original = next(c for c in candidates if c[1]['records'][c[2]['tokens'][4]['value']]['name'] == 'vertex')
    def rejected(label, mutate):
        bad = copy.deepcopy(original); mutate(bad)
        try: decode_sketch_attribute(bad)
        except (ValueError, KeyError, IndexError, TypeError): report['guards'].append({'case': label, 'rejected': True}); return
        raise AssertionError('accepted malformed '+label)
    rejected('signed decimal field', lambda r: r['tokens'][9].update(value='-6 0 1 0 1 1'))
    rejected('multiple spaces', lambda r: r['tokens'][9].update(value='6  0 1 0 1 1'))
    rejected('unobserved schema', lambda r: r['tokens'][8].update(value=2))
    rejected('text token wrong typed kind', lambda r: r['tokens'][9].update(kind='literal', tag=18))
    rejected('unconsumed payload trailer', lambda r: r.update(end_offset=r['end_offset']+1))
    rejected('noncontiguous typed payload offsets', lambda r: r['tokens'][7].update(offset=r['tokens'][7]['offset']+1))
    # Pure payload remains valid; production owner proof must reject wrong ownership.
    badparsed = copy.deepcopy(parsed); badrecord = badparsed['records'][original['index']]
    other = next(r for r in badparsed['records'] if r['section'] == 'geometry' and r['name'] == 'vertex' and r['index'] != original['tokens'][4]['value'])
    badrecord['tokens'][4]['value'] = other['index']
    assert decode_sketch_attribute(badrecord) == decode_sketch_attribute(original)
    shared = decode_asm_generic_tags(raw, badparsed, allow_fpm_tracking=True)
    assert any(r['attribute_record_index'] == original['index'] for r in shared['unresolved'])
    assert not any(r['attribute_record_index'] == original['index'] for r in shared['ignored_validated_other_definition_attributes'])
    report['guards'].append({'case': 'valid payload claimed by different typed VERTEX outside reciprocal owner chain', 'rejected_by_production_caller': True, 'pure_payload_unchanged': True})
    report['summary'] = {'archives': len(FILES), 'payload_replays': sum(counts.values()), 'owner_counts': dict(counts),
                         'typed_source_checks': sum(counts.values()), 'production_dictionary_exact_matches': sum(counts.values()),
                         'preserved_legacy_COEDGE_dictionaries': legacy_count, 'guards': len(report['guards']),
                         'saved_API_contexts': len(report['saved_API_contexts'])}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--zstd-library'); parser.add_argument('--output', default='sketch-attribute-decoding.json')
    args = parser.parse_args(); library = args.zstd_library
    if library is None:
        library = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report = validate(library); Path(args.output).write_text(json.dumps(report, indent=2)+'\n'); print(json.dumps(report['summary'], indent=2))
