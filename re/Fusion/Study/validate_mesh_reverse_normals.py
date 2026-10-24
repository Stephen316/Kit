"""Saved three-document/four-feature ReverseNormal and Cut pool evidence."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from fusion_archive import read_members
from fusion_metadata import design_records
from decode_basics import discover_features
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_normals import decode_mesh_normal_pools
from decode_mesh_reverse_normals import decode_mesh_reverse_normals, REVERSE
from validate_mesh_normals import _direction_error


def validate(zstd):
    root = Path(__file__).resolve().parent
    folder = root/'meshreversenormals-2bc2dd3780cc'
    truth = json.loads((folder/'ground_truth.json').read_text())
    checks, samples, guards, controls = [], [], [], []
    def check(label, condition, **evidence):
        if not condition:
            raise AssertionError(label)
        checks.append({'check': label, **evidence})
    def load(archive):
        members = read_members(root/archive, zstd)
        member = next(k for k in members if k.endswith('/FusionDesignSegmentType1/BulkStream.dat'))
        data = members[member]
        records, index = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
        features = []; discover_features(data, records, features, index)
        mesh = decode_mesh_contents_variants(data, records, member, members)
        return data, records, features, member, members, mesh
    def normal_check(label, mesh, api_mesh):
        pool = decode_mesh_normal_pools(mesh)
        check(label+' normal pool succeeds', len(pool['decoded']) == 1 and not pool['unresolved'])
        flat = api_mesh['display_triangle_mesh']['normalVectorsAsDouble']
        api_vectors = [flat[i:i+3] for i in range(0, len(flat), 3)]
        error = _direction_error(pool['decoded'][0]['derived_asset_unit_vectors'], api_vectors)
        check(label+' actual display directions corroborate independently qualified asset pool', error < 1e-7, max_symmetric_component_discrepancy=error)
        return pool, error, len(api_vectors)
    check('Actual terminal capture with no case errors', (folder/'complete.txt').is_file() and truth['errors'] == [])
    total_features = 0
    for actual in truth['samples']:
        archive = folder.name+'/'+actual['file']
        args = load(archive); data, records, features, member, members, mesh = args
        before = copy.deepcopy(mesh)
        result = decode_mesh_reverse_normals(data, records, features, member, members, mesh)
        check(archive+' exact exported hash and owned close returned true', hashlib.sha256((root/archive).read_bytes()).hexdigest() == actual['export']['sha256'] and actual['close_owned_document_returned'] is True)
        check(archive+' every captured feature independently decoded', len(result['decoded']) == len(actual['steps']) and not result['unresolved'])
        check(archive+' current mesh typed singleton and no geometry diagnostics', len(mesh['decoded']) == 1 and not mesh['unresolved'] and mesh['decoded'][0]['mesh_object_id'] == 213 and mesh['decoded'][0]['collection_mesh_object_ids'] == [213])
        native = mesh['decoded'][0]
        current = actual['component_meshes_after_reverse']
        check(archive+' actual singleton source custom name agrees', current['count'] == 1 and current['meshes'][0]['name'] == native['name'])
        pool, error, count = normal_check(archive, mesh, current['meshes'][0])
        feature_evidence = []
        for row, step in zip(result['decoded'], actual['steps']):
            settings = row['settings']; observed = step['feature_at_timeline_end']
            check(archive+' '+row['name']+' actual feature class/name/health and source equality', observed['objectType'] == 'adsk::fusion::MeshReverseNormalFeature' and observed['name'] == row['name'] and observed['healthState'] == 0 and observed['errorOrWarningMessage'] == '' and step['input_mesh_equals_target'] is True and step['rolled_mesh_equals_target'] is True)
            check(archive+' '+row['name']+' explicit owned proxy descriptor leaf and current native mesh agree', settings['native_mesh_selection']['owner_feature_object_id'] == row['feature_object_id'] and settings['native_mesh_selection']['mesh_object_id'] == settings['qualified_selected_mesh_object_id'] == 213)
            check(archive+' '+row['name']+' literal asset slots distinct typed paramesh assets', settings['asset_at_slot_2']['asset_object_id'] != settings['asset_at_slot_13']['asset_object_id'] and all(settings[k]['asset_member'].endswith('.paramesh') for k in ('asset_at_slot_2', 'asset_at_slot_13')))
            # Source identity is already fixed by typed selection and actual API
            # direct equality, before any numerical asset comparison. These
            # per-capture comparisons do not assign universal temporal slot names.
            asset_comparisons = []
            for slot, api_key in (('asset_at_slot_2', 'component_meshes_after'), ('asset_at_slot_13', 'component_meshes_before')):
                asset = settings[slot]; asset_mesh = copy.deepcopy(native)
                for key in ('asset_object_id', 'asset_member', 'asset_fusion_uuid', 'geometry'):
                    asset_mesh[key] = asset[key]
                api = step[api_key]
                check(archive+' '+row['name']+' '+slot+' actual observed singleton same named mesh', api['count'] == 1 and api['meshes'][0]['name'] == native['name'])
                _, discrepancy, api_count = normal_check(archive+' '+row['name']+' '+slot, {'decoded': [asset_mesh]}, api['meshes'][0])
                asset_comparisons.append({'stored_slot': slot, 'literal_asset_object_id': asset['asset_object_id'], 'saved_API_snapshot': api_key, 'direction_set_max_component_discrepancy': discrepancy, 'actual_API_display_vector_count': api_count, 'scope': 'Comparison for this actual API step only; no universal temporal slot semantics or replay'})
            feature_evidence.append({'feature_object_id': row['feature_object_id'], 'actual_step_index': step['step_index'], 'asset_direction_comparisons': asset_comparisons})
        if actual['case'] == 'closed_twice':
            a, b = [row['settings'] for row in result['decoded']]
            check(archive+' earlier literal slot2 differs from final current and equals later slot13', not a['slot_2_matches_current_native_mesh_asset'] and b['slot_2_matches_current_native_mesh_asset'] and a['asset_at_slot_2']['asset_object_id'] == b['asset_at_slot_13']['asset_object_id'] == 342 and a['other_feature_slot_13_references_to_this_slot_2'] == [{'feature_object_id': 327, 'stored_feature_index': 2, 'shared_asset_object_id': 342}])
        check(archive+' supplied mesh summary unchanged', mesh == before)
        total_features += len(result['decoded'])
        samples.append({'archive': archive, 'expected_decoded': result, 'expected_mesh_contents': mesh, 'expected_normal_pools': pool, 'actual_API_display_vector_count': count, 'direction_set_max_component_discrepancy': error, 'actual_feature_evidence': feature_evidence})
        if actual['case'] == 'closed_once': guard_args = args
    data, records, features, member, members, mesh = guard_args
    record = next(r for r in records if r.is_primary and r.class_guid == REVERSE)
    def guard(label, mutate=None, feature_mutate=None, mesh_mutate=None):
        bad_data = bytearray(data); bad_features = copy.deepcopy(features); bad_mesh = copy.deepcopy(mesh)
        if mutate: mutate(bad_data)
        if feature_mutate: feature_mutate(bad_features)
        if mesh_mutate: mesh_mutate(bad_mesh)
        result = decode_mesh_reverse_normals(bytes(bad_data), records, bad_features, member, members, bad_mesh)
        check(label, not result['decoded'] and len(result['unresolved']) == 1)
        guards.append({'guard': label, 'reason': result['unresolved'][0]['reason']})
    guard('Reject altered stored namespace', lambda d: d.__setitem__(record.body+44, ord('1')))
    guard('Reject altered repeated dependency count', lambda d: struct.pack_into('<I', d, record.body+119, 3))
    guard('Reject distinct asset requirement violation', lambda d: d.__setitem__(slice(record.body+13, record.body+24), d[record.body+2:record.body+13]))
    guard('Reject missing selected current mesh', mesh_mutate=lambda m: m.__setitem__('decoded', []))
    guard('Reject discovery offset disagreement', feature_mutate=lambda f: next(x for x in f if x['object_id'] == record.object_id).__setitem__('record_offset', record.start+1))
    guard('Reject selection owner backlink mismatch', lambda d: d.__setitem__(record.body+30, 2))
    # The Cut current identity is qualified before its unrelated retained-tool
    # diagnostic and numerical pool comparison are considered.
    archive = 'meshcombines-541ebb6cc93f/cut.f3d'
    args = load(archive); mesh = args[-1]
    actual = next(s for s in json.loads((root/Path(archive).parent/'ground_truth.json').read_text())['samples'] if s['file'] == 'cut.f3d')
    check('Cut actual archive hash', hashlib.sha256((root/archive).read_bytes()).hexdigest() == actual['export']['sha256'])
    check('Cut target native identity established, unrelated retained-tool diagnostic preserved', len(mesh['decoded']) == 1 and mesh['decoded'][0]['mesh_object_id'] == 213 and mesh['unresolved'] == [{'mesh_object_id': 226, 'reason': 'Unobserved opt-in native mesh prefix'}])
    pool, error, count = normal_check('Cut26/48/93', mesh, actual['component_meshes_after_combine']['meshes'][0])
    g = mesh['decoded'][0]['geometry']
    check('Only captured Cut tuple26/48/93 added', [len(g['stored_node_coordinates_float32']), len(g['triangle_node_indices'])//3, pool['decoded'][0]['stored_unit_vector_count']] == [26,48,93])
    cut = {'archive': archive, 'expected_normal_pools': pool, 'actual_API_display_vector_count': count, 'direction_set_max_component_discrepancy': error, 'prior_mesh_diagnostics': mesh['unresolved']}
    # Exact prior dictionaries protect both old layouts and prior five-pool stage.
    for report_name in ('mesh-normal-decoding.json', 'mesh-normal-variant-decoding.json'):
        report = json.loads((root/report_name).read_text())
        for old in report['samples']:
            got = decode_mesh_normal_pools(load(old['archive'])[-1])
            encoded = json.dumps(got, sort_keys=True, separators=(',', ':')).encode()
            expected = json.dumps(old['expected_decoded'], sort_keys=True, separators=(',', ':')).encode()
            check(old['archive']+' prior full normal dictionary canonical bytes unchanged', encoded == expected)
            controls.append({'archive': old['archive'], 'report': report_name, 'complete_summary_sha256': hashlib.sha256(encoded).hexdigest(), 'pool_count': len(got['decoded'])})
    bad = copy.deepcopy(mesh['decoded'][0]); block = bad['geometry']['buffers'][2]
    block['uncompressed_payload_hex'] += struct.pack('<2f',0.,0.).hex();block['uncompressed_size'] += 8
    rejected = decode_mesh_normal_pools({'decoded':[bad]})
    check('Reject adjacent unobserved Cut26/48/94 layout', not rejected['decoded'] and bool(rejected['unresolved']))
    guards.append({'guard':'Reject adjacent unobserved Cut26/48/94 layout','reason':rejected['unresolved'][0]['reason']})
    return {'scope': 'Three actual ReverseNormal documents/four features with typed selections/literal asset slots, saved API display-direction holdouts, and separately qualified Cut normal tuple. No shared ownership, geometry parsing or lifecycle changes.', 'sample_count':len(samples), 'decoded_feature_count':total_features, 'check_count':len(checks), 'malformed_guard_count':len(guards), 'samples':samples, 'cut_normal_holdout':cut, 'old_full_dictionary_controls':controls, 'old_normal_pool_dictionary_count':sum(c['pool_count'] for c in controls), 'checks':checks, 'malformed_guards':guards, 'limitations':['Native operation meaning is bounded to actual class/label/owned selection; no regeneration', 'Asset slots and cross-feature IDs literal; comparisons to saved API snapshots do not generalize temporal semantics', 'Display normal pools remain serialized ordered pools, without node/corner identity', 'No original PolygonMesh normal direction equivalence asserted', 'Opaque shared footer/state fields retained without flag meaning', 'Existing unrelated retained-source mesh diagnostics preserved'], 'source_sha256':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ('decode_mesh_reverse_normals.py','decode_mesh_normals.py','decode_mesh_geometry_variants.py','decode_mesh_selections.py','GenerateMeshReverseNormalContrasts.py')}, 'historical_normal_report_sha256':hashlib.sha256((root/'mesh-normal-decoding.json').read_bytes()).hexdigest()}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library');parser.add_argument('--output',default='mesh-reverse-normal-decoding.json');args=parser.parse_args()
    result=validate(args.zstd_library);Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('sample_count','decoded_feature_count','check_count','malformed_guard_count','old_normal_pool_dictionary_count')}))

if __name__ == '__main__': main()
