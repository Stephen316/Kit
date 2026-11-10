"""Exact named-operand incidence for saved single-edge/vertex source selections.

The descriptor's primary recipe and historical body anchor are sufficient when
an explicit same-blob BODY mapping and reciprocal cached topology survive.
Secondary geometry-only contexts remain opaque. Modified-away edges never
resolve by matching coordinates or choosing a nearby final edge.
"""
import copy
import math
import struct
import uuid

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags, match_recipe_tag_names
from decode_body_asm_identifiers import MAPPING, _body_identifiers
from decode_body_properties import BODY, COLLECTION
from decode_body_selections import ANCHOR, HELPER, SUPPORT, decode_body_selections
from decode_brep import decode_topology
from decode_parameters import read_string
from decode_pipe_edge_limits import decode_pipe_auxiliary_vertex_operand
from decode_pipe_recipe_incidence import decode_pipe_edge_recipe_operands
from decode_recipe_components import decode_counted_recipe
from decode_selection_context_recipes import TOPOLOGY
from decode_sketch import reference

SCOPE = 'Observed source descriptor primary recipe -> exact initial generic tags -> reciprocal cached source edge/vertex incidence in explicitly mapped same-asset BODY; secondary context cache and persistent/historical topology remain unresolved'
CACHE_LAYOUTS = {'50AEE8B4-9456-4DD7-847D-6F6C909BBB9D': (55, 75),
                 'B0B3FA59-C374-444F-B424-24AA5DE41645': (103,),
                 '994C518A-A831-400A-B7C7-16DAC55F4F1C': (28,)}


