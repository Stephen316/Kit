"""Bounded native naming/vertex joins, measured matrices and getter counterexamples."""

import argparse
import copy
import json
import math
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_basics import decode_basics
from decode_circular_placement_evidence import decode_circular_placement_evidence
from decode_sketch import reference
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT = Path(__file__).resolve().parent
CASES = ['body_full', 'body_negative', 'body_suppressed', 'body_symmetric', 'multiple_customaxis']


def same(a, b):
    return len(a) == len(b) and max(abs(x-y) for x, y in zip(a, b)) < 1e-8


def validate(zstd_library):
    folder = 'circularmodes-45f859c1f1b6'
    truth = json.loads((ROOT / folder / 'ground_truth.json').read_text())
    report = {'scope': 'Five saved root-component body-pattern fixtures; serialized native-key/face-naming/typed-vertex correspondence and cache-derived rigid matrices, preserving old getter warnings',
              'prior_evidence_read': ['circular-cache-rotation-audit.json', 'circular-getter-index-diagnostic.json'],
              'integration': {'function': 'decode_circular_placement_evidence(data,records,features,member,members,body_blob_bindings)',
                              'order': 'After native body/blob mapping recovery; helper independently revalidates raw controller/selection/anchor/BODY-ID chains and source topology',
                              'output': 'Separate decoded/unresolved summary. Do not replace existing pattern_placements or apply measured matrices to existing cache coordinates.',
                              'expected_summary_field': 'cases[].expected_summary',
                              'validation_command': '/usr/bin/python3 validate_circular_placement_evidence.py',
                              'shared_reader_changes_by_this_task': False},
              'method': 'Native element backlink->controller ordinal/key; feature-owned result anchor->native BODY->explicit same-blob stored BODY ID; complete reciprocal per-face counted naming tuples[source,common,key]; uniquely inherited face names->typed vertex incident-face signatures; proper rigid fit only after all eight vertex correspondences are fixed.',
              'cases': [], 'unsupported_controls': [], 'guards': [],
              'limitations': ['Measured matrices describe relative stored cache geometry, not serialized native per-element transform fields, intended transforms, feature recomputation or API getter corrections.',
                              'Count3 naming tuple correspondence is qualified within these owned source/result BODY groups. The common middle component is opaque and never coerced into a design-object ID.',
                              'Only explicit body-input six-face/eight-vertex/twelve-edge caches in one same-asset mapped history blob and identity BODY transform are supported.',
                              'Every face attribute in the chosen BODYs is audited. Unsupported attributes on unrelated geometry kinds do not silently broaden or invalidate this face-specific completeness claim.',
                              'Face and vertex identities are selected only by exact serialized naming and typed incidence. No matching by nearest coordinates, bounds, angles or result-list position is used.',
                              'Native element ordinal minus one is compared with saved API IDs only as a diagnostic in nonsymmetric captures, following existing suppression evidence; symmetric getter ordering remains unresolved.',
                              'Current visibility/final lifecycle, occurrence contexts, feature inputs, arbitrary CAD topology, exact regenerated geometry and native writing remain unsupported.']}
    counts = {'element_groups': 0, 'cache_body_correspondences': 0, 'typed_vertex_pairs': 0, 'suppressed_without_groups': 0}
    maximum_residual = 0.
    for case in CASES:
        relative = folder+'/'+case+'.f3d'; members = read_members(ROOT / relative, zstd_library)
        model = decode_basics(ROOT / relative, zstd_library); stream = model['streams'][0]; member = stream['member']
        records, _ = design_records(members[member], members[member.replace('BulkStream.dat', 'MetaStream.dat')])
        before = copy.deepcopy(stream['pattern_placements'])
        output = decode_circular_placement_evidence(members[member], records, stream['features'], member, members, stream['body_blob_bindings'])
        assert len(output['decoded']) == 1 and not output['unresolved'] and stream['pattern_placements'] == before
        evidence = output['decoded'][0]
        assert any(r['feature_object_id'] == evidence['feature_object_id'] for r in before['unresolved'])
        api = next(s for s in truth['samples'] if s['file'] == case+'.f3d')
        groups = evidence['element_cache_groups']
        assert len(groups) == len(api['pattern_elements'])-1-len(api['settings']['suppressed_element_ids'])
        assert sum(len(g['cache_bodies']) for g in groups)+len(evidence['source_native_body_object_ids']) == api['settings']['result_body_count']
        names = {b['object_id']: b['name'] for b in stream['body_properties']['bodies']}
        assert [names[i] for i in evidence['source_native_body_object_ids']] == api['settings']['input_names']
        getter_diagnostics = []
        for group in groups:
            counts['element_groups'] += 1
            matrices = [b['measured_relative_rigid_fit']['matrix'] for b in group['cache_bodies']]
            assert all(same(matrices[0], m) for m in matrices)
            for body in group['cache_bodies']:
                fit = body['measured_relative_rigid_fit']
                counts['cache_body_correspondences'] += 1; counts['typed_vertex_pairs'] += fit['matched_vertex_count']
                maximum_residual = max(maximum_residual, fit['maximum_vertex_residual_raw'])
                assert fit['matched_vertex_count'] == 8 and fit['maximum_vertex_residual_raw'] < 1e-8
            diagnostic = {'native_element_object_id': group['element_object_id'], 'stored_ordinal': group['stored_ordinal'],
                          'stored_naming_key': group['stored_naming_key'],
                          'typed_result_body_names': [names[b['result_native_body_object_id']] for b in group['cache_bodies']],
                          'measured_z_rotation_degrees_for_these_z_axis_fixtures': math.degrees(math.atan2(matrices[0][4], matrices[0][0]))}
            if not api['settings']['is_symmetric']:
                getter = next(e for e in api['pattern_elements'] if e['id'] == group['stored_ordinal']-1)
                diagnostic.update(saved_API_id_for_existing_nonsymmetric_ordinal_diagnostic=getter['id'],
                                  saved_API_transform=getter['transform'],
                                  saved_API_matrix_matches_measured_cache_matrix=same(getter['transform'], matrices[0]))
                assert not diagnostic['saved_API_matrix_matches_measured_cache_matrix']
            else:
                diagnostic['API_element_association_status'] = 'Unresolved symmetric getter ordering; no ID mapping inferred'
            getter_diagnostics.append(diagnostic)
        counts['suppressed_without_groups'] += len(evidence['suppressed_elements_without_generated_cache_group'])
        report['cases'].append({'file': relative, 'member': member, 'expected_summary': output,
                                'actual_API_settings': api['settings'], 'actual_API_pattern_elements': api['pattern_elements'],
                                'measured_vs_saved_getter_diagnostics': getter_diagnostics,
                                'old_circular_pattern_placement_warning_preserved': True})
        if case == 'body_symmetric':
            # This counterexample disproves accidental ordinal/result-list pairing.
            ordinal_four = next(g for g in groups if g['stored_ordinal'] == 4)
            assert ordinal_four['stored_naming_key'] == 304
            assert names[ordinal_four['cache_bodies'][0]['result_native_body_object_id']] == 'SeedBody0 (1)'
            report['symmetric_nonordinal_key_control'] = {'stored_ordinal': 4, 'stored_naming_key': 304,
                                                        'explicit_result_body_name': 'SeedBody0 (1)',
                                                        'scope': 'Key/naming join is independent of result-list order and suffix numbering'}
        if case == 'body_suppressed':
            assert evidence['suppressed_elements_without_generated_cache_group'][0]['stored_naming_key'] == 304
        if case == 'body_full':
            baseline = (members, stream, records, member, evidence)
    # Existing feature-input captures are explicit unsupported controls, not
    # silently generalized from the body-input naming grammar.
    for case in ('feature_optimized', 'feature_identical'):
        relative = folder+'/'+case+'.f3d'; members = read_members(ROOT / relative, zstd_library)
        stream = decode_basics(ROOT / relative, zstd_library)['streams'][0]; member = stream['member']
        records, _ = design_records(members[member], members[member.replace('BulkStream.dat', 'MetaStream.dat')])
        output = decode_circular_placement_evidence(members[member], records, stream['features'], member, members, stream['body_blob_bindings'])
        assert not output['decoded'] and len(output['unresolved']) == 1
        report['unsupported_controls'].append({'file': relative, 'unresolved': output['unresolved']})
    members, stream, records, member, evidence = baseline
    primary = {r.object_id: r for r in records if r.is_primary}
    def rejected(label, changed_data=None, changed_members=None):
        output = decode_circular_placement_evidence(changed_data or members[member], records, stream['features'], member,
                                                  changed_members or members, stream['body_blob_bindings'])
        assert not output['decoded'] and len(output['unresolved']) == 1
        report['guards'].append({'case': label, 'rejected': True, 'reason': output['unresolved'][0]['reason']})
    element = primary[evidence['element_cache_groups'][0]['element_object_id']]
    changed = bytearray(members[member]); struct.pack_into('<Q', changed, element.body+7, evidence['feature_object_id'])
    rejected('Element controller backlink changed', changed_data=bytes(changed))
    anchor = primary[evidence['element_cache_groups'][0]['cache_bodies'][0]['result_anchor_object_id']]
    changed = bytearray(members[member]); struct.pack_into('<Q', changed, anchor.body+92, evidence['control_record_object_id'])
    rejected('Owned result anchor source-feature backlink changed', changed_data=bytes(changed))
    mapping = primary[evidence['mapping_record_object_id']]
    changed = bytearray(members[member]); struct.pack_into('<Q', changed, mapping.body+6, 999999)
    rejected('Native handle/typed ASM BODY identifier bridge changed', changed_data=bytes(changed))
    blob_member = evidence['history_blob_member']; raw = members[blob_member]; parsed = inspect_asm(raw)
    target = evidence['element_cache_groups'][0]['cache_bodies'][0]
    attribute = parsed['records'][target['result_face_attribute_indices'][0]]
    changed = bytearray(raw); struct.pack_into('<q', changed, attribute['tokens'][4]['offset']+1, 1)
    rejected('Generic face attribute reciprocal owner changed', changed_members={**members, blob_member: bytes(changed)})
    changed = bytearray(raw); struct.pack_into('<q', changed, attribute['tokens'][14]['offset']+1, 2)
    rejected('Counted generated naming tuple size changed', changed_members={**members, blob_member: bytes(changed)})
    point_index = target['measured_relative_rigid_fit']['vertex_correspondence'][-1]['target']['point_index']
    point = parsed['records'][point_index]
    changed = bytearray(raw); struct.pack_into('<d', changed, point['tokens'][3]['offset']+1, point['tokens'][3]['value'][0]+.125)
    rejected('Eighth matched vertex contradicts rigid cache fit', changed_members={**members, blob_member: bytes(changed)})
    report['summary'] = dict(counts, saved_body_pattern_fixtures=5, explicit_feature_input_rejections=2,
                             maximum_typed_vertex_fit_residual_raw=maximum_residual,
                             getter_disagreement_warnings_preserved=5, malformed_guards=len(report['guards']),
                             new_API_calls=0, native_serialized_transform_fields_claimed=0)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='circular-placement-evidence-decoding.json')
    args = parser.parse_args()
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report = validate(str(zstd))
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
