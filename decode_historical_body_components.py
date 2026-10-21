"""Corroborated historical component contexts for mapped, unlisted bodies.

This never restores collection membership or classifies a body as current. The
retained BODY/collection/context chain must agree with an independently reciprocal
creator-anchor and paired dependency-scope chain. Only the observed Extrude and
SurfacePatch single-result-anchor layouts are accepted.
"""

import argparse
import copy
import json
from pathlib import Path
import struct
import uuid

from decode_body_mapping_variants import MAPPING
from decode_body_properties import BODY, COLLECTION
from decode_body_selections import decode_body_selections
from decode_boundary_fill_results import stored_body_membership
from decode_dependencies import GRAPH_GUID, SCOPE_GUID, decode_dependencies
from decode_extrude import optional_reference
from decode_parameters import read_string
from decode_sketch import reference

COMPONENT = 'E03784ED-5E19-4E14-B9F2-3B07017018CD'
CONTEXT = '372234A0-2A6C-4122-8047-E74DBA04F326'
AUXILIARY = 'E55D0457-898F-4A8E-B1A5-C85BDBA8794F'
CREATOR_ANCHOR_OFFSETS = {
    'DD405BC2-D673-44F0-8833-5CB2A1C186C7': ('Extrude', 151),
    'BF77AE1A-E8F6-43AB-A325-A2C984AF1C6B': ('SurfacePatch', 75),
}
SCOPE = ('Historical component context corroborated by retained native collection/context and reciprocal creator/dependency references; '
         'stored membership, current visibility and final lifecycle are unchanged')


