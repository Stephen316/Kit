"""Exact FDM payload replay, FACE/BODY provenance and axis-cache contrasts."""

import argparse
from collections import Counter
import copy
import json
import math
import struct
from pathlib import Path

from asm_records import inspect_asm
from decode_basics import decode_basics
from decode_asm_recipe_tags import decode_asm_generic_tags
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_brep import decode_topology
from decode_fdm_face_attributes import decode_fdm_face_attribute
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT = Path(__file__).resolve().parent


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def owner_chain(record, parsed):
    records = parsed['records']
    limit = next(r['index'] for r in records if r['record_kind'] == 'marker')
    t = record['tokens']; owner = t[4]['value']
    assert t[4]['kind'] == 'pointer' and 0 <= owner < limit and records[owner]['name'] == 'face'
    current, previous, chain = records[owner]['tokens'][0]['value'], -1, []
    while current != -1:
        assert 0 <= current < limit and current not in chain and len(chain) < 64
        chain.append(current); rec = records[current]; tokens = rec['tokens']
        assert rec['name'] == 'ATTRIB_CUSTOM-attrib'
        assert [v['kind'] for v in tokens[:5]] == ['pointer', 'integer', 'pointer', 'pointer', 'pointer']
        assert [tokens[i]['value'] for i in (0, 1, 3, 4)] == [-1, -1, previous, owner]
        previous, current = current, tokens[2]['value']
    assert record['index'] in chain
    return owner, chain


