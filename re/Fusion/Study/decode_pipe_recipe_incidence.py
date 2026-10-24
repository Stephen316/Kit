"""Observed two-named-face Pipe edge selectors and stored source topology.

Names join through exact serialized generic tags. Face/loop/coedge incidence
then distinguishes an owning source edge from detached same-named cache copies.
Coordinates, root ordinals and optional selector presence never select an edge.
"""
import math
import struct

from asm_records import inspect_asm
from decode_asm_recipe_tags import inspect_pipe_recipe_tags
from decode_brep import decode_topology
from decode_recipe_components import decode_counted_recipe

SCOPE = 'Observed Pipe two-named-face selector and linear endpoint face operands resolve one stored initial-geometry edge through reciprocal topology; cached source geometry/closure only, incomplete native operation and full Pipe tools unresolved'


def decode_pipe_edge_recipe_operands(recipe):
    """Decode observed selector operands; retain unresolved circular tail exactly."""
    payload = bytes.fromhex(recipe['payload_hex'])
    if recipe['payload_kind'] != 'edge_recipe_data' or len(payload) not in (116, 120):
        raise ValueError('Only captured116/120-byte Pipe edge operation payloads supported')
    direct, secondary, count = struct.unpack_from('<iiI', payload)
    names = recipe['name_table']
    if secondary != -1 or count != 2 or direct < -1 or direct >= len(names):
        raise ValueError('Unobserved Pipe named-edge/two-face operation prefix')

    def name_reference(cursor):
        index, stored_secondary = struct.unpack_from('<ii', payload, cursor)
        if not 0 <= index < len(names) or stored_secondary != -1:
            raise ValueError('Pipe operation name reference index/sentinel unsupported')
        return {'name_table_index': index, 'stored_secondary_index': stored_secondary}

    faces = [name_reference(12), name_reference(20)]
    if faces[0]['name_table_index'] == faces[1]['name_table_index']:
        raise ValueError('Pipe two-face selector requires distinct serialized face operands')
    result = {'recipe_object_id': recipe['object_id'], 'payload_length': len(payload),
              'stored_direct_edge_name_index': direct, 'stored_secondary_index': secondary,
              'face_name_references': faces, 'prefix_bytes_hex': payload[:28].hex(),
              'uninterpreted_remaining_payload_hex': payload[28:].hex()}
    used = {face['name_table_index'] for face in faces}
    if len(payload) == 116:
        if direct != -1 or len(names) != 4 or struct.unpack_from('<I', payload, 28)[0] != 2:
            raise ValueError('Unobserved linear Pipe recipe name/endpoint framing')
        vertices = []
        for ordinal, cursor in enumerate((32, 72)):
            if struct.unpack_from('<iI', payload, cursor) != (-1, 3):
                raise ValueError('Unobserved linear Pipe vertex three-face subrecipe')
            refs = [name_reference(cursor+8+8*i) for i in range(3)]
            indices = [ref['name_table_index'] for ref in refs]
            if len(set(indices)) != 3 or payload[cursor+32:cursor+40] != bytes(8):
                raise ValueError('Unobserved linear Pipe vertex reference list/tail')
            used.update(indices)
            vertices.append({'operand_ordinal': ordinal, 'stored_direct_vertex_name_index': -1,
                             'face_name_references': refs, 'stored_tail_fields_int32': [0, 0],
                             'subrecipe_bytes_hex': payload[cursor:cursor+40].hex()})
        if payload[112:] != bytes(4) or used != set(range(len(names))):
            raise ValueError('Unobserved linear Pipe operation trailer/name coverage')
        result.update(operand_layout='TwoFaceEdgeWithTwoThreeFaceVertexOperands',
                      vertex_face_operands=vertices, stored_edge_tail_field_int32=0)
    else:
        if direct < 0 or len(names) != 3 or direct in used or struct.unpack_from('<i', payload, 28)[0] != 1:
            raise ValueError('Unobserved circular Pipe named-edge/tail framing')
        used.add(direct)
        if used != set(range(len(names))):
            raise ValueError('Unobserved circular Pipe operation name coverage')
        result.update(operand_layout='NamedEdgeWithTwoFaceOperandsAndOpaque92ByteTail',
                      vertex_face_operands=None, stored_tail_first_int32=1,
                      tail_status='Exactly92 stored bytes retained; internal vertex/operation qualifiers unresolved')
    return result


