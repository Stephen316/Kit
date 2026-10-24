"""Observed active Mirror feature-compute modes and owned face-plane provenance.

Feature inputs resolve explicit native feature identities. A BRepFace plane
retains recipe/body provenance without supplying an unproved plane equation.
"""

import argparse
import json
import math
from pathlib import Path
import struct
import uuid

from decode_body_tools import decode_body_tool
from decode_body_tool_selections import decode_body_tool_selections
from decode_face_selections import resolve_native_faces
from decode_parameters import read_string
from decode_selection import native_proxy_references
from decode_sketch import attributes, reference, same


MIRROR = 'D1728651-3640-4CCF-8083-AF7703013978'


def decode_mirror_modes(data, records, body, feature, known, features, *, allowed_feature_counts=(1,)):
    if feature['kind'] != 'Mirror' or feature['class_guid'] != MIRROR:
        raise ValueError('Not an observed native Mirror feature')
    result = decode_body_tool(data, records, body, feature, known)
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: items[0] for identity, items in grouped.items() if len(items) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Mirror typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    props, cursor = attributes(body, 2) if body[1] else ({}, 2)
    if props:
        raise ValueError('Unobserved Mirror feature attributes')
    control_id = reference(body, cursor)
    _, control = typed(control_id, 'C444E6AD-33DC-4877-B037-A3A5518856B1')
    if len(control) != 133 or control[:2] != bytes(2) or reference(control, 107) != feature['object_id']:
        raise ValueError('Mirror control count/layout/owner mismatch')
    compute, entity_type = struct.unpack_from('<II', control, 37)
    if compute not in (0, 1, 2) or entity_type not in (1, 2):
        raise ValueError('Unobserved Mirror compute or input entity code')
    if not math.isfinite(result['stitch_tolerance_cm']) or result['stitch_tolerance_cm'] < 0:
        raise ValueError('Invalid Mirror stitch tolerance')
    collection_id = reference(body, cursor+11)
    _, collection = typed(collection_id, '8DB90DAE-3FF5-4E01-BACC-00AAA3EBB3EF')
    count = struct.unpack_from('<I', collection, 6)[0]
    if (collection[:6] != bytes(6) or not 1 <= count <= 1024 or len(collection) != 74+26*count
            or reference(collection, 10+26*count) != feature['object_id']
            or reference(collection, len(collection)-11) != feature['object_id']):
        raise ValueError('Mirror input entity collection count/owners disagree')
    proxy_id = reference(control, 118)
    proxy_record, proxy = typed(proxy_id, '2CA5A1CD-C99B-4C9B-91AF-57989148E841')
    proxy_ids, proxy_props = native_proxy_references(data, proxy_record)
    if proxy_props or reference(proxy, len(proxy)-11) != feature['object_id']:
        raise ValueError('Mirror control input proxy attributes/owner unsupported')
    descriptor_ids = [reference(collection, 10+26*i) for i in range(count)]
    if proxy_ids != descriptor_ids or len(set(descriptor_ids)) != count:
        raise ValueError('Mirror collection and control proxy descriptor lists disagree')
    if entity_type == 1:
        if count not in allowed_feature_counts:
            raise ValueError('Only captured single-Extrude Mirror feature input supported')
        selected = []
        named = {f['object_id']: f for f in features}
        for index, identity in enumerate(descriptor_ids):
            position = 10+26*index
            if struct.unpack_from('<I', collection, position+11)[0] != 1:
                raise ValueError('Mirror input association count unsupported')
            association_id = reference(collection, position+15)
            typed(association_id, 'C46D3EEB-40E1-43FA-83DC-9CB204335417')
            _, descriptor = typed(identity, '5A1BF548-241F-46FD-9FB5-E4B05126EB9D')
            if (len(descriptor) != 263 or descriptor[:2] != bytes(2)
                    or struct.unpack_from('<I', descriptor, 13)[0] != 1
                    or reference(descriptor, 252) != feature['object_id']):
                raise ValueError('Mirror feature descriptor count/owner unsupported')
            namespace, end = read_string(descriptor, 17)
            entity_guid, end = read_string(descriptor, end)
            if len(namespace) != 36 or len(entity_guid) != 36:
                raise ValueError('Mirror feature UUID field size unsupported')
            uuid.UUID(namespace)
            uuid.UUID(entity_guid)
            leaf_id = reference(descriptor, 2)
            _, leaf = typed(leaf_id, '90055C05-546C-4EE7-B3C9-3DD922AD0C9C')
            if len(leaf) != 10 or leaf[:2] != bytes(2):
                raise ValueError('Mirror feature identity leaf framing unsupported')
            source_id = struct.unpack_from('<Q', leaf, 2)[0]
            typed(source_id, 'DD405BC2-D673-44F0-8833-5CB2A1C186C7')
            source = named.get(source_id)
            if (source is None or source['kind'] != 'Extrude' or source['object_id'] == feature['object_id']
                    or source['class_guid'] != primary[source_id].class_guid):
                raise ValueError('Mirror input explicit source Extrude identity unresolved')
            selected.append({'kind': 'Feature', 'descriptor_object_id': identity,
                             'association_record_object_id': association_id, 'terminal_object_id': leaf_id,
                             'source_feature_object_id': source_id, 'source_feature_class_guid': source['class_guid'],
                             'source_feature_kind': source['kind'], 'source_feature_name': source.get('name'),
                             'namespace_text': namespace, 'entity_guid_text': entity_guid,
                             'association': 'Owned collection/proxy agree on descriptor; bounded typed leaf explicitly stores native source feature ID'})
        result.update(input_kind='Feature', input_count=count, input_feature_count=count,
                      input_body_count=0, input_face_count=0, input_features=selected, input_selections=selected,
                      input_entity_collection_object_id=collection_id, input_selection_record_object_ids=[proxy_id],
                      input_selection_status='Explicit owned single-Extrude feature input decoded; feature regeneration not applied' if count == 1
                          else 'Explicit owned ordered Extrude feature inputs decoded; feature regeneration not applied')
    else:
        if compute != 2:
            raise ValueError('Uncaptured stored Mirror body-input compute code')
        selection = decode_body_tool_selections(data, records, [{**feature, 'tool_settings': result}])
        if len(selection['decoded']) != 1 or selection['unresolved']:
            raise ValueError('Mirror body-input selections unresolved')
        result.update(selection['decoded'][0]['settings'])
        if result['input_body_count'] != count or result['input_face_count'] != 0:
            raise ValueError('Mirror body entity code and selected input kinds disagree')
        result.update(input_kind='Body', input_feature_count=0)
    result.update(pattern_entity_type={1: 'Features', 2: 'Bodies'}[entity_type], pattern_entity_type_code=entity_type,
                  pattern_compute_option_code=compute,
                  pattern_compute_option={0: 'Optimized', 1: 'Identical', 2: 'Adjust'}[compute] if entity_type == 1 else None,
                  compute_applies_to_feature_inputs=entity_type == 1,
                  compute_scope='Native control uint32 at37 matches actual Optimized/Identical/Adjust feature-input getters; stored body-input value retained with inactive compute semantics')
    plane_record, plane_proxy = typed(result['plane_selection_record_object_id'], '2CA5A1CD-C99B-4C9B-91AF-57989148E841')
    plane_ids, plane_props = native_proxy_references(data, plane_record)
    if plane_props or len(plane_ids) != 1 or reference(plane_proxy, len(plane_proxy)-11) != feature['object_id']:
        raise ValueError('Mirror plane proxy count/owner unsupported')
    descriptor_kind = ('5662F619-2281-4AD9-93DC-1FCFDA1062E7' if result['plane'] is None
                       else '5A1BF548-241F-46FD-9FB5-E4B05126EB9D')
    _, plane_descriptor = typed(plane_ids[0], descriptor_kind)
    plane_size, count_offset = (276, 15) if result['plane'] is None else (263, 13)
    if (len(plane_descriptor) != plane_size or struct.unpack_from('<I', plane_descriptor, count_offset)[0] != 1
            or reference(plane_descriptor, len(plane_descriptor)-11) != feature['object_id']):
        raise ValueError('Mirror plane descriptor count/owner unsupported')
    if result['plane'] is None:
        faces = resolve_native_faces(data, records, result['plane_selection_record_object_id'], feature['object_id'])
        if faces['attributes'] or len(faces['faces']) != 1 or entity_type != 2:
            raise ValueError('Only captured one face-plane with body input supported')
        result['plane_source'] = {'kind': 'BRepFaceRecipe', **faces['faces'][0],
                                  'selection_object_id': faces['selection_record_object_id'],
                                  'plane_geometry': None,
                                  'geometry_status': 'Owned face recipe and historical support body; native plane origin/normal and exact persistent face identity unresolved'}
        result['plane_selection_status'] = 'Owned BRepFace recipe/body provenance decoded; plane equation unresolved'
    return result


