"""Fixed rectangular BODY cache identity joins and measured-transform evidence."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_body_bindings import decode_body_bindings
from decode_rectangular_cache_evidence import decode_rectangular_cache_evidence, SCOPE
import decode_rectangular_cache_evidence as reader
from decode_sketch import reference
from fusion_archive import read_members
from fusion_metadata import design_records
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
POSITIVES = tuple('rectmodes-a069f8f4b8a2/'+name+'.f3d' for name in
    ('body_one', 'body_multiple_customaxis', 'body_sketchlines', 'body_negative')) + (
    'tools-fda3948848f4/RectangularPattern.f3d',
    'rectsymmetry-f09c57dcfd51/symmetric_one.f3d',
    'rectsymmetry-f09c57dcfd51/symmetric_both_even.f3d',
    'rectsymholdouts-cf85ce4a0382/multiple_bodies.f3d')
CONTROLS = ('rectmodes-a069f8f4b8a2/feature_optimized.f3d',
    'circularmodes-45f859c1f1b6/body_full.f3d',
    'surfacetools-856ca50cf4c7/offset_positive.f3d',
    'surfacebounds-ac801bb00fae/untrim_all.f3d')
FILES = POSITIVES+CONTROLS


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(zstd):
    checks, samples, guards = [], [], []
    counts = dict(element_cache_groups=0, result_BODY_correspondences=0, typed_vertex_pairs=0,
        source_BODY_routes=0, symmetric_body_cases=0, seed_nonfirst_controls=0)
    maximum = 0.
    saved = None
    overlap = None

    def check(label, value):
        if not value:
            raise AssertionError(label)
        checks.append(label)

    for archive in FILES:
        data, records, features, member, members = load(ROOT, archive, zstd)
        raw = decode_body_bindings(data, records, member, dict(streams=[dict(member=n,
            complete_token_stream=True, declared_root_records=[]) for n in members if n.endswith('.smbh')]))
        old = copy.deepcopy((features, raw))
        output = decode_rectangular_cache_evidence(data, records, features, member, members, raw)
        check(archive+' input metadata/bindings unchanged', (features, raw) == old)
        sample = dict(archive=archive, archive_sha256=sha(ROOT/archive), member=member, expected_summary=output)
        if archive in CONTROLS:
            check(archive+' complete empty control', output == dict(decoded=[], unresolved=[], scope=SCOPE))
            sample['empty_control'] = True
            samples.append(sample)
            continue
        check(archive+' one qualified Body pattern', len(output['decoded']) == 1 and not output['unresolved'])
        row = output['decoded'][0]
        check(archive+' BODY input retained with unknown API/logical/current identity',
            row['pattern_entity_type'] == 'Bodies' and row['stored_entity_type_code'] == 2
            and row['API_element_identity'] is None and row['logical_grid_identity'] is None
            and row['current_placement'] is None)
        check(archive+' complete key/source product proven before fits', row['complete_controller_source_group_bijection']
            and len(row['element_cache_groups']) == len(row['stored_instance_key_pairs'])
            and not row['stored_suppressed_element_keys'])
        pairs = dict(row['stored_instance_key_pairs'])
        source_ids = set(row['source_native_body_object_ids'])
        result_ids, anchor_ids, actual_product = set(), set(), set()
        for group in row['element_cache_groups']:
            counts['element_cache_groups'] += 1
            check(archive+' explicit controller pair '+str(group['stored_element_key']),
                pairs[group['stored_element_key']] == group['stored_naming_key'])
            check(archive+' every source represented in element group '+str(group['stored_element_key']),
                {b['source_native_body_object_id'] for b in group['cache_bodies']} == source_ids)
            for body in group['cache_bodies']:
                counts['result_BODY_correspondences'] += 1
                binding = body['result_body_binding']
                fit = body['measured_relative_rigid_fit']
                counts['typed_vertex_pairs'] += fit['matched_vertex_count']
                maximum = max(maximum, fit['maximum_vertex_residual_raw'])
                result_ids.add(body['result_native_body_object_id'])
                anchor_ids.add(body['result_anchor_object_id'])
                components = body['stored_face_naming_components']
                source = next(s for s in row['source_cache_bodies'] if s['source_native_body_object_id'] == body['source_native_body_object_id'])
                check(archive+' exact naming-source-key and anchor binding '+str(body['result_native_body_object_id']),
                    components == source['stored_source_naming_prefix']+[row['uninterpreted_common_feature_naming_component'], group['stored_naming_key']]
                    and body['result_body_anchor']['native_body_object_id'] == binding['native_body_object_id'] == body['result_native_body_object_id']
                    and body['result_body_anchor']['source_owner_object_id'] == row['feature_object_id']
                    and binding['stored_handle'] == binding['asm_stored_entity_id'])
                check(archive+' complete eight-vertex fit '+str(body['result_native_body_object_id']),
                    fit['matched_vertex_count'] == 8 and fit['maximum_vertex_residual_raw'] < 1e-8
                    and len({tuple(tuple(v) for v in p['incident_face_name_keys']) for p in fit['vertex_correspondence']}) == 8)
                actual_product.add((group['stored_naming_key'], source['stored_source_naming_prefix'][0]))
        expected = {(key, s['stored_source_naming_prefix'][0]) for key in pairs.values() for s in row['source_cache_bodies']}
        check(archive+' owned result identities form exact complete product', actual_product == expected
            and len(result_ids) == len(anchor_ids) == len(expected)
            and anchor_ids == set(row['owned_result_anchor_object_ids']) and not result_ids & source_ids)
        counts['source_BODY_routes'] += len(source_ids)
        if any(row['stored_symmetry_flags']):
            counts['symmetric_body_cases'] += 1
            check(archive+' symmetric seed is not inferred from array position', row['element_record_keys'].index(1) != 0)
            counts['seed_nonfirst_controls'] += 1
        truth_path = (ROOT/archive).parent/'ground_truth.json'
        truth = json.loads(truth_path.read_text())
        api = next(s for s in truth['samples'] if s['file'] == Path(archive).name)
        sample['saved_API_evidence'] = dict(source=str(truth_path.relative_to(ROOT)), source_sha256=sha(truth_path),
            actual_sample=api, scope='Actual counts/settings/getters only; no API ID, logical grid or per-body API assignment is inferred from order/coordinates')
        if 'settings' in api:
            check(archive+' actual body input/result counts corroborate native routes', api['settings']['pattern_entity_type'] == 2
                and api['settings']['input_count'] == len(source_ids)
                and api['settings']['result_body_count'] == len(source_ids)+len(result_ids)
                and api['settings']['suppressed_element_ids'] == [])
        if archive.endswith('/RectangularPattern.f3d'):
            identity = [1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.]
            coincident = [dict(element_key=g['stored_element_key'], naming_key=g['stored_naming_key'],
                result_native_body_object_id=b['result_native_body_object_id'], binding=b['result_body_binding'])
                for g in row['element_cache_groups'] for b in g['cache_bodies']
                if b['measured_relative_rigid_fit']['matrix'] == identity]
            check('Tool baseline has distinct keyed overlapping cache bodies', len(coincident) == 2
                and len({v['result_native_body_object_id'] for v in coincident}) == 2
                and len({v['naming_key'] for v in coincident}) == 2)
            overlap = dict(archive=archive, coincident_result_bodies=coincident,
                scope='Distinct native/controller/naming identities share relative cached geometry; a coordinate/nearest-fit identity rule would be ambiguous')
        if archive.endswith('/body_multiple_customaxis.f3d'):
            saved = data, records, features, member, members, raw, row
        samples.append(sample)

    data, records, features, member, members, raw, row = saved
    primary = {r.object_id: r for r in records if r.is_primary}
    def rejected(label, changed_data=None, changed_members=None, before_fit=False):
        original_fit = reader._fit
        def forbidden(*_args):
            raise AssertionError('Malformed key/source group reached fitting before complete identity proof')
        if before_fit:
            reader._fit = forbidden
        try:
            out = decode_rectangular_cache_evidence(changed_data if changed_data is not None else data,
                records, features, member, changed_members if changed_members is not None else members, raw)
        finally:
            reader._fit = original_fit
        check(label, not out['decoded'] and len(out['unresolved']) == 1)
        guards.append(dict(guard=label, rejected=True, reason=out['unresolved'][0]['reason'],
            verified_no_fit_before_rejection=before_fit))

    control = primary[row['control_record_object_id']]
    # Locate the explicit pair block by the observed optional-reference frame,
    # not a raw byte search or any grid-coordinate encoding.
    from decode_extrude import optional_reference
    _, cursor = optional_reference(data[control.body:control.end], 114)
    pair_start = cursor+29
    changed = bytearray(data)
    struct.pack_into('<Q', changed, control.body+pair_start+16+8, row['stored_instance_key_pairs'][0][1])
    rejected('Duplicate opaque controller naming key', changed_data=bytes(changed), before_fit=True)
    element = primary[row['element_record_object_ids'][0]]
    changed = bytearray(data)
    struct.pack_into('<Q', changed, element.body+7, row['feature_object_id'])
    rejected('Element controller backlink changed', changed_data=bytes(changed), before_fit=True)
    anchor = primary[row['owned_result_anchor_object_ids'][0]]
    changed = bytearray(data)
    struct.pack_into('<Q', changed, anchor.body+92, row['control_record_object_id'])
    rejected('Owned result anchor feature backlink changed', changed_data=bytes(changed), before_fit=True)
    mapping = primary[row['mapping_record_object_id']]
    changed = bytearray(data)
    struct.pack_into('<Q', changed, mapping.body+6, 999999)
    rejected('Native stored-ID BODY join corrupted', changed_data=bytes(changed), before_fit=True)
    blob_member = row['history_blob_member']
    blob = members[blob_member]
    parsed = inspect_asm(blob)
    first_body = row['element_cache_groups'][0]['cache_bodies'][0]
    attribute_id = first_body['complete_result_face_naming_proof'][0]['owner_attribute_indices'][0]
    attribute = parsed['records'][attribute_id]
    changed = bytearray(blob)
    struct.pack_into('<q', changed, attribute['tokens'][4]['offset']+1, 1)
    rejected('Generic face reciprocal owner changed', changed_members={**members, blob_member: bytes(changed)}, before_fit=True)
    changed = bytearray(blob)
    first_key = row['element_cache_groups'][0]['stored_naming_key']
    other_body = row['element_cache_groups'][1]['cache_bodies'][0]
    for face in other_body['complete_result_face_naming_proof']:
        for aid in face['owner_attribute_indices']:
            attribute = parsed['records'][aid]
            struct.pack_into('<q', changed, attribute['tokens'][-2]['offset']+1, first_key)
    rejected('Duplicate full naming-key/source group fails before fitting',
        changed_members={**members, blob_member: bytes(changed)}, before_fit=True)
    point_id = first_body['measured_relative_rigid_fit']['vertex_correspondence'][-1]['target']['point_index']
    point = parsed['records'][point_id]
    changed = bytearray(blob)
    struct.pack_into('<d', changed, point['tokens'][3]['offset']+1, point['tokens'][3]['value'][0]+.125)
    rejected('Identity-fixed eighth vertex contradicts rigid fit', changed_members={**members, blob_member: bytes(changed)})
    return dict(scope=SCOPE, samples=samples, overlapping_geometry_counterexample=overlap,
        validation=dict(positive_body_archives=len(POSITIVES), complete_empty_controls=len(CONTROLS),
            **counts, maximum_fit_residual_raw=maximum, focused_checks=len(checks), malformed_guards=len(guards),
            no_fit_identity_guards=sum(g['verified_no_fit_before_rejection'] for g in guards),
            main_calls=0, live_API_calls=0),
        checks=checks, malformed_guards=guards,
        integration=dict(callable='decode_rectangular_cache_evidence(data,records,features,member,members,body_blob_bindings)',
            summary='samples[].expected_summary is the full independent helper result, including four empty controls',
            stream='rectangular_cache_evidence', owner_attachment='feature.rectangular_cache_evidence',
            owner_key='feature_object_id', existing_outputs='No tool settings, controls, placements or warnings are changed'),
        source_sha256={f: sha(ROOT/f) for f in ('decode_rectangular_cache_evidence.py',
            'validate_rectangular_cache_evidence.py', 'decode_circular_placement_evidence.py',
            'decode_rectangular_pattern_modes.py', 'decode_body_asm_identifiers.py',
            'decode_body_selections.py', 'decode_asm_recipe_tags.py', 'decode_brep.py')},
        limitations=['No Cantor coordinate decoding or native-key/API-ID association is performed',
            'Measured matrices describe relative stored cache geometry only; no serialized per-element transform, regeneration or current placement claim',
            'Only zero-suppression BODY input with six-face/eight-vertex/twelve-edge identity-transform cache geometry is qualified',
            'Source/result naming groups and all typed vertex identities precede every fit; no result order, bounds or coordinate proximity selects a BODY',
            'Feature inputs are skipped with a complete empty result; symmetry flags remain literal and do not assign logical/API element ordering'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--zstd-library')
    parser.add_argument('--output', default='rectangular-cache-evidence-decoding.json')
    args = parser.parse_args()
    zstd = args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report = validate(zstd)
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['validation'], sort_keys=True))


if __name__ == '__main__':
    main()
