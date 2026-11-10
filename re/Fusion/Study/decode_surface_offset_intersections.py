"""Bounded Offset face-intersection operands and initial-cache incidence.

Seventeen trailing integers in each endpoint are deliberately opaque. This
qualifies the explicit naming/incidence constraints, not the full proprietary
selection procedure, an API handle, or a procedural surface's interior.
"""
import struct

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags, match_recipe_tag_names, _terms_key
from decode_asm_subtypes import decode_asm_subtypes
from decode_brep import decode_topology
from decode_one_face_edge_sources import _replay_recipe
from decode_untrim_sources import _face_cache

SCOPE = ('Observed 1476-byte singleton Offset FACE plus six two-FACE EDGE and twelve '
         'three-FACE endpoint constraints in an explicitly mapped initial BODY cache; '
         'complete names and reciprocal incidence qualify cache correspondence only. '
         'Endpoint 17-int procedure tails, API identity, traversal, current/persistent '
         'or historical state and VBL XYZ interiors remain unresolved.')


def decode_surface_offset_intersection_operands(recipe):
    """Replay all369 int32 words, retaining literal table and operand order."""
    raw = bytes.fromhex(recipe['payload_hex'])
    table = recipe['name_table']
    if (recipe['payload_kind'] != 'bounded_face_recipe_data' or len(raw) != 1476
            or recipe['payload_length'] != len(raw)
            or len(table) != 7 or [e['table_index'] for e in table] != list(range(7))):
        raise ValueError('Offset intersection recipe extent/complete table differs')
    keys = [_terms_key(entry['terms']) for entry in table]
    if any(not entry['terms'] or len(entry['terms']) > 16 for entry in table) or len(set(keys)) != 7:
        raise ValueError('Offset intersection complete name groups are empty or repeated')
    words = struct.unpack('<369i', raw)
    cursor = 0
    replay = []
    def read():
        nonlocal cursor
        if cursor >= len(words):
            raise ValueError('Offset intersection operand leaves bounded payload')
        value = words[cursor]
        cursor += 1
        replay.append(value)
        return value
    def expect(expected):
        if read() != expected:
            raise ValueError('Offset intersection observed header/count/sentinel differs')
    def name():
        value = read()
        if not 0 <= value < len(table):
            raise ValueError('Offset intersection name index leaves complete table')
        return value
    face = name()
    expect(-1)
    expect(6)
    children = []
    adjacent_names = []
    for ordinal in range(6):
        start = cursor
        expect(-1)
        expect(-1)
        expect(2)
        pair = [name()]
        expect(-1)
        pair.append(name())
        expect(-1)
        expect(2)
        if len(set(pair)) != 2 or pair.count(face) != 1:
            raise ValueError('Offset intersection EDGE must name outer FACE and a distinct neighbor')
        adjacent_names.append(next(i for i in pair if i != face))
        endpoints = []
        for endpoint in range(2):
            vstart = cursor
            expect(-1)
            expect(3)
            triple = []
            for _ in range(3):
                triple.append(name())
                expect(-1)
            expect(0)
            if len(set(triple)) != 3 or not set(pair) < set(triple):
                raise ValueError('Offset intersection endpoint FACE triple disagrees with EDGE pair')
            tail = [read() for _ in range(17)]
            if cursor - vstart != 26:
                raise ValueError('Offset intersection endpoint frame extent differs')
            endpoints.append(dict(endpoint_operand_ordinal=endpoint,
                stored_direct_vertex_name_index=-1, stored_face_count=3,
                face_name_indices=triple, stored_face_secondary_indices=[-1]*3,
                stored_edge_count=0, opaque_tail_int32=tail, opaque_tail_semantics=None,
                relative_offset=vstart*4, payload_hex=raw[vstart*4:cursor*4].hex(),
                scope='Three complete FACE operands plus bounded literal17-int tail; full procedure evaluation unknown'))
        expect(-1)
        if cursor - start != 61 or set(endpoints[0]['face_name_indices']) == set(endpoints[1]['face_name_indices']):
            raise ValueError('Offset intersection EDGE extent or distinct endpoint triples differ')
        children.append(dict(boundary_operand_ordinal=ordinal,
            stored_direct_edge_name_index=-1, stored_secondary_index=-1,
            stored_face_count=2, face_name_indices=pair,
            stored_face_secondary_indices=[-1]*2, stored_endpoint_count=2,
            endpoint_operands=endpoints, stored_final_qualifier_int32=-1,
            qualifier_semantics=None, relative_offset=start*4,
            payload_hex=raw[start*4:cursor*4].hex()))
    if len(set(adjacent_names)) != 6 or set(adjacent_names) | {face} != set(range(7)):
        raise ValueError('Offset intersection neighboring FACE operands do not exhaust complete table')
    if cursor != len(words) or struct.pack('<369i', *replay) != raw:
        raise ValueError('Offset intersection whole operation replay differs')
    # The shared native caller compares this complete reconstructed recipe to
    # its original record bytes. Here it also verifies all table encodings are
    # supported; this is not a claim that opaque operation tails are evaluated.
    _replay_recipe(recipe)
    return dict(stored_direct_face_name_index=face, stored_secondary_index=-1,
        stored_boundary_edge_count=6, boundary_edges=children,
        stored_neighbor_face_name_order=adjacent_names, payload_hex=raw.hex(),
        exact_full_operation_payload_replay=True, stored_int32_word_count=369,
        opaque_endpoint_tail_int32_count=17, full_selection_procedure_evaluated=False,
        scope=SCOPE)


