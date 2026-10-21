"""Closure-gated Pipe distance availability and explicit auxiliary vertex joins.

Only a separately resolved single source edge supplies closedness. Descriptor
flags, selector presence, coordinate agreement and recipe trailers never do.
Path opposition and the resulting partial Pipe geometry remain unresolved.
"""
import math
import struct

from decode_pipe_edge_controls import inspect_pipe_edge_controls
from decode_pipe_recipe_incidence import inspect_pipe_recipe_incidence
from decode_pipe_vertex_contexts import inspect_pipe_auxiliary_vertex_context
from decode_recipe_components import decode_counted_recipe

SCOPE = 'Observed single-BRep-edge Pipe distanceOne/distanceTwo availability from explicitly resolved cached source topology; auxiliary vertex recipe names source start identity; Path opposition and resulting partial geometry unresolved'


def _name_tuple(entry):
    return tuple((term['name'], term['stored_index'], tuple(term['stored_reference_components_int32']))
                 for term in entry['terms'])


def decode_pipe_auxiliary_vertex_operand(recipe):
    """Observed40-byte vertex recipe: direct -1, three named faces, twozeros."""
    payload = bytes.fromhex(recipe['payload_hex'])
    if (recipe['payload_kind'] != 'vertex_recipe_data' or len(payload) != 40
            or len(recipe['name_table']) != 3 or struct.unpack_from('<iI', payload) != (-1, 3)
            or payload[32:] != bytes(8)):
        raise ValueError('Unobserved Pipe auxiliary vertex recipe framing')
    refs = []
    for cursor in (8, 16, 24):
        index, secondary = struct.unpack_from('<ii', payload, cursor)
        if not 0 <= index < 3 or secondary != -1:
            raise ValueError('Pipe auxiliary vertex name index/sentinel disagrees')
        refs.append({'name_table_index': index, 'stored_secondary_index': secondary})
    if {item['name_table_index'] for item in refs} != {0, 1, 2}:
        raise ValueError('Pipe auxiliary vertex requires three distinct named faces')
    return {'recipe_object_id': recipe['object_id'], 'stored_direct_vertex_name_index': -1,
            'face_name_references': refs, 'stored_tail_fields_int32': [0, 0], 'payload_hex': payload.hex()}


