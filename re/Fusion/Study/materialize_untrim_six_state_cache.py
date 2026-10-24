"""Qualified six-state Untrim literal cache; separate from canonical geometry.

The explicit BODY pair and stored ID precede all shape checks. Derived loop
geometry does not assign chronology, current state, API identity or loop roles.
"""
import math

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags
from decode_brep import decode_topology
from materialize_asm_literal_view import materialize_asm_literal_view, SCOPE as FACTORY_SCOPE

SCOPE = ('Observed six-state slot0 side0 literal Untrim alias view with a reciprocal planar '
         'quad and optional full circular loop, and an explicit mapped BODY pair retaining '
         'its stored identifier. Nonserialized cache provenance only; semantic loop roles, '
         'chronology, pre-feature/current state and native historical/persistent/API identity unresolved.')


def materialize_untrim_six_state_cache(blob, *, initial_body_record_index,
                                      stored_body_identifier, parsed=None, history=None):
    """Return a qualified view using an independently native-mapped initial BODY."""
    if (type(initial_body_record_index) is not int or initial_body_record_index < 0
            or type(stored_body_identifier) is not int or stored_body_identifier <= 0):
        raise ValueError('Six-state Untrim view requires an explicit initial BODY index and positive stored identifier')
    literal = materialize_asm_literal_view(blob, parsed=parsed, history=history)
    history = literal['canonical_history']
    states = history['journal_states']
    if (len(states) != 6 or history['neighbor_chain'] != [0, 2, 4, 5, 3, 1]
            or states[1]['entries']):
        raise ValueError('Untrim cache view is outside the observed six-state journal family')
    canonical = inspect_asm(blob)
    table = history['geometry_entities']
    entities = [canonical['records'][r['inspection_record_index']] for r in table]
    body_ordinals = [r['geometry_entity_ordinal'] for r in table
        if r['inspection_record_index'] == initial_body_record_index
        and r['kind'] == 'body' and r['section'] == 'geometry']
    if len(body_ordinals) != 1:
        raise ValueError('Six-state Untrim initial BODY lacks one typed geometry ordinal')
    body_ordinal = body_ordinals[0]

    def body_id(record):
        tokens = record['tokens']
        if (record['name'] != 'body' or len(tokens) != 6 or tokens[1]['tag'] != 4
                or type(tokens[1]['value']) is not int):
            raise ValueError('Six-state Untrim BODY stored identifier framing differs')
        return tokens[1]['value']

    if body_id(entities[body_ordinal]) != stored_body_identifier:
        raise ValueError('Six-state Untrim supplied identifier disagrees with explicit initial BODY')
    initial_topology = decode_topology(canonical)
    if (initial_topology['unresolved'] or len(initial_topology['body_graphs']) != 3
            or sum(g['body_index'] == initial_body_record_index for g in initial_topology['body_graphs']) != 1):
        raise ValueError('Six-state Untrim initial three BODY graphs are incomplete or ambiguous')
    pairs = [e for e in states[0]['entries']
        if e['pointer_sides'][1]['stored_geometry_entity_ordinal'] == body_ordinal]
    aliases = {a['side1_entity_ordinal']: a['side0_entity_ordinal'] for a in literal['literal_pair_aliases']}
    if len(pairs) != 1 or body_ordinal not in aliases:
        raise ValueError('Six-state Untrim mapped BODY lacks one explicit nonnull pair')
    paired = aliases[body_ordinal]
    if body_id(entities[paired]) != stored_body_identifier:
        raise ValueError('Six-state Untrim paired BODY stored identifier differs from mapped initial BODY')
    dense = {ordinal: index for index, ordinal in enumerate(literal['selected_geometry_entity_ordinals'])}
    body_index = dense[paired]
    view = literal['view_parsed']
    topology = decode_topology(view)
    nodes = {n['index']: n for n in topology['nodes']}
    graphs = [g for g in topology['body_graphs'] if g['body_index'] == body_index]
    allowed_counts = [dict(lump=1, shell=1, face=1, loop=n, coedge=n+3, edge=n+3, vertex=n+3) for n in (1, 2)]
    if (topology['unresolved'] or len(topology['body_graphs']) != 3 or len(graphs) != 1
            or graphs[0]['counts'] not in allowed_counts
            or graphs[0]['surface_record_types'] != {'plane-surface': 1}
            or not graphs[0]['body_transform_is_identity']
            or nodes[body_index]['stored_entity_id'] != stored_body_identifier):
        raise ValueError('Six-state Untrim view lacks three complete graphs and a planar quad with optional circle')
    graph = graphs[0]
    face = nodes[graph['face_indices'][0]]
    plane = nodes[face['surface_index']]
    tolerance = 1e-10

    def finite(values):
        return all(math.isfinite(v) for v in values)

    if (not finite(plane['raw_origin']+plane['normal'])
            or not math.isclose(math.dist(plane['normal'], [0., 0., 0.]), 1., rel_tol=0., abs_tol=tolerance)):
        raise ValueError('Six-state Untrim plane is not finite with unit normal')

    def plane_error(point):
        return abs(sum((v-o)*n for v, o, n in zip(point, plane['raw_origin'], plane['normal'])))

    loop_checks, quad_count, circle_count = [], 0, 0
    for loop_id in graph['loop_indices']:
        loop = nodes[loop_id]
        current, coedges = loop['first_coedge_index'], []
        while current not in coedges and len(coedges) <= 4:
            coedge = nodes[current]
            edge = nodes[coedge['edge_index']]
            if (coedge['loop_index'] != loop_id or coedge['partner_index'] is not None
                    or edge['first_coedge_index'] != current or edge['is_reversed'] is not False
                    or type(coedge['is_reversed']) is not bool):
                raise ValueError('Six-state Untrim boundary edge/coedge ownership or stored reversal differs')
            coedges.append(current)
            current = coedge['next_coedge_index']
        if current != coedges[0] or len(coedges) not in (1, 4):
            raise ValueError('Six-state Untrim loop is outside singleton circle/four-line cycle framing')
        if len(coedges) == 4:
            quad_count += 1
            lines, oriented = [], []
            for coedge_id in coedges:
                coedge = nodes[coedge_id]
                edge = nodes[coedge['edge_index']]
                curve = nodes[edge['curve_index']]
                parameters = [edge['start_parameter'], edge['end_parameter']]
                vertices = [edge['start_vertex_index'], edge['end_vertex_index']]
                points = [nodes[nodes[v]['point_index']]['raw_origin'] for v in vertices]
                if (curve['kind'] != 'straight-curve'
                        or not finite(curve['raw_origin']+curve['direction']+parameters+sum(points, []))
                        or math.dist(curve['direction'], [0., 0., 0.]) <= tolerance
                        or parameters[0] >= parameters[1]):
                    raise ValueError('Six-state Untrim quad line/domain/point geometry differs')
                errors = [math.dist([o+t*d for o, d in zip(curve['raw_origin'], curve['direction'])], p)
                    for t, p in zip(parameters, points)]
                planar = [plane_error(p) for p in points]
                if max(errors+planar) > tolerance:
                    raise ValueError('Six-state Untrim line/domain endpoints disagree with typed planar points')
                oriented.append(vertices[::-1] if coedge['is_reversed'] else vertices)
                lines.append(dict(edge_view_record_index=edge['index'], curve_view_record_index=curve['index'],
                    coedge_view_record_index=coedge_id, stored_coedge_reversal=coedge['is_reversed'],
                    raw_domain=parameters, endpoint_raw_coordinate_errors=errors,
                    endpoint_plane_raw_coordinate_errors=planar))
            cycle = [v[0] for v in oriented]
            if len(set(cycle)) != 4 or not all(a[1] == b[0] for a, b in zip(oriented, oriented[1:]+oriented[:1])):
                raise ValueError('Six-state Untrim stored coedge reversal does not close the four-vertex cycle')
            loop_checks.append(dict(loop_view_record_index=loop_id, stored_curve_family='FourLines',
                oriented_vertex_cycle_view_record_indices=cycle, lines=lines,
                reversal_scope='Stored coedge Boolean selects start/end for reciprocal topological traversal only; no native UV or API traversal claim'))
        else:
            circle_count += 1
            coedge = nodes[coedges[0]]
            edge = nodes[coedge['edge_index']]
            curve = nodes[edge['curve_index']]
            point = nodes[nodes[edge['start_vertex_index']]['point_index']]['raw_origin']
            parameters = [edge['start_parameter'], edge['end_parameter']]
            if (coedge['previous_coedge_index'] != coedges[0]
                    or edge['start_vertex_index'] != edge['end_vertex_index']
                    or curve['kind'] != 'ellipse-curve' or curve['stored_axis_ratio'] != 1.
                    or not finite(curve['raw_origin']+curve['normal']+curve['stored_reference_axis']+point+parameters)
                    or not math.isfinite(curve['raw_major_radius']) or curve['raw_major_radius'] <= 0
                    or not math.isclose(math.dist(curve['normal'], [0., 0., 0.]), 1., rel_tol=0., abs_tol=tolerance)
                    or abs(sum(a*b for a, b in zip(curve['normal'], curve['stored_reference_axis']))) > tolerance
                    or not math.isclose(parameters[1]-parameters[0], 2*math.pi, rel_tol=0., abs_tol=1e-12)):
                raise ValueError('Six-state Untrim optional circle framing/domain differs')
            normal, axis = curve['normal'], curve['stored_reference_axis']
            minor = [normal[1]*axis[2]-normal[2]*axis[1], normal[2]*axis[0]-normal[0]*axis[2],
                normal[0]*axis[1]-normal[1]*axis[0]]
            errors = [math.dist([o+a*math.cos(t)+b*math.sin(t)
                for o, a, b in zip(curve['raw_origin'], axis, minor)], point) for t in parameters]
            alignment = abs(sum(a*b for a, b in zip(normal, plane['normal'])))
            if (max(errors+[plane_error(point), plane_error(curve['raw_origin'])]) > tolerance
                    or not math.isclose(alignment, 1., rel_tol=0., abs_tol=tolerance)):
                raise ValueError('Six-state Untrim optional circle/endpoints are not consistent with qualified plane')
            loop_checks.append(dict(loop_view_record_index=loop_id, stored_curve_family='FullCircle',
                edge_view_record_index=edge['index'], curve_view_record_index=curve['index'],
                coedge_view_record_index=coedge['index'], stored_coedge_reversal=coedge['is_reversed'],
                raw_domain=parameters, raw_radius=curve['raw_major_radius'],
                endpoint_raw_coordinate_errors=errors, absolute_plane_normal_dot=alignment))
    if quad_count != 1 or circle_count != len(graph['loop_indices'])-1:
        raise ValueError('Six-state Untrim view does not contain one quad and at most one circle')
    tags = decode_asm_generic_tags(blob, parsed=view, allow_fpm_tracking=True)
    if tags['unresolved']:
        raise ValueError('Six-state Untrim alias view lacks complete reciprocal naming ownership')
    wrapped_tags = dict(tags,
        scope='Naming in the nonserialized six-state Untrim literal view only; owner pointers qualified by original-record origins and explicit journal aliases',
        source_shared_reader_scope=tags['scope'], origin_map=literal['origin_map'],
        naming_namespace='Dense literal-view rows, distinct from serialized geometry entity ordinals and global inspection record indices')
    return dict(literal, initial_body_record_index=initial_body_record_index,
        initial_body_geometry_ordinal=body_ordinal, stored_body_identifier=stored_body_identifier,
        qualified_body_view_record_index=body_index, qualified_body_origin=literal['origin_map'][body_index],
        source_body_pair=dict(delta_state_slot=0, **pairs[0]), topology=topology, view_tag_summary=wrapped_tags,
        derived_stored_geometry_consistency=dict(tolerance_raw_units=tolerance, loops=loop_checks,
            finite_nondegenerate_line_domains=True, coplanar_with_qualified_plane=True,
            typed_domain_endpoints_consistent=True, oriented_four_vertex_cycle_closed=True,
            optional_circle_count=circle_count,
            scope='Derived stored-cache geometry after explicit BODY/pointer/topology qualification; no coordinate-chosen identity or semantic inside/outside loop assignment'),
        source_literal_factory_scope=FACTORY_SCOPE,
        qualification='Unique literal pairs, same mapped BODY stored identifier, complete pointer closure, three complete graphs and reciprocal planar quad with optional full circular loop',
        native_historical_BODY_identity=None, chronological_state=None, geometry_before_feature=None,
        current_state=None, semantic_loop_roles=None, scope=SCOPE)
