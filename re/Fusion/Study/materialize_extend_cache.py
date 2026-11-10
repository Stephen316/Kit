"""A bounded six-state Extend literal cache, separate from canonical ASM.

Only explicit pointer pairs qualify the mapped BODY and dense rows. The planar
quad and endpoint checks corroborate stored geometry after that qualification.
No chronological state, geometry before Extend or native historical identity is
selected; original bytes and offsets remain evidence rather than saved ASM.
"""
import math

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags
from decode_brep import decode_topology
from materialize_asm_literal_view import materialize_asm_literal_view, SCOPE as FACTORY_SCOPE

SCOPE = ('Observed six-state slot0 side0 literal alias view with a reciprocal four-line planar '
         'sheet and an explicit mapped BODY pair retaining its stored identifier. Nonserialized '
         'cache provenance only; chronology, pre-feature/current state, native historical identity '
         'and persistent/API topology remain unresolved.')
COUNTS = dict(lump=1, shell=1, face=1, loop=1, coedge=4, edge=4, vertex=4)


def materialize_extend_cache(blob, *, initial_body_record_index, stored_body_identifier,
                             parsed=None, history=None):
    """Return a qualified view using an independently native-mapped initial BODY."""
    if (type(initial_body_record_index) is not int or initial_body_record_index < 0
            or type(stored_body_identifier) is not int or stored_body_identifier <= 0):
        raise ValueError('Extend view requires an explicit initial BODY index and positive stored identifier')
    literal = materialize_asm_literal_view(blob, parsed=parsed, history=history)
    history = literal['canonical_history']
    states = history['journal_states']
    if (len(states) != 6 or history['neighbor_chain'] != [0, 2, 4, 5, 3, 1]
            or states[1]['entries']):
        raise ValueError('Extend cache view is outside the observed six-state journal family')
    canonical = inspect_asm(blob)
    table = history['geometry_entities']
    entities = [canonical['records'][row['inspection_record_index']] for row in table]
    body_ordinals = [row['geometry_entity_ordinal'] for row in table
        if row['inspection_record_index'] == initial_body_record_index
        and row['kind'] == 'body' and row['section'] == 'geometry']
    if len(body_ordinals) != 1:
        raise ValueError('Extend explicit initial BODY does not have one typed geometry ordinal')
    body_ordinal = body_ordinals[0]

    def body_id(record):
        ts = record['tokens']
        if (record['name'] != 'body' or len(ts) != 6 or ts[1]['tag'] != 4
                or type(ts[1]['value']) is not int):
            raise ValueError('Extend BODY stored identifier lacks the observed typed body framing')
        return ts[1]['value']

    if body_id(entities[body_ordinal]) != stored_body_identifier:
        raise ValueError('Extend supplied identifier disagrees with the explicit initial BODY')
    initial_topology = decode_topology(canonical)
    initial_graphs = [g for g in initial_topology['body_graphs'] if g['body_index'] == initial_body_record_index]
    if initial_topology['unresolved'] or len(initial_graphs) != 1 or len(initial_topology['body_graphs']) != 3:
        raise ValueError('Extend initial three BODY graphs are incomplete or ambiguous')
    body_pairs = [e for e in states[0]['entries']
        if e['pointer_sides'][1]['stored_geometry_entity_ordinal'] == body_ordinal]
    aliases = {a['side1_entity_ordinal']: a['side0_entity_ordinal'] for a in literal['literal_pair_aliases']}
    if len(body_pairs) != 1 or body_ordinal not in aliases:
        raise ValueError('Extend mapped initial BODY lacks one explicit nonnull literal pair')
    paired_ordinal = aliases[body_ordinal]
    if body_id(entities[paired_ordinal]) != stored_body_identifier:
        raise ValueError('Extend paired BODY stored identifier differs from the native-qualified initial identifier')
    dense = {ordinal: index for index, ordinal in enumerate(literal['selected_geometry_entity_ordinals'])}
    body_index = dense[paired_ordinal]
    view = literal['view_parsed']
    topology = decode_topology(view)
    graphs = [g for g in topology['body_graphs'] if g['body_index'] == body_index]
    nodes = {n['index']: n for n in topology['nodes']}
    if (topology['unresolved'] or len(topology['body_graphs']) != 3 or len(graphs) != 1
            or graphs[0]['counts'] != COUNTS or graphs[0]['surface_record_types'] != {'plane-surface': 1}
            or not graphs[0]['body_transform_is_identity']
            or nodes[body_index]['stored_entity_id'] != stored_body_identifier):
        raise ValueError('Extend view lacks three complete graphs and the observed reciprocal planar quad BODY')
    graph = graphs[0]
    face = nodes[graph['face_indices'][0]]
    plane = nodes[face['surface_index']]
    tolerance = 1e-10
    if (any(not math.isfinite(v) for v in plane['raw_origin']+plane['normal'])
            or not math.isclose(math.dist(plane['normal'], [0., 0., 0.]), 1., rel_tol=0., abs_tol=tolerance)):
        raise ValueError('Extend qualified plane fields are not finite with unit normal')
    loop = nodes[graph['loop_indices'][0]]
    if face['first_loop_index'] != loop['index'] or loop['next_loop_index'] is not None:
        raise ValueError('Extend qualified planar face does not own one loop')
    coedges, vertex_cycle, line_checks = [], [], []
    current = loop['first_coedge_index']
    for _ in range(4):
        coedge = nodes[current]
        edge = nodes[coedge['edge_index']]
        curve = nodes[edge['curve_index']]
        if (current in coedges or coedge['loop_index'] != loop['index']
                or coedge['partner_index'] is not None or edge['first_coedge_index'] != current
                or curve['kind'] != 'straight-curve'
                or edge['is_reversed'] is not False or coedge['is_reversed'] is not False):
            raise ValueError('Extend boundary is outside the observed four unpartnered forward line coedges')
        endpoints = [nodes[nodes[edge[key]]['point_index']]['raw_origin']
            for key in ('start_vertex_index', 'end_vertex_index')]
        values = plane['raw_origin']+curve['raw_origin']+curve['direction']+sum(endpoints, [])
        parameters = [edge['start_parameter'], edge['end_parameter']]
        if (any(not math.isfinite(v) for v in values+parameters)
                or math.dist(curve['direction'], [0., 0., 0.]) <= tolerance
                or parameters[0] >= parameters[1]):
            raise ValueError('Extend stored line/domain/endpoint fields are not finite and nondegenerate')
        endpoint_errors, plane_errors = [], []
        for parameter, point in zip(parameters, endpoints):
            expected = [o+parameter*d for o, d in zip(curve['raw_origin'], curve['direction'])]
            endpoint_errors.append(math.dist(expected, point))
            plane_errors.append(abs(sum((v-o)*n for v, o, n in zip(point, plane['raw_origin'], plane['normal']))))
        following = nodes[coedge['next_coedge_index']]
        if (max(endpoint_errors+plane_errors) > tolerance
                or edge['end_vertex_index'] != nodes[following['edge_index']]['start_vertex_index']):
            raise ValueError('Extend typed line/domain endpoints do not form the qualified coplanar vertex cycle')
        coedges.append(current)
        vertex_cycle.append(edge['start_vertex_index'])
        line_checks.append(dict(edge_view_record_index=edge['index'], curve_view_record_index=curve['index'],
            raw_domain=parameters, endpoint_raw_coordinate_errors=endpoint_errors,
            endpoint_plane_raw_coordinate_errors=plane_errors))
        current = coedge['next_coedge_index']
    if current != coedges[0] or len(set(vertex_cycle)) != 4 or set(coedges) != set(graph['coedge_indices']):
        raise ValueError('Extend quad traversal does not cover exactly four distinct reciprocal vertices/coedges')
    geometry_check = dict(tolerance_raw_units=tolerance, lines=line_checks,
        vertex_cycle_view_record_indices=vertex_cycle, finite_nondegenerate_line_domains=True,
        coplanar_with_qualified_plane=True, typed_domain_endpoints_consistent=True,
        closed_four_vertex_cycle=True,
        scope='Derived stored-cache consistency after explicit BODY/pointer/topology qualification; no geometric identity choice, API source assignment or general traversal/parameter interpretation')
    tags = decode_asm_generic_tags(blob, parsed=view, allow_fpm_tracking=True)
    if tags['unresolved']:
        raise ValueError('Extend alias view lacks complete reciprocal naming ownership')
    wrapped_tags = dict(tags,
        scope='Naming in the nonserialized literal Extend alias view only; owner pointers qualified by original-record origins and explicit journal aliases',
        source_shared_reader_scope=tags['scope'], origin_map=literal['origin_map'],
        naming_namespace='Dense literal-view rows, distinct from serialized geometry entity ordinals and global inspection record indices')
    return dict(literal, initial_body_record_index=initial_body_record_index,
        initial_body_geometry_ordinal=body_ordinal, stored_body_identifier=stored_body_identifier,
        qualified_body_view_record_index=body_index,
        qualified_body_origin=literal['origin_map'][body_index],
        source_body_pair=dict(delta_state_slot=0, **body_pairs[0]), topology=topology,
        view_tag_summary=wrapped_tags, derived_stored_geometry_consistency=geometry_check,
        source_literal_factory_scope=FACTORY_SCOPE,
        qualification='Unique kind-preserving literal pairs, same mapped BODY stored identifier, complete pointer closure, three complete graphs and reciprocal four-line planar quad topology',
        native_historical_BODY_identity=None, chronological_state=None, geometry_before_feature=None,
        current_state=None, scope=SCOPE)
