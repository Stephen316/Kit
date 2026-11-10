"""Saved mixed-collection zero-BRep maps; no live or main-reader execution."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from decode_body_bindings import decode_body_bindings
from decode_body_mapping_variants import decode_body_mapping_variants
from decode_mixed_body_collections import decode_mixed_body_collections
from decode_mixed_empty_body_mappings import decode_mixed_empty_body_mappings
from validate_mesh_remesh import load
from validate_mixed_body_collection_integration import FILES

ROOT = Path(__file__).resolve().parent


def validate(root, zstd, baseline_path):
    baseline = json.loads(baseline_path.read_text())
    assert baseline['baseline_commit'] == '0db5338'
    before = {Path(row['file']).relative_to(root).as_posix(): row for row in baseline['before']}
    assert set(before) == set(FILES)
    report = dict(scope='Exact empty native BRep mappings only; meshes in a component mixed list are never mapped as BRep/ASM roots',
        interface='decode_mixed_empty_body_mappings(data,records,assembly,*,mixed_collections=None,body_properties=None)->decoded/unresolved/scope',
        baseline=dict(commit='0db5338', cache_path=str(baseline_path),
            cache_sha256=hashlib.sha256(baseline_path.read_bytes()).hexdigest(), main_regenerated_by_this_validator=False),
        samples=[], API_count_contrasts=[], old_controls=[], guards=[],
        source_sha256={name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in (
            'decode_mixed_empty_body_mappings.py', 'decode_mixed_body_collections.py',
            'decode_body_mapping_variants.py', 'decode_body_bindings.py', 'decode_body_properties.py',
            'validate_mixed_empty_body_mappings.py')})
    loaded, qualified_by = {}, {}
    for archive in FILES:
        data, records, features, member, members = load(root, archive, zstd)
        loaded[archive] = (data, records, features, member, members)
        original = before[archive]
        stream = next(s for s in original['streams'] if s['member'] == member)
        assembly, properties = stream['assembly_decoding'], stream['body_properties']
        saved_inputs = copy.deepcopy((features, assembly, properties))
        qualified = decode_mixed_body_collections(data, records, assembly, properties)
        summary = decode_mixed_empty_body_mappings(data, records, assembly,
            mixed_collections=qualified, body_properties=properties)
        assert not summary['unresolved'], (archive, summary)
        assert (features, assembly, properties) == saved_inputs, archive
        qualified_by[archive] = qualified
        for row in summary['decoded']:
            assert row['body_count'] == 0 and row['bindings'] == [] and row['history_blob_member'] is None
            assert row['mapping_status'] == 'ExplicitEmptyMappingNoBodiesOrBlob'
            proof = row['mixed_collection_proof']
            assert proof['listed_mesh_object_ids'] and proof['BRep_member_object_ids'] == []
            assert proof['exact_full_mapping_payload_replay'] is True
            assert all(proof[key] is None for key in ('mesh_ASM_binding', 'API_handle_assignment', 'lifecycle'))
            assert len(bytes.fromhex(proof['mapping_payload_hex'])) == 22
            errors = stream['body_blob_bindings']['unresolved']
            assert any(e['object_id'] == row['mapping_record_object_id']
                       and e['reason'] == 'Unsupported native body mapping count' for e in errors)
        report['samples'].append(dict(archive=archive,
            archive_sha256=hashlib.sha256((root/archive).read_bytes()).hexdigest(),
            expected_decoded=summary,
            expected_prior_body_bindings=stream['body_blob_bindings'],
            expected_prior_mapping_variants=stream['body_mapping_variants'],
            input_features_assembly_properties_unchanged=True))
        # The unmodified original readers still report the same pure-empty and
        # positive variants; the new pass only supplies absent mixed-list rows.
        if archive.startswith(('advanced-', 'namedbodies-', 'assembly-')):
            assert not summary['decoded'], archive
            default_variants = decode_body_mapping_variants(data, records, member,
                original['asm_decoding'], properties)
            assert default_variants == stream['body_mapping_variants'], archive
            default_binding = decode_body_bindings(data, records, member,
                original['asm_decoding'], properties)
            for mapping in default_binding['decoded']:
                assert mapping['body_count'] > 0 and mapping['bindings']
            report['old_controls'].append(dict(archive=archive,
                complete_default_mapping_variants_exact=True,
                default_positive_mapping_count=len(default_binding['decoded']),
                existing_explicit_empty_mapping_count=sum(m['body_count'] == 0
                    for m in default_variants['decoded']), new_mixed_mapping_count=0))

    # Independent final API collections corroborate count domains, without
    # assigning individual API handles to native mesh or BRep records.
    for capture in ('meshconverts-4b42d39fb1d5', 'meshconvertoperations-5af73924aa60'):
        truth_path = root/capture/'ground_truth.json'
        truth = json.loads(truth_path.read_text())
        for sample in truth['samples']:
            archive = capture+'/'+sample['file']
            ordinary = [row for row in qualified_by[archive]['decoded']
                        if row['role'] == 'StoredHistoryMapping74CA' and row['component_object_id'] == 3]
            # Pure BRep/no-mesh collections are intentionally outside A's new
            # variant pass; read their already-qualified old body collection.
            stream = before[archive]['streams'][0]
            if ordinary:
                assert len(ordinary) == 1
                body_ids = ordinary[0]['body_member_object_ids']
                mesh_ids = ordinary[0]['mesh_member_object_ids']
            else:
                collection = next(c for c in stream['body_properties']['collections']
                                  if c['object_id'] == 7)
                body_ids, mesh_ids = collection['body_object_ids'], []
            actual_brep_count = sample['component_brep_after_convert']['count']
            actual_mesh_count = sample['component_meshes_after_convert']['count']
            assert len(body_ids) == actual_brep_count and len(mesh_ids) == actual_mesh_count, archive
            report['API_count_contrasts'].append(dict(archive=archive,
                ground_truth_sha256=hashlib.sha256(truth_path.read_bytes()).hexdigest(),
                actual_convert_status=sample['convert_status'],
                actual_component_BRep_count=actual_brep_count, actual_component_mesh_count=actual_mesh_count,
                native_BRep_member_object_ids=body_ids, native_mesh_member_object_ids=mesh_ids,
                individual_native_API_assignment=None,
                scope='Independent count/class contrasts only; failed Prismatic operation stays failed'))

    archive = 'meshconverts-4b42d39fb1d5/prismatic_closed.f3d'
    data, records, _, member, _ = loaded[archive]
    stream = before[archive]['streams'][0]
    assembly, properties = stream['assembly_decoding'], stream['body_properties']
    original = next(s['expected_decoded'] for s in report['samples'] if s['archive'] == archive)
    assert len(original['decoded']) == 1
    identity = original['decoded'][0]['mapping_record_object_id']
    mapping = next(r for r in records if r.is_primary and r.object_id == identity)
    component = next(r for r in records if not r.is_primary and r.object_id == 3
                     and r.class_guid == '42054630-20A0-40E1-B969-CFE9E742F5C9')
    context_id = original['decoded'][0]['context_record_object_id']
    context = next(r for r in records if r.is_primary and r.object_id == context_id)
    changes = (
        ('Nonzero mapping count contradicts exact empty frame', mapping.body+2, struct.pack('<I', 1)),
        ('Mapping owner redirects to auxiliary collection', mapping.body+7, struct.pack('<Q', 22)),
        ('Nonempty filename contradicts empty22-byte frame', mapping.body+18, struct.pack('<I', 1)),
        ('Component ordinary collection slot redirects to auxiliary role', component.body+77, struct.pack('<Q', 22)),
        ('Context component owner loses typed reciprocal association', context.body+13, struct.pack('<Q', 0)))
    for label, offset, value in changes:
        changed = bytearray(data)
        changed[offset:offset+len(value)] = value
        current = decode_mixed_empty_body_mappings(bytes(changed), records, assembly,
                                                  body_properties=properties)
        assert not any(row['mapping_record_object_id'] == identity for row in current['decoded']), label
        report['guards'].append(dict(label=label, recovered_mapping_absent=True,
            new_mapping_diagnostics=current['unresolved']))
    stale = copy.deepcopy(qualified_by[archive])
    stale['decoded'][0]['mesh_member_object_ids'] = [0]
    current = decode_mixed_empty_body_mappings(data, records, assembly,
        mixed_collections=stale, body_properties=properties)
    assert not current['decoded'] and current['unresolved']
    report['guards'].append(dict(label='Supplied mixed-collection proof is stale', reasons=current['unresolved']))
    report['summary'] = dict(focused_archives=len(report['samples']),
        recovered_zero_BRep_mappings=sum(len(s['expected_decoded']['decoded']) for s in report['samples']),
        no_blob_or_mesh_ASM_bindings=True, API_count_contrasts=len(report['API_count_contrasts']),
        pure_empty_positive_control_archives=len(report['old_controls']), malformed_guards=len(report['guards']),
        main_runs=0, live_calls=0)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--zstd-library', required=True)
    parser.add_argument('--baseline-cache', type=Path, default=Path('/private/tmp/fusion-mixed-body-baseline.json'))
    parser.add_argument('--output', type=Path, default=ROOT/'mixed-empty-body-mapping-decoding.json')
    args = parser.parse_args()
    report = validate(args.root.resolve(), args.zstd_library, args.baseline_cache)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps(report['summary']))
