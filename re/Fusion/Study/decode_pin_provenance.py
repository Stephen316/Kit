"""Observed native Pin feature -> owned context frame -> occurrence provenance.

A native Pin record is historical structural evidence. No general current
Occurrence.isGrounded state, suppression effect or joint solving is inferred.
"""

import argparse
import json
from pathlib import Path
import struct
import uuid

from decode_assembly import (OCCURRENCE_GUID, OCCURRENCE_COLLECTION_GUID,
                             occurrence as decode_native_occurrence,
                             collection as decode_native_collection)
from decode_parameters import read_string
from decode_placement import IDENTITY
from decode_sketch import reference

PIN = '21E03EC1-0E53-406D-A852-6D088D4D1E95'
FRAME = '2E3AC990-483D-4A55-8662-C064B976A957'
LINK = '549FBB80-B890-473E-A5C0-415D3D9BF4E6'
WRAPPER = 'FF415D89-A1DB-44AC-B824-E9A772B86ED4'
ROUTE = '96CBEA21-17E0-4BCB-BA77-04EA87B47934'


def decode_pin_provenance(data, records, assembly, features=None):
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: items[0] for identity, items in grouped.items() if len(items) == 1}
    components = {item['object_id']: item for item in assembly['components']}
    occurrences = assembly['native_occurrences']
    feature_map = {f['object_id']: f for f in (features or [])}
    decoded, unresolved = [], []

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Pin typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    def uuid_text(payload, position):
        text, cursor = read_string(payload, position)
        if len(text) != 36:
            raise ValueError('Pin occurrence route UUID length unsupported')
        uuid.UUID(text)
        return text, cursor

    for record in records:
        if not record.is_primary or record.class_guid != PIN:
            continue
        try:
            owner = record.object_id
            if primary.get(owner) != record:
                raise ValueError('Ambiguous native Pin feature identity')
            body = data[record.body:record.end]
            if len(body) != 189 or body[:3] != b'\0\0\1':
                raise ValueError('Unobserved native Pin feature layout')
            frame_id = reference(body, 3)
            _, frame = typed(frame_id, FRAME)
            if (len(frame) != 78 or frame[:20] != bytes(20)
                    or struct.unpack_from('<I', frame, 20)[0] != 3 or frame[24:37] != bytes(13)
                    or frame[48:50] != b'\1\0' or reference(frame, 50) != owner
                    or frame[72:] != struct.pack('<I', 1)+bytes(2)):
                raise ValueError('Pin context frame layout/reciprocal owner unsupported')
            link_id = reference(frame, 37)
            _, link = typed(link_id, LINK)
            if (len(link) != 85
                    or link[:38] != bytes.fromhex('0000000000000000000000000000030100000001000000010200000000000000000101000000')
                    or link[49:59] != bytes.fromhex('01000000020000000100')
                    or link[70:73] != b'\1\1\1' or link[84:] != b'\1'
                    or reference(link, 73) != owner):
                raise ValueError('Pin context link layout/reciprocal owner unsupported')
            component_id = reference(link, 38)
            typed(component_id, 'E03784ED-5E19-4E14-B9F2-3B07017018CD')
            if component_id not in components:
                raise ValueError('Pin context link owning component unresolved')
            scope_id = reference(link, 59)
            typed(scope_id, '54F9ACE8-B5B8-4A6E-B582-64F629511DE4')
            feature = feature_map.get(owner)
            if feature is not None and feature.get('component_object_id', component_id) != component_id:
                raise ValueError('Pin feature and context-link component owners disagree')
            wrapper_id = reference(frame, 61)
            _, wrapper = typed(wrapper_id, WRAPPER)
            if len(wrapper) != 18 or wrapper[:7] != bytes.fromhex('00000001000000'):
                raise ValueError('Unobserved Pin single-route wrapper prefix/count')
            route_id = reference(wrapper, 7)
            _, route = typed(route_id, ROUTE)
            if len(route) != 406 or route[:6] != bytes.fromhex('000001000000'):
                raise ValueError('Unobserved Pin single-occurrence route')
            occurrence_guid, cursor = uuid_text(route, 6)
            namespace, cursor = uuid_text(route, cursor)
            entity_guid, cursor = uuid_text(route, cursor)
            if route[cursor:cursor+8] != struct.pack('<Q', 2):
                raise ValueError('Pin route endpoint count/header unsupported')
            repeated_namespace, cursor = uuid_text(route, cursor+8)
            endpoint_guid, cursor = uuid_text(route, cursor)
            if repeated_namespace != namespace or route[cursor:] != struct.pack('<QI', 2, 0):
                raise ValueError('Pin route repeated namespace/footer mismatch')
            matches = [o for o in occurrences if o['instance_guid_text'] == occurrence_guid]
            if len(matches) != 1 or matches[0]['component_object_id'] not in components:
                raise ValueError('Pin route instance GUID does not select one known native occurrence')
            occurrence = matches[0]
            occurrence_record, _ = typed(occurrence['object_id'], OCCURRENCE_GUID)
            raw_occurrence = decode_native_occurrence(data[occurrence_record.payload_start:occurrence_record.end], occurrence['object_id'])
            if (raw_occurrence['instance_guid_text'] != occurrence_guid
                    or raw_occurrence['component_object_id'] != occurrence['component_object_id']):
                raise ValueError('Pin route and independently framed native occurrence disagree')
            collection_id = raw_occurrence['parent_collection_object_id']
            collection_record, _ = typed(collection_id, OCCURRENCE_COLLECTION_GUID)
            collection = decode_native_collection(data[collection_record.body:collection_record.end], collection_id)
            if (collection['component_object_id'] != component_id
                    or occurrence['object_id'] not in collection['occurrence_object_ids']):
                raise ValueError('Pin target occurrence is not a direct reciprocal member of the owner component collection')
            paths = [p for p in assembly.get('occurrence_paths', []) if p['native_occurrence_object_id'] == occurrence['object_id']]
            decoded.append({'feature_object_id': owner, 'feature_class_guid': PIN,
                            'native_kind_label': 'Pin', 'frame_object_id': frame_id,
                            'frame_link_object_id': link_id, 'owner_component_object_id': component_id,
                            'owner_component_name': components[component_id]['name'], 'scope_reference_object_id': scope_id,
                            'route_wrapper_object_id': wrapper_id, 'route_object_id': route_id,
                            'native_occurrence_object_id': occurrence['object_id'],
                            'native_occurrence_class_guid': primary[occurrence['object_id']].class_guid,
                            'target_component_object_id': occurrence['component_object_id'],
                            'target_component_name': components[occurrence['component_object_id']]['name'],
                            'target_parent_occurrence_collection_object_id': collection_id,
                            'occurrence_paths': [p['path'] for p in paths], 'instance_number': occurrence['instance_number'],
                            'instance_guid_text': occurrence_guid, 'route_namespace_text': namespace,
                            'route_entity_guid_text': entity_guid, 'route_endpoint_guid_text': endpoint_guid,
                            'stored_context_matrix': list(IDENTITY),
                            'association': 'Pin explicitly references typed frame; frame and context link reciprocally reference Pin; route instance GUID uniquely matches decoded native occurrence',
                            'verified_current_is_grounded': None,
                            'state_scope': 'Historical native Pin provenance only; current isGrounded getter unavailable, suppression/lifecycle effects and grounding/kinematic solving not applied',
                            'matrix_scope': 'Stored context identity encoding; no solved assembly placement inferred'})
        except (ValueError, KeyError, IndexError, struct.error) as error:
            unresolved.append({'feature_object_id': record.object_id, 'class_guid': PIN, 'reason': str(error)})
    return {'decoded': decoded, 'unresolved': unresolved,
            'scope': 'Observed one-frame Pin feature provenance; no general current grounding state or joint solving'}