def resolve_surface_offset_intersections(blob, parsed, tags, topology, body_id,
                                         recipe, operands=None, naming=None):
    """Resolve names and topological intersections before copying geometry.

    All supplied helper structures are revalidated against the unchanged blob.
    The native caller independently proves descriptor/anchor/mapping ownership;
    this function requires its explicitly supplied BODY graph, never a nearest
    or enumeration-selected graph.
    """
    fresh_parsed = inspect_asm(blob)
    if parsed != fresh_parsed:
        raise ValueError('Offset intersection parsed records differ from original blob')
    fresh_tags = decode_asm_generic_tags(blob, parsed=fresh_parsed, allow_fpm_tracking=True)
    if tags != fresh_tags or tags['unresolved']:
        raise ValueError('Offset intersection complete naming summary differs or is unresolved')
    fresh_topology = decode_topology(fresh_parsed,
        subtype_catalog=decode_asm_subtypes(blob, parsed=fresh_parsed))
    if topology != fresh_topology:
        raise ValueError('Offset intersection topology differs from original blob')
    fresh_operands = decode_surface_offset_intersection_operands(recipe)
    if operands is not None and operands != fresh_operands:
        raise ValueError('Offset intersection supplied operation differs from complete recipe')
    operands = fresh_operands
    fresh_naming = match_recipe_tag_names(recipe, tags, parsed=parsed)
    if naming is not None and naming != fresh_naming:
        raise ValueError('Offset intersection supplied naming differs from complete terms')
    naming = fresh_naming
    entries = {entry['name_table_index']:entry for entry in naming['name_entries']}
    if set(entries) != set(range(7)) or any(entry['candidate_count'] != 1 for entry in entries.values()):
        raise ValueError('Offset intersection FACE names absent or globally ambiguous')
    graphs = [g for g in topology['body_graphs'] if g['body_index'] == body_id]
    if len(graphs) != 1 or graphs[0]['body_transform_is_identity'] is not True:
        raise ValueError('Offset intersection requires one explicit identity-transform BODY graph')
    graph = graphs[0]
    nodes = {node['index']:node for node in topology['nodes']}
    face_ids = {}
    matched = []
    for index in range(7):
        candidate = entries[index]['candidates'][0]
        identity = candidate['owner_record_index']
        if (candidate['owner_kind'] != 'face' or candidate['body_graph_membership'] != [body_id]
                or identity not in graph['face_indices'] or nodes[identity]['kind'] != 'face'):
            raise ValueError('Offset intersection name is not one FACE in the explicitly mapped BODY')
        face_ids[index] = identity
        values = [tag for tag in tags['tags']
                  if tag['attribute_record_index'] == candidate['attribute_record_index']]
        if len(values) != 1:
            raise ValueError('Offset intersection matched full attribute provenance is ambiguous')
        matched.append(dict(name_table_index=index, tag=values[0]))
    if len(set(face_ids.values())) != 7:
        raise ValueError('Offset intersection distinct full names alias one FACE')
    face_id = face_ids[operands['stored_direct_face_name_index']]
    # Build complete incidence in this one typed BODY; no surface evaluator or
    # point value participates in selecting any edge or endpoint.
    edge_routes = {identity:[] for identity in graph['edge_indices']}
    vertex_faces = {identity:set() for identity in graph['vertex_indices']}
    for identity in graph['coedge_indices']:
        coedge = nodes[identity]
        loop = nodes.get(coedge['loop_index'])
        edge = nodes.get(coedge['edge_index'])
        if (loop is None or loop['kind'] != 'loop' or loop['index'] not in graph['loop_indices']
                or loop['face_index'] not in graph['face_indices'] or edge is None
                or edge['index'] not in edge_routes
                or nodes[coedge['next_coedge_index']]['previous_coedge_index'] != identity
                or nodes[coedge['previous_coedge_index']]['next_coedge_index'] != identity
                or nodes[coedge['next_coedge_index']]['loop_index'] != loop['index']
                or nodes[coedge['previous_coedge_index']]['loop_index'] != loop['index']):
            raise ValueError('Offset intersection BODY coedge/loop/edge incidence is not reciprocal')
        partner = nodes.get(coedge['partner_index'])
        if (partner is None or partner['index'] not in graph['coedge_indices']
                or partner['edge_index'] != edge['index'] or partner['partner_index'] != identity):
            raise ValueError('Offset intersection closed BODY partner incidence differs')
        edge_routes[edge['index']].append(dict(face_record_index=loop['face_index'],
            loop_record_index=loop['index'], coedge_record_index=identity,
            partner_coedge_record_index=partner['index'], edge_record_index=edge['index']))
        for vertex in (edge['start_vertex_index'], edge['end_vertex_index']):
            if vertex not in vertex_faces:
                raise ValueError('Offset intersection EDGE endpoint leaves explicit BODY')
            vertex_faces[vertex].add(loop['face_index'])
    edge_faces = {identity:{route['face_record_index'] for route in routes}
                  for identity, routes in edge_routes.items()}
    for identity, routes in edge_routes.items():
        if len(routes) != 2 or nodes[identity]['first_coedge_index'] not in {r['coedge_record_index'] for r in routes}:
            raise ValueError('Offset intersection closed BODY EDGE has inconsistent coedge membership')
    face_loops = [nodes[identity] for identity in graph['loop_indices'] if nodes[identity]['face_index'] == face_id]
    if len(face_loops) != 1 or nodes[face_id]['first_loop_index'] != face_loops[0]['index']:
        raise ValueError('Offset intersection selected FACE must own one complete loop')
    loop = face_loops[0]
    face_coedges = {identity for identity in graph['coedge_indices'] if nodes[identity]['loop_index'] == loop['index']}
    if len(face_coedges) != 6 or loop['first_coedge_index'] not in face_coedges:
        raise ValueError('Offset intersection selected FACE loop does not have six coedges')
    cycle = []
    cursor = loop['first_coedge_index']
    while cursor not in cycle:
        if cursor not in face_coedges:
            raise ValueError('Offset intersection selected FACE cycle leaves owned coedges')
        cycle.append(cursor)
        cursor = nodes[cursor]['next_coedge_index']
    if cursor != cycle[0] or set(cycle) != face_coedges:
        raise ValueError('Offset intersection selected FACE loop cycle is incomplete')
    boundary = []
    for child in operands['boundary_edges']:
        pair = [face_ids[index] for index in child['face_name_indices']]
        edges = [identity for identity, faces in edge_faces.items() if faces == set(pair)]
        if len(edges) != 1:
            raise ValueError('Offset intersection two complete FACE names do not fix one EDGE')
        edge_id = edges[0]
        edge = nodes[edge_id]
        selected_routes = [route for route in edge_routes[edge_id] if route['face_record_index'] == face_id]
        if len(selected_routes) != 1 or selected_routes[0]['coedge_record_index'] not in face_coedges:
            raise ValueError('Offset intersection named EDGE is outside selected FACE loop')
        route = selected_routes[0]
        endpoint_rows = []
        for endpoint in child['endpoint_operands']:
            triple = [face_ids[index] for index in endpoint['face_name_indices']]
            vertices = [identity for identity, faces in vertex_faces.items() if faces == set(triple)]
            if len(vertices) != 1:
                raise ValueError('Offset intersection three complete FACE names do not fix one endpoint')
            vertex_id = vertices[0]
            vertex = nodes[vertex_id]
            point = nodes[vertex['point_index']]
            if (vertex['kind'] != 'vertex' or point['kind'] != 'point'
                    or vertex_id not in (edge['start_vertex_index'], edge['end_vertex_index'])):
                raise ValueError('Offset intersection endpoint is not a typed point on the named EDGE')
            incident_edges = {identity for identity in graph['edge_indices']
                if vertex_id in (nodes[identity]['start_vertex_index'], nodes[identity]['end_vertex_index'])}
            if vertex['first_edge_index'] not in incident_edges:
                raise ValueError('Offset intersection endpoint first EDGE is not incident')
            endpoint_rows.append(dict(endpoint_operand_ordinal=endpoint['endpoint_operand_ordinal'],
                face_name_indices=endpoint['face_name_indices'], face_operand_record_indices=triple,
                vertex_record_index=vertex_id, point_record_index=point['index'], raw_point=point['raw_origin'],
                incident_edge_record_indices=sorted(incident_edges),
                stored_edge_endpoint_role='Start' if vertex_id == edge['start_vertex_index'] else 'End',
                opaque_tail_int32=endpoint['opaque_tail_int32'], opaque_tail_semantics=None))
        ordered_vertices = [endpoint['vertex_record_index'] for endpoint in endpoint_rows]
        if (len(set(ordered_vertices)) != 2
                or set(ordered_vertices) != {edge['start_vertex_index'], edge['end_vertex_index']}):
            raise ValueError('Offset intersection endpoint operands do not exhaust distinct EDGE endpoints')
        coedge = nodes[route['coedge_record_index']]
        boundary.append(dict(boundary_operand_ordinal=child['boundary_operand_ordinal'],
            edge_record_index=edge_id, coedge_record_index=coedge['index'], loop_record_index=loop['index'],
            face_name_indices=child['face_name_indices'], face_operand_record_indices=pair,
            complete_edge_face_incidence=edge_routes[edge_id],
            stored_edge_reversal=edge['is_reversed'], stored_coedge_reversal=coedge['is_reversed'],
            stored_edge_endpoint_vertex_indices=[edge['start_vertex_index'], edge['end_vertex_index']],
            operand_endpoint_vertex_indices=ordered_vertices,
            stored_endpoint_order_relation='PreservedStoredEndpointOrder' if ordered_vertices ==
                [edge['start_vertex_index'], edge['end_vertex_index']] else 'ReversedStoredEndpointOrder',
            endpoint_incidence=endpoint_rows))
    coedge_order = [row['coedge_record_index'] for row in boundary]
    if len(set(coedge_order)) != 6 or set(coedge_order) != face_coedges:
        raise ValueError('Offset intersection EDGE operands do not exhaust selected FACE boundary')
    next_order = all(nodes[a]['next_coedge_index'] == b for a, b in zip(coedge_order, coedge_order[1:] + coedge_order[:1]))
    previous_order = all(nodes[a]['previous_coedge_index'] == b for a, b in zip(coedge_order, coedge_order[1:] + coedge_order[:1]))
    relation = 'NextCoedge' if next_order else 'PreviousCoedge' if previous_order else 'StoredBoundaryMembershipOrderOnly'
    face_cache = _face_cache(topology, body_id, face_id)
    face_cache['scope'] = 'Mapped initial Offset intersection FACE/cache with explicit partial surface definition; no XYZ interior, API or historical-state assignment'
    proof_ids = {body_id, face_id, nodes[face_id]['surface_index']}
    proof_ids.update(graph['lump_indices'])
    proof_ids.update(graph['shell_indices'])
    for row in boundary:
        for endpoint in row['endpoint_incidence']:
            proof_ids.update((endpoint['vertex_record_index'], endpoint['point_record_index']))
            for edge_id in endpoint['incident_edge_record_indices']:
                edge = nodes[edge_id]
                proof_ids.update((edge_id, edge['curve_index']))
                for route in edge_routes[edge_id]:
                    proof_ids.update(route.values())
    proof_ids.update(face_ids.values())
    proof_ids = sorted(proof_ids)
    if any(parsed['records'][identity]['section'] != 'geometry' for identity in proof_ids):
        raise ValueError('Offset intersection provenance leaves initial geometry section')
    return dict(face_record_index=face_id, cached_face=face_cache, boundary_incidence=boundary,
        stored_boundary_order_relation=relation, stored_order_follows_next_coedge=next_order,
        stored_order_follows_previous_coedge=previous_order, selected_face_topological_coedge_cycle=cycle,
        source_record_indices=proof_ids,
        matched_name_attributes=matched, source_geometry_diagnostics=topology['unresolved'],
        full_selection_procedure_evaluated=False, API_handle_identity=None,
        persistent_topology_identity=None, qualified_historical_state=None, scope=SCOPE)
