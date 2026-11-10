"""Focused actual trim-reference controls, complete tuple joins and API portions."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_basics import decode_basics
from decode_profile_cache_correspondence import decode_profile_cache_correspondence
from decode_profiles import read_loops
from decode_trimmed_profiles import decode_trimmed_profiles, read_trimmed_profile_loops
from fusion_archive import read_members
from fusion_metadata import design_records
from asm_records import inspect_asm

ROOT = Path(__file__).resolve().parent
CAPTURE = 'trimmedprofiles-a804f8da1496'
FILES = tuple(CAPTURE+'/'+name+'.f3d' for name in ('circle_lens', 'circle_right_complement', 'rectangle_overlap'))


def evaluate_stored(curve, parameter):
    if curve['kind'] == 'straight-curve':
        return [origin+parameter*direction for origin, direction in zip(curve['raw_origin'], curve['direction'])]
    assert curve['kind'] == 'ellipse-curve'
    normal, major = curve['normal'], curve['stored_reference_axis']
    minor = [normal[1]*major[2]-normal[2]*major[1], normal[2]*major[0]-normal[0]*major[2], normal[0]*major[1]-normal[1]*major[0]]
    return [origin+a*math.cos(parameter)+b*curve['stored_axis_ratio']*math.sin(parameter)
            for origin, a, b in zip(curve['raw_origin'], major, minor)]


def signature(points):
    # Independent whole-set comparison only, after native identity is established.
    return (tuple(sorted(tuple(round(x, 8) for x in point) for point in (points[0], points[2]))),
            tuple(round(x, 8) for x in points[1]))


def validate(zstd=None, model_cache=None):
    model_cache = model_cache or {}
    report = {'scope': 'Three actual selected-profile captures; typed native ownership and complete six-literal sketch-attribute join first, then independent whole-set API geometry checks',
              'interface': 'decode_trimmed_profiles(data,records,features,member,members,body_identifier_summary)',
              'integration': 'Separate trimmed_profiles summary and source-feature attachment trimmed_profile_cache_correspondences. Root may expose qualified membership and clear only the same-feature old trim-layout warning after complete owned-cache proof; source-trim evaluator warnings and canonical whole-curve helper behavior remain explicit.',
              'samples': [], 'legacy_default_controls': [], 'guards': [], 'limitations': [
                  'Selectors(1,2)/(2,2) are literal controls, not interpreted as endpoint IDs, segment ordinals, angles or source trim parameters.',
                  'The secondary tag remains zero even for actual trimmed profile portions. Zero is not a proof of whole-curve geometry.',
                  'Every source retains both matching COEDGE candidates. Geometry never selects an association; API comparison occurs only after the native descriptor/Sketch/source-BODY/full-tuple proof.',
                  'Stored edge/curve parameter intervals and endpoint order are not converted to API ProfileCurve parameterization or traversal.',
                  'Only captured Line/Circle sources with unique tags and selector pairs(1,1)/(1,2)/(2,2), code3, secondary0, direction0/1 and opaque0 are accepted.',
                  'No general trim construction, solver, persistent geometry lifecycle, modified-cache equality or native writing.']}
    truth = json.loads((ROOT/CAPTURE/'ground_truth.json').read_text())
    assert len(truth['samples']) == 3 and not truth['errors'] and (ROOT/CAPTURE/'complete.txt').is_file()
    contexts = []
    checks = 0
    def check(condition):
        nonlocal checks
        assert condition
        checks += 1
    totals = {'files': 0, 'selected_source_references': 0, 'matching_COEDGEs': 0, 'unique_cached_edges': 0,
              'API_portion_geometry_set_checks': 0, 'stored_edge_endpoint_checks': 0,
              'partial_circle_portions': 0, 'partial_line_portions': 0}
    for relative in FILES:
        path = ROOT/relative
        members = read_members(path, zstd)
        model = model_cache.get(relative)
        if model is None:
            model = decode_basics(path, zstd)
        stream = model['streams'][0]
        member = stream['member']; data = members[member]
        records, _ = design_records(data, members[member.replace('BulkStream.dat','MetaStream.dat')])
        features_before = copy.deepcopy(stream['features'])
        result = decode_trimmed_profiles(data, records, stream['features'], member, members, stream['body_asm_identifiers'])
        check(not result['unresolved'] and len(result['decoded']) == 1)
        check(features_before == stream['features'])
        row = result['decoded'][0]
        api = next(sample for sample in truth['samples'] if sample['file'] == path.name)
        check(api['export']['sha256'] == hashlib.sha256(path.read_bytes()).hexdigest())
        api_curves = [curve for loop in api['selected_profile']['loops'] for curve in loop['curves']]
        expected = []
        for curve in api_curves:
            check(not curve['getter_errors'] and not curve['portion_geometry']['getter_errors'])
            check(len(curve['source_indices_by_api_equality']) == 1)
            source = api['source_curves'][curve['source_indices_by_api_equality'][0]]
            check(source['object_type'] == curve['underlying_sketch_entity_type'])
            points = [point['result_cm'][1] for point in curve['portion_geometry']['evaluated_points']]
            expected.append(signature(points))
            if curve['underlying_sketch_entity_type'].endswith('SketchCircle'):
                check(source['full_sketch_geometry']['object_type'].endswith('Circle3D'))
                check(curve['portion_geometry']['object_type'].endswith('Arc3D'))
                bounds = curve['portion_geometry']['parameter_extents']
                check(bounds[0] and 0 < bounds[2]-bounds[1] < 2*math.pi)
                totals['partial_circle_portions'] += 1
            else:
                check(source['full_sketch_geometry']['object_type'].endswith('Line3D'))
                full = source['full_sketch_geometry']['data']; portion = curve['portion_geometry']['data']
                check(math.dist(full[1],full[2]) > math.dist(portion[1],portion[2])+1e-9)
                totals['partial_line_portions'] += 1
        actual = []
        unique_edges = set()
        for source in row['source_curves']:
            check(len(source['cached_coedge_candidates']) == 2)
            totals['selected_source_references'] += 1
            for candidate in source['cached_coedge_candidates']:
                totals['matching_COEDGEs'] += 1
                check(candidate['stored_decimal_text_fields'] == source['stored_profile_reference']['stored_coedge_text_fields'])
                start, end = candidate['stored_edge_parameter_interval']
                check(all(math.isfinite(value) for value in (start,end)) and end > start)
                points = [evaluate_stored(candidate['stored_curve_geometry'], t) for t in (start,(start+end)/2,end)]
                endpoints = [point['raw_position'] for point in candidate['cached_endpoint_points']]
                check(all(any(math.dist(point, endpoint) < 1e-9 for endpoint in endpoints) for point in (points[0],points[2])))
                totals['stored_edge_endpoint_checks'] += 2
                if candidate['edge_record_index'] not in unique_edges:
                    unique_edges.add(candidate['edge_record_index']); actual.append(signature(points))
        check(sorted(actual) == sorted(expected))
        check(len(unique_edges) == len(api_curves))
        totals['files'] += 1; totals['unique_cached_edges'] += len(unique_edges)
        totals['API_portion_geometry_set_checks'] += 1
        report['samples'].append({'file': relative, 'archive_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                  'expected_summary': result, 'features_unchanged': True,
                                  'API_geometry_corroboration': {'identity_join_uses_geometry': False,
                                      'whole_set_endpoint_and_midpoint_signatures_match': True,
                                      'distinct_cached_edges': len(unique_edges), 'actual_API_portion_count': len(api_curves),
                                      'stored_parameterization_not_equated_with_API_parameterization': True,
                                      'full_source_geometry_recorded_separately': True}})
        contexts.append((data, records, stream, member, members, result))
    # Old helper's exact four saved dictionaries, not only matching counts.
    frozen = json.loads((ROOT/'profile-cache-correspondence-decoding.json').read_text())['samples']
    for old in frozen:
        relative = old['file']; members = read_members(ROOT/relative, zstd)
        model = model_cache.get(relative)
        if model is None:
            model = decode_basics(ROOT/relative, zstd)
        stream = model['streams'][0]; member = stream['member']; data = members[member]
        records, _ = design_records(data, members[member.replace('BulkStream.dat','MetaStream.dat')])
        current = decode_profile_cache_correspondence(data, records, stream['features'], member, members, stream['body_asm_identifiers'])
        check(current == old['expected_summary'])
        extension = decode_trimmed_profiles(data, records, stream['features'], member, members, stream['body_asm_identifiers'])
        check(not extension['decoded'] and not extension['unresolved'])
        report['legacy_default_controls'].append({'file': relative, 'exact_frozen_helper_dictionary_equal': True,
                                                   'no_extension_rows_or_diagnostics_for_whole_references': True})
    # Focused malformed saved bytes: all remaining native feature/record inputs stay unchanged.
    data, records, stream, member, members, result = contexts[0]
    target = result['decoded'][0]; by = {record.object_id: record for record in records if record.is_primary}
    definition = by[target['profile_loop_definition_object_id']]
    refs = [ref for loop in target['profile_loops'] for ref in loop['curve_references']]
    first_offset = definition.body+refs[0]['stored_tuple_offset_in_definition']
    def reject(label, bad_data=None, bad_members=None):
        observed = decode_trimmed_profiles(data if bad_data is None else bad_data, records, stream['features'], member,
                                           members if bad_members is None else bad_members, stream['body_asm_identifiers'])
        check(not observed['decoded'] and bool(observed['unresolved']))
        report['guards'].append({'case': label, 'rejected': True, 'reason': observed['unresolved'][0]['reason']})
    for label, offset, fmt, value in (
        ('Uncaptured selector value3',24,'<I',3),
        ('Nonzero secondary tag',12,'<Q',1),
        ('Direction outside captured0/1',20,'<I',2),
        ('Nonzero opaque u64',32,'<Q',1),
    ):
        bad = bytearray(data); struct.pack_into(fmt,bad,first_offset+offset,value); reject(label,bad_data=bytes(bad))
    bad = bytearray(data)
    second_offset = definition.body+refs[1]['stored_tuple_offset_in_definition']
    struct.pack_into('<Q',bad,second_offset+4,refs[0]['entity_tag'])
    reject('Repeated source tag without independent portion identity',bad_data=bytes(bad))
    blob_member = target['history_blob_member']; blob = members[blob_member]; parsed = inspect_asm(blob)
    candidate = target['source_curves'][0]['cached_coedge_candidates'][0]
    attribute = parsed['records'][candidate['attribute_record_index']]
    text_token = attribute['tokens'][9]
    fields = list(candidate['stored_decimal_text_fields']); fields[-2] = '2' if fields[-2] == '1' else '1'
    replacement = ' '.join(fields).encode('ascii'); check(len(replacement) == len(text_token['value']))
    bad = bytearray(blob); bad[text_token['offset']+2:text_token['offset']+2+len(replacement)] = replacement
    bad_members = dict(members); bad_members[blob_member] = bytes(bad)
    reject('One cache selector disagrees with full native tuple',bad_members=bad_members)
    sketch = next(feature for feature in stream['features'] if feature['kind']=='Sketch' and feature['sketch_object_id']==target['native_sketch_object_id'])
    try:
        read_loops(data[definition.body:definition.end], target['profile_descriptor_object_id'], sketch)
    except ValueError as error:
        check('trim-reference layout' in str(error)); report['guards'].append({'case':'Unchanged original reader rejects actual new selector pairs','rejected':True,'reason':str(error)})
    else:
        raise AssertionError('Original whole-reference reader silently widened')
    report['summary'] = {**totals, 'legacy_exact_dictionary_controls':len(report['legacy_default_controls']),
                         'malformed_and_strict_default_guards':len(report['guards']), 'checks':checks}
    report['provenance'] = {'capture_truth_sha256':hashlib.sha256((ROOT/CAPTURE/'ground_truth.json').read_bytes()).hexdigest(),
                            'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in (
                                'decode_trimmed_profiles.py','validate_trimmed_profiles.py','decode_profiles.py','decode_profile_cache_correspondence.py','GenerateTrimmedProfileContrasts.py')}}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zstd-library', default=None)
    parser.add_argument('--model-cache',type=Path,default=None,help='Optional baseline full-output cache with files/before arrays; absent files are decoded once')
    parser.add_argument('--output',type=Path,default=ROOT/'trimmed-profile-decoding.json')
    args = parser.parse_args(); cache = {}
    if args.model_cache:
        data = json.loads(args.model_cache.read_text());cache = dict(zip(data['files'],data['before']))
    result = validate(args.zstd_library,cache)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['summary'],indent=2))