def decode_selection_recipe_incidence(data, records, features, member, members, body_identifier_summary,
                                      body_selections=None, *, descriptor_ids=None):
    """Return associations/unresolved/scope, keyed by descriptor_object_id.

    Geometry-only secondary context failures must not be cleared by this result.
    Optional descriptor_ids narrows examination; it supplies no semantic truth.
    """
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: rows[0] for identity, rows in grouped.items() if len(rows) == 1}
    bodies = body_selections if body_selections is not None else decode_body_selections(data, records)
    anchors = {}
    for anchor in bodies['body_anchors']:
        anchors.setdefault(anchor['object_id'], []).append(anchor)
    wanted = None if descriptor_ids is None else set(descriptor_ids)

    def typed(identity, guid=None):
        rec = primary.get(identity)
        if rec is None or guid is not None and rec.class_guid != guid:
            raise ValueError('Source recipe incidence typed reference missing, ambiguous or wrong class')
        return rec, data[rec.body:rec.end]

    def text_uuid(payload, cursor):
        value, end = read_string(payload, cursor)
        if len(value) != 36:
            raise ValueError('Source descriptor UUID extent unsupported')
        uuid.UUID(value)
        return value, end

    def mapped_blob(native_body_id):
        choices = [(mapping, binding) for mapping in body_identifier_summary['decoded'] for binding in mapping['bindings']
                   if binding['native_body_object_id'] == native_body_id]
        if len(choices) != 1:
            raise ValueError('Source body does not have one explicit ASM mapping')
        mapping, binding = choices[0]
        _, payload = typed(mapping['mapping_record_object_id'], MAPPING)
        typed(native_body_id, BODY)
        if payload[:2] != bytes(2):
            raise ValueError('Source native mapping prefix disagrees')
        count = struct.unpack_from('<I', payload, 2)[0]
        cursor = 6+16*count
        if not 1 <= count <= 1024 or cursor+16 > len(payload):
            raise ValueError('Source native mapping count/extent unsupported')
        pairs = [struct.unpack_from('<QQ', payload, 6+16*i) for i in range(count)]
        if pairs.count((binding['stored_handle'], native_body_id)) != 1:
            raise ValueError('Source native mapping body/handle pair disagrees')
        owner = reference(payload, cursor)
        typed(owner, COLLECTION)
        if mapping['owner_object_id'] != owner or mapping['body_count'] != count or payload[cursor+11] != 0:
            raise ValueError('Source native mapping owner/count/separator disagrees')
        filename, end = read_string(payload, cursor+12)
        if (end != len(payload) or not filename.startswith('BREP.') or not filename.endswith('.smbh')
                or '/' in filename or '\\' in filename):
            raise ValueError('Source native mapping blob filename unsupported')
        blob_member = member.rsplit('/FusionDesignSegmentType1/', 1)[0]+'/Breps.BlobParts/'+filename
        if blob_member != mapping['history_blob_member'] or blob_member not in members:
            raise ValueError('Source explicit same-asset history blob disagrees')
        blob = members[blob_member]
        parsed = inspect_asm(blob)
        roots, _, _ = _body_identifiers(parsed, blob)
        if (set(roots) != {handle for handle, _ in pairs}
                or roots[binding['stored_handle']]['index'] != binding['asm_body_index']):
            raise ValueError('Source native handle/typed ASM BODY association not bijective')
        root = parsed['records'][binding['asm_body_index']]
        if root['name'] != 'body' or root['tokens'][1]['kind'] != 'integer' or root['tokens'][1]['value'] != binding['stored_handle']:
            raise ValueError('Source mapped BODY stored ID disagrees')
        return blob_member, blob, parsed, binding['asm_body_index'], mapping['mapping_record_object_id']

    associations, unresolved = [], []
    for record in records:
        if not record.is_primary or record.class_guid != TOPOLOGY or wanted is not None and record.object_id not in wanted:
            continue
        payload = data[record.body:record.end]
        # Scope only the observed single geometry-only context family. Existing
        # explicit naming-route contexts and unrelated descriptor shapes stay elsewhere.
        if wanted is None:
            if len(payload) != 276:
                continue
            try:
                context_rec, context_payload = typed(reference(payload, 183))
                if len(context_payload) not in CACHE_LAYOUTS.get(context_rec.class_guid, ()):
                    continue
            except (ValueError, IndexError, struct.error):
                continue
        detail = {}
        try:
            if primary.get(record.object_id) is not record:
                raise ValueError('Source descriptor identity ambiguous')
            if (len(payload) != 276 or payload[:3] != bytes(3) or payload[3] not in (0, 1)
                    or struct.unpack_from('<I', payload, 15)[0] != 1
                    or payload[171:183] != struct.pack('<QI', 2, 1)
                    or struct.unpack_from('<I', payload, 194)[0] != 1):
                raise ValueError('Source descriptor single-context/anchor framing unsupported')
            namespace, cursor = text_uuid(payload, 19)
            entity, cursor = text_uuid(payload, cursor)
            if cursor != 171:
                raise ValueError('Source descriptor namespace pair extent disagrees')
            owner = reference(payload, 265)
            typed(owner)
            context_id = reference(payload, 183)
            context_rec, context_payload = typed(context_id)
            if len(context_payload) not in CACHE_LAYOUTS.get(context_rec.class_guid, ()) or context_payload[:2] != bytes(2):
                raise ValueError('Only captured geometry-only secondary context frames supported')
            anchor_id = reference(payload, 198)
            _, anchor_payload = typed(anchor_id, ANCHOR)
            matches = anchors.get(anchor_id, [])
            if len(matches) != 1:
                raise ValueError('Source descriptor historical body anchor unresolved')
            anchor = matches[0]
            if (len(anchor_payload) != 102 or reference(anchor_payload, 80) != anchor['native_body_object_id']
                    or reference(anchor_payload, 91) != anchor['source_owner_object_id']):
                raise ValueError('Source descriptor anchor native body/owner disagrees')
            if (payload[223:227] != b'\1\1\0\0' or payload[235:239] != b'\1\1\0\0'
                    or payload[250:253] != b'\1\0\0' or payload[264] != 0):
                raise ValueError('Source descriptor trailer markers disagree')
            helper_id, support_id = reference(payload, 239), reference(payload, 253)
            _, helper = typed(helper_id, HELPER)
            _, support = typed(support_id, SUPPORT)
            if helper not in (bytes(10), bytes.fromhex('0001000000000000000000000000')):
                raise ValueError('Source descriptor helper framing unsupported')
            if (len(support) < 39 or support[:6] != bytes(6) or support[-8:] != bytes(8)):
                raise ValueError('Source descriptor reciprocal support framing unsupported')
            count = struct.unpack_from('<I', support, 8)[0]
            if count not in (0, 1, 2) or len(support) != 39+19*count or support[6:8] != (b'\1\1' if count else bytes(2)):
                raise ValueError('Source support counted entries disagree')
            sources = [reference(support, 12+19*i) for i in range(count)]
            if any(i not in primary for i in sources) or reference(support, 12+19*count) != record.object_id:
                raise ValueError('Source descriptor/support ownership not reciprocal')
            if anchor['source_owner_object_id'] not in sources:
                raise ValueError('Source support does not explicitly name historical source owner')
            recipe_rec, _ = typed(reference(payload, 4), '7ACC2A03-0261-4879-A14A-A93D661A5BDC')
            recipe = decode_counted_recipe(data, recipe_rec)
            if recipe['payload_kind'] == 'edge_recipe_data':
                raw = bytes.fromhex(recipe['payload_hex'])
                if len(raw) not in (116, 120) or struct.unpack_from('<i', raw, len(raw)-4)[0] not in (0, -1):
                    raise ValueError('Source edge operation extent/final qualifier unsupported')
                normalized = copy.deepcopy(recipe)
                normalized['payload_hex'] = (raw[:-4]+bytes(4)).hex()
                operands = decode_pipe_edge_recipe_operands(normalized)
                operands['stored_original_final_int32'] = struct.unpack_from('<i', raw, len(raw)-4)[0]
                operands['uninterpreted_remaining_payload_hex'] = raw[28:].hex()
                if operands['vertex_face_operands'] is not None:
                    operands['stored_edge_tail_field_int32'] = operands['stored_original_final_int32']
                operands['original_payload_hex'] = raw.hex()
                operands['final_field_status'] = 'Observed opaque0/-1 qualifier retained; no history/direction meaning assigned'
                vertex_operands = operands['vertex_face_operands']
                refs = operands['face_name_references']
            elif recipe['payload_kind'] == 'vertex_recipe_data':
                operands = decode_pipe_auxiliary_vertex_operand(recipe)
                refs, vertex_operands = operands['face_name_references'], None
            else:
                raise ValueError('Source recipe kind not captured edge/vertex operand family')
            blob_member, blob, parsed, body_id, mapping_id = mapped_blob(anchor['native_body_object_id'])
            tags = decode_asm_generic_tags(blob, parsed)
            correspondence = match_recipe_tag_names(recipe, tags, parsed=parsed)
            topology = decode_topology(parsed)
            if topology['unresolved']:
                raise ValueError('Incomplete cached initial BODY topology prevents incidence uniqueness')
            nodes = {node['index']: node for node in topology['nodes']}
            graphs = topology['body_graphs']
            source_graphs = [g for g in graphs if g['body_index'] == body_id]
            if len(source_graphs) != 1 or source_graphs[0]['body_transform_is_identity'] is not True:
                raise ValueError('Source BODY graph missing/ambiguous or transformed')
            graph = source_graphs[0]
            names = {row['name_table_index']: row for row in correspondence['name_entries']}

            def face(ref):
                row = names[ref['name_table_index']]
                if row['candidate_count'] != 1:
                    raise ValueError('Source face operand name correspondence absent or ambiguous')
                candidate = row['candidates'][0]
                face_id = candidate['owner_record_index']
                if (candidate['owner_kind'] != 'face' or candidate['body_graph_membership'] != [body_id]
                        or face_id not in graph['face_indices'] or nodes[face_id]['kind'] != 'face'):
                    raise ValueError('Source face operand not typed member of explicit mapped BODY')
                return {'name_table_index': ref['name_table_index'], 'face_record_index': face_id,
                        'attribute_record_index': candidate['attribute_record_index']}

            faces = [face(ref) for ref in refs]
            needed = {row['face_record_index'] for row in faces}
            edge_faces, vertex_faces, routes = {}, {}, {}
            # decode_topology already validates BODY/lump/shell/face chains and
            # closed coedge rings, next/previous reciprocity and partner edges.
            for g in graphs:
                for coedge_id in g['coedge_indices']:
                    coedge = nodes[coedge_id]
                    loop = nodes[coedge['loop_index']]
                    edge = nodes[coedge['edge_index']]
                    face_id = loop['face_index']
                    edge_faces.setdefault(edge['index'], set()).add(face_id)
                    for vertex in (edge['start_vertex_index'], edge['end_vertex_index']):
                        vertex_faces.setdefault(vertex, set()).add(face_id)
                    routes.setdefault(edge['index'], []).append({'body_index': g['body_index'], 'face_index': face_id,
                        'loop_index': loop['index'], 'coedge_index': coedge_id, 'edge_index': edge['index']})
            candidates = [identity for identity, incident in (edge_faces if recipe['payload_kind'] == 'edge_recipe_data' else vertex_faces).items()
                          if incident == needed]
            detail = {'recipe_object_id': recipe['object_id'], 'payload_kind': recipe['payload_kind'],
                      'named_face_operands': faces, 'initial_incidence_candidate_record_indices': candidates,
                      'native_body_object_id': anchor['native_body_object_id'], 'history_blob_member': blob_member,
                      'explicit_asm_body_index': body_id, 'stored_original_payload_hex': recipe['payload_hex']}
            if len(candidates) != 1:
                raise ValueError('Named source operands do not identify exactly one surviving initial-cache entity; historical state replay unresolved')
            selected = candidates[0]
            collection_key = 'edge_indices' if recipe['payload_kind'] == 'edge_recipe_data' else 'vertex_indices'
            if [g['body_index'] for g in graphs if selected in g[collection_key]] != [body_id]:
                raise ValueError('Selected cached source membership disagrees with explicit BODY mapping')
            cached, endpoint_associations, direct = None, [], None
            if recipe['payload_kind'] == 'edge_recipe_data':
                edge = nodes[selected]
                if vertex_operands is not None:
                    for operand in vertex_operands:
                        endpoint_faces = [face(ref) for ref in operand['face_name_references']]
                        expected = {row['face_record_index'] for row in endpoint_faces}
                        vertices = [v for v, incident in vertex_faces.items() if incident == expected]
                        if len(vertices) != 1:
                            raise ValueError('Source endpoint face operands do not identify one cached vertex')
                        endpoint_associations.append({'operand_ordinal': operand['operand_ordinal'],
                            'face_operands': endpoint_faces, 'vertex_record_index': vertices[0]})
                    if [row['vertex_record_index'] for row in endpoint_associations] != [edge['start_vertex_index'], edge['end_vertex_index']]:
                        raise ValueError('Source ordered endpoint operands disagree with typed edge vertices')
                if operands['stored_direct_edge_name_index'] >= 0:
                    direct = names[operands['stored_direct_edge_name_index']]
                    if len([c for c in direct['candidates'] if c['owner_kind'] == 'edge' and c['owner_record_index'] == selected]) != 1:
                        raise ValueError('Source direct edge-name candidate disagrees with unique face incidence')
                if edge['is_reversed'] is not False:
                    raise ValueError('Reversed cached source edge outside captured scope')
                curve = nodes[edge['curve_index']]
                endpoints = [nodes[nodes[v]['point_index']]['raw_origin'] for v in (edge['start_vertex_index'], edge['end_vertex_index'])]
                if curve['kind'] == 'straight-curve' and vertex_operands is not None:
                    geometry = {'kind': 'Line', 'raw_origin': curve['raw_origin'], 'direction': curve['direction']}
                    if edge['start_vertex_index'] == edge['end_vertex_index'] or not edge['end_parameter'] > edge['start_parameter']:
                        raise ValueError('Degenerate/nonpositive cached source Line unsupported')
                    closed = False
                elif (curve['kind'] == 'ellipse-curve' and vertex_operands is None
                      and curve['stored_axis_ratio'] == 1 and edge['start_vertex_index'] == edge['end_vertex_index']
                      and math.isclose(edge['end_parameter']-edge['start_parameter'], 2*math.pi, abs_tol=1e-10)):
                    geometry = {'kind': 'Circle', 'raw_center': curve['raw_origin'], 'normal': curve['normal'],
                        'raw_reference_axis': curve['stored_reference_axis'], 'raw_radius': curve['raw_major_radius']}
                    closed = True
                else:
                    raise ValueError('Cached source primitive not admitted by observed operand layout')
                cached = {'kind': 'Edge', 'edge_record_index': selected, 'curve_record_index': edge['curve_index'],
                    'geometry': geometry, 'raw_endpoint_points': endpoints,
                    'endpoint_vertex_record_indices': [edge['start_vertex_index'], edge['end_vertex_index']],
                    'parameter_domain': [edge['start_parameter'], edge['end_parameter']], 'is_closed': closed,
                    'incidence_routes': routes[selected]}
            else:
                vertex = nodes[selected]
                point = nodes[vertex['point_index']]
                if point['kind'] != 'point':
                    raise ValueError('Cached source vertex does not reference typed point')
                cached = {'kind': 'Vertex', 'vertex_record_index': selected, 'point_record_index': point['index'],
                          'raw_point': point['raw_origin']}
            associations.append({'descriptor_object_id': record.object_id, 'owner_object_id': owner,
                'recipe_object_id': recipe['object_id'], 'recipe_payload_kind': recipe['payload_kind'],
                'context_object_id': context_id, 'context_class_guid': context_rec.class_guid,
                'context_status': 'Secondary cache kept separate; no context geometry evaluated and any independently supported secondary naming route remains unchanged',
                'namespace_text': namespace, 'entity_guid_text': entity, 'body_anchor_object_id': anchor_id,
                'native_body_object_id': anchor['native_body_object_id'], 'historical_source_owner_object_id': anchor['source_owner_object_id'],
                'mapping_record_object_id': mapping_id, 'history_blob_member': blob_member, 'explicit_asm_body_index': body_id,
                'helper_object_id': helper_id, 'support_object_id': support_id,
                'support_source_object_ids': sources, 'operation_operands': operands,
                'named_face_operands': faces, 'endpoint_operand_associations': endpoint_associations,
                'direct_edge_naming_candidates': direct, 'cached_source': cached,
                'identity_scope': 'Unique exact stored naming plus reciprocal surviving initial topology in explicit same-asset body; not universal persistent identity or historical-state evaluation',
                'coordinate_scope': 'Raw initial cache coordinates in observed identity-transform root-component source bodies; no general header-unit or occurrence conversion',
                'scope': SCOPE})
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            unresolved.append({'descriptor_object_id': record.object_id, 'reason': str(error),
                               'bounded_operand_evidence': detail or None})
    return {'associations': associations, 'unresolved': unresolved, 'scope': SCOPE}