def inspect_pipe_edge_limits(data, records, body, feature, features, member, members, body_identifier_summary,
                             *, source_evidence=None, incidence_evidence=None):
    """Return bounded API-distance availability, never full Pipe settings.

    Optional evidence must come from the identical inputs. Incidence includes
    explicitly typed, reciprocally validated source BODY/face/loop/coedge/edge
    naming joins; no API getter truth is accepted as a decoder input.
    """
    source = source_evidence if source_evidence is not None else inspect_pipe_edge_controls(data, records, body, feature, features)
    incidence = incidence_evidence if incidence_evidence is not None else inspect_pipe_recipe_incidence(
        data, records, body, feature, features, member, members, body_identifier_summary, source_evidence=source)
    if (source['feature_object_id'] != feature['object_id'] or incidence['feature_object_id'] != feature['object_id']
            or incidence['source_recipe_object_id'] != source['path']['recipe']['object_id']
            or incidence['source_descriptor_object_id'] != source['path']['descriptor_object_id']
            or incidence['native_source_body_object_id'] != source['path']['native_body_object_id']
            or incidence['source_body_anchor_object_id'] != source['path']['body_anchor_object_id']):
        raise ValueError('Pipe limits source/incidence ownership or role disagrees')
    primary = {}
    for record in records:
        if record.is_primary:
            primary.setdefault(record.object_id, []).append(record)

    def recipe(identity):
        choices = primary.get(identity, [])
        if len(choices) != 1 or choices[0].class_guid != '7ACC2A03-0261-4879-A14A-A93D661A5BDC':
            raise ValueError('Pipe limits recipe typed identity missing or ambiguous')
        return decode_counted_recipe(data, choices[0])

    edge_recipe = recipe(incidence['source_recipe_object_id'])
    context_recipe = recipe(source['path']['context_recipe']['object_id'])
    edge_payload, context_payload = (bytes.fromhex(r['payload_hex']) for r in (edge_recipe, context_recipe))
    if (edge_recipe['payload_kind'] != 'edge_recipe_data' or context_recipe['payload_kind'] != 'edge_recipe_data'
            or edge_recipe['name_table'] != context_recipe['name_table'] or len(edge_payload) not in (116, 120)
            or len(context_payload) != len(edge_payload) or edge_payload[:-4] != context_payload[:-4]
            or edge_payload[-4:] != bytes(4) or context_payload[-4:] != struct.pack('<i', -1)):
        raise ValueError('Pipe limits requires captured source/context recipe copy with0/-1 final fields')
    closed = incidence['cached_source_edge_is_closed']
    geometry_kind = incidence['cached_source_geometry']['kind']
    if type(closed) is not bool or geometry_kind not in ('Line', 'Circle'):
        raise ValueError('Pipe limits requires independently resolved observed source closure and geometry')
    controls = source['native_parameter_controls']
    one, stored_along = (controls[role]['stored_value'] for role in ('AgainstDistance', 'AlongDistance'))
    if (not all(math.isfinite(value) for value in (one, stored_along))
            or not 0 < one <= 1 or not 0 <= stored_along <= 1):
        raise ValueError('Pipe limits invalid captured fraction range')
    auxiliary_join = None
    if closed:
        if geometry_kind != 'Circle' or one+stored_along > 1+1e-12:
            raise ValueError('Pipe closed-source active fractions exceed one or primitive disagrees')
        two = stored_along
        available = True
        along_role = 'ActiveDistanceTwo'
    else:
        if geometry_kind != 'Line' or not math.isclose(one, stored_along, rel_tol=0, abs_tol=1e-12):
            raise ValueError('Pipe open-source stored AlongDistance must duplicate distanceOne')
        two = None
        available = False
        along_role = 'InactiveCopyOfDistanceOne'
        auxiliary = inspect_pipe_auxiliary_vertex_context(data, records, body, feature, features, source_evidence=source)
        vertex_recipe = recipe(auxiliary['vertex_recipe_object_id'])
        vertex_operand = decode_pipe_auxiliary_vertex_operand(vertex_recipe)
        edge_names = [_name_tuple(entry) for entry in edge_recipe['name_table']]
        vertex_names = [_name_tuple(entry) for entry in vertex_recipe['name_table']]
        if len(set(edge_names)) != len(edge_names) or len(set(vertex_names)) != len(vertex_names):
            raise ValueError('Pipe auxiliary/edge name tuples must be individually unique')
        mapping = []
        mapped_indices = []
        for ref in vertex_operand['face_name_references']:
            index = ref['name_table_index']
            matches = [i for i, name in enumerate(edge_names) if name == vertex_names[index]]
            if len(matches) != 1:
                raise ValueError('Pipe auxiliary vertex face lacks one exact source-edge name tuple')
            mapped_indices.append(matches[0])
            mapping.append({'auxiliary_name_table_index': index, 'edge_name_table_index': matches[0]})
        vertex_operands = incidence['operation_operands']['vertex_face_operands']
        if not vertex_operands or len(vertex_operands) != 2:
            raise ValueError('Pipe open-source endpoint operand incidence absent')
        first_indices = [ref['name_table_index'] for ref in vertex_operands[0]['face_name_references']]
        if mapped_indices != first_indices:
            raise ValueError('Pipe auxiliary vertex operand is not the ordered source-start face subrecipe')
        resolved = incidence['line_vertex_operand_associations']
        endpoints = incidence['cached_endpoint_points']
        if (len(resolved) != 2 or resolved[0]['operand_ordinal'] != 0
                or resolved[0]['vertex_record_index'] != endpoints[0]['vertex_record_index']):
            raise ValueError('Pipe auxiliary start operand lacks reciprocal source vertex incidence')
        # Coordinate agreement validates a cache after identity joins; it never chooses that identity.
        if not all(math.isclose(a, b, abs_tol=1e-10) for a, b in zip(auxiliary['cached_position_cm'], endpoints[0]['raw_point'])):
            raise ValueError('Pipe auxiliary cache disagrees with independently named source start vertex')
        auxiliary_join = {'selection_object_id': auxiliary['selection_object_id'],
            'descriptor_object_id': auxiliary['descriptor_object_id'], 'context_object_id': auxiliary['context_object_id'],
            'vertex_recipe_object_id': vertex_recipe['object_id'], 'vertex_operand': vertex_operand,
            'exact_name_tuple_remap': mapping, 'source_vertex_operand_ordinal': 0,
            'source_vertex_record_index': resolved[0]['vertex_record_index'],
            'source_face_operands': resolved[0]['face_operands'],
            'association': 'Auxiliary three-face recipe equals stored edge start-vertex subrecipe after exact full-name tuple remapping; source vertex identity follows reciprocal incidence, not coordinates',
            'path_direction_status': 'This names the stored source-edge start vertex; its general role in Path direction remains unresolved without an opposed-Path contrast'}
    return {'feature_object_id': feature['object_id'], 'source_recipe_object_id': incidence['source_recipe_object_id'],
        'source_descriptor_object_id': incidence['source_descriptor_object_id'],
        'native_source_body_object_id': incidence['native_source_body_object_id'],
        'history_blob_member': incidence['history_blob_member'], 'source_edge_record_index': incidence['source_edge_record_index'],
        'cached_source_edge_is_closed': closed, 'cached_source_geometry_kind': geometry_kind,
        'distance_one_fraction': one, 'distance_one_binding_object_id': controls['AgainstDistance']['binding_object_id'],
        'distance_two_available': available, 'distance_two_fraction': two,
        'stored_along_distance_fraction': stored_along, 'along_distance_binding_object_id': controls['AlongDistance']['binding_object_id'],
        'stored_along_distance_role': along_role,
        'availability_basis': 'Single source-edge closure proved by explicit named-face incidence and typed source topology, plus documented Pipe distanceTwo behavior and contrasted saved getters. Selector presence and descriptor flag are not closure inputs.',
        'auxiliary_source_vertex': auxiliary_join,
        'context_recipe_copy': {'source_recipe_object_id': edge_recipe['object_id'], 'context_recipe_object_id': context_recipe['object_id'],
            'payload_length': len(edge_payload), 'source_final_int32': 0, 'context_final_int32': -1,
            'shared_prefix_hex': edge_payload[:-4].hex(),
            'field_status': 'Stored0/-1 difference is invariant across all observed open/closed/full/partial and negative-line captures; no Path opposition or limit meaning assigned'},
        'path_is_opposed_to_entity': None, 'partial_path_parameter_domain': None,
        'partial_geometry_status': 'distanceOne/Two are active Pipe fractions. Stored source domain and API PathEntity.curve describe the full input edge; resulting partial Pipe parameter limits and path opposition remain unresolved.',
        'tool_settings_status': 'Unresolved; bounded active fractions and source vertex provenance only, full Pipe tool decoding not claimed',
        'scope': SCOPE}


