"""Supplemental named Extend operands in a qualified literal alternate cache."""
import math
import struct

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags, match_recipe_tag_names
from decode_extend_edge_sources import EXTEND, decode_extend_edge_sources, decode_extend_edge_operands
from decode_one_face_edge_sources import _replay_recipe
from decode_untrim_sources import _face_cache

SCOPE = ('Observed complete Extend named operands in a closed literal slot0/side0 alternate cache '
         'qualified by an explicit native source BODY pair. Separate from initial-cache provenance; '
         'selected source, chronology, before-feature/current/persistent/API identity and traversal unresolved.')


def decode_extend_cache_sources(data, records, features, member, members,
                                body_identifier_summary, body_selections=None):
    result = dict(associations=[],unresolved=[],scope=SCOPE)
    if not any(r.is_primary and r.class_guid == EXTEND for r in records):
        return result
    from materialize_extend_cache import materialize_extend_cache
    native = decode_extend_edge_sources(data,records,features,member,members,body_identifier_summary,body_selections)
    for error in native['unresolved']:
        result['unresolved'].append(dict(owner_object_id=error['owner_object_id'],
            reason='Fresh native Extend source route unresolved: '+error['reason']))
    caches = {}
    for source in native['associations']:
        owner = source['owner_object_id']
        try:
            native_operands = source['descriptor_operands']
            if len(native_operands) not in (1,2):
                raise ValueError('Extend cache requires captured one/two native descriptor operands')
            route = native_operands[0]
            if any(any(o[k] != route[k] for k in ('native_body_object_id','mapping_record_object_id',
                    'history_blob_member','explicit_asm_body_index','body_anchor_object_id',
                    'historical_source_owner_object_id')) for o in native_operands):
                raise ValueError('Extend cache native operands disagree on explicitly mapped source')
            blob_member,initial_body = route['history_blob_member'],route['explicit_asm_body_index']
            bindings = [b for m in body_identifier_summary['decoded']
                if m['mapping_record_object_id'] == route['mapping_record_object_id'] and m['history_blob_member'] == blob_member
                for b in m['bindings'] if b['native_body_object_id'] == route['native_body_object_id']]
            if len(bindings) != 1 or bindings[0]['asm_body_index'] != initial_body:
                raise ValueError('Extend cache explicit native mapped BODY no longer unique')
            stored_identifier = bindings[0]['stored_handle']
            key = blob_member,initial_body,stored_identifier
            if key not in caches:
                blob = members[blob_member];parsed = inspect_asm(blob)
                view = materialize_extend_cache(blob,initial_body_record_index=initial_body,
                    stored_body_identifier=stored_identifier,parsed=parsed)
                vp,topology = view['view_parsed'],view['topology']
                tags = decode_asm_generic_tags(blob,parsed=vp,allow_fpm_tracking=True)
                if topology['unresolved'] or tags['unresolved']:
                    raise ValueError('Extend alternate cache naming/topology incomplete')
                caches[key] = view,tags
            view,tags = caches[key];vp,topology = view['view_parsed'],view['topology']
            body_id = view['qualified_body_view_record_index']
            nodes = {n['index']:n for n in topology['nodes']}
            graphs = [g for g in topology['body_graphs'] if g['body_index'] == body_id]
            if len(graphs) != 1 or not graphs[0]['body_transform_is_identity']:
                raise ValueError('Extend alternate cache lacks one identity-transform qualified BODY')
            graph = graphs[0];operands = []
            for native_operand in native_operands:
                recipe = native_operand['recipe']
                if _replay_recipe(recipe).hex() != native_operand['full_counted_recipe_payload_hex']:
                    raise ValueError('Extend alternate cache complete native recipe replay differs')
                operation = decode_extend_edge_operands(recipe)
                naming = match_recipe_tag_names(recipe,tags,parsed=vp)
                entries = {e['name_table_index']:e for e in naming['name_entries']}
                if set(entries) != set(range(4)) or any(e['candidate_count'] != 1 for e in entries.values()):
                    raise ValueError('Extend alternate cache requires four globally unique complete names')
                matched = [entries[i]['candidates'][0] for i in range(4)]
                if ([n['owner_kind'] for n in matched] != ['edge','face','edge','edge']
                        or any(n['body_graph_membership'] != [body_id] for n in matched)):
                    raise ValueError('Extend alternate named operands leave explicitly qualified BODY')
                face_id = matched[1]['owner_record_index']
                edge_ids = [matched[i]['owner_record_index'] for i in (0,2,3)]
                if len(set(edge_ids)) != 3:
                    raise ValueError('Extend alternate direct and adjacent named edges are not distinct')
                face = _face_cache(topology,body_id,face_id)
                face['scope'] = 'Qualified literal nonserialized alternate cache; no before-feature or historical state label'
                routes = [];paired_loops = []
                for eid in edge_ids:
                    edge = nodes[eid]
                    incident = [nodes[c] for g in topology['body_graphs'] for c in g['coedge_indices'] if nodes[c]['edge_index'] == eid]
                    if len(incident) != 1:
                        raise ValueError('Extend alternate named edge lacks one reciprocal boundary coedge')
                    coedge = incident[0];loop = nodes[coedge['loop_index']]
                    if (edge['first_coedge_index'] != coedge['index'] or coedge['partner_index'] is not None
                            or loop['face_index'] != face_id or loop['index'] not in graph['loop_indices']
                            or nodes[coedge['next_coedge_index']]['previous_coedge_index'] != coedge['index']
                            or nodes[coedge['previous_coedge_index']]['next_coedge_index'] != coedge['index']):
                        raise ValueError('Extend alternate edge/coedge/loop/face incidence is not reciprocal')
                    paired_loops.append(loop['index'])
                    routes.append(dict(edge_view_record_index=eid,coedge_view_record_index=coedge['index'],
                        loop_view_record_index=loop['index'],face_view_record_index=face_id,
                        stored_coedge_reversal=coedge['is_reversed']))
                if len(set(paired_loops)) != 1:
                    raise ValueError('Extend alternate named endpoint edges do not share the named face loop')
                edge = nodes[edge_ids[0]];endpoints = []
                for operand,adjacent in zip(operation['endpoint_operands'],edge_ids[1:]):
                    other = nodes[adjacent]
                    common = {edge['start_vertex_index'],edge['end_vertex_index']} & {other['start_vertex_index'],other['end_vertex_index']}
                    if len(common) != 1:
                        raise ValueError('Extend alternate endpoint intersection is not unique')
                    vertex_id = next(iter(common));vertex = nodes[vertex_id];point = nodes[vertex['point_index']]
                    if vertex_id not in graph['vertex_indices'] or point['kind'] != 'point':
                        raise ValueError('Extend alternate endpoint vertex/point outside qualified BODY')
                    role = 'Start' if vertex_id == edge['start_vertex_index'] else 'End'
                    endpoints.append(dict(operand_ordinal=operand['operand_ordinal'],
                        stored_inline_edge_name_order=operand['stored_inline_edge_name_order'],
                        adjacent_edge_name_index=operand['adjacent_edge_name_index'],adjacent_edge_view_record_index=adjacent,
                        vertex_view_record_index=vertex_id,point_view_record_index=point['index'],
                        stored_edge_endpoint_role=role,vertex=vertex,point=point))
                if len({e['vertex_view_record_index'] for e in endpoints}) != 2 or {e['stored_edge_endpoint_role'] for e in endpoints} != {'Start','End'}:
                    raise ValueError('Extend alternate operand intersections do not exhaust distinct stored endpoints')
                curve = nodes[edge['curve_index']]
                if curve['kind'] != 'straight-curve' or type(edge['is_reversed']) is not bool:
                    raise ValueError('Extend alternate selected geometry outside captured straight-edge cache')
                values = curve['raw_origin']+curve['direction']+[edge['start_parameter'],edge['end_parameter']]
                values += [x for e in endpoints for x in e['point']['raw_origin']]
                if any(not math.isfinite(x) for x in values) or not edge['end_parameter'] > edge['start_parameter']:
                    raise ValueError('Extend alternate cache coordinates/domain not finite/positive')
                selected = {body_id,face_id,face['surface']['index']}
                selected.update(n['attribute_record_index'] for n in matched)
                for boundary in face['boundary_edges']:
                    selected.update([boundary['edge']['index'],boundary['curve']['index']])
                    selected.update(n['index'] for n in boundary['vertices']+boundary['points'])
                for r in face['incidence_routes']: selected.update(r.values())
                origins = [o for o in view['origin_map'] if o['view_record_index'] in selected]
                if len(origins) != len(selected):
                    raise ValueError('Extend alternate published geometry/name origins missing or ambiguous')
                operands.append(dict(operand_ordinal=native_operand['operand_ordinal'],
                    selection_record_object_id=native_operand['selection_record_object_id'],
                    descriptor_object_id=native_operand['descriptor_object_id'],recipe_object_id=recipe['object_id'],
                    recipe=recipe,operation_operands=operation,full_counted_recipe_payload_hex=native_operand['full_counted_recipe_payload_hex'],
                    exact_full_counted_recipe_replay=True,alternate_naming_correspondence=naming,
                    ordered_endpoint_intersections=endpoints,
                    operand_vertex_order=[e['vertex_view_record_index'] for e in endpoints],
                    stored_edge_vertex_order=[edge['start_vertex_index'],edge['end_vertex_index']],
                    operand_to_stored_endpoint_order=[e['stored_edge_endpoint_role'] for e in endpoints],
                    cached_operand=dict(edge=edge,curve=curve,face=face,incidence_routes=routes,
                        parameter_domain=[edge['start_parameter'],edge['end_parameter']],stored_edge_reversal=edge['is_reversed']),
                    selected_cache_origins=origins,exact_selected_source_identity=None,current_source_identity=None,
                    persistent_source_identity=None,API_handle_identity=None,qualified_historical_state=None,traversal=None))
            result['associations'].append(dict(owner_object_id=owner,descriptor_operands=operands,
                native_body_object_id=route['native_body_object_id'],body_anchor_object_id=route['body_anchor_object_id'],
                historical_source_owner_object_id=route['historical_source_owner_object_id'],mapping_record_object_id=route['mapping_record_object_id'],
                history_blob_member=blob_member,explicit_initial_asm_body_index=initial_body,native_stored_body_identifier=stored_identifier,
                qualified_body_view_record_index=body_id,
                alternate_cache_provenance={k:v for k,v in view.items() if k not in ('view_parsed','topology')},
                exact_selected_source_identity=None,current_source_identity=None,persistent_source_identity=None,
                API_handle_identity=None,qualified_historical_state=None,traversal=None,scope=SCOPE))
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error) as error:
            result['unresolved'].append(dict(owner_object_id=owner,reason=str(error)))
    return result
