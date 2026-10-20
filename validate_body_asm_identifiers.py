"""Focused saved-file controls for the observed per-blob BODY identifier join."""

import argparse
import copy
import json
import math
from pathlib import Path
import struct
import uuid

from asm_records import inspect_asm
from decode_basics import decode_basics
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_bindings import decode_body_bindings
from decode_body_mapping_variants import decode_body_mapping_variants
from fusion_archive import read_members
from fusion_metadata import design_records

FILES = [
    'namedbodies-3c7c11fc2924/namedbodies.f3d',
    'boundaryfills-a0953038318b/new_middle.f3d',
    'boundaryfills-a0953038318b/new_middle_remove.f3d',
    'boundaryfills-a0953038318b/new_two.f3d',
    'assembly-acc48a9dc05d/assembly.f3d',
    'advanced-627f7fe095f4/advanced.f3d',
    'mirrorassemblydatum-700af16e9fc6/nested_occurrence_yz.f3d',
]

PRIOR_SUCCESS_CONTROLS = [
    'circularmodes-45f859c1f1b6/multiple_customaxis.f3d',
    'jointmodes-20d3aef2a07d/revolute.f3d',
    'bodymodes-405fbd002680/shell_both.f3d',
    'rectmodes-a069f8f4b8a2/body_sketchlines.f3d',
]
EXISTING_UNSUPPORTED_CONTROL = 'pipeedgecontrasts-5bd287323ae7/circle_full.f3d'


def baseline_bindings(data, records, member, model, stream):
    """Rebuild pre-keyed bindings; never reuse the main reader's patched result."""
    result = decode_body_bindings(data, records, member, model['asm_decoding'], stream['body_properties'])
    variants = decode_body_mapping_variants(data, records, member, model['asm_decoding'], stream['body_properties'])
    existing = {m['mapping_record_object_id'] for m in result['decoded']}
    result['decoded'].extend(m for m in variants['decoded'] if m['mapping_record_object_id'] not in existing)
    recovered = {m['mapping_record_object_id'] for m in variants['decoded']}
    result['unresolved'] = [m for m in result['unresolved'] if m['object_id'] not in recovered]
    return result


def close_points(a, b):
    return len(a) == len(b) and all(all(math.isclose(x, y, abs_tol=1e-9, rel_tol=1e-9)
                                      for x, y in zip(p, q)) for p, q in zip(sorted(a), sorted(b)))