def validate_fixtures(root, zstd_library=None):
    """Six saved getter contrasts; explicit selector identity and bounded guards."""
    import copy
    import json
    from pathlib import Path
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records

    root = Path(root)
    folder = 'pipeedgecontrasts-5bd287323ae7'
    files = [(folder+'/'+sample['file'], sample) for sample in json.loads((root/folder/'ground_truth.json').read_text())['samples']]
    other = 'pipepaths-3d11bd427946'
    files += [(other+'/'+sample['file'], sample) for sample in json.loads((root/other/'ground_truth.json').read_text())['samples']
              if sample['file'] == 'brep_edge_circular.f3d']
    report = {'scope': SCOPE, 'interface': 'inspect_pipe_edge_limits(data,records,body,feature,features,member,members,body_identifier_summary,*,source_evidence=None,incidence_evidence=None)',
        'validator': 'validate_fixtures(root,zstd_library=None)',
        'integration': 'Separate partial Pipe limit evidence. Reuse source and incidence from identical inputs; expose distanceOne/Two availability and explicit auxiliary source-start vertex provenance only. Never clear full Pipe tool failures or populate Path opposition/partial curve.',
        'expected_outputs': 'samples[].expected_summary is complete inspector result for exact main equality checks',
        'SDK_evidence': {
            'local_definition': '/Users/stephenh/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Python/defs/adsk/fusion.py',
            'PipeFeature.distanceTwo': 'The installed getter contract returns null for an open path and a reverse-path distance for a closed path. Availability follows independently resolved single-edge closure, not optional selector presence.',
            'PipeFeatureInput.distanceOne_distanceTwo': 'Input distances are fractions in[0,1]. Closed-path distanceOne+distanceTwo may not exceed1; open-path distanceTwo setting is ignored.',
            'PipeFeature.path': 'Starting point is the starting point of the first path curve. This documents an API role but does not decode stored Path opposition from the current all-unopposed captures.'},
        'grammar': {
            'distance_roles': 'Existing owned typed native bindings AgainstDistance@13 and AlongDistance@24 retain their model-parameter roles. AgainstDistance matches API distanceOne across contrasted full/partial open/closed cases. AlongDistance is active API distanceTwo only on the independently resolved closed single source edge, otherwise an inactive duplicate of AgainstDistance.',
            'auxiliary_vertex': 'Observed40-byte vertex_recipe_data: int32 -1,uint32 count3,three (name index,int32 -1) pairs,two int32zeros. All three complete name tuples map uniquely into the source edge recipe, in exactly the same operand order as its start-vertex subrecipe. The already validated reciprocal incidence supplies the vertex identity.',
            'context_copy': 'Explicit owned context edge recipe repeats full source name table and every payload byte except final int32: source0,context-1. This invariant is retained without direction/limit semantics.'},
        'limitations': [
            'All six saved PathEntity.isOpposedToEntity getters are false; the corpus has no native true/false contrast. Stored auxiliary source-start identity does not establish a universal Path opposition flag.',
            'Descriptor flag1 occurs for both open negative Line and closed Circle while all API opposition flags stay false. No closedness or Path opposition is assigned to that byte.',
            'Circular92-byte recipe tail remains opaque. Its primary/context last-field0/-1 distinction is invariant across full/partial cases and cannot encode those active limits by itself.',
            'Actual PathEntity.curve is the full input geometry even when Pipe distanceOne/Two are partial. Its full length/domain is not the resulting Pipe path extent.',
            'Only independently resolved captured single source Line/Circle, solid circular NewBody, root-component identity-transform cases are admitted. Multi-edge paths, opposed cases, arcs, non-circular curves, occurrence transforms and full Pipe tool regeneration remain unresolved.'],
        'samples': [], 'comparisons': [], 'malformed_guards': [], 'counterexamples': [],
        'next_discriminating_capture': {
            'case': 'Same explicitly selected open BRepEdge represented by an API-supported Path that returns isOpposedToEntityTrue, contrasted with existingFalse; capture both full and partial distanceOne',
            'must_capture': 'Actual rolled-back Path ordered members, isOpposedToEntity, source tokens/start/end identities, source natural/trimmed evaluator, PathEntity.curve evaluator, distanceOne/Two, all native refs, and independent result-body geometry',
            'purpose': 'Separate native stored source-start selection and descriptor direction-like cache flags from actual Path member opposition. A reversed world-space line alone is insufficient.'}}
    loaded = {}

    def check(label, actual, expected):
        assert actual == expected, (label, actual, expected)
        report['comparisons'].append({'label': label, 'actual': actual, 'expected': expected, 'passed': True})

    for filename, sample in files:
        members = read_members(root/filename, zstd_library)
        stream = decode_basics(root/filename, zstd_library)['streams'][0]
        data = members[stream['member']]
        records, _ = design_records(data, members[stream['member'].replace('BulkStream.dat', 'MetaStream.dat')])
        features = stream['features']
        feature = next(f for f in features if f['kind'] == 'Pipe')
        rec = next(r for r in records if r.is_primary and r.object_id == feature['object_id'])
        body = data[rec.body:rec.end]
        source = inspect_pipe_edge_controls(data, records, body, feature, features)
        incidence = inspect_pipe_recipe_incidence(data, records, body, feature, features, stream['member'], members, stream['body_asm_identifiers'], source_evidence=source)
        evidence = inspect_pipe_edge_limits(data, records, body, feature, features, stream['member'], members, stream['body_asm_identifiers'], source_evidence=source, incidence_evidence=incidence)
        api = sample['settings']
        path = api['path']
        source_api = path['members'][0]['source']
        check(filename+' single input source', path['count'], 1)
        check(filename+' source closure agrees independent API', evidence['cached_source_edge_is_closed'], path['is_closed'])
        check(filename+' active distanceOne agrees actual getter', evidence['distance_one_fraction'], api['distance_one'])
        check(filename+' distanceTwo availability agrees actual getter presence', evidence['distance_two_available'], api['distance_two'] is not None)
        check(filename+' active distanceTwo agrees actual getter', evidence['distance_two_fraction'], api['distance_two'])
        check(filename+' Path opposition remains unresolved', evidence['path_is_opposed_to_entity'], None)
        check(filename+' partial Pipe parameter domain remains unresolved', evidence['partial_path_parameter_domain'], None)
        check(filename+' source/context recipe final fields retain0/-1',
              [evidence['context_recipe_copy']['source_final_int32'], evidence['context_recipe_copy']['context_final_int32']], [0, -1])
        if not path['is_closed']:
            join = evidence['auxiliary_source_vertex']
            check(filename+' exact auxiliary name remap names first endpoint', join['source_vertex_record_index'], incidence['cached_endpoint_points'][0]['vertex_record_index'])
            check(filename+' inactive AlongDistance retains actual distanceOne copy', evidence['stored_along_distance_fraction'], api['distance_one'])
        else:
            check(filename+' active AlongDistance retained', evidence['stored_along_distance_role'], 'ActiveDistanceTwo')
        source_length = source_api['trimmed_edge_evaluator']['length_cm']
        input_length = path['members'][0]['actual_path_geometry']['length_cm']
        check(filename+' actual PathEntity curve remains full source length', math.isclose(source_length, input_length, abs_tol=1e-8), True)
        observation = {'distance_one': api['distance_one'], 'distance_two': api['distance_two'], 'source_is_closed': path['is_closed'],
            'source_geometry_type': source_api['natural_geometry']['geometry_type'],
            'is_opposed_to_entity': path['members'][0]['is_opposed_to_entity'],
            'descriptor_flag_byte3': source['path']['stored_descriptor_flag_byte3'],
            'source_edge_length_cm': source_length, 'actual_full_input_PathEntity_curve_length_cm': input_length,
            'source_trimmed_parameter_domain': source_api['trimmed_edge_evaluator']['parameter_extents'],
            'actual_full_input_PathEntity_parameter_domain': path['members'][0]['actual_path_geometry']['parameter_extents']}
        if api['distance_one'] < 1:
            report['counterexamples'].append({'file': filename,
                'observation': 'Partial Pipe distance fractions coexist with a full-length PathEntity.curve getter; this getter must not populate partial Pipe limits',
                'actual': observation})
        report['samples'].append({'file': filename, 'expected_summary': evidence, 'API_observation': observation,
            'API_evidence_status': 'Saved getter comparisons only after native closure/name/owner joins; no API values passed into decoder'})
        loaded[Path(filename).name] = data, records, body, feature, features, stream, members, source, incidence, evidence

    negative = loaded['line_offset_negative_partial.f3d'][-1]
    check('Negative Line does not infer reverse Path', negative['path_is_opposed_to_entity'], None)
    flags = [(s['API_observation']['descriptor_flag_byte3'], s['API_observation']['is_opposed_to_entity']) for s in report['samples']]
    check('Descriptor flag varies while every actual opposition staysFalse', sorted(set(flags)), [(0, False), (1, False)])
    report['counterexamples'].append({'observation': 'Actual opposition staysFalse for both stored descriptor flags0/1 and both world-space Line directions; neither flag nor direction signs decode opposition', 'flag_and_API_opposition_pairs': sorted(set(flags))})

    def reject(label, action):
        try:
            action()
        except (ValueError, KeyError, IndexError, struct.error) as error:
            report['malformed_guards'].append({'label': label, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError(label+' was accepted')

    data, records, body, feature, features, stream, members, source, incidence, evidence = loaded['line_offset_negative_partial.f3d']
    primary = {r.object_id: r for r in records if r.is_primary}
    vertex_record = primary[evidence['auxiliary_source_vertex']['vertex_recipe_object_id']]
    vertex_recipe = decode_counted_recipe(data, vertex_record)
    payload = bytes.fromhex(vertex_recipe['payload_hex'])
    start = data.find(payload, vertex_record.body, vertex_record.end)
    assert start >= 0
    for label, offset, value in [('Auxiliary vertex wrong face count', 4, 2), ('Auxiliary vertex unknown face-name index', 8, 99),
                                 ('Auxiliary vertex duplicate face operand', 16, 1)]:
        changed = bytearray(data)
        struct.pack_into('<i', changed, start+offset, value)
        reject(label, lambda changed=changed: inspect_pipe_edge_limits(bytes(changed), records, body, feature, features,
            stream['member'], members, stream['body_asm_identifiers']))
    context_record = primary[source['path']['context_recipe']['object_id']]
    changed = bytearray(data)
    struct.pack_into('<i', changed, context_record.end-4, 0)
    reject('Context recipe final field mismatch', lambda: inspect_pipe_edge_limits(bytes(changed), records, body, feature, features,
        stream['member'], members, stream['body_asm_identifiers']))
    bad_incidence = copy.deepcopy(incidence)
    bad_incidence['source_descriptor_object_id'] += 1
    reject('Cross-role incidence evidence descriptor', lambda: inspect_pipe_edge_limits(data, records, body, feature, features,
        stream['member'], members, stream['body_asm_identifiers'], source_evidence=source, incidence_evidence=bad_incidence))
    bad_feature = copy.deepcopy(feature)
    next(p for p in bad_feature['parameters'] if p['role'] == 'AlongDistance')['raw_float64'] = .3
    reject('Open source AlongDistance copy disagreement', lambda: inspect_pipe_edge_limits(data, records, body, bad_feature, features,
        stream['member'], members, stream['body_asm_identifiers']))
    report['validation'] = {'saved_files': len(files), 'distanceTwo_available_closed': 2, 'distanceTwo_unavailable_open': 4,
        'explicit_auxiliary_source_start_vertex_joins': 4, 'comparisons_passed': len(report['comparisons']),
        'malformed_guards_passed': len(report['malformed_guards']), 'opposition_claims': 0, 'partial_geometry_claims': 0,
        'full_Pipe_tool_failures_cleared': 0, 'new_API_calls': 0}
    return report
