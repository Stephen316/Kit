"""Bounded BoundaryFill owned NewBody anchors and stored membership facts.

Feature-owned result anchors, removal actions, retained body/collection pointers,
and reciprocal collection membership are separate facts. None is promoted to a
universal current-visible/final-body classifier.
"""

import argparse
import json
from pathlib import Path
import struct
import uuid

from decode_body_properties import BODY, COLLECTION
from decode_body_selections import ANCHOR, PROXY, decode_body_selections
from decode_boundary_fill import BOUNDARY_FILL_GUID, decode_boundary_fill
from decode_direct_body_features import decode_direct_body_features
from decode_parameters import read_string
from decode_selection import native_proxy_references
from decode_sketch import reference

COMPONENT = 'E03784ED-5E19-4E14-B9F2-3B07017018CD'
SCOPE = ('Observed BoundaryFill NewBody result anchors, modifying-operation result body selections and stored collection/removal facts; '
         'current visibility, final-body lifetime and general regeneration remain unresolved')


def _typed_records(data, records):
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: items[0] for identity, items in grouped.items() if len(items) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('BoundaryFill result typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]
    return primary, typed


def stored_body_membership(data, records, identity):
    """Return literal stored pointers/list membership, including absent members."""
    _, typed = _typed_records(data, records)
    native, body = typed(identity, BODY)
    collection_id = reference(body, len(body) - 11)
    _, collection = typed(collection_id, COLLECTION)
    if collection[:2] == bytes(2):
        cursor = 2
    elif collection[:6] == bytes.fromhex('000100000000'):
        cursor = 6  # Observed optional empty attribute table only.
    else:
        raise ValueError('Unsupported result body collection prefix/attributes')
    if len(collection) < cursor + 24 or collection[cursor] != 0:
        raise ValueError('Unsupported result body collection framing')
    count = struct.unpack_from('<I', collection, cursor + 5)[0]
    start = cursor + 9
    if count > 100000 or start + 11 * count > len(collection):
        raise ValueError('Result body collection member count exceeds bounds')
    members = [reference(collection, start + 11 * i) for i in range(count)]
    repeated = len(collection) - 15 - 11 * count
    if (repeated < start + 11 * count or struct.unpack_from('<I', collection, repeated)[0] != count
            or [reference(collection, repeated + 4 + 11 * i) for i in range(count)] != members
            or len(set(members)) != count):
        raise ValueError('Result body collection repeated membership disagrees')
    for member_id in members:
        _, member = typed(member_id, BODY)
        if reference(member, len(member) - 11) != collection_id:
            raise ValueError('Listed result body/collection ownership is not reciprocal')
    component = reference(collection, len(collection) - 11)
    typed(component, COMPONENT)
    listed = identity in members
    return {'native_body_object_id': identity,
            'native_body_collection_reference_offset': native.end - 11,
            'referenced_collection_object_id': collection_id,
            'repeated_collection_member_object_ids': members,
            'is_listed_in_repeated_collection': listed,
            'membership_status': ('Explicit reciprocal stored collection membership' if listed else
                                  'Native body retains a collection reference but is absent from both stored member lists'),
            'collection_component_object_id': component,
            'component_scope': 'Typed collection-to-component reference; absent-member pointer does not establish active ownership',
            'visibility_status': 'Current visibility/final lifecycle not inferred from stored membership'}


def decode_boundary_fill_results(data, records):
    """Return decoded/unresolved/scope, keyed by feature_object_id.

    Existing BoundaryFill controls and direct-body readers validate the prefix,
    tools, removal ownership and selected-cell framing. This pass adds the next
    explicitly counted anchor/proxy tables and rechecks typed anchor ownership.
    """
    primary, typed = _typed_records(data, records)
    if not any(record.class_guid == BOUNDARY_FILL_GUID for record in primary.values()):
        return {'decoded': [], 'unresolved': [], 'scope': SCOPE}
    selections = decode_body_selections(data, records)
    anchors = {a['object_id']: a for a in selections['body_anchors']}
    descriptors = {d['object_id']: d for d in selections['body_descriptors']}
    direct = decode_direct_body_features(data, records, selections)
    removals = {item['feature_object_id']: item for item in direct['decoded'] if item['kind'] == 'RemoveBody'}
    decoded, unresolved = [], []
    for record in primary.values():
        if record.class_guid != BOUNDARY_FILL_GUID:
            continue
        try:
            payload = data[record.body:record.end]
            controls = decode_boundary_fill(data, records, payload,
                                            {'object_id': record.object_id, 'class_guid': BOUNDARY_FILL_GUID})
            cursor = controls['selected_definition_end_offset']
            if payload[cursor:cursor + 4] != bytes(4):
                raise ValueError('Unsupported BoundaryFill post-cell anchor-table marker')
            count = struct.unpack_from('<I', payload, cursor + 4)[0]
            expected = 1 if controls['operation'] == 'NewBody' else 0
            if count != expected or cursor + 8 + 11 * count > len(payload):
                raise ValueError('Unsupported BoundaryFill operation/owned-result-anchor count combination')
            anchor_ids = [reference(payload, cursor + 8 + 11 * i) for i in range(count)]
            owned = {a['object_id'] for a in anchors.values() if a['source_owner_object_id'] == record.object_id}
            if set(anchor_ids) != owned or len(set(anchor_ids)) != count:
                raise ValueError('BoundaryFill counted anchor list and owned typed anchors disagree')
            results = []
            for anchor_id in anchor_ids:
                typed(anchor_id, ANCHOR)
                anchor = anchors.get(anchor_id)
                if anchor is None or anchor['source_owner_object_id'] != record.object_id:
                    raise ValueError('BoundaryFill result anchor owner is unresolved or different')
                typed(anchor['native_body_object_id'], BODY)
                results.append({'body_anchor_object_id': anchor_id,
                                'native_body_object_id': anchor['native_body_object_id'],
                                'source_owner_object_id': record.object_id,
                                'role': 'Feature-owned NewBody result anchor',
                                'role_scope': 'Observed NewBody result association; not a current-visible/final-body classification',
                                'stored_membership': stored_body_membership(data, records, anchor['native_body_object_id'])})
            position = cursor + 8 + 11 * count
            if payload[position:position + 4] != bytes(4):
                raise ValueError('Unsupported BoundaryFill post-anchor proxy-table marker')
            proxy_count = struct.unpack_from('<I', payload, position + 4)[0]
            if proxy_count != (0 if controls['operation'] == 'NewBody' else 1):
                raise ValueError('Unsupported BoundaryFill post-anchor proxy count')
            proxy_ids = [reference(payload, position + 8 + 11 * i) for i in range(proxy_count)]
            input_proxy_ids = [t['selection_record_object_id'] for t in controls['tools'] if t['kind'] == 'Body']
            if set(proxy_ids) & set(input_proxy_ids):
                raise ValueError('BoundaryFill result proxy is not distinct from its input tool proxies')
            selected_results = []
            for proxy_id in proxy_ids:
                proxy_record, proxy = typed(proxy_id, PROXY)
                descriptor_ids, properties = native_proxy_references(data, proxy_record)
                if (properties or not descriptor_ids or reference(proxy, len(proxy) - 11) != record.object_id
                        or len(set(descriptor_ids)) != len(descriptor_ids)):
                    raise ValueError('BoundaryFill result proxy list/owner/attributes unsupported')
                for descriptor_id in descriptor_ids:
                    descriptor = descriptors.get(descriptor_id)
                    if descriptor is None or descriptor['owner_object_id'] != record.object_id:
                        raise ValueError('BoundaryFill result descriptor is unresolved or incorrectly owned')
                    selected_results.append({
                        'selection_record_object_id': proxy_id, 'descriptor_object_id': descriptor_id,
                        'body_anchor_object_id': descriptor['body_anchor_object_id'],
                        'native_body_object_id': descriptor['native_body_object_id'],
                        'source_owner_object_id': descriptor['source_owner_object_id'],
                        'role': 'Modifying-operation result selection of an explicit historical body',
                        'role_scope': 'Stored result association; no current-visible/final lifecycle inference',
                        'stored_membership': stored_body_membership(data, records, descriptor['native_body_object_id']),
                    })
            position += 8 + 11 * proxy_count
            namespace, end = read_string(payload, position)
            if len(namespace) != 36:
                raise ValueError('Unsupported BoundaryFill result-table metadata namespace')
            uuid.UUID(namespace)
            inputs = []
            for tool in controls['tools']:
                if tool['kind'] != 'Body':
                    continue
                descriptor = descriptors.get(tool['descriptor_object_id'])
                if descriptor is None or descriptor['owner_object_id'] != record.object_id:
                    raise ValueError('BoundaryFill input body descriptor unresolved or incorrectly owned')
                inputs.append({'selection_record_object_id': tool['selection_record_object_id'],
                               'descriptor_object_id': descriptor['object_id'],
                               'body_anchor_object_id': descriptor['body_anchor_object_id'],
                               'native_body_object_id': descriptor['native_body_object_id'],
                               'source_owner_object_id': descriptor['source_owner_object_id'],
                               'role': 'Explicit BoundaryFill historical body tool',
                               'stored_membership': stored_body_membership(data, records, descriptor['native_body_object_id'])})
            if (len({r['native_body_object_id'] for r in selected_results}) != len(selected_results)
                    or any(not any(r['native_body_object_id'] == i['native_body_object_id']
                                   and r['body_anchor_object_id'] == i['body_anchor_object_id'] for i in inputs)
                           for r in selected_results)):
                raise ValueError('BoundaryFill modifying result does not identify a unique explicit historical input body')
            actions = []
            for identity in controls['remove_body_feature_object_ids']:
                action = removals.get(identity)
                if action is None or action['parent_boundary_fill_object_id'] != record.object_id:
                    raise ValueError('BoundaryFill result/removal association lacks its validated owned action')
                if not any(i['native_body_object_id'] == action['native_body_object_id']
                           and i['body_anchor_object_id'] == action['body_anchor_object_id'] for i in inputs):
                    raise ValueError('BoundaryFill removal action does not identify an explicit tool anchor')
                actions.append({'remove_body_feature_object_id': identity,
                                'native_body_object_id': action['native_body_object_id'],
                                'body_anchor_object_id': action['body_anchor_object_id'],
                                'matching_tool_selection_record_object_id': action['matching_parent_tool_selection_record_object_id'],
                                'stored_membership': stored_body_membership(data, records, action['native_body_object_id']),
                                'action_scope': action['action_scope']})
            decoded.append({'feature_object_id': record.object_id, 'operation': controls['operation'],
                            'owned_result_anchor_table_relative_offset': cursor,
                            'owned_result_body_count': count, 'owned_result_bodies': results,
                            'result_selection_bodies': selected_results,
                            'explicit_result_body_count': count + len(selected_results),
                            'historical_body_tools': inputs, 'owned_remove_body_actions': actions,
                            'result_selection_proxy_object_ids': proxy_ids,
                            'result_selection_scope': 'Distinct owned result proxy selects historical tool identities; current-body lifetime remains unresolved',
                            'metadata_namespace_text': namespace, 'remaining_metadata_byte_count': len(payload) - end,
                            'empty_anchor_scope': 'Zero owned anchors does not mean zero API resulting bodies',
                            'scope': SCOPE})
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            unresolved.append({'feature_object_id': record.object_id, 'reason': str(error)})
    return {'decoded': decoded, 'unresolved': unresolved, 'scope': SCOPE}


def validate(zstd_library):
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records
    import math

    root = Path(__file__).resolve().parent
    folder = root / 'boundaryfills-a0953038318b'
    truth = json.loads((folder / 'ground_truth.json').read_text())
    report = {'scope': SCOPE, 'integration': {
        'function': 'decode_boundary_fill_results(data, records)',
        'returns': 'decoded/unresolved/scope; decoded items keyed by feature_object_id',
        'dependencies': 'Existing BoundaryFill controls, body selections and direct-body feature parsers, all called internally on stored records',
        'suggested_settings_keys': ['owned_result_body_count', 'owned_result_bodies', 'result_selection_bodies',
                                    'explicit_result_body_count', 'result_selection_proxy_object_ids'],
        'summary_only_evidence': ['historical_body_tools', 'owned_remove_body_actions', 'stored_membership'],
        'expected_output': 'samples[].expected_summary contains the complete new standalone output for exact comparison',
        'validation_command': '/usr/bin/python3 decode_boundary_fill_results.py --validate',
    }, 'native_layout': {
        'post_selected_cells': 'At existing selected_definition_end_offset: u32zero,u32anchorCount,11byte anchor refs,u32zero,u32proxyCount,11byte proxy refs,bounded UUID UTF16 namespace',
        'NewBody': 'Observed one owned D263 anchor, explicitly referencing typed native BODY and naming BoundaryFill as source owner; no result proxy',
        'modifying_operations': 'Observed zero owned anchors plus one distinct owned result proxy; Join has two owned body descriptors, Cut/Intersect one. Result bodies must match explicit historical input body/anchor pairs.',
        'membership': 'Native BODY trailer points to typed collection. Bounded leading and repeated trailing member lists plus native member backreferences independently establish listed membership; absence is retained literally.',
    }, 'samples': [], 'guards': [], 'lifecycle_contrasts': [], 'limitations': [
        'Result associations describe this stored feature, not all final/current bodies of a document.',
        'Zero feature-owned anchors does not mean zero API resulting bodies.',
        'A retained collection pointer is not reciprocal membership when the body is absent from both lists.',
        'Reciprocal collection membership alone cannot choose current/final bodies: PM/DM pairs can both be listed in separate collections of the same component.',
        'Default UI result names are observed in API truth only; empty native stored names remain empty.',
        'Geometry checks corroborate already linked identities; geometry/name/order never select a native-to-ASM association.',
        'General suppression/rollback/edit state, sourceBodies getter identity and arbitrary lifecycle solving remain unproved.',
    ]}
    contexts = {}

    def points_close(a, b):
        return len(a) == len(b) and all(math.isclose(x, y, abs_tol=1e-9, rel_tol=1e-9)
                                      for p, q in zip(a, b) for x, y in zip(p, q))

    for actual in truth['samples']:
        path = folder / actual['file']
        members = read_members(path, zstd_library)
        model = decode_basics(path, zstd_library)
        stream = model['streams'][0]
        member = stream['member']
        data = members[member]
        records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
        result = decode_boundary_fill_results(data, records)
        assert not result['unresolved'] and len(result['decoded']) == 1
        item = result['decoded'][0]
        assert item['operation'] == {0: 'Join', 1: 'Cut', 2: 'Intersect', 3: 'NewBody'}[actual['operation']]
        bodies = item['owned_result_bodies'] + item['result_selection_bodies']
        assert item['explicit_result_body_count'] == len(bodies) == len(actual['output_bodies'])
        by_properties = {b['object_id']: b for b in stream['body_properties']['bodies']}
        keyed = {b['native_body_object_id']: (m['history_blob_member'], b['asm_body_index'])
                 for m in stream['body_blob_bindings']['decoded'] for b in m['bindings'] if 'asm_body_index' in b}
        geometry = []
        for body, api in zip(bodies, actual['output_bodies']):
            identity = body['native_body_object_id']
            native_name = by_properties[identity]['name']
            if item['operation'] != 'NewBody':
                assert native_name == api['name']
            if identity not in keyed:
                geometry.append({'native_body_object_id': identity, 'stored_name': native_name,
                                 'actual_API_feature_body_name': api['name'], 'actual_API_bounds_match': None,
                                 'geometry_status': 'Native feature/body association decoded; ASM geometry association remains unresolved',
                                 'ASM_association_errors': stream['body_asm_identifiers']['unresolved']})
                continue
            blob, index = keyed[identity]  # Typed stored-ID join is established before geometric corroboration.
            asm = next(s for s in model['asm_decoding']['streams'] if s['member'] == blob)
            graph = next(g for g in asm['topology']['body_graphs'] if g['body_index'] == index)
            assert graph['body_transform_is_identity']
            positions = graph['raw_vertex_positions']
            bounds = [list(map(min, zip(*positions))), list(map(max, zip(*positions)))]
            expected = [api['geometry']['min_cm'], api['geometry']['max_cm']]
            assert points_close(bounds, expected), (path.name, identity, bounds, expected)
            geometry.append({'native_body_object_id': identity, 'asm_body_index': index,
                             'stored_name': native_name, 'actual_API_feature_body_name': api['name'],
                             'result_vertex_bounds_cm': bounds, 'actual_API_bounds_match': True,
                             'identity_source': 'Explicit feature anchor/descriptor and typed per-blob BODY stored-ID join; comparison after identity association'})
        if actual['is_remove_tools']:
            assert len(item['owned_remove_body_actions']) == 2
            assert all(not a['stored_membership']['is_listed_in_repeated_collection']
                       for a in item['owned_remove_body_actions'])
            assert all(b['stored_membership']['is_listed_in_repeated_collection'] for b in item['owned_result_bodies'])
        sample = {'file': str(path.relative_to(root)), 'expected_summary': result,
                  'actual_API_output_bodies': actual['output_bodies'],
                  'checks': {'explicit_result_count_matches_API': True,
                             'available_result_bounds_match_API_after_typed_identity_join': True,
                             'unresolved_result_geometry_count': sum(g['actual_API_bounds_match'] is None for g in geometry),
                             'modifying_result_names_match_API': True if item['operation'] != 'NewBody' else None,
                             'zero_owned_anchor_count_with_nonzero_API_results': item['owned_result_body_count'] == 0},
                  'result_geometry_corroboration': geometry}
        report['samples'].append(sample)
        contexts[path.name] = data, records, result

    def rejected(case, label, changed):
        data, records, _ = contexts[case]
        result = decode_boundary_fill_results(bytes(changed), records)
        assert not result['decoded'] and len(result['unresolved']) == 1, (label, result)
        report['guards'].append({'guard': label, 'rejected': True, 'reason': result['unresolved'][0]['reason']})

    data, records, output = contexts['new_middle.f3d']
    item = output['decoded'][0]
    primary = {r.object_id: r for r in records if r.is_primary}
    feature = primary[item['feature_object_id']]
    changed = bytearray(data)
    struct.pack_into('<I', changed, feature.body + item['owned_result_anchor_table_relative_offset'] + 4, 2)
    rejected('new_middle.f3d', 'Owned result anchor count cannot exceed the observed operation layout', changed)
    changed = bytearray(data)
    anchor = primary[item['owned_result_bodies'][0]['body_anchor_object_id']]
    struct.pack_into('<Q', changed, anchor.body + 92, item['historical_body_tools'][0]['source_owner_object_id'])
    rejected('new_middle.f3d', 'Counted result anchor must reciprocate the BoundaryFill owner', changed)
    collection = primary[item['owned_result_bodies'][0]['stored_membership']['referenced_collection_object_id']]
    payload = data[collection.body:collection.end]
    count = struct.unpack_from('<I', payload, 7)[0]
    repeated = len(payload) - 15 - 11 * count
    changed = bytearray(data)
    struct.pack_into('<Q', changed, collection.body + repeated + 5, item['owned_result_bodies'][0]['native_body_object_id'])
    rejected('new_middle.f3d', 'Both stored collection member lists must agree', changed)
    data, records, output = contexts['cut_middle.f3d']
    item = output['decoded'][0]
    primary = {r.object_id: r for r in records if r.is_primary}
    proxy = primary[item['result_selection_proxy_object_ids'][0]]
    changed = bytearray(data)
    struct.pack_into('<Q', changed, proxy.end - 10, item['historical_body_tools'][0]['source_owner_object_id'])
    rejected('cut_middle.f3d', 'Distinct result proxy must be owned by the BoundaryFill', changed)
    descriptor = primary[item['result_selection_bodies'][0]['descriptor_object_id']]
    changed = bytearray(data)
    struct.pack_into('<Q', changed, descriptor.end - 10, item['historical_body_tools'][0]['source_owner_object_id'])
    rejected('cut_middle.f3d', 'Result descriptor must be owned by the BoundaryFill', changed)

    # Existing BaseFeature/Mirror captures explain why collection membership is
    # not promoted to a document-wide current-visible-body classification.
    for relative in ['splinepatches-ac5e846e59c0/splinepatches.f3d',
                     'mirrorassemblydatum-700af16e9fc6/nested_occurrence_yz.f3d']:
        path = root / relative
        members = read_members(path, zstd_library)
        model = decode_basics(path, zstd_library)
        stream = model['streams'][0]
        member = stream['member']
        data = members[member]
        records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
        pairs = []
        for base in stream['direct_body_features']['decoded']:
            if base['kind'] != 'BaseFeature':
                continue
            pair = [{'native_body_object_id': p['native_body_object_id'],
                     'passive_reference': p['passive_reference'],
                     'stored_membership': stored_body_membership(data, records, p['native_body_object_id'])}
                    for p in base['body_pair']]
            assert all(p['stored_membership']['is_listed_in_repeated_collection'] for p in pair)
            assert pair[0]['native_body_object_id'] != pair[1]['native_body_object_id']
            pairs.append({'feature_object_id': base['feature_object_id'], 'name': base['name'], 'distinct_body_pair': pair,
                          'explicit_owned_result_body_object_id': base['anchored_result_native_body_object_id']})
        passive_bodies = [p for p in stream['body_properties']['bodies'] if 'passive_reference_attribute' in p]
        passive = [{'native_body_object_id': p['object_id'], 'stored_name': p['name'],
                    'passive_reference_attribute': p['passive_reference_attribute'],
                    'stored_membership': stored_body_membership(data, records, p['object_id'])} for p in passive_bodies]
        assert pairs or passive
        report['lifecycle_contrasts'].append({'file': relative, 'BaseFeature_pairs': pairs, 'passive_bodies': passive,
            'conclusion': 'Distinct reciprocal PM/DM bodies can both be stored collection members. Owned result anchors are a narrower role; no universal current-body selector is inferred.',
            'missing_API_contrast': 'No saved sourceBodies edit/rollback identity getter establishes native PM/DM current-state roles.'})
    relative = 'namedbodies-3c7c11fc2924/namedbodies.f3d'
    path = root / relative
    members = read_members(path, zstd_library)
    stream = decode_basics(path, zstd_library)['streams'][0]
    member = stream['member']
    data = members[member]
    records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
    actual = json.loads((path.parent / 'ground_truth.json').read_text())['bodies']
    native = [{'native_body_object_id': b['object_id'], 'stored_name': b['name'],
               'stored_membership': stored_body_membership(data, records, b['object_id'])}
              for b in stream['body_properties']['bodies']]
    assert sorted(b['stored_name'] for b in native) == sorted(b['name'] for b in actual)
    assert all(b['stored_membership']['is_listed_in_repeated_collection'] for b in native)
    report['lifecycle_contrasts'].append({
        'file': relative, 'listed_native_bodies': native,
        'actual_API_body_labels': [b['name'] for b in actual],
        'checks': {'actual_body_label_multiset_and_count_match_stored_named_members': True},
        'conclusion': 'This saved positive control agrees with four named API bodies; PM/DM and removed-tool contrasts prevent generalizing membership into a current-visible-body rule.',
        'identity_scope': 'Native name/collection references are decoded first; API labels are corroboration, never a native/ASM identity join',
    })
    report['summary'] = {'boundary_fill_files': len(report['samples']),
                         'owned_NewBody_result_associations': sum(s['expected_summary']['decoded'][0]['owned_result_body_count'] for s in report['samples']),
                         'modifying_historical_result_associations': sum(len(s['expected_summary']['decoded'][0]['result_selection_bodies']) for s in report['samples']),
                         'result_API_bounds_matches': sum(g['actual_API_bounds_match'] is True for s in report['samples'] for g in s['result_geometry_corroboration']),
                         'result_ASM_geometry_associations_unresolved': sum(g['actual_API_bounds_match'] is None for s in report['samples'] for g in s['result_geometry_corroboration']),
                         'typed_removal_actions_with_absent_membership': 2,
                         'zero_owned_anchor_nonzero_API_result_controls': 3,
                         'malformed_guards': len(report['guards']), 'lifecycle_contrast_files': len(report['lifecycle_contrasts'])}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate', action='store_true')
    parser.add_argument('--zstd-library')
    parser.add_argument('--output', default='boundary-fill-result-decoding.json')
    args = parser.parse_args()
    if not args.validate:
        parser.error('Use --validate for focused saved-file validation')
    zstd = args.zstd_library or next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    result = validate(zstd)
    Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['summary'], sort_keys=True))