def validate(zstd_library):
    root = Path(__file__).resolve().parent
    report = {'status': 'Observed typed same-blob identifier match corroborated in focused saved fixtures',
              'universal_identity_claim': False, 'cases': [], 'guards': [], 'api_corroboration': [],
              'uuid_checks': [], 'ordinal_counterexamples': [], 'prior_success_controls': [],
              'baseline_method': 'Raw decode_body_bindings plus fresh body_mapping_variants recovery, independent of integrated keyed patches',
              'limitations': [
                  'Identifier keys are scoped to one explicitly referenced blob, never global ASM record indices.',
                  'Only bounded initial geometry root BODY records are accepted; history/snapshot pointers are not interpreted.',
                  'Current visibility, final-body lifecycle, material and component ownership are not established by this association.',
                  'Geometry/name/API comparisons occur after the stored identifier join and never select associations.',
                  'Empty native tables associate no bodies or ASM streams.',
                  'Retire ordinal candidates for every populated mapping, including keyed validation failures.',
              ]}
    named_context = None
    for relative in FILES:
        path = root / relative
        members = read_members(path, zstd_library)
        model = decode_basics(path, zstd_library)
        case = {'file': relative, 'mappings': [], 'unresolved': []}
        for stream in model['streams']:
            member = stream['member']
            data = members[member]
            records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
            bindings = baseline_bindings(data, records, member, model, stream)
            decoded = decode_body_asm_identifiers(data, records, member, members, bindings)
            assert not decoded['unresolved'], (relative, decoded['unresolved'])
            assert len(decoded['decoded']) == sum(m['body_count'] > 0 for m in bindings['decoded'])
            case['mappings'].extend(decoded['decoded'])
            case['empty_table_count'] = sum(m['body_count'] == 0 for m in bindings['decoded'])
            original = {m['mapping_record_object_id']: m for m in bindings['decoded']}
            for mapping in decoded['decoded']:
                parsed = inspect_asm(members[mapping['history_blob_member']])
                asm = next(s for s in model['asm_decoding']['streams'] if s['member'] == mapping['history_blob_member'])
                graphs = {g['body_index']: g for g in asm['topology']['body_graphs']}
                old_mapping = original[mapping['mapping_record_object_id']]
                for ordinal, patch in enumerate(mapping['bindings']):
                    old_root = old_mapping['bindings'][ordinal].get('candidate_asm_body_index')
                    assert patch['previous_ordinal_candidate'] == old_root
                    assert patch['ordinal_candidate_conflict'] == (old_root is not None and old_root != patch['asm_body_index'])
                    if patch['ordinal_candidate_conflict']:
                        report['ordinal_counterexamples'].append({
                            'file': relative, 'mapping_record_object_id': mapping['mapping_record_object_id'],
                            'native_body_object_id': patch['native_body_object_id'], 'stored_handle': patch['stored_handle'],
                            'ordinal_asm_body_index': old_root, 'identifier_asm_body_index': patch['asm_body_index']})
                    if relative.startswith('namedbodies-'):
                        native = next(e for e in old_mapping['bindings'] if e['native_body_object_id'] == patch['native_body_object_id'])
                        truth = json.loads((path.parent / 'ground_truth.json').read_text())
                        actual = next(b for b in truth['bodies'] if b['name'] == native['name'])
                        graph = graphs[patch['asm_body_index']]
                        assert close_points(graph['raw_vertex_positions'], actual['vertex_positions_cm'])
                        assert all(graph['counts'][k] == actual[k + '_count'] for k in ['face', 'edge', 'vertex'])
                        report['api_corroboration'].append({
                            'file': relative, 'native_body_object_id': patch['native_body_object_id'],
                            'name': native['name'], 'component_name': native['component_name'],
                            'vertex_set_and_face_edge_vertex_counts_match_actual_api': True})
                    if relative.endswith('new_middle_remove.f3d') and patch['native_body_object_id'] == 442:
                        actual = next(s for s in json.loads((path.parent / 'ground_truth.json').read_text())['samples']
                                      if s['file'] == path.name)
                        positions = graphs[patch['asm_body_index']]['raw_vertex_positions']
                        bounds = [list(map(min, zip(*positions))), list(map(max, zip(*positions)))]
                        api = actual['output_bodies'][0]['geometry']
                        assert close_points(bounds, [api['min_cm'], api['max_cm']])
                        report['api_corroboration'].append({
                            'file': relative, 'native_body_object_id': 442, 'asm_body_index': patch['asm_body_index'],
                            'result_vertex_bounds_match_actual_api': True, 'bounds_cm': bounds,
                            'api_is_remove_tools': actual['is_remove_tools'],
                            'caution': 'This corroborates one saved result; no general current-body classifier is implemented.'})
                native_ids = {p['native_body_object_id'] for p in mapping['bindings']}
                for anchor in stream.get('body_selections', {}).get('body_anchors', []):
                    if anchor['native_body_object_id'] not in native_ids:
                        continue
                    text = anchor['native_uuid_text']
                    raw = members[mapping['history_blob_member']]
                    checks = {name: raw.find(value) for name, value in [
                        ('ascii', text.encode()), ('utf16le', text.encode('utf-16le')),
                        ('uuid_network_bytes', uuid.UUID(text).bytes), ('uuid_little_endian_bytes', uuid.UUID(text).bytes_le)]}
                    report['uuid_checks'].append({'file': relative, 'native_body_object_id': anchor['native_body_object_id'],
                                                  'native_uuid_text': text, 'same_blob_raw_encoding_offsets': checks})
            if relative.startswith('namedbodies-'):
                named_context = (data, records, member, members, bindings, decoded)
        report['cases'].append(case)
    assert len(report['ordinal_counterexamples']) == 2
    data, records, member, members, bindings, decoded = named_context
    mapping = next(m for m in decoded['decoded'] if m['body_count'] == 2)
    map_record = next(r for r in records if r.is_primary and r.object_id == mapping['mapping_record_object_id'])
    blob = mapping['history_blob_member']
    parsed = inspect_asm(members[blob])

    def rejected(label, changed_data=data, changed_members=members, changed_bindings=bindings):
        result = decode_body_asm_identifiers(changed_data, records, member, changed_members, changed_bindings)
        errors = [e for e in result['unresolved'] if e['mapping_record_object_id'] == mapping['mapping_record_object_id']]
        assert len(errors) == 1 and errors[0]['ordinal_candidates_must_be_discarded'], (label, result)
        assert not any(m['mapping_record_object_id'] == mapping['mapping_record_object_id'] for m in result['decoded'])
        report['guards'].append({'guard': label, 'rejected': True, 'reason': errors[0]['reason']})

    changed = bytearray(data)
    struct.pack_into('<Q', changed, map_record.body + 6 + 16 * mapping['body_count'] + 1, 401)
    rejected('Mapping owner must resolve to typed BodyCollection, not a BODY', changed_data=bytes(changed))
    changed = bytearray(data)
    struct.pack_into('<Q', changed, map_record.body + 6, 999)
    cb = copy.deepcopy(bindings)
    next(m for m in cb['decoded'] if m['mapping_record_object_id'] == mapping['mapping_record_object_id'])['bindings'][0]['stored_handle'] = 999
    rejected('Native mapping handle missing from initial ASM BODY identifier set', changed_data=bytes(changed), changed_bindings=cb)
    changed = bytearray(members[blob])
    struct.pack_into('<q', changed, parsed['records'][2]['tokens'][1]['offset'] + 1,
                     parsed['records'][1]['tokens'][1]['value'])
    rejected('Duplicate typed ASM BODY stored entity ID', changed_members={**members, blob: bytes(changed)})
    changed = bytearray(members[blob])
    lump = parsed['records'][parsed['records'][1]['tokens'][3]['value']]
    struct.pack_into('<q', changed, lump['tokens'][5]['offset'] + 1, 2)
    rejected('ASM BODY/lump owner points to a different BODY', changed_members={**members, blob: bytes(changed)})
    changed = bytearray(members[blob])
    changed[parsed['records'][1]['tokens'][1]['offset']] = 12
    rejected('ASM BODY identifier must be an integer token, not pointer token', changed_members={**members, blob: bytes(changed)})
    for relative in PRIOR_SUCCESS_CONTROLS + [EXISTING_UNSUPPORTED_CONTROL]:
        path = root / relative
        members = read_members(path, zstd_library)
        model = decode_basics(path, zstd_library)
        control = {'file': relative, 'old_ordinal_candidates': 0, 'keyed_associations': 0,
                   'old_candidates_withdrawn': 0, 'old_candidates_changed': 0, 'unresolved': []}
        for stream in model['streams']:
            member = stream['member']
            data = members[member]
            records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
            bindings = baseline_bindings(data, records, member, model, stream)
            decoded = decode_body_asm_identifiers(data, records, member, members, bindings)
            old = {(m['mapping_record_object_id'], e['native_body_object_id']): e['candidate_asm_body_index']
                   for m in bindings['decoded'] for e in m['bindings'] if 'candidate_asm_body_index' in e}
            new = {(m['mapping_record_object_id'], e['native_body_object_id']): e['asm_body_index']
                   for m in decoded['decoded'] for e in m['bindings']}
            control['old_ordinal_candidates'] += len(old)
            control['keyed_associations'] += len(new)
            control['old_candidates_withdrawn'] += sum(key not in new for key in old)
            control['old_candidates_changed'] += sum(key in new and value != new[key] for key, value in old.items())
            control['unresolved'].extend(decoded['unresolved'])
            if relative == EXISTING_UNSUPPORTED_CONTROL:
                for mapping in bindings['decoded']:
                    if not mapping['body_count']:
                        continue
                    parsed = inspect_asm(members[mapping['history_blob_member']])
                    control['declared_root_kinds'] = [r['name'] for r in parsed['records'][:parsed['header']['stored_entity_count']]]
        assert control['old_candidates_withdrawn'] == 0 and control['old_candidates_changed'] == 0
        if relative in PRIOR_SUCCESS_CONTROLS:
            assert control['old_ordinal_candidates'] > 0 and not control['unresolved']
            assert control['keyed_associations'] == control['old_ordinal_candidates']
            report['prior_success_controls'].append(control)
        else:
            assert control['old_ordinal_candidates'] == 0 and len(control['unresolved']) == 1
            control['status'] = 'Already had no ordinal association; stricter key rejection withdraws no prior candidate'
            report['existing_unsupported_control'] = control
    report['summary'] = {'files': len(report['cases']),
                         'populated_mappings': sum(len(c['mappings']) for c in report['cases']),
                         'body_associations': sum(len(m['bindings']) for c in report['cases'] for m in c['mappings']),
                         'empty_tables_left_empty': sum(c['empty_table_count'] for c in report['cases']),
                         'ordinal_counterexamples': len(report['ordinal_counterexamples']),
                         'actual_api_corroborations': len(report['api_corroboration']), 'malformed_guards': len(report['guards']),
                         'diverse_prior_success_files': len(report['prior_success_controls']),
                         'diverse_prior_candidates_preserved': sum(c['old_ordinal_candidates'] for c in report['prior_success_controls']),
                         'diverse_prior_candidates_withdrawn': sum(c['old_candidates_withdrawn'] for c in report['prior_success_controls']),
                         'existing_unsupported_files_with_no_prior_candidate': 1}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zstd-library')
    parser.add_argument('--output', default='body-asm-identifier-decoding.json')
    args = parser.parse_args()
    zstd = args.zstd_library or next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report = validate(zstd)
    Path(args.output).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['summary'], sort_keys=True))
