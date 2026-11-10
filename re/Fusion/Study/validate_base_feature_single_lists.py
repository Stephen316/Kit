"""Saved singleton BaseFeature framing, reciprocal ownership and partial scope."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from decode_base_feature_single_lists import decode_base_feature_single_lists, decode_base_feature_single_list
from decode_base_feature_empty_lists import decode_base_feature_empty_lists
from decode_direct_body_features import decode_direct_body_features
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
CAPTURE = 'meshconvertoperations-5af73924aa60'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(root, zstd):
    folder = root/CAPTURE
    truth = json.loads((folder/'ground_truth.json').read_text())
    journal = [json.loads(line) for line in (folder/'journal.jsonl').read_text().splitlines() if line]
    assert (folder/'complete.txt').is_file() and not truth['errors'] and len(truth['samples']) == 3
    assert journal[-1]['phase'] == 'batch_complete' and journal[-1]['sample_count'] == 3 and journal[-1]['error_count'] == 0
    closes = [e for e in journal if e['phase'] == 'owned_document_close_returned']
    assert len(closes) == 3 and all(e['returned'] is True and e['save'] is False for e in closes)
    assert sha(folder/'executed-generator-source.txt') == truth['executed_generator_sha256']
    report = dict(interface='decode_base_feature_single_lists(data,records,features,*,body_selections=None)->partial/unresolved/scope',
        capture=CAPTURE, samples=[], guards=[], old_controls=[],
        actual_terminal_journal=journal[-1], actual_close_journal=closes,
        executed_generator_sha256=truth['executed_generator_sha256'])
    saved = None
    for actual in truth['samples']:
        archive = CAPTURE+'/'+actual['file']
        data, records, features, _, _ = load(root, archive, zstd)
        before = copy.deepcopy(features)
        decoded = decode_base_feature_single_lists(data, records, features)
        checks = dict(export_hash_matches=sha(root/archive) == actual['export']['sha256'],
            actual_close_true=actual['close_owned_document_returned'] is True,
            top_level_getters_and_active_input_getters_healthy=actual['getter_errors'] == [] and actual['input_before_add']['input_getter_errors'] == [],
            features_unchanged=features == before, no_unresolved=not decoded['unresolved'])
        if actual['case'].startswith('base_feature_'):
            assert len(decoded['partial']) == 1
            row = decoded['partial'][0]
            bases_before = actual['history_before_convert']['base_features'];bases_after = actual['history_after_convert']['base_features']
            added = [b for b in bases_after if b['name'] not in {old['name'] for old in bases_before}]
            checks.update(
                actual_documented_null_recorded=actual['convert_status'] == 'NullReturnedNonParametricOperation' and actual['actual_returned_identity'] is None,
                actual_Convert_collection_remains_zero=actual['convert_collection_count_before'] == actual['convert_collection_count_after'] == 0,
                actual_exactly_one_added_BaseFeature=len(bases_before) == 1 and len(bases_after) == 2 and len(added) == 1,
                actual_BaseFeature_healthy=added[0]['healthState'] == 0 and added[0]['errorOrWarningMessage'] == '',
                actual_single_BRep_source_and_result=len(added[0]['brep_source_bodies']) == len(added[0]['brep_bodies']) == actual['component_brep_after_convert']['count'] == 1,
                stored_empty_name_not_API_display_name=row['stored_name'] == '' and row['name'] is None and added[0]['name'] == 'Base Feature2',
                explicit_singleton_and_anchor_counts=len(row['stored_body_table_object_ids']) == len(row['result_anchor_object_ids']) == len(row['anchored_result_native_body_object_ids']) == 1,
                distinct_native_table_and_anchored_result=row['stored_body_table_object_ids'][0] != row['anchored_result_native_body_object_ids'][0],
                source_mesh_and_lifecycle_unqualified=row['source_mesh_object_id'] is None and row['PM_DM_body_pair_semantics'] is None and row['entire_contained_object_state'] is None,
                exact_full_payload_replay=row['stored_payload']['exact_full_payload_replay'] is True,
                old_direct_reader_failure_retained=any(r['feature_object_id'] == row['feature_object_id'] and r['reason'] == 'Unobserved BaseFeature single-pair/list framing' for r in decode_direct_body_features(data, records)['unresolved']))
            saved = data, records, features, row
        else:
            checks['no_false_singleton_for_two_mesh_Parametric'] = decoded['partial'] == []
            checks['Parametric_return_separately_recorded'] = actual['convert_status'] == 'ObjectReturned' and actual['actual_returned_identity']['objectType'] == 'adsk::fusion::MeshConvertFeature'
        assert all(checks.values()), (archive, checks)
        report['samples'].append(dict(archive=archive, archive_sha256=sha(root/archive), expected_decoded=decoded,
            checks=checks, actual_operation_input=actual['input_before_add'],
            actual_BaseFeatures_before=actual['history_before_convert']['base_features'], actual_BaseFeatures_after=actual['history_after_convert']['base_features']))
    # Default existing readers are untouched; independently stored old outputs stay exact.
    paired = json.loads((root/'direct-body-feature-decoding.json').read_text())['samples'][0]
    data, records, features, _, _ = load(root, paired['file'], zstd)
    assert decode_direct_body_features(data, records) == paired['expected_summary']
    assert decode_base_feature_single_lists(data, records, features)['partial'] == []
    report['old_controls'].append(dict(archive=paired['file'], prior_paired_summary_exact=True, no_false_singleton=True))
    old = next(r for r in json.loads((root/'base-feature-empty-list-decoding.json').read_text())['samples'] if r['archive'] == 'meshcontrasts-10c2557c91a3/stl_centimeter.f3d')
    data, records, features, _, _ = load(root, old['archive'], zstd)
    assert decode_base_feature_empty_lists(data, records, features) == old['expected_decoded']
    assert decode_base_feature_single_lists(data, records, features)['partial'] == []
    report['old_controls'].append(dict(archive=old['archive'], prior_empty_list_summary_exact=True, no_false_singleton=True))
    data, records, features, row = saved
    primary = {r.object_id:r for r in records if r.is_primary}
    feature = next(f for f in features if f['object_id'] == row['feature_object_id'])
    def guard(label, identity, offset, replacement):
        changed = bytearray(data);record = primary[identity]
        changed[record.body+offset:record.body+offset+len(replacement)] = replacement
        try:
            decode_base_feature_single_list(bytes(changed), records, feature)
        except (ValueError, IndexError, struct.error, UnicodeError) as error:
            report['guards'].append(dict(check=label, passed=True, reason=str(error)))
        else:
            raise AssertionError(label)
    identity = row['feature_object_id']
    guard('Count2 is not singleton branch', identity, 1, struct.pack('<I',2))
    guard('Repeated table body must agree', identity, 35, b'\1'+struct.pack('<Q',row['anchored_result_native_body_object_ids'][0])+bytes(2))
    guard('Controller owner must reciprocate', row['controller']['object_id'], 14, b'\1'+struct.pack('<Q',204)+bytes(2))
    guard('Owned result anchor owner must agree', row['result_anchor_object_ids'][0], 91, b'\1'+struct.pack('<Q',204)+bytes(2))
    guard('Uncontrasted metadata remains literal5', identity, 179, struct.pack('<I',2))
    guard('Stored empty name cannot become captured display name', identity, 219, struct.pack('<I',1))
    report['summary'] = dict(actual_saved_files=3, partial_singleton_definitions=2, old_default_summary_controls=2,
        malformed_guards=len(report['guards']), checks=sum(len(r['checks']) for r in report['samples']), full_main_runs=0, live_API_calls=0)
    report['source_sha256'] = {name:sha(root/name) for name in ('decode_base_feature_single_lists.py','validate_base_feature_single_lists.py',
        'decode_base_feature_empty_lists.py','decode_direct_body_features.py','decode_body_selections.py','decode_timeline.py')}
    report['limitations'] = ['The native stored name is empty; API Base Feature2 is retained only as an independent display getter.',
        'Native body table and result anchor establish distinct serialized identities. No source mesh ID, reciprocal PM/DM pair or conversion operation is inferred from the capture cause.',
        'Only the observed singleton definition is partial. Existing unsupported BaseFeature and current mesh diagnostics remain; general direct edits, history replay, final visibility and regeneration are unresolved.',
        'Result BODY/ASM identity proof belongs to the separate result-context helper; this definition does not choose bodies by coordinates or list order.']
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zstd-library', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT/'base-feature-single-list-decoding.json')
    args = parser.parse_args();report = validate(ROOT, args.zstd_library)
    args.output.write_text(json.dumps(report, indent=2)+'\n');print(json.dumps(report['summary'], sort_keys=True))