def decode_historical_body_components(data, records, bindings, assembly):
    """Return decoded binding patches/unresolved/scope; never mutate inputs.

    Call after typed body/blob associations and before body-cache placement.
    Apply only the two component fields plus historical_component_context to the
    matching binding. Do not update body_properties or collection membership.
    """
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: items[0] for identity, items in grouped.items() if len(items) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Historical component typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    component_groups = {}
    for component in assembly['components']:
        component_groups.setdefault(component['object_id'], []).append(component)
    components = {identity: values[0] for identity, values in component_groups.items()
                  if len(values) == 1 and identity in primary and primary[identity].class_guid == COMPONENT}
    anchors_by_body = {}
    for anchor in decode_body_selections(data, records)['body_anchors']:
        anchors_by_body.setdefault(anchor['native_body_object_id'], []).append(anchor)
    source_ids = {a['source_owner_object_id'] for values in anchors_by_body.values() for a in values}
    source_features = [{'object_id': identity} for identity in source_ids]
    dependencies = decode_dependencies(data, records, source_features, {**assembly, 'components': list(components.values())})
    by_source = {feature['object_id']: feature for feature in source_features}
    bad_dependency_ids = {item['object_id'] for item in dependencies['unresolved']}
    graphs = {g['object_id']: g for g in dependencies['graphs'] if g['object_id'] not in bad_dependency_ids}
    datums = {s['object_id']: s for s in dependencies['component_scope_datums'] if s['object_id'] not in bad_dependency_ids}
    decoded, unresolved, skipped = [], [], 0
    for mapping in bindings['decoded']:
        missing = [entry for entry in mapping['bindings'] if entry.get('component_object_id') is None]
        skipped += len(mapping['bindings']) - len(missing)
        if not missing:
            continue
        for entry in missing:
            identity = entry['native_body_object_id']
            try:
                _, payload = typed(mapping['mapping_record_object_id'], MAPPING)
                if payload[:2] != bytes(2):
                    raise ValueError('Unsupported historical native mapping prefix')
                count = struct.unpack_from('<I', payload, 2)[0]
                end_entries = 6 + 16 * count
                if not 1 <= count <= 100000 or end_entries + 16 > len(payload):
                    raise ValueError('Historical native mapping count exceeds bounds')
                pairs = [struct.unpack_from('<QQ', payload, 6 + 16 * i) for i in range(count)]
                if (count != mapping['body_count'] or pairs != [(b['stored_handle'], b['native_body_object_id']) for b in mapping['bindings']]
                        or len({h for h, _ in pairs}) != count or len({b for _, b in pairs}) != count):
                    raise ValueError('Historical mapping entries disagree with explicit stored identities')
                owner = reference(payload, end_entries)
                if owner != mapping['owner_object_id'] or payload[end_entries + 11] != 0:
                    raise ValueError('Historical mapping owner/separator disagrees')
                filename, end = read_string(payload, end_entries + 12)
                if (end != len(payload) or not filename.startswith('BREP.') or not filename.endswith('.smbh')
                        or '/' in filename or '\\' in filename
                        or not mapping['history_blob_member'].endswith('/Breps.BlobParts/' + filename)):
                    raise ValueError('Historical mapping blob filename framing disagrees')
                uuid.UUID(filename[5:-5])
                typed(identity, BODY)
                membership = stored_body_membership(data, records, identity)
                if membership['referenced_collection_object_id'] != owner:
                    raise ValueError('Historical BODY pointer and explicit mapping owner disagree')
                if membership['is_listed_in_repeated_collection']:
                    raise ValueError('Only missing-owner bodies absent from both member lists are supported')
                _, collection = typed(owner, COLLECTION)
                cursor = 2 if collection[:2] == bytes(2) else 6
                count_members = struct.unpack_from('<I', collection, cursor + 5)[0]
                position = cursor + 9 + 11 * count_members
                if collection[position] != 1:
                    raise ValueError('Historical collection mapping marker unsupported')
                auxiliary, position = optional_reference(collection, position + 1)
                if auxiliary is not None:
                    typed(auxiliary, AUXILIARY)
                if reference(collection, position) != mapping['mapping_record_object_id']:
                    raise ValueError('Historical collection/mapping reference is not reciprocal')
                position += 11
                if collection[position] != 1:
                    raise ValueError('Historical collection context marker unsupported')
                context_id = reference(collection, position + 1)
                _, context = typed(context_id, CONTEXT)
                repeated = len(collection) - 15 - 11 * count_members
                if collection[position + 12:repeated] != b'\0':
                    raise ValueError('Historical collection middle/footer boundary unsupported')
                component = membership['collection_component_object_id']
                if len(context) != 23 or context[:12] != bytes(12) or reference(context, 12) != component:
                    raise ValueError('Historical collection context/component references disagree')
                if component not in components:
                    raise ValueError('Historical collection component has no validated assembly definition')
                anchors = anchors_by_body.get(identity, [])
                if len(anchors) != 1:
                    raise ValueError('Historical BODY creator anchor missing or ambiguous')
                anchor = anchors[0]
                creator_id = anchor['source_owner_object_id']
                creator = primary.get(creator_id)
                if creator is None or creator.class_guid not in CREATOR_ANCHOR_OFFSETS:
                    raise ValueError('Historical BODY creator is outside the observed Extrude/SurfacePatch layouts')
                kind, offset = CREATOR_ANCHOR_OFFSETS[creator.class_guid]
                creator_body = data[creator.body:creator.end]
                if (creator_body[offset - 4:offset] != struct.pack('<I', 1)
                        or reference(creator_body, offset) != anchor['object_id']
                        or creator_body[offset + 11:offset + 19] != bytes(8)):
                    raise ValueError('Historical creator/owned-result-anchor references are not reciprocal')
                namespace, _ = read_string(creator_body, offset + 19)
                if len(namespace) != 36:
                    raise ValueError('Historical creator anchor metadata namespace framing unsupported')
                uuid.UUID(namespace)
                source = by_source.get(creator_id, {})
                if any(table['graph_object_id'] in bad_dependency_ids for table in source.get('native_dependency_tables', [])):
                    raise ValueError('Historical creator dependency graph has unresolved or conflicting scope evidence')
                datum_id = source.get('component_scope_object_id')
                datum = datums.get(datum_id)
                if (datum is None or source.get('component_object_id') != component
                        or datum['component_object_id'] != component):
                    raise ValueError('Historical collection and creator dependency component scopes disagree or are unresolved')
                typed(datum_id, SCOPE_GUID)
                proofs = []
                for table in source.get('native_dependency_tables', []):
                    graph = graphs.get(table['graph_object_id'])
                    if graph is None:
                        continue
                    typed(graph['object_id'], GRAPH_GUID)
                    scope_edges = [e for e in table['edges'] if e['stored_flags'] == 4096 and e['object_id'] == datum_id]
                    if len(scope_edges) == 1:
                        proofs.append({'graph_object_id': graph['object_id'], 'graph_owner_object_id': graph['owner_object_id'],
                                       'component_scope_datum_object_id': datum_id, 'stored_scope_edge_flags': 4096,
                                       'paired_table_validation': graph['validation']})
                if len(proofs) != 1:
                    raise ValueError('Historical creator lacks a unique validated paired dependency-scope proof')
                proof = {'context_kind': 'HistoricalBodyComponentContext',
                         'native_body_object_id': identity, 'collection_object_id': owner,
                         'collection_context_object_id': context_id, 'collection_component_object_id': component,
                         'is_listed_in_repeated_collection': False,
                         'body_anchor_object_id': anchor['object_id'], 'creator_feature_object_id': creator_id,
                         'creator_feature_class_guid': creator.class_guid, 'creator_feature_kind': kind,
                         'creator_anchor_reference_relative_offset': offset, 'dependency_scope_proof': proofs[0],
                         'association': 'Retained typed BODY/collection/context references agree with reciprocal creator/result-anchor and paired dependency component scope',
                         'membership_status': 'Absent from both stored collection member lists; membership is not restored',
                         'visibility_status': 'Historical stored context only; current visibility/final lifecycle unresolved'}
                decoded.append({'mapping_record_object_id': mapping['mapping_record_object_id'],
                                'native_body_object_id': identity, 'component_object_id': component,
                                'component_name': components[component]['name'],
                                'historical_component_context': proof})
            except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
                unresolved.append({'mapping_record_object_id': mapping['mapping_record_object_id'],
                                   'native_body_object_id': identity, 'reason': str(error)})
    return {'decoded': decoded, 'unresolved': unresolved, 'already_owned_body_bindings_unchanged': skipped, 'scope': SCOPE}


