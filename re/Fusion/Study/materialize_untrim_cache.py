"""A bounded literal slot0/side0 Untrim cache view, separate from canonical ASM.

No chronological state, geometry before the feature or native historical identity
is selected. Original bytes/offsets remain evidence; dense pointers are a view.
"""
import copy
import math

from asm_records import inspect_asm
from decode_asm_history import decode_asm_history
from decode_asm_recipe_tags import decode_asm_generic_tags
from decode_brep import decode_topology

SCOPE = ('Observed five-state slot0 side0 literal alias view with reciprocal two-circular-loop '
         'sheet topology and an explicit BODY pair retaining its stored identifier. Nonserialized '
         'cache provenance only; chronology, pre-feature/current state, native historical identity '
         'and persistent/API topology remain unresolved.')
COUNTS = dict(lump=1, shell=1, face=1, loop=2, coedge=2, edge=2, vertex=2)


def materialize_untrim_cache(blob, *, initial_body_record_index, stored_body_identifier,
                            parsed=None, history=None):
    """Return topology/view_parsed and exact original-record origins/pair evidence.

    The caller supplies an independently native-qualified initial BODY index and
    stored identifier. Neither an ordinal nor a geometric match supplies them.
    """
    if (type(initial_body_record_index) is not int or initial_body_record_index < 0
            or type(stored_body_identifier) is not int or stored_body_identifier <= 0):
        raise ValueError('Untrim view requires an explicit initial BODY index and positive stored identifier')
    canonical = inspect_asm(blob)
    if parsed is not None and parsed != canonical:
        raise ValueError('Untrim view supplied parsed records differ from original bytes')
    parsed = canonical
    canonical_history = decode_asm_history(blob, parsed=parsed)
    if history is not None and history != canonical_history:
        raise ValueError('Untrim view supplied history differs from the canonical pointer namespace')
    history = canonical_history
    states = history['journal_states']
    if (len(states) != 5 or history['neighbor_chain'] != [0, 2, 4, 3, 1]
            or states[1]['entries']):
        raise ValueError('Untrim cache view is outside the observed five-state journal family')
    table = history['geometry_entities']
    originals = parsed['records']
    entities = [originals[row['inspection_record_index']] for row in table]
    body_ordinals = [row['geometry_entity_ordinal'] for row in table
        if row['inspection_record_index'] == initial_body_record_index
        and row['kind'] == 'body' and row['section'] == 'geometry']
    if len(body_ordinals) != 1:
        raise ValueError('Untrim explicit initial BODY does not have one typed geometry ordinal')
    body_ordinal = body_ordinals[0]
    body_record = entities[body_ordinal]

    def body_id(record):
        ts = record['tokens']
        if (record['name'] != 'body' or len(ts) != 6 or ts[1]['tag'] != 4
                or type(ts[1]['value']) is not int):
            raise ValueError('Untrim BODY stored identifier lacks the observed typed body framing')
        return ts[1]['value']

    if body_id(body_record) != stored_body_identifier:
        raise ValueError('Untrim supplied identifier disagrees with the explicit initial BODY')
    initial_topology = decode_topology(parsed)
    initial_graphs = [g for g in initial_topology['body_graphs'] if g['body_index'] == initial_body_record_index]
    if initial_topology['unresolved'] or len(initial_graphs) != 1:
        raise ValueError('Untrim source initial BODY topology is incomplete or ambiguous')
    aliases, alias_evidence = {}, []
    selected = [[], []]
    for entry in states[0]['entries']:
        left, right = entry['pointer_sides']
        x, y = left['stored_geometry_entity_ordinal'], right['stored_geometry_entity_ordinal']
        if x == y == -1:
            raise ValueError('Untrim alias view cannot qualify an empty pointer pair')
        for side, pointer in enumerate((left, right)):
            ordinal = pointer['stored_geometry_entity_ordinal']
            if ordinal == -1:
                continue
            if pointer['target_section'] != ('trailing_states' if side == 0 else 'geometry'):
                raise ValueError('Untrim alias pair leaves the explicit initial/trailing sections')
            selected[side].append(ordinal)
        if x != -1 and y != -1:
            if left['target_kind'] != right['target_kind']:
                raise ValueError('Untrim literal journal alias changes the typed entity kind')
            if y in aliases or x in aliases.values():
                raise ValueError('Untrim literal journal aliases are not unique and bijective')
            aliases[y] = x
            alias_evidence.append(dict(entry_ordinal=entry['entry_ordinal'],
                side1_entity_ordinal=y, side0_entity_ordinal=x,
                side1_inspection_record_index=right['inspection_record_index'],
                side0_inspection_record_index=left['inspection_record_index'],
                kind=left['target_kind'], pointer_sides=entry['pointer_sides'],
                scope='Literal pair-local pointer alias for this view only; not persistent or historical native identity'))
    if any(len(ids) != len(set(ids)) for ids in selected):
        raise ValueError('Untrim alias view repeats a nonnull journal side ordinal')
    left, right = map(set, selected)
    initial = {e['geometry_entity_ordinal'] for e in table if e['section'] == 'geometry'}
    if not left or not right or left & right or not right <= initial:
        raise ValueError('Untrim alias view does not separate bounded initial and trailing tables')
    body_pairs = [e for e in states[0]['entries']
        if e['pointer_sides'][1]['stored_geometry_entity_ordinal'] == body_ordinal]
    if len(body_pairs) != 1 or body_ordinal not in aliases:
        raise ValueError('Untrim mapped initial BODY lacks one explicit nonnull literal pair')
    paired_ordinal = aliases[body_ordinal]
    paired_body = entities[paired_ordinal]
    if body_id(paired_body) != stored_body_identifier:
        raise ValueError('Untrim paired BODY stored identifier differs from the native-qualified initial identifier')
    chosen = sorted((initial-right) | left)
    dense = {ordinal:index for index,ordinal in enumerate(chosen)}
    origins, viewed_records, rewrites = [], [], []
    naive_dangling = 0
    for ordinal in chosen:
        original = entities[ordinal]
        viewed = copy.deepcopy(original)
        viewed['index'] = dense[ordinal]
        viewed['section'] = 'geometry'
        origins.append(dict(view_record_index=dense[ordinal], geometry_entity_ordinal=ordinal,
            inspection_record_index=original['index'], section=original['section'], kind=original['name'],
            original_record_offset=original['offset'], original_record_end_offset=original['end_offset']))
        for field, token in enumerate(viewed['tokens']):
            if token['tag'] != 12 or token['value'] == -1:
                continue
            raw = token['value']
            if raw not in dense:
                naive_dangling += 1
            target = aliases.get(raw, raw)
            if target not in dense:
                raise ValueError('Untrim literal aliases leave a dangling geometry pointer')
            token['value'] = dense[target]
            rewrites.append(dict(view_record_index=dense[ordinal], source_geometry_entity_ordinal=ordinal,
                source_inspection_record_index=original['index'], token_field=field,
                token_offset=token['offset'], stored_target_geometry_entity_ordinal=raw,
                aliased_target_geometry_entity_ordinal=target,
                target_source_inspection_record_index=entities[target]['index'],
                target_view_record_index=dense[target], used_literal_pair_alias=raw in aliases))
        viewed_records.append(viewed)
    view = dict(records=viewed_records, complete_token_stream=True, is_materialized_view=True,
        scope='Nonserialized Untrim literal alias view; original byte offsets retained but pointer values and row indices are dense view identifiers')
    topology = decode_topology(view)
    body_index = dense[paired_ordinal]
    graphs = [g for g in topology['body_graphs'] if g['body_index'] == body_index]
    nodes = {n['index']:n for n in topology['nodes']}
    if (topology['unresolved'] or len(graphs) != 1 or graphs[0]['counts'] != COUNTS
            or graphs[0]['surface_record_types'] != {'plane-surface':1}
            or not graphs[0]['body_transform_is_identity'] or nodes[body_index]['stored_entity_id'] != stored_body_identifier):
        raise ValueError('Untrim view lacks the observed reciprocal two-loop planar BODY topology')
    graph = graphs[0]
    plane = nodes[nodes[graph['face_indices'][0]]['surface_index']]
    tolerance = 1e-10
    if any(not math.isfinite(v) for v in plane['raw_origin']+plane['normal']):
        raise ValueError('Untrim view plane fields are not finite')
    circle_checks = []
    for loop_id in graph['loop_indices']:
        loop = nodes[loop_id]
        coedge = nodes[loop['first_coedge_index']]
        edge = nodes[coedge['edge_index']]
        curve = nodes[edge['curve_index']]
        if (coedge['loop_index'] != loop_id or coedge['next_coedge_index'] != coedge['index']
                or coedge['previous_coedge_index'] != coedge['index'] or coedge['partner_index'] is not None
                or edge['first_coedge_index'] != coedge['index'] or edge['start_vertex_index'] != edge['end_vertex_index']
                or edge['is_reversed'] is not False or coedge['is_reversed'] is not False
                or curve['kind'] != 'ellipse-curve' or curve['stored_axis_ratio'] != 1.
                or not math.isclose(edge['end_parameter']-edge['start_parameter'],2*math.pi,rel_tol=0.,abs_tol=1e-12)):
            raise ValueError('Untrim view loop is outside the observed closed circular singleton-coedge framing')
        radius = curve['raw_major_radius']
        point = nodes[nodes[edge['start_vertex_index']]['point_index']]['raw_origin']
        values = curve['raw_origin']+curve['normal']+curve['stored_reference_axis']+point+[radius]
        if any(not math.isfinite(v) for v in values) or radius <= 0:
            raise ValueError('Untrim view circle fields or vertex points are not finite/positive')
        offset = [a-b for a,b in zip(curve['raw_origin'],plane['raw_origin'])]
        alignment = sum(a*b for a,b in zip(curve['normal'],plane['normal']))
        if (abs(sum(a*b for a,b in zip(offset,plane['normal']))) > tolerance
                or not math.isclose(abs(alignment),1.,rel_tol=0.,abs_tol=tolerance)):
            raise ValueError('Untrim view circles are not coplanar/normal-aligned with the qualified plane')
        normal, axis = curve['normal'], curve['stored_reference_axis']
        minor_axis = [normal[1]*axis[2]-normal[2]*axis[1],
                      normal[2]*axis[0]-normal[0]*axis[2],
                      normal[0]*axis[1]-normal[1]*axis[0]]
        errors = []
        for parameter in (edge['start_parameter'],edge['end_parameter']):
            expected = [o+a*math.cos(parameter)+b*math.sin(parameter)
                for o,a,b in zip(curve['raw_origin'],axis,minor_axis)]
            error = math.dist(expected,point)
            if error > tolerance:
                raise ValueError('Untrim typed vertex point disagrees with its stored circle/domain endpoints')
            errors.append(error)
        circle_checks.append(dict(loop_view_record_index=loop_id,edge_view_record_index=edge['index'],
            curve_view_record_index=curve['index'],raw_center=curve['raw_origin'],raw_radius=radius,
            absolute_plane_normal_dot=abs(alignment),endpoint_raw_coordinate_errors=errors))
    if (math.dist(circle_checks[0]['raw_center'],circle_checks[1]['raw_center']) > tolerance
            or abs(circle_checks[0]['raw_radius']-circle_checks[1]['raw_radius']) <= tolerance):
        raise ValueError('Untrim view circular boundaries are not concentric with distinct positive radii')
    geometry_check = dict(tolerance_raw_units=tolerance,circles=circle_checks,
        same_center=True,positive_distinct_radii=True,coplanar_with_qualified_plane=True,
        typed_domain_endpoints_consistent=True,
        scope='Derived stored-cache consistency after explicit BODY/pointer/topology qualification; no geometric identity choice, general parameter/traversal map or native inner/outer flag')
    tag_summary = decode_asm_generic_tags(blob, parsed=view, allow_fpm_tracking=True)
    if tag_summary['unresolved']:
        raise ValueError('Untrim alias view lacks complete reciprocal naming ownership')
    wrapped_tags = dict(tag_summary,
        scope='Naming in the nonserialized literal Untrim alias view only; owner pointers are qualified by original-record origins and explicit journal aliases',
        source_shared_reader_scope=tag_summary['scope'], origin_map=origins,
        naming_namespace='Dense literal-view rows, distinct from serialized geometry entity ordinals and global inspection record indices')
    return dict(state_slot=0, pointer_side=0, baseline='Explicit initial geometry section',
        initial_body_record_index=initial_body_record_index, initial_body_geometry_ordinal=body_ordinal,
        stored_body_identifier=stored_body_identifier, qualified_body_view_record_index=body_index,
        qualified_body_origin=origins[body_index],
        source_body_pair=dict(delta_state_slot=0, **body_pairs[0]),
        canonical_history=history, selected_geometry_entity_ordinals=chosen,
        origin_map=origins, literal_pair_aliases=alias_evidence, rewritten_pointer_evidence=rewrites,
        naive_membership_dangling_pointer_count=naive_dangling, qualified_dangling_pointer_count=0,
        topology=topology, view_parsed=view, view_tag_summary=wrapped_tags,
        derived_stored_geometry_consistency=geometry_check,
        qualification='Unique kind-preserving literal pairs, same BODY stored identifier, complete pointer closure and reciprocal two-circular-loop planar topology',
        native_historical_BODY_identity=None, chronological_state=None, geometry_before_feature=None,
        current_state=None, inner_outer_loop_classification=None, scope=SCOPE)