def validate_fixtures(root, zstd_library):
    from decode_basics import decode_basics
    from decode_selection import known_construction_entities
    from fusion_archive import read_members
    from fusion_metadata import design_records

    folder = root/'mirrorfeatures-1ffa1b15c612'
    truth = json.loads((folder/'ground_truth.json').read_text())
    assert (folder/'complete.txt').is_file() and len(truth['samples']) == 4 and not truth['errors']
    report = {'api_version': truth['fusion_version'], 'samples': [], 'negative_checks': [],
              'interface': 'decode_mirror_modes(data,records,body,feature,known,features)',
              'validation_command': 'python3 decode_mirror_modes.py --validate --zstd-library <local libzstd path>',
              'integration': "Call for Mirror instead of base body-tool parser, or fallback to base for unobserved combinations. Body-tool selection pass must skip Mirror input_kind='Feature' already resolved here."}
    for sample in truth['samples']:
        assert not sample['getter_errors']
        archive = folder/sample['file']
        main = decode_basics(archive, zstd_library)
        stream = next(s for s in main['streams'] if any(f['kind'] == 'Mirror' for f in s['features']))
        members = read_members(archive, zstd_library)
        data = members[stream['member']]
        records, _ = design_records(data, members.get(stream['member'].replace('BulkStream.dat','MetaStream.dat')))
        by = {r.object_id: r for r in records if r.is_primary}
        feature = next(f for f in stream['features'] if f['kind'] == 'Mirror')
        record = by[feature['object_id']]
        known = known_construction_entities(data, records, stream['features'])
        direct_feature = {k: v for k, v in feature.items() if k != 'tool_settings'}
        result = decode_mirror_modes(data, records, data[record.body:record.end], direct_feature, known, stream['features'])
        api = sample['settings']
        checks = {'stored_compute_code_matches_actual_getter': result['pattern_compute_option_code'] == api['compute_option'],
                  'combine_matches_actual': result['is_combine'] == api['is_combine'],
                  'tolerance_matches_actual_getter_not_request': same([result['stitch_tolerance_cm']], [api['stitch_tolerance_cm']]),
                  'input_count_matches_actual': result['input_count'] == len(sample['actual_inputs'])}
        if result['input_kind'] == 'Feature':
            checks.update(active_compute_is_explicitly_decoded=result['compute_applies_to_feature_inputs'] and result['pattern_compute_option'] in ('Optimized','Identical','Adjust'),
                          source_feature_types_match_actual=[s['source_feature_kind']+'Feature' for s in result['input_features']] == [a['entity_type'].split('::')[-1] for a in sample['actual_inputs']],
                          ordered_source_feature_names_match_actual=[s['source_feature_name'] for s in result['input_features']] == [a['name'] for a in sample['actual_inputs']],
                          plane_kind_matches_actual=sample['actual_mirror_plane']['entity_type'] == 'adsk::fusion::'+result['plane']['entity']['kind'],
                          plane_origin_normal_match_actual=same(result['plane']['entity']['origin_cm'], sample['actual_mirror_plane']['origin_cm']) and same(result['plane']['entity']['normal'], sample['actual_mirror_plane']['normal']))
            negative_feature_case = data, records, feature, known, stream['features'], by, result
        else:
            properties = {b['object_id']: b for b in stream['body_properties']['bodies']}
            checks.update(body_compute_is_inactive=result['compute_applies_to_feature_inputs'] is False and result['pattern_compute_option'] is None,
                          input_body_names_match_actual=[properties[s['native_body_object_id']]['name'] for s in result['input_selections']] == [a['name'] for a in sample['actual_inputs']],
                          actual_plane_is_face=sample['actual_mirror_plane']['entity_type'] == 'adsk::fusion::BRepFace',
                          face_plane_support_body_matches_actual=properties[result['plane_source']['native_body_object_id']]['name'] == sample['actual_mirror_plane']['source_body']['name'],
                          native_plane_equation_remains_unknown=result['plane'] is None and result['plane_source']['plane_geometry'] is None)
            negative_face_case = data, records, feature, known, stream['features'], by, result
        assert all(checks.values()), (sample['file'], checks)
        report['samples'].append({'archive': str(archive.relative_to(root)), 'checks': checks, 'decoded': result,
                                  'actual_settings': api, 'actual_inputs': sample['actual_inputs'], 'actual_mirror_plane': sample['actual_mirror_plane'],
                                  'source_and_result_scope': 'Actual Feature.bodies includes input and mirrored bodies in these captures; no direct result-body count/topology association inferred from geometry'})
    for case, label, record_id, offset, replacement in [
        (negative_feature_case, 'Unsupported active compute enum', negative_feature_case[-1]['control_record_object_id'], 37, struct.pack('<I', 99)),
        (negative_feature_case, 'Feature descriptor wrong owner', negative_feature_case[-1]['input_features'][0]['descriptor_object_id'], 253, struct.pack('<Q', 999999)),
        (negative_feature_case, 'Explicit source feature absent', negative_feature_case[-1]['input_features'][0]['terminal_object_id'], 2, struct.pack('<Q', 999999)),
        (negative_face_case, 'Face-plane descriptor wrong owner', negative_face_case[-1]['plane_source']['descriptor_object_id'], 266, struct.pack('<Q', 999999))]:
        data, records, feature, known, features, by, result = case
        record = by[record_id]
        changed = bytearray(data)
        changed[record.body+offset:record.body+offset+len(replacement)] = replacement
        feature_record = by[feature['object_id']]
        try:
            decode_mirror_modes(bytes(changed), records, data[feature_record.body:feature_record.end], feature, known, features)
        except (ValueError, KeyError, IndexError, struct.error) as error:
            report['negative_checks'].append({'check': label, 'passed': True, 'reason': str(error)})
        else:
            raise AssertionError(label)
    report['limitations'] = ['Active compute enum/input-kind fields are independently contrasted; only one Extrude feature input and captured body selections supported.',
                             'Face-plane provenance does not establish native plane equation or persistent ASM face identity; plane geometry remains unresolved.',
                             'Body-input compute getter is captured but does not enable active feature-compute semantics.',
                             'Generator requested stitch tolerance0.001cm, but all actual getters and native bindings report0.0001cm; decoder validates actual getter agreement.',
                             'No mirrored result geometry regeneration, face topology reconstruction, occurrence inputs or general feature inputs solved.']
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate', required=True, action='store_true')
    parser.add_argument('--zstd-library', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path(__file__).with_name('mirror-mode-decoding.json'))
    args = parser.parse_args()
    report = validate_fixtures(Path(__file__).resolve().parent, args.zstd_library)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'samples': len(report['samples']), 'negative_checks': len(report['negative_checks']), 'output': str(args.output)}))