def inspect_pipe_recipe_incidence(data, records, body, feature, features, member, members, body_identifier_summary,
                                  *, source_evidence=None, tag_evidence=None):
    """Cached edge association/geometry/closure only; never full tool_settings."""
    evidence = tag_evidence if tag_evidence is not None else inspect_pipe_recipe_tags(
        data, records, body, feature, features, member, members, body_identifier_summary,
        source_evidence=source_evidence)
    if evidence['feature_object_id'] != feature['object_id']:
        raise ValueError('Pipe recipe naming evidence owner disagrees')
    matching_records = [r for r in records if r.is_primary and r.object_id == evidence['source_recipe_object_id']]
    if len(matching_records) != 1:
        raise ValueError('Pipe incidence recipe identity missing or ambiguous')
    recipe = decode_counted_recipe(data, matching_records[0])
    operands = decode_pipe_edge_recipe_operands(recipe)
    blob_member = evidence['history_blob_member']
    if blob_member not in members or not blob_member.startswith(member.rsplit('/FusionDesignSegmentType1/', 1)[0]+'/Breps.BlobParts/'):
        raise ValueError('Pipe incidence source blob leaves explicit same asset')
    parsed = inspect_asm(members[blob_member])
    topology = decode_topology(parsed)
    if topology['unresolved']:
        raise ValueError('Pipe incidence requires complete reciprocal initial BODY topology coverage')
    nodes = {node['index']: node for node in topology['nodes']}
    graphs = topology['body_graphs']
    source_graphs = [g for g in graphs if g['body_index'] == evidence['explicit_asm_source_body_index']]
    if len(source_graphs) != 1 or source_graphs[0]['body_transform_is_identity'] is not True:
        raise ValueError('Pipe incidence requires one explicitly mapped identity-transform source BODY graph')
    source_graph = source_graphs[0]
    name_entries = {entry['name_table_index']: entry for entry in evidence['recipe_naming_correspondence']['name_entries']}

    def named_face(reference):
        entry = name_entries.get(reference['name_table_index'])
        if entry is None or entry['candidate_count'] != 1:
            raise ValueError('Pipe face operand lacks a unique exact serialized naming correspondence')
        candidate = entry['candidates'][0]
        identity = candidate['owner_record_index']
        if (candidate['owner_kind'] != 'face' or candidate['body_graph_membership'] != [source_graph['body_index']]
                or identity not in source_graph['face_indices'] or nodes.get(identity, {}).get('kind') != 'face'):
            raise ValueError('Pipe face operand does not name a typed face of the explicit source BODY')
        return {'name_table_index': reference['name_table_index'], 'attribute_record_index': candidate['attribute_record_index'],
                'face_record_index': identity}

    face_operands = [named_face(reference) for reference in operands['face_name_references']]
    face_ids = {operand['face_record_index'] for operand in face_operands}
    edge_faces, vertex_faces, incidence_routes = {}, {}, {}
    for graph in graphs:
        for identity in graph['coedge_indices']:
            coedge = nodes.get(identity)
            if coedge is None or coedge['kind'] != 'coedge':
                raise ValueError('Pipe source incidence coedge unresolved')
            loop = nodes.get(coedge['loop_index'])
            edge = nodes.get(coedge['edge_index'])
            if (loop is None or loop['kind'] != 'loop' or loop['face_index'] not in graph['face_indices']
                    or coedge['loop_index'] not in graph['loop_indices']
                    or edge is None or edge['kind'] != 'edge' or edge['index'] not in graph['edge_indices']):
                raise ValueError('Pipe face/loop/coedge/edge ownership is not reciprocal')
            face_id, edge_id = loop['face_index'], edge['index']
            edge_faces.setdefault(edge_id, set()).add(face_id)
            for vertex in (edge['start_vertex_index'], edge['end_vertex_index']):
                vertex_faces.setdefault(vertex, set()).add(face_id)
            incidence_routes.setdefault(edge_id, []).append({'body_index': graph['body_index'],
                'face_index': face_id, 'loop_index': loop['index'], 'coedge_index': identity, 'edge_index': edge_id})
    matches = [identity for identity, faces in edge_faces.items() if faces == face_ids]
    if len(matches) != 1:
        raise ValueError('Two named Pipe faces do not have exactly one common reciprocal edge')
    selected_id = matches[0]
    memberships = [g['body_index'] for g in graphs if selected_id in g['edge_indices']]
    if memberships != [source_graph['body_index']]:
        raise ValueError('Pipe incidence edge source BODY membership disagrees or is ambiguous')
    edge = nodes[selected_id]
    if edge['is_reversed'] is not False or edge['first_coedge_index'] is None:
        raise ValueError('Unobserved reversed/detached Pipe incidence edge variant')
    start_id, end_id = edge['start_vertex_index'], edge['end_vertex_index']
    vertex_results = []
    if operands['vertex_face_operands'] is not None:
        for operand in operands['vertex_face_operands']:
            faces = [named_face(reference) for reference in operand['face_name_references']]
            needed = {item['face_record_index'] for item in faces}
            candidates = [identity for identity, incident in vertex_faces.items() if incident == needed]
            if len(candidates) != 1:
                raise ValueError('Pipe vertex three-face operand does not identify one reciprocal vertex')
            vertex_results.append({'operand_ordinal': operand['operand_ordinal'], 'face_operands': faces,
                                   'vertex_record_index': candidates[0]})
        if [item['vertex_record_index'] for item in vertex_results] != [start_id, end_id] or start_id == end_id:
            raise ValueError('Pipe stored endpoint operands disagree with ordered source edge vertex identities')
    direct_index = operands['stored_direct_edge_name_index']
    direct_discriminator = None
    if direct_index >= 0:
        candidates = name_entries[direct_index]['candidates']
        if not candidates or any(candidate['owner_kind'] != 'edge' for candidate in candidates):
            raise ValueError('Direct Pipe edge-name operand has no exact typed edge candidates')
        surviving = [candidate for candidate in candidates if candidate['owner_record_index'] == selected_id]
        if len(surviving) != 1:
            raise ValueError('Named Pipe edge and two-face incidence do not select the same unique owner')
        direct_discriminator = {'name_table_index': direct_index, 'original_candidates': candidates,
                                'surviving_edge_record_index': selected_id,
                                'rejected_owner_record_indices': [candidate['owner_record_index'] for candidate in candidates if candidate['owner_record_index'] != selected_id],
                                'basis': 'Serialized face operands require reciprocal incidence; detached copies have no face incidence. No coordinate/root-order choice.'}
    curve = nodes.get(edge['curve_index'])
    endpoints = []
    for identity in (start_id, end_id):
        vertex = nodes.get(identity)
        point = nodes.get(vertex['point_index']) if vertex and vertex['kind'] == 'vertex' else None
        if point is None or point['kind'] != 'point':
            raise ValueError('Pipe incidence edge endpoint point cache unresolved')
        endpoints.append({'vertex_record_index': identity, 'point_record_index': point['index'], 'raw_point': point['raw_origin']})
    if curve is None or not math.isfinite(edge['start_parameter']) or not math.isfinite(edge['end_parameter']):
        raise ValueError('Pipe incidence source curve/parameter cache unresolved')
    if operands['operand_layout'].startswith('TwoFaceEdge'):
        if curve['kind'] != 'straight-curve' or start_id == end_id or not edge['end_parameter'] > edge['start_parameter']:
            raise ValueError('Unobserved source geometry for captured linear Pipe recipe operand layout')
        closed = False
        geometry = {'kind': 'Line', 'raw_origin': curve['raw_origin'], 'direction': curve['direction'],
                    'natural_parameter_interval': curve['parameter_interval']}
    else:
        if (curve['kind'] != 'ellipse-curve' or start_id != end_id
                or not math.isclose(curve['stored_axis_ratio'], 1., abs_tol=1e-12)
                or not math.isclose(edge['end_parameter']-edge['start_parameter'], 2*math.pi, abs_tol=1e-10)):
            raise ValueError('Unobserved source geometry for captured circular Pipe recipe operand layout')
        closed = True
        geometry = {'kind': 'Circle', 'raw_center': curve['raw_origin'], 'normal': curve['normal'],
                    'raw_reference_axis': curve['stored_reference_axis'], 'raw_radius': curve['raw_major_radius'],
                    'stored_axis_ratio': curve['stored_axis_ratio'], 'natural_parameter_interval': curve['parameter_interval']}
    return {'feature_object_id': feature['object_id'], 'source_recipe_object_id': recipe['object_id'],
            'source_descriptor_object_id': evidence['source_descriptor_object_id'],
            'source_body_anchor_object_id': evidence['source_body_anchor_object_id'],
            'native_source_body_object_id': evidence['native_source_body_object_id'],
            'history_blob_member': blob_member, 'explicit_asm_source_body_index': source_graph['body_index'],
            'operation_operands': operands, 'face_operands': face_operands,
            'source_edge_record_index': selected_id, 'source_edge_incidence_routes': incidence_routes[selected_id],
            'line_vertex_operand_associations': vertex_results,
            'direct_edge_name_disambiguation': direct_discriminator,
            'cached_source_curve_record_index': edge['curve_index'], 'cached_source_geometry': geometry,
            'cached_endpoint_points': endpoints, 'cached_source_edge_is_closed': closed,
            'closure_basis': 'Same stored endpoint vertex identity plus full circular parameter span, or distinct typed endpoint identities on a nondegenerate Line; never optional selector/descriptor flag',
            'cached_source_edge_parameter_domain': [edge['start_parameter'], edge['end_parameter']],
            'Pipe_path_partial_limit_status': 'Source edge parameter domain is separate from Pipe distanceOne/distanceTwo fractions and resulting Pipe path limits',
            'path_is_opposed_to_entity': None,
            'coordinate_scope': 'Raw ASM initial cache coordinates; agree with cm in captured identity-transform root-component cases, no header-unit conversion or occurrence transform inferred',
            'tool_settings_status': 'Unresolved; bounded cached source association and closure only, complete native recipe operation and full Pipe tool semantics not claimed',
            'scope': SCOPE}