def validate_fixtures(root, zstd_library=None):
    """Seven positive saved-source cases, three historical/incomplete controls."""
    import json
    from pathlib import Path
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records

    root = Path(root)
    cases = [('revolveaxes-14700158dba9/brep_edge_offset_x.f3d', [350], 1),
             ('revolveaxes-a83b542c4a07/brep_edge.f3d', [350], 1),
             ('silhouettedirections-805c2eaa2411/faces_brep_edge_x.f3d', [366], 1),
             ('silhouettedirections-805c2eaa2411/faces_custom_axis_x.f3d', [287], 1),
             ('sketchprojections-67c0c4531b8f/body_edge.f3d', [311], 1),
             ('holeplacements-04adf73afe93/center_edge.f3d', [303], 1),
             ('loftpointholdouts-bb91509a13e4/vertex_construction_sharp_end.f3d', [330], 1),
             ('edgemodes-52695761f185/chamfer_multiple.f3d', [286, 298], 0),
             ('edgemodes-52695761f185/fillet_curvature.f3d', [287], 0),
             ('edgemodes-87edbf67527b/chamfer_angle.f3d', [286], 0)]
    report = {'scope': SCOPE,
        'interface': 'decode_selection_recipe_incidence(data,records,features,member,members,body_identifier_summary,body_selections=None,*,descriptor_ids=None)',
        'expected_outputs': 'samples[].expected_summary contains full helper result using only samples[].descriptor_ids; controls[].expected_summary likewise',
        'integration': 'Late independent selection_recipe_incidence summary, with associations keyed descriptor_object_id and cached_source annotations only. Preserve all geometry-only secondary-context failures and existing successful context dictionaries. Do not reinterpret descriptor flag, source recipe qualifier or surviving source BODY cache as solved historical/final state.',
        'grammar': {
            'source_route': 'Owned276-byte descriptor with count1 context and count1 anchor; typed reciprocal support explicitly names historical source owner. Anchor names native BODY, which maps via an exact stored handle to typed initial ASM BODY in the explicitly referenced same-asset blob.',
            'edge': 'Observed116-byte edge recipe shares the Pipe two-face/two-three-face-vertex operand grammar; final int32 may be0/-1 and is retained opaque. Observed120-byte circular variant retains its92-byte tail exactly without evaluating it.',
            'vertex': 'Observed40-byte vertex recipe has int32direct-1,count3,three exact named-face operands and two storedzero fields. Reciprocal source vertex incidence must match the complete face triple uniquely.',
            'selection': 'Exact complete name/index/counted-component tuples join to reciprocally owned generic-tag attributes. A unique edge has exactly the two named incident faces; endpoint triples identify ordered typed endpoint vertices. Vertex selections have exactly the three named incident faces. Geometry is inspected only after this identity joins.',
            'secondary_context': 'Typed55/75-byte edge cache,103-byte circular cache or28-byte point cache stays separate. The75-byte projection route can already have an independently decoded secondary naming link; this primary-recipe join does not replace it.'},
        'limitations': [
            'A matching named face pair does not guarantee a currently surviving edge. Chamfer/Fillet remove the selected edge and alter the same native BODY; current-cache absence is not permission to choose a nearby edge or replay unqualified trailing records.',
            'Some modified Fillet bodies include unsupported cached topology/geometry. Their incomplete coverage blocks uniqueness claims and remains unresolved.',
            'Only observed identity-transform initial BODY topology, single edge Line/Circle and vertex three-face operands are admitted. Surface-boundary recipe families and generic-tag layouts outside the existing strict reader remain unresolved.',
            'The edge operation final0/-1 field is opaque. Circular92-byte operation qualifiers, context geometry, historical-state replay, universal persistent topology and regeneration remain unresolved.',
            'Projected-source cache retains source z=2 while captured projected output lies at z=0. Output coordinates do not select source identity and do not substitute for the actual unprojected source.',
            'AtCenter Hole fixture did not capture an actual BRepEdge getter; its selected source circle center is corroborated by the actual hole position and documented generator setup, not an invented source getter.'],
        'history_FPM_followup': {
            'file': 'edgemodes-52695761f185/chamfer_multiple.f3d',
            'observation': 'Trailing geometry contains two FPM_tracked_attrib_def attributes whose literal payload values286/298 correspond numerically to the two native descriptors. Attribute owners are trailing edges, with typed geometry pointer ordinals distinct from global inspection indices.',
            'candidate_records': [{'attribute_inspection_record_index': 149, 'owner_geometry_pointer_ordinal': 142, 'owner_inspection_record_index': 148, 'stored_literal': 286},
                                  {'attribute_inspection_record_index': 151, 'owner_geometry_pointer_ordinal': 144, 'owner_inspection_record_index': 150, 'stored_literal': 298}],
            'status': 'Research candidates only; no historical source identity or geometry exposed. Need independently qualified journal state and typed reciprocal owner/topology replay before using this numeric correspondence.',
            'next_action': 'Investigate FPM attribute framing and exact delta-state slot mentions using initial+trailing geometry entity pointer table; keep journal side/chronology unresolved until proven.'},
        'samples': [], 'controls': [], 'comparisons': [], 'malformed_guards': []}
    loaded = {}

    def check(label, actual, expected):
        assert actual == expected, (label, actual, expected)
        report['comparisons'].append({'label': label, 'actual': actual, 'expected': expected, 'passed': True})

    def same_points(a, b):
        return len(a) == len(b) and all(len(x) == len(y) and all(math.isclose(u, v, abs_tol=1e-9) for u, v in zip(x, y)) for x, y in zip(a, b))

    for filename, ids, expected_count in cases:
        path = root/filename
        members = read_members(path, zstd_library)
        stream = decode_basics(path, zstd_library)['streams'][0]
        data = members[stream['member']]
        records, _ = design_records(data, members[stream['member'].replace('BulkStream.dat', 'MetaStream.dat')])
        result = decode_selection_recipe_incidence(data, records, stream['features'], stream['member'], members,
            stream['body_asm_identifiers'], stream['body_selections'], descriptor_ids=ids)
        check(filename+' expected source association count', len(result['associations']), expected_count)
        actual = next(sample for sample in json.loads((path.parent/'ground_truth.json').read_text())['samples'] if sample['file'] == path.name)
        entry = {'file': filename, 'descriptor_ids': ids, 'expected_summary': result}
        if not expected_count:
            check(filename+' every requested source remains unresolved', [row['descriptor_object_id'] for row in result['unresolved']], ids)
            entry['API_observation'] = {'edge_sets': actual['settings']['edge_sets'],
                'evidence_scope': 'Actual Fillet/Chamfer settings and generator edge selections exist, but no source entity geometry getter was captured; cache absence is preserved without geometry inference.'}
            for row in result['unresolved']:
                if row['bounded_operand_evidence']:
                    check(filename+f" descriptor{row['descriptor_object_id']} no current source edge", row['bounded_operand_evidence']['initial_incidence_candidate_record_indices'], [])
            report['controls'].append(entry)
            continue
        check(filename+' no requested association failure', result['unresolved'], [])
        row = result['associations'][0]
        source = row['cached_source']
        check(filename+' descriptor identity retained', row['descriptor_object_id'], ids[0])
        if source['kind'] == 'Edge':
            check(filename+' resolved edge incidence includes exactly named faces',
                  sorted({route['face_index'] for route in source['incidence_routes']}), sorted(f['face_record_index'] for f in row['named_face_operands']))
        if filename.startswith('revolveaxes'):
            api = actual['actual_axis']
            check(filename+' actual source endpoint getters', same_points(source['raw_endpoint_points'], [api['start_cm'], api['end_cm']]), True)
            check(filename+' actual source primitive', 'adsk::core::'+source['geometry']['kind']+'3D', api['geometry_type'])
            body = next(b for b in stream['body_properties']['bodies'] if b['object_id'] == row['native_body_object_id'])
            check(filename+' source body name vs actual getter', body['name'], api['body_name'])
            entry['API_observation'] = {'entity_type': api['entity_type'], 'source_body_name': api['body_name'],
                                       'start_cm': api['start_cm'], 'end_cm': api['end_cm'], 'geometry_type': api['geometry_type']}
        elif filename.startswith('silhouettedirections'):
            api = actual['actual_direction']
            if 'definition_edge' in api:
                api = api['definition_edge']
            check(filename+' actual source endpoint getters', same_points(source['raw_endpoint_points'], [api['start_vertex_cm'], api['end_vertex_cm']]), True)
            check(filename+' actual source primitive', 'adsk::core::'+source['geometry']['kind']+'3D', api['geometry_type'])
            check(filename+' source parameter domain vs actual trimmed edge evaluator', same_points([source['parameter_domain']], [api['actual_trimmed_edge_evaluator']['parameter_extents']]), True)
            body = next(b for b in stream['body_properties']['bodies'] if b['object_id'] == row['native_body_object_id'])
            check(filename+' source body name vs actual getter', body['name'], api['body']['name'])
            entry['API_observation'] = {'entity_type': api['entity_type'], 'source_body_name': api['body']['name'],
                'start_cm': api['start_vertex_cm'], 'end_cm': api['end_vertex_cm'], 'trimmed_evaluator': api['actual_trimmed_edge_evaluator']}
        elif filename.startswith('sketchprojections'):
            api = actual['settings']
            output = api['outputs'][0]
            check(filename+' actual source/reference getter types', [api['source_type'], output['referenced_type']], ['adsk::fusion::BRepEdge']*2)
            check(filename+' projected XY endpoints agree source XY after independent source identity',
                  same_points([p[:2] for p in source['raw_endpoint_points']], [output['start_world_cm'][:2], output['end_world_cm'][:2]]), True)
            check(filename+' source/output Z remain explicitly distinct', [source['raw_endpoint_points'][0][2], output['start_world_cm'][2]], [2., 0.])
            entry['API_observation'] = {'source_type': api['source_type'], 'referenced_type': output['referenced_type'],
                'projected_start_world_cm': output['start_world_cm'], 'projected_end_world_cm': output['end_world_cm'],
                'scope': 'Actual projected output getter, not an uncaptured original source-edge geometry getter'}
        elif filename.startswith('holeplacements'):
            check(filename+' selected cached primitive is a closed Circle', [source['geometry']['kind'], source['is_closed']], ['Circle', True])
            check(filename+' cached source circle center vs actual AtCenter hole position', same_points([source['geometry']['raw_center']], [actual['position_cm']]), True)
            entry['API_observation'] = {'position_definition': actual['position_definition'], 'position_cm': actual['position_cm'],
                'scope': 'No original BRepEdge getter captured; generator setPositionAtCenter uses controlled top circular edge.'}
        else:
            api = actual['vertex_before_construction']
            check(filename+' selected cached kind vs actual source getter', source['kind'], 'Vertex')
            check(filename+' selected point vs actual vertex getter', same_points([source['raw_point']], [api['world_point_cm']]), True)
            body = next(b for b in stream['body_properties']['bodies'] if b['object_id'] == row['native_body_object_id'])
            check(filename+' source body name vs actual getter', body['name'], api['body_name'])
            entry['API_observation'] = {'entity_type': api['entity_type'], 'source_body_name': api['body_name'], 'world_point_cm': api['world_point_cm']}
        entry['API_evidence_scope'] = 'Saved API truth used only after exact stored-name and reciprocal-topology identity joins; no getter truth injected into decoder.'
        report['samples'].append(entry)
        loaded[filename] = data, records, stream, members, row

    filename = 'revolveaxes-14700158dba9/brep_edge_offset_x.f3d'
    data, records, stream, members, row = loaded[filename]
    primary = {r.object_id: r for r in records if r.is_primary}

    def rejected(label, changed_data=data, changed_members=members, identifiers=None):
        result = decode_selection_recipe_incidence(changed_data, records, stream['features'], stream['member'], changed_members,
            identifiers if identifiers is not None else stream['body_asm_identifiers'], stream['body_selections'], descriptor_ids=[row['descriptor_object_id']])
        assert not result['associations'] and len(result['unresolved']) == 1, label
        report['malformed_guards'].append({'label': label, 'rejected': True, 'reason': result['unresolved'][0]['reason']})

    for label, identity, offset, value in [('Descriptor anchor count', row['descriptor_object_id'], 194, 2),
                                          ('Nonreciprocal support descriptor', row['support_object_id'], 31, row['owner_object_id'])]:
        changed = bytearray(data)
        rec = primary[identity]
        if label == 'Descriptor anchor count':
            struct.pack_into('<I', changed, rec.body+offset, value)
        else:
            # reference begins with its typed marker; replace only the native u64 field.
            struct.pack_into('<Q', changed, rec.body+offset+1, value)
        rejected(label, bytes(changed))
    rec = primary[row['recipe_object_id']]
    recipe = decode_counted_recipe(data, rec)
    raw = bytes.fromhex(recipe['payload_hex'])
    start = data.find(raw, rec.body, rec.end)
    assert start >= 0
    changed = bytearray(data)
    struct.pack_into('<i', changed, start+12, 99)
    rejected('Source recipe out-of-range face operand', bytes(changed))
    changed = bytearray(data)
    changed[start+32:start+72], changed[start+72:start+112] = raw[72:112], raw[32:72]
    rejected('Source recipe ordered endpoint operands swapped', bytes(changed))
    identifiers = copy.deepcopy(stream['body_asm_identifiers'])
    identifiers['decoded'][0]['history_blob_member'] = 'UnrelatedAsset/Breps.BlobParts/BREP.fake.smbh'
    rejected('Cross-asset source blob mapping', identifiers=identifiers)
    blob = members[row['history_blob_member']]
    parsed = inspect_asm(blob)
    route = row['cached_source']['incidence_routes'][0]
    token = parsed['records'][route['coedge_index']]['tokens'][8]
    changed = bytearray(blob)
    struct.pack_into('<q', changed, token['offset']+1, -1)
    modified_members = dict(members)
    modified_members[row['history_blob_member']] = bytes(changed)
    rejected('Broken source face-loop-coedge route', changed_members=modified_members)
    report['validation'] = {'saved_files': len(cases), 'positive_source_associations': len(report['samples']),
        'edge_associations': 6, 'vertex_associations': 1, 'historical_or_incomplete_controls': len(report['controls']),
        'comparisons_passed': len(report['comparisons']), 'malformed_guards_passed': len(report['malformed_guards']),
        'geometry_only_context_failures_cleared': 0, 'historical_source_recovery_claims': 0, 'new_API_calls': 0}
    return report