def validate(zstd_library):
    from decode_basics import decode_basics
    from decode_body_asm_identifiers import decode_body_asm_identifiers
    from decode_body_placement import decode_body_placement
    from fusion_archive import read_members
    from fusion_metadata import design_records
    from validate_body_asm_identifiers import baseline_bindings
    root = Path(__file__).resolve().parent
    files = ['boundaryfills-a0953038318b/new_middle_remove.f3d',
             'surfacetools-856ca50cf4c7/stitch_tight.f3d', 'surfacetools-856ca50cf4c7/stitch_loose.f3d']
    controls = ['boundaryfills-a0953038318b/new_middle.f3d',
                'namedbodies-3c7c11fc2924/namedbodies.f3d',
                'splinepatches-ac5e846e59c0/splinepatches.f3d',
                'mirrorassemblydatum-700af16e9fc6/nested_occurrence_yz.f3d']
    report = {'scope': SCOPE, 'integration': {
        'function': 'decode_historical_body_components(data, records, bindings, assembly)',
        'order': 'After native body/blob/ASM identifier association, before body placement; assembly components must already be decoded',
        'apply': 'For successful mapping/native-body IDs only, add component_object_id,component_name,historical_component_context to the matching binding',
        'preserve': 'Do not update native body_properties membership/ownership or collection member lists; do not infer a current/final body set',
        'placement_scope': 'Expose historical_component_context on derived placements; coordinates compose stored caches only, without historical assembly-state replay or current-visible-body inference',
        'validation_command': '/usr/bin/python3 decode_historical_body_components.py --validate',
    }, 'native_proof': {
        'collection_chain': 'BODY trailer ->typed collection equals explicit native mapping owner. Collection->mapping is reciprocal; repeated memberlists omit BODY. Collection context and footer independently reference same typed component.',
        'creator_chain': 'Unique typed D263 anchor ->BODY and creator. Known Extrude@151/SurfacePatch@75 single-anchor table reciprocates that exact anchor; bounded following metadata UUID is checked.',
        'dependency_chain': 'Fresh dependency decode validates forward/reverse edge multisets; source creator->scope datum edge4096 resolves to typed component. Collection component and creator scope must agree.',
    }, 'samples': [], 'unchanged_controls': [], 'guards': [], 'limitations': [
        'Only observed Extrude and SurfacePatch single-result-anchor layouts are supported; other creators and ambiguous anchors remain unresolved.',
        'Absent membership stays absent; this does not restore removed/consumed bodies to current collections.',
        'No active/current/final body role, PM/DM source identity, suppression/rollback lifetime or general assembly-state solving is inferred.',
        'Stored cache placement in the corroborated component does not replay that component occurrence history.',
        'Independent API removal/result counts describe features, not a complete native-ID lifecycle oracle.',
    ]}
    contexts = {}

    def prepare(relative):
        path = root / relative
        model = decode_basics(path, zstd_library)
        members = read_members(path, zstd_library)
        stream = model['streams'][0]
        member = stream['member']
        data = members[member]
        records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
        bindings = baseline_bindings(data, records, member, model, stream)
        identifiers = decode_body_asm_identifiers(data, records, member, members, bindings)
        assert not identifiers['unresolved']
        for mapping in bindings['decoded']:
            keyed = next((m for m in identifiers['decoded'] if m['mapping_record_object_id'] == mapping['mapping_record_object_id']), None)
            if keyed:
                patches = {p['native_body_object_id']: p for p in keyed['bindings']}
                for entry in mapping['bindings']:
                    entry.pop('candidate_asm_body_index', None)
                    entry.update(patches[entry['native_body_object_id']])
        return path, model, stream, data, records, bindings

    for relative in files + controls:
        path, model, stream, data, records, bindings = prepare(relative)
        original_bindings = copy.deepcopy(bindings)
        original_properties = copy.deepcopy(stream['body_properties'])
        result = decode_historical_body_components(data, records, bindings, stream['assembly_decoding'])
        assert bindings == original_bindings and stream['body_properties'] == original_properties
        assert not result['unresolved']
        if relative in controls:
            assert not result['decoded']
            report['unchanged_controls'].append({'file': relative, 'existing_binding_and_property_outputs_unchanged': True,
                                                  'owned_body_binding_count': result['already_owned_body_bindings_unchanged']})
            continue
        assert len(result['decoded']) == 2
        before = decode_body_placement(bindings, stream['assembly_decoding'], model['asm_decoding'])
        patched = copy.deepcopy(bindings)
        for patch in result['decoded']:
            mapping = next(m for m in patched['decoded'] if m['mapping_record_object_id'] == patch['mapping_record_object_id'])
            entry = next(e for e in mapping['bindings'] if e['native_body_object_id'] == patch['native_body_object_id'])
            entry.update({key: patch[key] for key in ['component_object_id', 'component_name', 'historical_component_context']})
        after = decode_body_placement(patched, stream['assembly_decoding'], model['asm_decoding'])
        assert len(before['unresolved']) == 2 and not after['unresolved']
        previous = {b['native_body_object_id']: b for b in before['bodies']}
        current = {b['native_body_object_id']: b for b in after['bodies']}
        assert all(current[identity] == body for identity, body in previous.items())
        assert len(after['bodies']) == len(before['bodies']) + 2
        truth = json.loads(path.with_name('ground_truth.json').read_text())
        actual = next(s for s in truth['samples'] if s['file'] == path.name)
        if relative.startswith('boundaryfills-'):
            assert actual['is_remove_tools'] is True and len(actual['tool_names']) == 2
            actions = stream['direct_body_features']['decoded']
            removed_ids = {a['native_body_object_id'] for a in actions if a['kind'] == 'RemoveBody'}
            assert removed_ids == {p['native_body_object_id'] for p in result['decoded']}
            assert all(not p['historical_component_context']['is_listed_in_repeated_collection'] for p in result['decoded'])
            api = {'actual_is_remove_tools': True, 'actual_input_tool_names': actual['tool_names'],
                   'actual_feature_result_names': [b['name'] for b in actual['output_bodies']],
                   'typed_RemoveBody_actions_match_historical_body_ids': sorted(removed_ids),
                   'scope': 'API removal getter plus typed native actions corroborate historical context; no current-visibility inference'}
        else:
            assert actual['settings']['selected_item_count'] == 2 and actual['settings']['result_body_count'] == 1
            assert all(p['historical_component_context']['creator_feature_kind'] == 'SurfacePatch' for p in result['decoded'])
            api = {'actual_selected_item_count': 2, 'actual_feature_result_body_count': 1,
                   'scope': 'Stored source patch contexts remain separate from the stitched result; API counts alone do not establish arbitrary lifetime semantics'}
        report['samples'].append({'file': relative, 'expected_summary': result,
                                  'API_observation': api,
                                  'placement_check': {'previous_body_entries_exact': True, 'new_historical_cache_contexts': 2,
                                                      'before_unresolved_ids': sorted(b['native_body_object_id'] for b in before['unresolved']),
                                                      'after_unresolved': after['unresolved']},
                                  'membership_and_body_properties_unchanged': True})
        contexts[relative] = data, records, bindings, stream['assembly_decoding'], result

    relative = files[0]
    data, records, bindings, assembly, output = contexts[relative]
    by = {r.object_id: r for r in records if r.is_primary}
    patch = next(p for p in output['decoded'] if p['native_body_object_id'] == 275)
    proof = patch['historical_component_context']

    def rejected(label, changed):
        result = decode_historical_body_components(bytes(changed), records, bindings, assembly)
        assert not any(p['native_body_object_id'] == 275 for p in result['decoded'])
        failures = [e for e in result['unresolved'] if e['native_body_object_id'] == 275]
        assert len(failures) == 1, (label, result)
        report['guards'].append({'guard': label, 'rejected': True, 'reason': failures[0]['reason']})

    changed = bytearray(data)
    struct.pack_into('<Q', changed, by[275].end - 10, 22)
    rejected('Retained BODY collection pointer must equal the explicit mapping owner even when both collections share a component', changed)
    changed = bytearray(data)
    creator = by[proof['creator_feature_object_id']]
    struct.pack_into('<Q', changed, creator.body + proof['creator_anchor_reference_relative_offset'] + 1, 358)
    rejected('Creator feature must reciprocate the exact BODY anchor, not another same-component creator anchor', changed)
    changed = bytearray(data)
    anchor = by[proof['body_anchor_object_id']]
    struct.pack_into('<Q', changed, anchor.body + 92, 322)
    rejected('Anchor owner cannot switch to another same-component feature without a reciprocal creator link', changed)
    changed = bytearray(data)
    datum = by[proof['dependency_scope_proof']['component_scope_datum_object_id']]
    struct.pack_into('<Q', changed, datum.body + 4, 202)
    rejected('Creator scope datum component must resolve to a typed component definition', changed)
    changed = bytearray(data)
    graph = by[proof['dependency_scope_proof']['graph_object_id']]
    body = data[graph.body:graph.end]
    position = 3
    row_count = struct.unpack_from('<I', body, position)[0]
    position += 4
    found = None
    for _ in range(row_count):
        row_id = reference(body, position)
        count = struct.unpack_from('<I', body, position + 11)[0]
        position += 15
        for i in range(count):
            target = reference(body, position + 15 * i)
            flags = struct.unpack_from('<I', body, position + 15 * i + 11)[0]
            if row_id == proof['creator_feature_object_id'] and target == datum.object_id and flags == 4096:
                found = graph.body + position + 15 * i + 11
        position += 15 * count
    assert found is not None
    struct.pack_into('<I', changed, found, 1)
    rejected('Forward-only scope-edge flag change must fail paired dependency-table corroboration', changed)
    report['summary'] = {'historical_fixture_files': len(report['samples']),
                         'corroborated_historical_component_contexts': sum(len(s['expected_summary']['decoded']) for s in report['samples']),
                         'missing_cache_contexts_recovered': 6, 'membership_restorations': 0,
                         'unchanged_control_files': len(report['unchanged_controls']), 'malformed_guards': len(report['guards'])}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate', action='store_true')
    parser.add_argument('--zstd-library')
    parser.add_argument('--output', default='historical-body-component-decoding.json')
    args = parser.parse_args()
    if not args.validate:
        parser.error('Use --validate for the focused saved-file checks')
    zstd = args.zstd_library or next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    result = validate(zstd)
    Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['summary'], sort_keys=True))