def encode_pipe_edge_recipe_operands(operands):
    """Replay bounded operand fields; preserve every uninterpreted circular byte."""
    output = struct.pack('<iiI', operands['stored_direct_edge_name_index'], operands['stored_secondary_index'], 2)
    for reference in operands['face_name_references']:
        output += struct.pack('<ii', reference['name_table_index'], reference['stored_secondary_index'])
    if operands['vertex_face_operands'] is None:
        return output+bytes.fromhex(operands['uninterpreted_remaining_payload_hex'])
    output += struct.pack('<I', 2)
    for vertex in operands['vertex_face_operands']:
        output += struct.pack('<iI', vertex['stored_direct_vertex_name_index'], 3)
        for reference in vertex['face_name_references']:
            output += struct.pack('<ii', reference['name_table_index'], reference['stored_secondary_index'])
        output += struct.pack('<ii', *vertex['stored_tail_fields_int32'])
    return output+struct.pack('<i', operands['stored_edge_tail_field_int32'])


def validate_fixtures(root, zstd_library=None):
    """Focused saved API comparisons and malformed operand/reciprocal-route guards."""
    import copy
    import json
    from pathlib import Path
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records

    root = Path(root)
    folder = 'pipeedgecontrasts-5bd287323ae7'
    files = [(folder+'/'+s['file'], s) for s in json.loads((root/folder/'ground_truth.json').read_text())['samples']]
    folder = 'pipepaths-3d11bd427946'
    files += [(folder+'/'+s['file'], s) for s in json.loads((root/folder/'ground_truth.json').read_text())['samples']
              if s['file'] == 'brep_edge_circular.f3d']
    report = {'scope': SCOPE, 'interfaces': {
        'inspector': 'inspect_pipe_recipe_incidence(data,records,body,feature,features,member,members,body_identifier_summary,*,source_evidence=None,tag_evidence=None)',
        'operand_parser': 'decode_pipe_edge_recipe_operands(recipe)',
        'exact_replay': 'encode_pipe_edge_recipe_operands(operands)',
        'validator': 'validate_fixtures(root,zstd_library=None)',
        'expected_outputs': 'samples[].expected_summary contains the entire per-feature inspector output for exact main integration comparisons',
        'integration': 'Separate pipe_recipe_incidence summary and cached-source annotation only. Retain every full Pipe settings failure and leave Path direction/partial limits unresolved.'},
        'grammar': {
            'common_prefix': 'int32 direct-edge name index (-1 or observed0), int32 secondary -1, uint32 face_count2, two pairs (int32 name-table index,int32 -1). Exact framed native names match complete generic-tag term groups.',
            'line116': 'After28-byte prefix: uint32 endpoint_count2; two40-byte vertex operands, each int32 directvertex -1,uint32 face_count3, three name-index/-1 pairs,two stored zero int32; final stored zero int32. Face triples uniquely select ordered endpoint vertices through reciprocal topology.',
            'circle120': 'Common28-byte prefix plus exactly92 retained bytes beginning int32 1. Direct-edge name may match detached and owning edges. Two explicit face operands disambiguate by reciprocal incidence; remaining circular qualifiers are not interpreted.',
            'association': 'Unique exact named-face matches, validated BODY/lump/shell/face/loop/coedge rings and edge references, exactly one edge incident to the two named faces. Source BODY membership checked only after incidence uniqueness. No coordinates, ordinal matching or name-duplicate filtering by source-body membership.',
            'closure': 'Cached source topology only: distinct endpoint identities on positive-domain straight curve means open; identical endpoint identity on ratio-one ellipse with full2pi edge domain means closed. Pipe direction and partial-limit semantics remain separate.'},
        'limitations': [
            'The circular92-byte operation tail is retained exactly and not evaluated. No complete native recipe operation, universal naming engine, persistent topology identity or regeneration is claimed.',
            'Only the observed root-component identity-transform initial geometry and116/120-byte edge operand layouts are admitted. Reversed edges, arcs, transforms, other term counts and unresolved BODY topology are rejected.',
            'Raw ASM coordinates are preserved. Saved cm getters independently corroborate these fixtures; no general ASM header-unit or occurrence conversion is inferred.',
            'Source edge parameter domain differs from normalized natural Line/Circle evaluators and Pipe distanceOne/distanceTwo fractions. Actual Path opposition and final partial Path shape are not decoded.',
            'The older brep_edge_circular filename refers to Pipe section shape; the actual source getter and decoded source are an open Line.'],
        'samples': [], 'comparisons': [], 'malformed_guards': []}
    saved_circle = saved_line = None

    def check(label, actual, expected):
        assert actual == expected, (label, actual, expected)
        report['comparisons'].append({'label': label, 'actual': actual, 'expected': expected, 'passed': True})

    def close(actual, expected):
        return len(actual) == len(expected) and all(math.isclose(a, b, abs_tol=1e-9) for a, b in zip(actual, expected))

    for filename, sample in files:
        path = root/filename
        members = read_members(path, zstd_library)
        stream = decode_basics(path, zstd_library)['streams'][0]
        data = members[stream['member']]
        records, _ = design_records(data, members[stream['member'].replace('BulkStream.dat', 'MetaStream.dat')])
        features = stream['features']
        feature = next(f for f in features if f['kind'] == 'Pipe')
        record = next(r for r in records if r.is_primary and r.object_id == feature['object_id'])
        body = data[record.body:record.end]
        evidence = inspect_pipe_recipe_incidence(data, records, body, feature, features, stream['member'], members, stream['body_asm_identifiers'])
        recipe_record = next(r for r in records if r.is_primary and r.object_id == evidence['source_recipe_object_id'])
        recipe = decode_counted_recipe(data, recipe_record)
        check(filename+' native operand replay', encode_pipe_edge_recipe_operands(evidence['operation_operands']).hex(), recipe['payload_hex'])
        api = sample['settings']
        source = api['path']['members'][0]['source']
        check(filename+' actual single source member', api['path']['count'], 1)
        check(filename+' cached source closure vs actual Path getter', evidence['cached_source_edge_is_closed'], api['path']['is_closed'])
        check(filename+' typed primitive vs natural source getter',
              'adsk::core::'+evidence['cached_source_geometry']['kind']+'3D', source['natural_geometry']['geometry_type'])
        check(filename+' stored source edge domain vs trimmed source evaluator',
              close(evidence['cached_source_edge_parameter_domain'], source['trimmed_edge_evaluator']['parameter_extents']), True)
        expected_points = [source.get(side+'_vertex', {}).get('point_cm', source.get(side+'_vertex_point_cm')) for side in ('start', 'end')]
        check(filename+' endpoint caches vs source vertex getters',
              all(close(item['raw_point'], point) for item, point in zip(evidence['cached_endpoint_points'], expected_points)), True)
        geometry = evidence['cached_source_geometry']
        cache_samples_agree = []
        for actual in source['trimmed_edge_evaluator']['samples']:
            parameter = actual['parameter']
            if geometry['kind'] == 'Line':
                point = [origin+parameter*direction for origin, direction in zip(geometry['raw_origin'], geometry['direction'])]
                tangent = geometry['direction']
            else:
                normal, major = geometry['normal'], geometry['raw_reference_axis']
                minor = [normal[1]*major[2]-normal[2]*major[1], normal[2]*major[0]-normal[0]*major[2], normal[0]*major[1]-normal[1]*major[0]]
                point = [center+a*math.cos(parameter)+b*math.sin(parameter) for center, a, b in zip(geometry['raw_center'], major, minor)]
                tangent = [-a*math.sin(parameter)+b*math.cos(parameter) for a, b in zip(major, minor)]
            cache_samples_agree.append(close(point, actual['point_cm']) and close(tangent, actual['tangent']))
        check(filename+' selected primitive vs independent trimmed source points and tangents', all(cache_samples_agree), True)
        source_body = next(b for b in stream['body_properties']['bodies'] if b['object_id'] == evidence['native_source_body_object_id'])
        check(filename+' explicit native body name vs source getter', source_body['name'], source['body_name'])
        check(filename+' Path direction remains unknown', evidence['path_is_opposed_to_entity'], None)
        check(filename+' full tool settings remain unresolved', 'Unresolved' in evidence['tool_settings_status'], True)
        routes = evidence['source_edge_incidence_routes']
        check(filename+' selected edge has exactly named incident faces',
              sorted({r['face_index'] for r in routes}), sorted(f['face_record_index'] for f in evidence['face_operands']))
        if evidence['cached_source_edge_is_closed']:
            selection = evidence['direct_edge_name_disambiguation']
            check(filename+' original edge-name ambiguity retained', len(selection['original_candidates']), 2)
            check(filename+' detached same-named edge rejected by face incidence', selection['rejected_owner_record_indices'], [2])
            check(filename+' opaque circular tail retained exact length', len(bytes.fromhex(evidence['operation_operands']['uninterpreted_remaining_payload_hex'])), 92)
            saved_circle = (data, records, body, feature, features, stream, members, evidence, recipe)
        else:
            check(filename+' both ordered endpoint IDs independently resolved by face triples',
                  [v['vertex_record_index'] for v in evidence['line_vertex_operand_associations']],
                  [v['vertex_record_index'] for v in evidence['cached_endpoint_points']])
            saved_line = (data, records, body, feature, features, stream, members, evidence, recipe)
        report['samples'].append({'file': filename, 'expected_summary': evidence,
            'API_observation': {'source_type': source['entity_type'], 'source_geometry_type': source['natural_geometry']['geometry_type'],
                'path_is_closed': api['path']['is_closed'], 'source_trimmed_parameter_domain': source['trimmed_edge_evaluator']['parameter_extents'],
                'natural_parameter_domain': source['natural_geometry']['parameter_extents'], 'distance_one': api['distance_one'], 'distance_two': api['distance_two'],
                'is_opposed_to_entity': api['path']['members'][0]['is_opposed_to_entity']},
            'API_evidence_status': 'Independent getters used only after serialized naming/incidence resolves source identity; no getter injected into decoder inputs'})

    def reject(label, action):
        try:
            action()
        except (ValueError, IndexError, KeyError, struct.error) as error:
            report['malformed_guards'].append({'label': label, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError(label+' was accepted')

    data, records, body, feature, features, stream, members, evidence, recipe = saved_circle
    for label, offset, value in [('Wrong face operand count', 8, 3), ('Out-of-range face name index', 12, 99),
                                 ('Duplicate face name operands', 20, 1), ('Non-minus-one face sentinel', 16, 0)]:
        changed = copy.deepcopy(recipe)
        payload = bytearray.fromhex(changed['payload_hex'])
        struct.pack_into('<i', payload, offset, value)
        changed['payload_hex'] = payload.hex()
        reject(label, lambda changed=changed: decode_pipe_edge_recipe_operands(changed))
    changed = copy.deepcopy(recipe)
    changed['payload_hex'] = changed['payload_hex'][:-2]
    reject('Truncated circular tail', lambda: decode_pipe_edge_recipe_operands(changed))

    # Mutate actual native recipe bytes, retaining syntactically valid existing name index.
    # Selecting the edge-name group as a face must fail typed matching, not choose by geometry.
    recipe_record = next(r for r in records if r.is_primary and r.object_id == evidence['source_recipe_object_id'])
    raw = bytes.fromhex(recipe['payload_hex'])
    raw_start = data.find(raw, recipe_record.body, recipe_record.end)
    assert raw_start >= 0 and data.find(raw, raw_start+1, recipe_record.end) == -1
    changed_data = bytearray(data)
    struct.pack_into('<i', changed_data, raw_start+12, 0)
    reject('Edge-name reused as face violates distinct operand coverage', lambda: inspect_pipe_recipe_incidence(
        bytes(changed_data), records, body, feature, features, stream['member'], members, stream['body_asm_identifiers']))

    # Break a real face/coedge route in the explicitly referenced blob.
    blob_member = evidence['history_blob_member']
    blob = members[blob_member]
    parsed = inspect_asm(blob)
    route = evidence['source_edge_incidence_routes'][0]
    token = parsed['records'][route['coedge_index']]['tokens'][8]
    changed_blob = bytearray(blob)
    struct.pack_into('<q', changed_blob, token['offset']+1, -1)
    changed_members = dict(members)
    changed_members[blob_member] = bytes(changed_blob)
    reject('Broken reciprocal coedge-loop source route', lambda: inspect_pipe_recipe_incidence(
        data, records, body, feature, features, stream['member'], changed_members, stream['body_asm_identifiers']))

    data, records, body, feature, features, stream, members, evidence, recipe = saved_line
    recipe_record = next(r for r in records if r.is_primary and r.object_id == evidence['source_recipe_object_id'])
    raw = bytes.fromhex(recipe['payload_hex'])
    raw_start = data.find(raw, recipe_record.body, recipe_record.end)
    assert raw_start >= 0
    # Swap intact vertex operands. Their face triples still resolve, but to the wrong ordered endpoints.
    changed_data = bytearray(data)
    changed_data[raw_start+32:raw_start+72] = raw[72:112]
    changed_data[raw_start+72:raw_start+112] = raw[32:72]
    reject('Swapped endpoint face subrecipes fail ordered vertex identity guard', lambda: inspect_pipe_recipe_incidence(
        bytes(changed_data), records, body, feature, features, stream['member'], members, stream['body_asm_identifiers']))
    report['validation'] = {'saved_files': len(files), 'source_edges_resolved': len(files), 'open_line_sources': 4, 'closed_circle_sources': 2,
        'exact_operand_payload_replays': len(files), 'comparisons_passed': len(report['comparisons']),
        'malformed_guards_passed': len(report['malformed_guards']), 'full_Pipe_settings_failures_cleared': 0,
        'new_API_calls': 0}
    return report
