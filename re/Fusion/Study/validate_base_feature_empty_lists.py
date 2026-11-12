"""Focused ten-file empty-list BaseFeature provenance and paired-body controls."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from decode_base_feature_empty_lists import BASE_FEATURE, decode_base_feature_empty_lists
from decode_basics import decode_basics
from decode_direct_body_features import decode_direct_body_features
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT = Path(__file__).resolve().parent
FILES = (
    'meshcontrasts-10c2557c91a3/stl_centimeter.f3d',
    'meshcontrasts-10c2557c91a3/stl_millimeter.f3d',
    'meshcontrasts-10c2557c91a3/triangle_data_centimeter.f3d',
    'meshplanecuts-18f2683c83f5/split_body_minimal_fill.f3d',
    'meshplanecuts-18f2683c83f5/trim_minimal_fill.f3d',
    'meshplanecuts-18f2683c83f5/trim_no_fill.f3d',
    'meshreduces-780954a23308/adaptive_count_six.f3d',
    'meshreduces-780954a23308/adaptive_proportion_fifty.f3d',
    'meshreduces-780954a23308/uniform_count_six.f3d',
    'meshreduces-8f01528f7f21/adaptive_proportion_fifty.f3d',
)
PAIR_CONTROLS = ('splinepatches-ac5e846e59c0/splinepatches.f3d',
                 'splinepatches-900d152c2380/splinepatches.f3d')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(zstd):
    cache_path = Path('/private/tmp/fusion-mesh-operations-outputs.json')
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else None
    outputs = dict(zip(cache['files'], cache['after'])) if cache else {}
    truths = {}
    report = {'scope': 'Ten saved Mesh/PlaneCut/Reduce BaseFeatures with absent pair branch and zero result-anchor list, plus two paired-body control archives; no full corpus/main rerun or live calls',
        'interface': 'decode_base_feature_empty_lists(data,records,features)->partial/unresolved/scope; partial rows contain definition/controller/ownership/history only, no kind/tool_settings and no feature mutation',
        'integration': 'Optional partial provenance attachment by feature_object_id; keep UnsupportedFeature, old direct-body diagnostic, discovery counts, timeline kind, mesh owners, body properties and placements unchanged',
        'schema': {'initial_prefix_hex': '0001000000000000000001000000000000',
            'controller_ref': 17, 'reserved_uint32': 28, 'result_anchor_count': 32,
            'nil_uuid_string': 44, 'repeated_controller_ref': 127, 'raw_metadata_uint32': 138,
            'kind_label_string': 142, 'metadata_semantics': 'Literal2, no interpretation',
            'controller': '71bytes; owner refs14/60; literal separator20zero+010000 before typed bookkeepingref48; bookkeeping39bytes/backlink12; opaque8bytes retained',
            'ownership': 'Inherited CB owners of feature/controller agree; typed3A6D collection/inherited834C counted membership unique; C342 container footer collection backlink at end-22',
            'history': 'C342 footer explicit typed2F4 historyref at end-55; history owner matches container and counted list contains feature exactly once'},
        'samples': [], 'controls': [], 'malformed_guards': [],
        'limitations': ['Absent stored body-pair branch and zero result anchors do not mean every possible contained-object category is empty.',
            'No MeshBody is assigned to this BaseFeature: captured mesh native/API ownership remains separately qualified.',
            'Original MeshContrasts vector getter failures remain None/errors; they are not evidence for empty lists.',
            'MeshReduce base timeline getter used feature.timelineObject, not base.timelineObject; its NameError and later wrong-source index are retained as generator limitations, not BaseFeature timeline truth.',
            'Native ordered history entry position is explicit provenance, not general edit-state, solver or current/final lifecycle evidence.']}
    contexts = []
    reliable_empty = vector_errors = 0

    def load(filename):
        members = read_members(ROOT/filename, zstd)
        output = outputs.get(filename)
        if output is None:
            output = decode_basics(ROOT/filename, zstd)
        stream, = output['streams']
        data = members[stream['member']]
        records, _ = design_records(data, members[stream['member'].replace('BulkStream.dat', 'MetaStream.dat')])
        return data, records, stream['features']

    for filename in FILES:
        data, records, features = load(filename)
        before = copy.deepcopy(features)
        direct_before = decode_direct_body_features(data, records)
        summary = decode_base_feature_empty_lists(data, records, features)
        assert features == before and not summary['unresolved']
        row, = summary['partial']
        assert 'kind' not in row and 'tool_settings' not in row
        feature, = [f for f in features if f['object_id'] == row['feature_object_id']]
        assert feature['class_guid'] == BASE_FEATURE and feature['kind'] == 'UnsupportedFeature'
        assert row['definition']['stored_result_anchor_count'] == 0
        assert row['definition']['stored_result_anchor_object_ids'] == []
        assert row['definition']['entire_contained_object_state'] is None and row['definition']['mesh_owner_object_ids'] is None
        assert any(e['feature_object_id'] == feature['object_id'] and e['reason'] == 'Unobserved BaseFeature single-pair/list framing' for e in direct_before['unresolved'])
        assert decode_direct_body_features(data, records) == direct_before
        payload = row['stored_payload']
        assert bytes.fromhex(payload['hex']) == data[payload['offset']:payload['end_offset']]
        primary = {r.object_id: r for r in records if r.is_primary}
        controller = primary[row['controller']['object_id']]
        assert bytes.fromhex(row['controller']['payload_hex']) == data[controller.body:controller.end]
        history = primary[row['history']['object_id']]
        assert bytes.fromhex(row['history']['payload_hex']) == data[history.body:history.end]
        directory = Path(filename).parent.as_posix()
        if directory not in truths:
            path = ROOT/directory/'ground_truth.json'
            truths[directory] = json.loads(path.read_text())
        truth = truths[directory]
        sample, = [s for s in truth['samples'] if s['file'] == Path(filename).name]
        if directory == 'meshcontrasts-10c2557c91a3':
            actual = sample['after_edit']
            assert actual['base']['name'] == row['name'] and actual['base']['healthState'] == 0
            assert actual['base_brep_bodies'] == []
            assert actual['base_mesh_bodies'] is None and actual['base_brep_source_bodies'] is None
            errors = [e for e in actual['getter_errors'] if e['getter'] in ('base.meshBodies', 'base.sourceBodies')]
            assert len(errors) == 2 and all('AttributeError' in e['error'] for e in errors)
            evidence = {'actual_after_edit_base': actual['base'], 'actual_brep_bodies': [],
                'mesh_and_source_body_vector_getter_failures': errors,
                'scope': 'Only BRep bodies emptiness was read successfully; failed vector fields remain unknown'}
            vector_errors += 2
        else:
            actual = sample['base_after_edit']
            assert actual['name'] == row['name'] and actual['healthState'] == 0 and not actual['errorOrWarningMessage']
            for key in ('mesh_bodies', 'brep_source_bodies', 'brep_bodies'):
                assert actual[key] == []
            evidence = {'actual_after_edit_base': actual,
                'scope': 'Successful getters return empty BRep and mesh collections at this saved API point; no native mesh-owner link is synthesized'}
            reliable_empty += 1
        report['samples'].append({'archive': filename, 'archive_sha256': digest(ROOT/filename),
            'expected_decoded': summary, 'actual_API_evidence': evidence,
            'full_feature_controller_and_history_byte_replays': True,
            'original_unsupported_feature_and_direct_body_reason_retained': True,
            'feature_mutations': 0})
        contexts.append((data, records, features, row))
    data, records, features, row = contexts[3]
    record, = [r for r in records if r.is_primary and r.object_id == row['feature_object_id']]
    primary = {r.object_id: r for r in records if r.is_primary}
    def reject(label, mutate):
        bad = bytearray(data)
        altered = copy.deepcopy(records)
        mutate(bad, altered)
        result = decode_base_feature_empty_lists(bytes(bad), altered, features)
        assert not result['partial'] and len(result['unresolved']) == 1
        assert features == contexts[3][2]
        report['malformed_guards'].append({'case': label, 'reason': result['unresolved'][0]['reason']})
    reject('Unexpected result-anchor count', lambda b, rs: struct.pack_into('<I', b, record.body+32, 1))
    reject('Unobserved raw metadata', lambda b, rs: struct.pack_into('<I', b, record.body+138, 3))
    controller = primary[row['controller']['object_id']]
    reject('Wrong typed controller class', lambda b, rs: next(r for r in rs if r.is_primary and r.object_id == controller.object_id).__setattr__('class_guid', '00000000-0000-0000-0000-000000000000'))
    reject('Controller copied owner differs', lambda b, rs: struct.pack_into('<Q', b, controller.body+61, controller.object_id))
    bookkeeping = primary[row['controller']['bookkeeping_object_id']]
    reject('Bookkeeping backlink differs', lambda b, rs: struct.pack_into('<Q', b, bookkeeping.body+13, record.object_id))
    reject('Collection inherited membership count differs', lambda b, rs: struct.pack_into('<I', b, row['ownership']['membership_fragment_offset'], 1))
    reject('History container points at collection instead of history', lambda b, rs: struct.pack_into('<Q', b,
        row['history']['container_history_reference_offset']+1, row['ownership']['collection_object_id']))
    history = primary[row['history']['object_id']]
    reject('History owner differs', lambda b, rs: struct.pack_into('<Q', b, history.body+3, row['ownership']['collection_object_id']))
    paired = 0
    historical = json.loads((ROOT/'direct-body-feature-decoding.json').read_text())
    for filename in PAIR_CONTROLS:
        data, records, features = load(filename)
        before = copy.deepcopy(features)
        summary = decode_base_feature_empty_lists(data, records, features)
        assert not summary['partial'] and not summary['unresolved'] and features == before
        direct = decode_direct_body_features(data, records)
        expected, = [s for s in historical['samples'] if s['file'] == filename]
        assert direct == expected['expected_summary']
        paired += sum(r['kind'] == 'BaseFeature' for r in direct['decoded'])
        report['controls'].append({'archive': filename,
            'new_helper_has_no_rows_diagnostics_or_mutation': True,
            'existing_paired_body_output_exact_against_historical_report': True})
    report['provenance'] = {'helper_sha256': digest(ROOT/'decode_base_feature_empty_lists.py'),
        'validator_sha256': digest(ROOT/'validate_base_feature_empty_lists.py'),
        'ground_truth_sha256': {d+'/ground_truth.json': digest(ROOT/d/'ground_truth.json') for d in truths},
        'saved_stage_output_cache_used_for_ten_targets': bool(cache),
        'saved_cache_scope': 'Features from frozen mesh-operation stage only; raw native bytes independently reread from each archive',
        'runtime_classification': 'Partial provenance only; no UnsupportedFeature, discovery, timeline, tool or ownership changes'}
    report['summary'] = {'saved_positive_archives': 10, 'partial_native_definitions': 10,
        'full_feature_controller_history_byte_replay_groups': 10,
        'reliable_API_empty_collection_controls': reliable_empty,
        'retained_original_vector_getter_errors': vector_errors,
        'paired_body_control_archives': 2, 'paired_body_records_preserved_exact': paired,
        'malformed_guards': len(report['malformed_guards']), 'feature_mutations': 0,
        'new_mesh_owner_claims': 0, 'entire_feature_empty_claims': 0, 'live_API_calls': 0}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--zstd-library')
    parser.add_argument('--output', type=Path, default=ROOT/'base-feature-empty-list-decoding.json')
    args = parser.parse_args()
    zstd = args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report = validate(zstd)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
