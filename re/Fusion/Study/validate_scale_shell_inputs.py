"""Focused actual-getter validation for Scale Sketch/vertex and mixed Shell inputs."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from decode_basics import decode_basics
from decode_body_tool_selections import decode_body_tool_selections
from decode_scale_inputs import decode_scale_sketch, decode_scale_vertex_points
from decode_selection import known_construction_entities
from decode_sketch import numbers, reference, same
from fusion_archive import read_members
from fusion_metadata import design_records


def read_case(archive, zstd_library):
    main = decode_basics(archive, zstd_library)
    stream = next(s for s in main['streams'] if s.get('features'))
    members = read_members(archive, zstd_library)
    data = members[stream['member']]
    records, _ = design_records(data, members.get(stream['member'].replace('BulkStream.dat', 'MetaStream.dat')))
    by = {r.object_id: r for r in records if r.is_primary}
    return data, records, stream, by


def validate_fixtures(root, zstd_library):
    folder = root/'scaleshellinputs-97ef1cfd19e4'
    truth = json.loads((folder/'ground_truth.json').read_text())
    assert len(truth['samples']) == 5 and not truth['errors'] and (folder/'complete.txt').is_file()
    report = {'api_version': truth['fusion_version'], 'samples': [], 'negative_checks': [], 'typed_vertex_cache_controls': [],
              'decoder_sha256': {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ('decode_scale_inputs.py','decode_body_tool_selections.py')},
              'validation_command': 'python3 validate_scale_shell_inputs.py --validate --zstd-library <local libzstd path>',
              'scope': 'Five integrated main outputs and direct Scale Sketch/vertex plus Shell body-selection passes compared to actual API getters; requested ordering retained separately'}
    for sample in truth['samples']:
        assert not sample['getter_errors']
        archive = folder/sample['file']
        data, records, stream, by = read_case(archive, zstd_library)
        features = stream['features']
        feature = next(f for f in features if f['kind'] in ('Scale','Shell'))
        settings = feature['tool_settings']
        properties = {b['object_id']: b for b in stream['body_properties']['bodies']}
        selected = settings['input_selections']
        if settings.get('input_kind') == 'Sketch':
            decoded_inputs = [{'entity_type': 'adsk::fusion::Sketch', 'sketch_name': s['sketch_name']} for s in selected]
        else:
            decoded_inputs = [{'entity_type': 'adsk::fusion::BRep'+s['kind'], 'body_name': properties[s['native_body_object_id']]['name']} for s in selected]
        def identities(items):
            return [(a['entity_type'], a.get('sketch_name', a.get('body_name'))) for a in items]
        actual, requested = sample['actual_inputs'], sample['requested_input_entities']
        checks = {'actual_source_types_names_and_order_match': identities(decoded_inputs) == identities(actual),
                  'input_count_matches_actual': settings['input_count'] == len(actual),
                  'body_count_matches_actual': settings['input_body_count'] == sum(a['entity_type'].endswith('BRepBody') for a in actual),
                  'face_count_matches_actual': settings['input_face_count'] == sum(a['entity_type'].endswith('BRepFace') for a in actual)}
        if feature['kind'] == 'Scale':
            checks.update(is_uniform_matches_actual=settings['is_uniform'] == sample['settings']['is_uniform'],
                          factor_matches_actual=same([settings['factor']], [sample['settings']['factor']]))
            point = settings['point']
            api_point = sample['actual_point']
            if point['entity']['kind'] == 'BRepVertexRecipe':
                position = point['cached_position_cm']
                checks.update(actual_source_is_vertex_recipe_kind=api_point['entity_type']=='adsk::fusion::BRepVertex' and point['entity']['recipe']['payload_kind']=='vertex_recipe_data',
                              vertex_historical_body_name_matches_actual=properties[point['entity']['native_body_object_id']]['name']==api_point['body_name'],
                              typed_context_and_backend_caches_agree=same(point['context_cached_position_cm'], position),
                              vertex_identity_scope_remains_explicit='persistent ASM vertex identity unresolved' in point['association'])
                direct_features = copy.deepcopy(features)
                direct_feature = next(f for f in direct_features if f['object_id'] == feature['object_id'])
                direct_feature['tool_settings']['point'] = None
                direct = decode_scale_vertex_points(data, records, direct_features, stream['body_selections'])
                checks['direct_vertex_pass_redecodes_same_point']=len(direct['decoded'])==1 and not direct['unresolved'] and direct['decoded'][0]['point']==point
                vertex_case = data, records, stream, by, feature, point
            else:
                position = point['entity']['position_cm']
                checks['point_kind_matches_actual']=api_point['entity_type']=='adsk::fusion::'+point['entity']['kind']
                checks['point_name_matches_actual']=point['entity']['name']==api_point['name']
            checks['point_position_cache_matches_actual']=same(position, api_point['position_cm'])
            if settings.get('input_kind') == 'Sketch':
                known = known_construction_entities(data, records, features)
                record = by[feature['object_id']]
                direct_feature = {k: v for k, v in feature.items() if k != 'tool_settings'}
                direct = decode_scale_sketch(data, records, data[record.body:record.end], direct_feature, known, features)
                checks['direct_sketch_pass_matches_integrated']=direct==settings
                sketch_case = data, records, stream, by, feature, known
        else:
            api = sample['settings']
            checks.update(tangent_chain_matches_actual=settings['is_tangent_chain']==api['is_tangent_chain'],
                          shell_type_matches_actual=settings['stored_shell_type']==api['shell_type'],
                          inside_thickness_matches_actual=same([settings['inside_thickness_cm']], [api['inside_thickness_cm']]),
                          outside_thickness_matches_actual=settings['outside_thickness_cm']==api['outside_thickness_cm'],
                          actual_order_is_normalized_from_request=identities(actual)!=identities(requested),
                          native_order_follows_actual_not_request=identities(decoded_inputs)!=identities(requested))
            direct = decode_body_tool_selections(data, records, features)
            checks['direct_body_selection_pass_matches_integrated']=(not direct['unresolved'] and len(direct['decoded'])==1
                 and direct['decoded'][0]['settings']['input_selections']==selected)
            if settings['input_face_count']:
                face = next(s for s in selected if s['kind']=='Face')
                body = next(s for s in selected if s['kind']=='Body')
                checks['mixed_face_and_body_have_distinct_source_bodies']=face['native_body_object_id']!=body['native_body_object_id']
                checks['mixed_face_has_bounded_recipe']=face['recipe']['payload_kind']=='bounded_face_recipe_data'
        assert all(checks.values()), (sample['file'], checks)
        report['samples'].append({'archive': str(archive.relative_to(root)), 'checks': checks, 'decoded_settings': settings,
                                  'actual_input_identities': identities(actual), 'requested_input_identities': identities(requested),
                                  'api_normalized_input_order': identities(actual)!=identities(requested),
                                  'actual_point': sample.get('actual_point'), 'actual_settings': sample['settings']})
    data, records, stream, by, feature, known = sketch_case
    selected = feature['tool_settings']['input_selections'][0]
    for label, identity, offset, replacement in (
            ('Sketch descriptor owner mismatch', selected['descriptor_object_id'], 242, struct.pack('<Q',999999)),
            ('Sketch leaf ID absent from native source sketches', selected['terminal_object_id'], 2, struct.pack('<Q',999999))):
        record = by[identity]
        changed = bytearray(data)
        changed[record.body+offset:record.body+offset+len(replacement)] = replacement
        feature_record = by[feature['object_id']]
        try:
            decode_scale_sketch(bytes(changed), records, data[feature_record.body:feature_record.end], feature, known, stream['features'])
        except (ValueError, KeyError, IndexError, struct.error) as error:
            report['negative_checks'].append({'check':label,'passed':True,'reason':str(error)})
        else:
            raise AssertionError(label)
    data, records, stream, by, feature, point = vertex_case
    for label, identity, offset, replacement in (
            ('Vertex backend owner mismatch', point['selection_object_id'],168,struct.pack('<Q',999999)),
            ('Typed vertex coordinate cache disagrees with backend', point['context_object_id'],2,struct.pack('<d',point['cached_position_cm'][0]+0.5))):
        record = by[identity]
        changed = bytearray(data)
        changed[record.body+offset:record.body+offset+len(replacement)] = replacement
        copied = copy.deepcopy(stream['features'])
        copied_feature = next(f for f in copied if f['object_id']==feature['object_id'])
        copied_feature['tool_settings']['point'] = None
        original_inputs = copy.deepcopy(copied_feature['tool_settings']['input_selections'])
        out = decode_scale_vertex_points(bytes(changed), records, copied, stream['body_selections'])
        passed = (not out['decoded'] and len(out['unresolved'])==1 and copied_feature['tool_settings']['point'] is None
                  and copied_feature['tool_settings']['input_selections']==original_inputs)
        assert passed, (label,out)
        report['negative_checks'].append({'check':label,'passed':True,'reason':out['unresolved'][0]['reason'],
                                          'scope':'Existing input bodies retained; no valid point emitted or fabricated'})
    # Independent existing Pipe auxiliary vertex contexts contrast coordinates.
    pipefolder = root/'pipeedgecontrasts-5bd287323ae7'
    pipe_truth = json.loads((pipefolder/'ground_truth.json').read_text())
    for sample in pipe_truth['samples']:
        if not sample['case'].startswith('line_'):
            continue
        data, records, stream, by = read_case(pipefolder/sample['file'], zstd_library)
        feature = next(f for f in stream['features'] if f['kind']=='Pipe')
        feature_record = by[feature['object_id']]
        body = data[feature_record.body:feature_record.end]
        backend_id = reference(body,68)
        backend_record = by[backend_id]
        backend = data[backend_record.body:backend_record.end]
        descriptor_record = by[reference(backend,79)]
        descriptor = data[descriptor_record.body:descriptor_record.end]
        context_id = reference(descriptor,183)
        context_record = by[context_id]
        context = data[context_record.body:context_record.end]
        actual = sample['source_before_pipe']['start_vertex']['point_cm']
        checks = {'context_class_is_same_typed_vertex_cache':context_record.class_guid=='994C518A-A831-400A-B7C7-16DAC55F4F1C',
                  'context_framing_matches_Scale':len(context)==28 and context[:2]==bytes(2) and context[-2:]==b'\1\0',
                  'cache_matches_backend_and_actual_start_vertex':same(numbers(context,2,3),numbers(backend,23,3)) and same(numbers(context,2,3),actual),
                  'backend_and_descriptor_are_owned_by_pipe':reference(backend,167)==feature['object_id'] and reference(descriptor,265)==feature['object_id']}
        assert all(checks.values()), (sample['file'],checks)
        report['typed_vertex_cache_controls'].append({'archive':str((pipefolder/sample['file']).relative_to(root)),
             'backend_object_id':backend_id,'descriptor_object_id':descriptor_record.object_id,'context_object_id':context_id,
             'context_class_guid':context_record.class_guid,'context_cached_position_cm':numbers(context,2,3),
             'actual_source_start_vertex_cm':actual,'checks':checks,
             'scope':'Independent coordinate-cache evidence only; exact Pipe selection role/persistent vertex identity not inferred'})
    report['coverage']={'Scale_Shell_captures':5,'malformed_guards':4,'independent_Pipe_coordinate_cache_controls':3}
    report['limitations']=['Scale vertex recipe and corroborated backend/context coordinates do not establish persistent ASM vertex identity or source-vertex evaluation.',
                           'Requested Shell order is reversed/normalized in actual getters; native ordered selections agree with actual getters, not request order.',
                           'Sketch scaling history replay and modified result geometry are not implemented; source identity/factor/point controls are validated.',
                           'Mixed Shell face recipes establish historical source-body provenance; persistent ASM face mapping remains unresolved.',
                           'Root-component coordinate-cache contrasts do not prove arbitrary occurrence transforms or assembly joint solving.']
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate',required=True,action='store_true')
    parser.add_argument('--zstd-library',required=True,type=Path)
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('scale-shell-input-decoding.json'))
    args=parser.parse_args()
    report=validate_fixtures(Path(__file__).resolve().parent,args.zstd_library)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'samples':len(report['samples']),'negative_checks':len(report['negative_checks']),
                      'cache_controls':len(report['typed_vertex_cache_controls']),'output':str(args.output)}))