def validate_fixtures(root, zstd_library):
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records

    folder = root/'jointmodes-20d3aef2a07d'
    truth = json.loads((folder/'ground_truth.json').read_text())
    assert len(truth['samples']) == 8 and not truth['errors'] and (folder/'complete.txt').is_file()
    report = {'api_version': truth['fusion_version'], 'samples': [], 'negative_checks': [],
              'interface': 'decode_pin_provenance(data,records,assembly,features=None)',
              'request_evidence': {'source': 'GenerateJointModes.py', 'statement': 'occurrences[0].isGrounded = True', 'occurrence_component_name': 'Fixed',
                                   'scope': 'Generator request; captures save occurrence names/transforms but no isGrounded getter. Native Pin association is verified separately.'},
              'validation_command': 'python3 decode_pin_provenance.py --validate --zstd-library <local libzstd path>'}
    for sample in truth['samples']:
        archive = folder/sample['file']
        main = decode_basics(archive, zstd_library)
        stream = next(s for s in main['streams'] if s.get('assembly_decoding', {}).get('native_occurrences'))
        members = read_members(archive, zstd_library)
        data = members[stream['member']]
        records, _ = design_records(data, members.get(stream['member'].replace('BulkStream.dat','MetaStream.dat')))
        by = {r.object_id: r for r in records if r.is_primary}
        out = decode_pin_provenance(data, records, stream['assembly_decoding'], stream['features'])
        assert len(out['decoded']) == 1 and not out['unresolved'], (sample['file'], out)
        item = out['decoded'][0]
        actual = [o for o in sample['occurrences'] if o['component_name'] == item['target_component_name']]
        checks = {'one_owned_pin_route_resolves': len(out['decoded']) == 1,
                  'target_component_matches_requested_fixed': item['target_component_name'] == 'Fixed',
                  'target_occurrence_path_matches_independent_actual_name': len(actual) == 1 and item['occurrence_paths'] == [actual[0]['name']],
                  'target_matches_actual_joint_second_occurrence': item['occurrence_paths'] == [sample['settings']['occurrence_two_name']],
                  'current_grounded_state_not_invented': item['verified_current_is_grounded'] is None,
                  'actual_capture_has_no_grounded_getter': all('is_grounded' not in o and 'isGrounded' not in o for o in sample['occurrences'])}
        assert all(checks.values()), (sample['file'], checks)
        report['samples'].append({'archive': str(archive.relative_to(root)), 'checks': checks, 'decoded': item,
                                  'actual_occurrence_names': [o['name'] for o in sample['occurrences']]})
        negative_case = data, records, stream, by, item
    data, records, stream, by, item = negative_case
    frame = by[item['frame_object_id']]
    link = by[item['frame_link_object_id']]
    wrapper = by[item['route_wrapper_object_id']]
    route = by[item['route_object_id']]
    existing = item['instance_guid_text']
    changed_guid = ('0' if existing[0] != '0' else '1')+existing[1:]
    for label, offset, replacement in [('Frame reciprocal Pin owner mismatch', frame.body+51, struct.pack('<Q', 999999)),
                                        ('Context link reciprocal Pin owner mismatch', link.body+74, struct.pack('<Q', 999999)),
                                        ('Route wrapper count unsupported', wrapper.body+3, struct.pack('<I', 2)),
                                        ('Route valid UUID absent from native occurrences', route.body+10, changed_guid.encode('utf-16le'))]:
        changed = bytearray(data)
        changed[offset:offset+len(replacement)] = replacement
        out = decode_pin_provenance(bytes(changed), records, stream['assembly_decoding'], stream['features'])
        assert not out['decoded'] and len(out['unresolved']) == 1, (label, out)
        report['negative_checks'].append({'check': label, 'passed': True, 'reason': out['unresolved'][0]['reason']})
    report['limitations'] = ['No saved API isGrounded getter: generator request, native Pin provenance and verified current state remain distinct.',
                             'Only observed single root-level target routes, reciprocal owner links and identity-encoded frames supported; nested routes/alternate frame matrices unsupported.',
                             'Route namespace/entity/endpoint UUIDs retained without geometric meaning; target occurrence comes from exact instance-GUID equality, never coordinates or names.',
                             'No suppression/lifecycle grounding semantics or assembly/joint solving applied.']
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate', required=True, action='store_true')
    parser.add_argument('--zstd-library', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path(__file__).with_name('pin-provenance-decoding.json'))
    args = parser.parse_args()
    report = validate_fixtures(Path(__file__).resolve().parent, args.zstd_library)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'samples': len(report['samples']), 'negative_checks': len(report['negative_checks']), 'output': str(args.output)}))