def validate(zstd_library):
    contexts = {}
    def load(relative):
        if relative not in contexts:
            members = read_members(ROOT / relative, zstd_library)
            model = decode_basics(ROOT / relative, zstd_library); stream = model['streams'][0]; member = stream['member']
            records, _ = design_records(members[member], members[member.replace('BulkStream.dat', 'MetaStream.dat')])
            primary = {r.object_id: r for r in records if r.is_primary}
            joins = decode_body_asm_identifiers(members[member], records, member, members, stream['body_blob_bindings'])
            assert not joins['unresolved']
            contexts[relative] = members, model, stream, primary, joins
        return contexts[relative]
    report = {'scope': 'Nineteen observed initial FACE-owned FDM attributes in twelve saved thread/tapped-hole archives; payload framing and independent owner/BODY/axis-cache evidence only',
              'integration': {'payload_function': 'decode_fdm_face_attributes.decode_fdm_face_attribute(record)',
                              'expected_payload_field': 'records[].expected_payload',
                              'owner_callsite': 'Root generic-tag reader may recognize this other definition only after its strict initial FACE owner and reciprocal chain checks; payload helper itself performs no ownership or feature-ID lookup.',
                              'validation_command': '/usr/bin/python3 validate_fdm_face_attributes.py', 'shared_edits_by_this_task': False},
              'records': [], 'feature_id_counterexamples': [], 'partial_thread_extent_counterexamples': [], 'guards': [],
              'limitations': ['FDM feature literal303/304 is not a typed native object reference. Actual Thread/Hole object IDs differ; coincident helper/recipe numbers are not feature associations.',
                              'The terminal0/1 flag is preserved without assigning handedness, internal/external state or a parent-hole semantic. Standalone internal and external threads both store0.',
                              'Three position vectors are literal face-cache fields. Their axis alignment and full-cylinder boundary-center agreement do not establish active thread offset/length or native face parameter roles.',
                              'Modeled feature_data has no position triples; its kind/count fields are preserved without reconstructing helical geometry.',
                              'Independent typed owner/body routes give cache provenance only. Native selected input-face and FDM-to-feature persistent identity remain unresolved.',
                              'No new API capture, solver, current/final lifecycle inference or geometry regeneration is performed.']}
    sources = []; axis_count = 0; center_count = 0; mismatched_extent = 0
    production_catalogs = {}
    for relative, member, index in TARGETS:
        members, model, stream, primary, joins = load(relative)
        raw = members[member]; parsed = inspect_asm(raw); record = parsed['records'][index]
        payload = decode_fdm_face_attribute(record); sources.append(record)
        assert bytes.fromhex(payload['payload_hex']) == raw[payload['payload_offset']:payload['payload_end_offset']]
        face_index, chain = owner_chain(record, parsed)
        if (relative, member) not in production_catalogs:
            production_catalogs[relative, member] = decode_asm_generic_tags(raw, parsed=parsed, allow_fpm_tracking=True)
        shared = production_catalogs[relative, member]
        recognized = [item for item in shared['ignored_validated_other_definition_attributes']
                      if item['attribute_record_index'] == index]
        recognized_item, = recognized
        assert {key: recognized_item[key] for key in payload} == payload
        assert recognized_item['owner_kind'] == 'face' and recognized_item['owner_record_index'] == face_index
        assert recognized_item['owner_attribute_chain'] == chain
        assert not any(item['attribute_record_index'] == index for item in shared['unresolved'])
        topology = decode_topology(parsed); nodes = {n['index']: n for n in topology['nodes']}
        graphs = [g for g in topology['body_graphs'] if face_index in g['face_indices']]
        graph, = graphs
        body_entries = [(m, b) for m in joins['decoded'] if m['history_blob_member'] == member for b in m['bindings'] if b['asm_body_index'] == graph['body_index']]
        mapping, body = body_entries[0]
        assert len(body_entries) == 1 and parsed['records'][graph['body_index']]['tokens'][1]['value'] == body['asm_stored_entity_id']
        entry = {'file': relative, 'member': member, 'record_index': index, 'expected_payload': payload,
                 'owner_face_index': face_index, 'reciprocal_owner_attribute_chain': chain,
                 'asm_body_index': graph['body_index'], 'asm_body_stored_entity_id': body['asm_stored_entity_id'],
                 'native_body_object_id': body['native_body_object_id'],
                 'native_body_mapping_object_id': mapping['mapping_record_object_id'],
                 'identity_status': 'Exact FACE/typed BODY/native-body provenance; FDM feature identity remains unresolved',
                 'production_shared_reader': {'recognized_other_definition': True,
                    'all_expected_payload_keys_equal': True, 'owner_kind': recognized_item['owner_kind'],
                    'owner_record_index': recognized_item['owner_record_index'],
                    'owner_attribute_chain': recognized_item['owner_attribute_chain']}}
        thread_features = [f for f in stream['features'] if f['kind'] == 'Thread']
        hole_features = [f for f in stream['features'] if f['kind'] == 'Hole']
        literal = payload['stored_feature_literal']
        assert literal not in {f['object_id'] for f in thread_features+hole_features}
        collision = primary.get(literal)
        entry['native_feature_literal_control'] = {'stored_literal': literal,
            'actual_native_thread_object_ids': [f['object_id'] for f in thread_features],
            'actual_native_hole_object_ids': [f['object_id'] for f in hole_features],
            'same_number_primary_record_class': collision.class_guid if collision else None,
            'numeric_literal_is_actual_thread_or_hole_id': False}
        if not any(c['file'] == relative for c in report['feature_id_counterexamples']):
            report['feature_id_counterexamples'].append({'file': relative, **entry['native_feature_literal_control']})
        truth = json.loads((ROOT / Path(relative).parent / 'ground_truth.json').read_text())
        api = next(s for s in truth['samples'] if s['file'] == Path(relative).name)['settings']
        thread, = thread_features
        settings = thread['tool_settings']
        assert settings['is_modeled'] == api['is_modeled'] and settings['is_full_length'] == api['is_full_length']
        entry['saved_API_context'] = {key: api.get(key) for key in ('is_modeled', 'is_full_length', 'is_internal', 'is_right_handed', 'stored_length_cm', 'stored_offset_cm', 'thread_length_cm', 'thread_offset_cm')}
        if payload['stored_position_vectors']:
            face = nodes[face_index]; surface = nodes[face['surface_index']]
            geometry = surface.get('analytic_surface')
            assert geometry and geometry['kind'] == 'Cylinder'
            origin, axis = geometry['raw_origin'], geometry['axis']
            positions = payload['stored_position_vectors']; axis_errors = []
            for point in positions:
                delta = [p-o for p, o in zip(point, origin)]; along = dot(delta, axis)
                axis_errors.append(math.hypot(*[d-along*a for d, a in zip(delta, axis)]))
            assert max(axis_errors) < 1e-10
            assert positions[0] == positions[2]
            span = math.dist(positions[0], positions[1]); axis_count += 1
            circle_centers = []
            for coedge in nodes.values():
                if coedge['kind'] != 'coedge' or nodes[coedge['loop_index']]['face_index'] != face_index:
                    continue
                edge = nodes[coedge['edge_index']]; curve = nodes.get(edge['curve_index'])
                if curve and curve['kind'] == 'ellipse-curve' and math.isclose(curve['stored_axis_ratio'], 1., abs_tol=1e-10):
                    circle_centers.append({'coedge_index': coedge['index'], 'edge_index': edge['index'],
                                           'curve_index': curve['index'], 'raw_center': curve['raw_origin']})
            endpoint_center_errors = [min((math.dist(point, c['raw_center']) for c in circle_centers), default=None) for point in positions[:2]]
            centers_agree = bool(circle_centers) and all(error is not None and error < 1e-10 for error in endpoint_center_errors)
            if centers_agree:
                center_count += 1
            entry['position_cache_geometry'] = {'owner_surface_index': surface['index'], 'surface_kind': 'Cylinder',
                'raw_surface_axis': axis, 'three_axis_alignment_errors_raw': axis_errors,
                'first_third_position_equal': True, 'first_second_axis_span_raw': span,
                'explicit_boundary_circle_centers': circle_centers,
                'endpoint_center_errors_raw': endpoint_center_errors,
                'both_positions_match_typed_boundary_circle_centers': centers_agree,
                'scope': 'Axis/cylinder cache corroboration; native thread limits not inferred'}
            if not api['is_full_length']:
                active_length = api['thread_length_cm'] if 'thread_length_cm' in api else api['stored_length_cm']
                active_offset = api['thread_offset_cm'] if 'thread_offset_cm' in api else api['stored_offset_cm']
                assert math.isclose(settings['active_length_cm'], active_length, abs_tol=1e-12)
                assert math.isclose(settings['active_offset_cm'], active_offset, abs_tol=1e-12)
                assert not math.isclose(span, active_length, abs_tol=1e-8)
                mismatched_extent += 1
                report['partial_thread_extent_counterexamples'].append({'file': relative, 'record_index': index,
                    'stored_axis_position_span_raw': span, 'saved_API_active_thread_length_cm': active_length,
                    'saved_API_active_thread_offset_cm': active_offset,
                    'typed_full_cylinder_boundary_center_agreement': centers_agree,
                    'consequence': 'Position span is not the active thread length; payload positions are not labelled thread limits'})
        report['records'].append(entry)
    assert len(report['records']) == 19 and len(contexts) == 12
    assert Counter(r['expected_payload']['stored_payload_name'] for r in report['records']) == {'thread_face_data': 12, 'feature_data': 7}
    base = next(s for s in sources if len(s['tokens']) == 18)
    def reject(label, mutate):
        source = copy.deepcopy(base); mutate(source['tokens'])
        try:
            decode_fdm_face_attribute(source)
        except (ValueError, IndexError) as error:
            report['guards'].append({'case': label, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError('Malformed FDM payload accepted: '+label)
    reject('Schema version literal changed', lambda t: t[6].update(value=3))
    reject('Payload name/count pairing changed', lambda t: t[12].update(value=2))
    reject('Nonfinite cached position', lambda t: t[14].update(value=[float('nan'), 0., 0.]))
    reject('Unobserved terminal flag', lambda t: t[17].update(value=2))
    reject('Unexpected extra field', lambda t: t.append({'kind': 'integer', 'tag': 4, 'value': 0, 'offset': t[-1]['offset']+9}))
    # Payload remains valid while its claimed FACE owner is changed. The
    # production caller must reject that association through its own chain proof.
    relative, member, index = next(target for target in TARGETS
                                  if target[0] == TARGETS[0][0] and target[2] == sources[0]['index'])
    raw = load(relative)[0][member]
    original = inspect_asm(raw)
    record = original['records'][index]
    owner = record['tokens'][4]['value']
    other_face = next(r['index'] for r in original['records'] if r['section'] == 'geometry'
                      and r['name'] == 'face' and r['index'] != owner)
    changed = bytearray(raw)
    struct.pack_into('<q', changed, record['tokens'][4]['offset']+1, other_face)
    changed = bytes(changed); reparsed = inspect_asm(changed)
    assert reparsed['complete_token_stream']
    assert decode_fdm_face_attribute(reparsed['records'][index]) == decode_fdm_face_attribute(record)
    rejected = decode_asm_generic_tags(changed, parsed=reparsed, allow_fpm_tracking=True)
    assert not any(item['attribute_record_index'] == index for item in rejected['ignored_validated_other_definition_attributes'])
    reasons = [item['reason'] for item in rejected['unresolved'] if item['attribute_record_index'] == index]
    assert len(reasons) == 1
    report['guards'].append({'case': 'Production caller rejects valid payload with nonreciprocal FACE owner',
                             'rejected': True, 'reason': reasons[0],
                             'pure_payload_unchanged': True, 'enforcing_reader': 'decode_asm_generic_tags'})
    report['summary'] = {'saved_files': len(contexts), 'fdm_payloads_replayed': len(report['records']),
                         'thread_face_data_payloads': 12, 'feature_data_payloads': 7,
                         'reciprocal_FACE_owner_chains': len(report['records']), 'typed_BODY_native_body_joins': len(report['records']),
                         'position_axis_corroborations': axis_count, 'two_boundary_circle_center_corroborations': center_count,
                         'feature_literal_not_native_ID_counterexamples': len(report['feature_id_counterexamples']),
                         'partial_thread_span_counterexamples': mismatched_extent, 'malformed_guards': len(report['guards']),
                         'native_feature_identity_associations_claimed': 0,
                         'production_shared_reader_payload_matches': len(report['records']),
                         'production_shared_reader_owner_chain_matches': len(report['records']),
                         'production_owner_chain_guard_rejections': 1}
    return report


# Durable record inventory from the parent's initial-ASM FDM framing discovery.
TARGETS = [('tappedholes-409e96788503/cosmetic_full.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.1891a4a3-5dad-4510-9839-21b53403cd7c.smbh',
  11),
 ('tappedholes-409e96788503/cosmetic_partial.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.f430a677-d121-497e-b11b-792eee686f60.smbh',
  11),
 ('tappedholes-409e96788503/modeled_full.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.2c6df07f-81b0-495a-ba58-9dd21c84b060.smbh',
  7),
 ('tappedholes-409e96788503/modeled_full.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.2c6df07f-81b0-495a-ba58-9dd21c84b060.smbh',
  12),
 ('tappedholes-409e96788503/modeled_full.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.2c6df07f-81b0-495a-ba58-9dd21c84b060.smbh',
  18),
 ('tappedholes-409e96788503/modeled_full.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.2c6df07f-81b0-495a-ba58-9dd21c84b060.smbh',
  28),
 ('tappedholes-409e96788503/modeled_full.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.2c6df07f-81b0-495a-ba58-9dd21c84b060.smbh',
  70),
 ('threadmodes-6b6a0a9b4a69/partial_high.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.6ba43899-473c-4e7e-932a-832f35cdbec9.smbh',
  7),
 ('threadmodes-6b6a0a9b4a69/partial_low.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.6efa38b9-99cb-4f23-b62c-e3c2d74aac81.smbh',
  7),
 ('threadmodes-9574579d310b/left_handed.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.69129bb4-f8c4-446c-b720-0b89fb586cd3.smbh',
  7),
 ('threadmodes-d51d2ae60564/cosmetic_full.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.471a01b0-df17-4d63-9a20-153feae4d235.smbh',
  7),
 ('threadmodes-d51d2ae60564/internal.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.00b29012-222f-44de-ba11-10f208adc1a9.smbh',
  7),
 ('threadmodes-d51d2ae60564/left_handed.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.b569d3e5-19e9-47f6-8ab0-f258edefafa1.smbh',
  7),
 ('threadmodes-d51d2ae60564/modeled_full.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.7369d28b-2150-4279-8aaa-bcfbde1e1a33.smbh',
  7),
 ('threadmodes-d51d2ae60564/modeled_full.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.7369d28b-2150-4279-8aaa-bcfbde1e1a33.smbh',
  12),
 ('threadmodes-d51d2ae60564/modeled_full.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.7369d28b-2150-4279-8aaa-bcfbde1e1a33.smbh',
  18),
 ('threadmodes-d51d2ae60564/modeled_full.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.7369d28b-2150-4279-8aaa-bcfbde1e1a33.smbh',
  48),
 ('threadmodes-d51d2ae60564/partial_high.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.a42cbeb2-efc2-4837-a51f-1707e4b6e118.smbh',
  7),
 ('threadmodes-d51d2ae60564/partial_low.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.e2159196-cd6a-46ef-a8f1-c7d4e2203c1d.smbh',
  7)]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='fdm-face-attribute-decoding.json')
    args = parser.parse_args()
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report = validate(str(zstd))
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
