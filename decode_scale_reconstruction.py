"""Derived straight-profile Extrude prisms checked against Scale caches.

Native profile tags and typed incidence fix vertices, EDGEs and FACEs before
coordinates are read. Geometry is derived from native Sketch/Extrude controls
and the independently selected Scale point/factors, never fitted to the cache.
Literal journal views remain explicitly nonchronological corroboration.
"""
import math
import struct

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags, _terms_key, encode_generic_tag_payload, match_recipe_tag_names
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_selections import decode_body_selections
from decode_brep import decode_topology
from decode_pipe_edge_limits import decode_pipe_auxiliary_vertex_operand
from decode_placement import rigid_matrix, transform_point
from decode_recipe_components import decode_counted_recipe
from decode_scale_prism_geometry import derive_scaled_prism
from decode_scale_reconstruction_sources import qualify_scale_reconstruction_sources
from materialize_asm_literal_view import materialize_asm_literal_view

SCALE = 'D45FD6C4-161B-4240-BFAC-83A7C2C97A0C'
TOLERANCE = 1e-8
SCOPE = ('Derived native four-Line Sketch/untapered NewBody Extrude prism and selected-point '
         'Scale affine geometry, corroborated against identity-joined initial serialized '
         'BODY vertices/straight carriers/planar boundaries. Literal paired source-like '
         'cache views have no chronology; API/persistent/current/historical identity, '
         'native UV conventions and general feature regeneration remain unresolved.')


def _finite(values, label):
    if any(not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) for v in values):
        raise ValueError('Scale reconstruction nonfinite '+label)


def _residual(a,b,label):
    _finite(list(a)+list(b),label)
    difference = [x-y for x,y in zip(a,b)]
    _finite(difference,label+' residual')
    value = max(map(abs,difference),default=0.)
    if len(a) != len(b) or value > TOLERANCE:
        raise ValueError('Scale reconstruction '+label+' disagrees with native-derived geometry')
    return value


def _face_names(blob,parsed,graph):
    """Keep complete SIGNED generic terms; no suffix is a feature identity."""
    tags = decode_asm_generic_tags(blob,parsed,allow_fpm_tracking=True)
    if tags['unresolved']:
        raise ValueError('Scale reconstruction complete generic naming coverage unresolved')
    rows = []
    for identity in graph['face_indices']:
        found = [t for t in tags['tags'] if t['owner_kind']=='face' and t['owner_record_index']==identity]
        if not found or len({_terms_key(t['terms']) for t in found}) != 1:
            raise ValueError('Scale reconstruction full FACE naming group absent or ambiguous')
        for tag in found:
            if encode_generic_tag_payload(tag) != blob[tag['payload_offset']:tag['payload_end_offset']]:
                raise ValueError('Scale reconstruction full signed FACE payload replay differs')
        rows.append(dict(face_record_index=identity,complete_terms=found[0]['terms'],
            full_generic_attributes=found,
            signed_component_semantics=None,
            scope='Whole literal naming groups and validated owner chains; no numeric component is a native feature ID'))
    if len(rows)!=6 or len({_terms_key(row['complete_terms']) for row in rows})!=6:
        raise ValueError('Scale reconstruction requires six distinct complete FACE name groups')
    return rows,tags


def _whole_prism_topology(graph,nodes):
    """Require the entire bounded closed BODY, including literal heads."""
    counts = {'lump_indices':1,'shell_indices':1,'face_indices':6,
        'loop_indices':6,'coedge_indices':24,'edge_indices':12,'vertex_indices':8}
    if (any(len(graph[key])!=count or len(set(graph[key]))!=count for key,count in counts.items())
            or graph['body_transform_is_identity'] is not True):
        raise ValueError('Scale reconstruction cache is outside the bounded identity-frame prism')
    body = nodes[graph['body_index']]
    lump = nodes[graph['lump_indices'][0]]
    shell = nodes[graph['shell_indices'][0]]
    if (body['first_lump_index']!=lump['index'] or body['first_wire_index'] is not None
            or lump['body_index']!=body['index'] or lump['next_lump_index'] is not None
            or lump['first_shell_index']!=shell['index'] or shell['lump_index']!=lump['index']
            or shell['next_shell_index'] is not None or shell['subshell_index'] is not None
            or shell['first_wire_index'] is not None):
        raise ValueError('Scale reconstruction BODY requires exactly one reciprocal lump/shell and no wires')
    for edge_id in graph['edge_indices']:
        edge = nodes[edge_id]
        uses = [nodes[c] for c in graph['coedge_indices'] if nodes[c]['edge_index']==edge_id]
        if (len(uses)!=2 or edge['first_coedge_index'] not in {c['index'] for c in uses}
                or len({nodes[c['loop_index']]['face_index'] for c in uses})!=2):
            raise ValueError('Scale reconstruction closed EDGE requires two distinct FACE uses and an incident head')
        for coedge,other in ((uses[0],uses[1]),(uses[1],uses[0])):
            if (coedge['partner_index']!=other['index'] or other['partner_index']!=coedge['index']
                    or coedge['loop_index'] not in graph['loop_indices']
                    or nodes[coedge['loop_index']]['face_index'] not in graph['face_indices']):
                raise ValueError('Scale reconstruction whole-prism coedge partners are not reciprocal other uses')
    for vertex_id in graph['vertex_indices']:
        vertex = nodes[vertex_id]
        incident = {edge for edge in graph['edge_indices'] if vertex_id in (
            nodes[edge]['start_vertex_index'],nodes[edge]['end_vertex_index'])}
        if (len(incident)!=3 or vertex['first_edge_index'] not in incident
                or nodes[vertex['point_index']]['kind']!='point'):
            raise ValueError('Scale reconstruction VERTEX requires three EDGEs, incident head and typed point')


def _prism_identities(group,graph,nodes):
    """All identity choices here use IDs/incidence; never point coordinates."""
    _whole_prism_topology(graph,nodes)
    profile = group['profile_cache_correspondence']
    sketch = group['source_sketch']
    native = {}
    for entity in sketch['geometry']:
        if entity['object_id'] in native:
            raise ValueError('Scale reconstruction native Sketch entity ID is ambiguous')
        native[entity['object_id']] = entity
    curves = profile['source_curves']
    if len(curves)!=4 or any(c['native_entity_kind']!='Line' for c in curves):
        raise ValueError('Scale reconstruction needs four explicitly owned profile Lines')
    points_to_lines,profile_edges,profile_proofs = {},{},[]
    for curve in curves:
        line = native[curve['native_entity_object_id']]
        if line['kind']!='Line' or line['entity_tag']!=curve['native_entity_tag']:
            raise ValueError('Scale reconstruction native Line/tag identity differs')
        candidates = curve['cached_coedge_candidates']
        edge_ids = {c['edge_record_index'] for c in candidates}
        coedges = {c['coedge_record_index'] for c in candidates}
        if len(candidates)!=2 or len(coedges)!=2 or len(edge_ids)!=1:
            raise ValueError('Scale reconstruction profile Line must identify two uses of one EDGE')
        edge_id = next(iter(edge_ids))
        if edge_id not in graph['edge_indices']:
            raise ValueError('Scale reconstruction tagged profile EDGE leaves mapped BODY')
        for candidate in candidates:
            coedge = nodes[candidate['coedge_record_index']]
            loop = nodes[coedge['loop_index']]
            partner = nodes.get(coedge['partner_index'])
            if (coedge['index'] not in graph['coedge_indices'] or coedge['edge_index']!=edge_id
                    or loop['face_index']!=candidate['face_record_index']
                    or partner is None or partner['index'] not in coedges
                    or partner['partner_index']!=coedge['index'] or partner['edge_index']!=edge_id):
                raise ValueError('Scale reconstruction tagged profile EDGE/coedge ancestry differs')
        if edge_id in profile_edges.values():
            raise ValueError('Scale reconstruction different native Lines alias one profile EDGE')
        profile_edges[line['object_id']] = edge_id
        for identity in (line['start_point_id'],line['end_point_id']):
            if native[identity]['kind']!='Point':
                raise ValueError('Scale reconstruction Line endpoint is not a typed native SketchPoint')
            points_to_lines.setdefault(identity,[]).append(line['object_id'])
        profile_proofs.append(dict(native_line_object_id=line['object_id'],native_curve_tag=line['entity_tag'],
            native_endpoint_object_ids=[line['start_point_id'],line['end_point_id']],
            cached_profile_edge_record_index=edge_id,profile_coedge_record_indices=sorted(coedges)))
    if len(points_to_lines)!=4 or any(len(lines)!=2 or len(set(lines))!=2 for lines in points_to_lines.values()):
        raise ValueError('Scale reconstruction profile is not one closed four-point Line cycle')
    all_profile_edges = set(profile_edges.values())
    bottom,opposite,connectors = {},{},{}
    for identity,lines in sorted(points_to_lines.items()):
        edges = [nodes[profile_edges[line]] for line in lines]
        intersection = {edges[0]['start_vertex_index'],edges[0]['end_vertex_index']} & {
            edges[1]['start_vertex_index'],edges[1]['end_vertex_index']}
        if len(intersection)!=1:
            raise ValueError('Scale reconstruction two native profile Lines do not fix one cache VERTEX')
        bottom[identity] = next(iter(intersection))
    if len(set(bottom.values()))!=4:
        raise ValueError('Scale reconstruction distinct native profile points alias cache vertices')
    for identity,vertex in bottom.items():
        incident = [edge for edge in graph['edge_indices'] if vertex in (
            nodes[edge]['start_vertex_index'],nodes[edge]['end_vertex_index'])]
        extra = [edge for edge in incident if edge not in all_profile_edges]
        if len(incident)!=3 or len(extra)!=1:
            raise ValueError('Scale reconstruction profile VERTEX lacks one distinct extrusion EDGE')
        edge = nodes[extra[0]]
        other = {edge['start_vertex_index'],edge['end_vertex_index']}-{vertex}
        if len(other)!=1 or next(iter(other)) in bottom.values():
            raise ValueError('Scale reconstruction extrusion EDGE does not identify an opposite layer')
        opposite[identity] = next(iter(other))
        connectors[identity] = edge['index']
    if len(set(opposite.values()))!=4 or set(bottom.values())|set(opposite.values()) != set(graph['vertex_indices']):
        raise ValueError('Scale reconstruction native profile incidence does not exhaust eight cache vertices')
    edges = [dict(edge_index=i,vertex_indices=[nodes[i]['start_vertex_index'],nodes[i]['end_vertex_index']])
             for i in graph['edge_indices']]
    faces = []
    for face_id in graph['face_indices']:
        face = nodes[face_id]
        loops = [nodes[i] for i in graph['loop_indices'] if nodes[i]['face_index']==face_id]
        if len(loops)!=1 or face['first_loop_index']!=loops[0]['index']:
            raise ValueError('Scale reconstruction each FACE must own one quad loop')
        loop = loops[0]
        cycle,vertices = [],[]
        current = loop['first_coedge_index']
        while current not in cycle:
            if current not in graph['coedge_indices'] or len(cycle)>=4:
                raise ValueError('Scale reconstruction FACE coedge ring is not a bounded quad')
            coedge = nodes[current]
            if (coedge['loop_index']!=loop['index']
                    or nodes[coedge['next_coedge_index']]['previous_coedge_index']!=current
                    or nodes[coedge['previous_coedge_index']]['next_coedge_index']!=current):
                raise ValueError('Scale reconstruction FACE coedge ring is not reciprocal')
            edge = nodes[coedge['edge_index']]
            pair = [edge['start_vertex_index'],edge['end_vertex_index']]
            if coedge['is_reversed']: pair.reverse()
            if vertices and vertices[-1][1]!=pair[0]:
                raise ValueError('Scale reconstruction raw coedge endpoint cycle does not close')
            cycle.append(current)
            vertices.append(pair)
            current = coedge['next_coedge_index']
        if (current!=cycle[0] or len(cycle)!=4 or vertices[-1][1]!=vertices[0][0]
                or len({pair[0] for pair in vertices})!=4):
            raise ValueError('Scale reconstruction FACE endpoint ring is not one complete quad')
        faces.append(dict(face_index=face_id,vertex_cycle=[pair[0] for pair in vertices],
            raw_coedge_cycle=cycle,stored_FACE_is_reversed=face['is_reversed']))
    return dict(bottom=bottom,opposite=opposite,connectors=connectors,profile_line_edge_proofs=profile_proofs,
        edge_vertex_pairs=edges,face_vertex_cycles=faces,
        identity_scope='Native Sketch endpoint IDs and profile-tag/COEDGE/EDGE plus reciprocal prism incidence; fixed before coordinates')


def _line_geometry(segment,edge,nodes):
    curve = nodes[edge['curve_index']]
    if curve['kind']!='straight-curve':
        raise ValueError('Scale reconstruction fixed prism EDGE is not a stored straight curve')
    origin,direction = curve['raw_origin'],curve['direction']
    start,end = segment['start_position_cm'],segment['end_position_cm']
    delta = [b-a for a,b in zip(start,end)]
    _finite(origin+direction+start+end,'straight carrier')
    norm2 = sum(v*v for v in direction)
    if not math.isfinite(norm2) or norm2<=0:
        raise ValueError('Scale reconstruction stored straight carrier is degenerate')
    scale = sum(a*b for a,b in zip(delta,direction))/norm2
    offset = sum((a-b)*v for a,b,v in zip(start,origin,direction))/norm2
    _finite([scale,offset],'derived native Line parameter coefficients')
    direction_error = _residual(delta,[scale*v for v in direction],'complete straight direction coefficient')
    origin_error = _residual(start,[o+offset*v for o,v in zip(origin,direction)],'complete straight origin coefficient')
    parameters = [edge['start_parameter'],edge['end_parameter']]
    parameter_error = _residual([offset,offset+scale],parameters,'finite EDGE domain endpoints')
    evaluations = []
    for ordinal,(vertex_id,predicted,parameter) in enumerate(zip(
            (edge['start_vertex_index'],edge['end_vertex_index']),(start,end),parameters)):
        point = nodes[nodes[vertex_id]['point_index']]
        evaluated = [o+parameter*v for o,v in zip(origin,direction)]
        residual = _residual(predicted,evaluated,'native straight endpoint evaluation')
        _residual(predicted,point['raw_origin'],'derived EDGE endpoint/typed point')
        evaluations.append(dict(stored_endpoint_ordinal=ordinal,vertex_index=vertex_id,
            point_index=point['index'],native_parameter=parameter,evaluated_raw_position=evaluated,
            derived_scaled_position_cm=predicted,stored_raw_position=point['raw_origin'],residual_raw=residual))
    return dict(edge_index=edge['index'],native_EDGE=edge,native_Line=curve,
        derived_segment=segment,mathematical_segment_to_native_Line_parameter=dict(scale=scale,offset=offset,
            formula='native_t=scale*derived_segment_tau+offset; derived_tau in[0,1]',
            direction_coefficient_residual_raw=direction_error,origin_coefficient_residual_raw=origin_error,
            EDGE_parameter_endpoint_residual_raw=parameter_error),endpoint_evaluations=evaluations,
        native_traversal_semantics=None,scope='Complete straight carrier coefficients and finite stored EDGE endpoints, after incidence identity')


def _plane_geometry(boundary,face,nodes):
    plane = nodes[face['surface_index']]
    if plane['kind']!='plane-surface':
        raise ValueError('Scale reconstruction fixed prism FACE is not a stored Plane')
    normal,origin = plane['normal'],plane['raw_origin']
    mathematical_normal = boundary['outward_mathematical_unit_normal']
    constant = boundary['plane_constant_cm']
    _finite(normal+origin+mathematical_normal+[constant],'planar carrier')
    dot = sum(a*b for a,b in zip(normal,mathematical_normal))
    if not math.isfinite(dot) or not math.isclose(abs(dot),1.,rel_tol=0.,abs_tol=TOLERANCE):
        raise ValueError('Scale reconstruction mathematical/native Plane normals are not parallel')
    sign = 1. if dot>=0 else -1.
    coefficient_error = _residual(normal,[sign*v for v in mathematical_normal],'complete Plane linear coefficients up to sign')
    stored_constant = sum(n*o for n,o in zip(normal,origin))
    constant_error = _residual([stored_constant],[sign*constant],'complete Plane constant coefficient up to sign')
    corners = []
    for vertex_id,predicted in zip(boundary['vertex_cycle'],boundary['corner_positions_cm']):
        point = nodes[nodes[vertex_id]['point_index']]
        point_error = _residual(predicted,point['raw_origin'],'derived quad/typed boundary point')
        residual = sum(n*(x-o) for n,x,o in zip(normal,predicted,origin))
        if not math.isfinite(residual) or abs(residual)>TOLERANCE:
            raise ValueError('Scale reconstruction derived quad leaves native Plane')
        corners.append(dict(vertex_index=vertex_id,point_index=point['index'],derived_scaled_position_cm=predicted,
            stored_raw_position=point['raw_origin'],native_Plane_equation_residual_raw=residual,
            typed_point_residual_raw=point_error))
    return dict(face_index=face['index'],native_FACE=face,native_Plane=plane,
        derived_planar_quad=boundary,mathematical_to_stored_normal_sign=sign,
        normal_linear_coefficient_residual_raw=coefficient_error,plane_constant_residual_raw=constant_error,
        boundary_point_correspondence=corners,native_UV_convention=None,FACE_sense_interpretation=None,
        scope='Same mathematical planar carrier and four identity-fixed boundary points; chosen outward normal is not native FACE sense or UV')


def _literal_view(blob,parsed,topology,body_id,stored_id,vertex_predictions,initial_names):
    view = materialize_asm_literal_view(blob,parsed=parsed,state_slot=0,pointer_side=0)
    aliases = view['literal_pair_aliases']
    body_pairs = [r for r in aliases if r['kind']=='body' and r['side1_inspection_record_index']==body_id]
    if len(body_pairs)!=1:
        raise ValueError('Scale reconstruction literal view needs one explicit source BODY pair')
    origins = view['origin_map']
    def corresponding(identity,kind):
        paired = [r for r in aliases if r['kind']==kind and r['side1_inspection_record_index']==identity]
        if len(paired)>1:
            raise ValueError('Scale reconstruction literal cache correspondence is ambiguous')
        target = paired[0]['side0_inspection_record_index'] if paired else identity
        rows = [r for r in origins if r['inspection_record_index']==target and r['kind']==kind]
        if len(rows)!=1:
            raise ValueError('Scale reconstruction explicit literal alias/origin correspondence absent')
        return rows[0]['view_record_index'],dict(initial_record_index=identity,kind=kind,
            literal_pair=paired[0] if paired else None,view_origin=rows[0])
    vb,body_origin = corresponding(body_id,'body')
    viewed = decode_topology(view['view_parsed'])
    if viewed['unresolved']:
        raise ValueError('Scale reconstruction literal source-like view topology is incomplete')
    nodes = {n['index']:n for n in viewed['nodes']}
    initial_nodes = {n['index']:n for n in topology['nodes']}
    graphs = [g for g in viewed['body_graphs'] if g['body_index']==vb]
    if (len(graphs)!=1 or not graphs[0]['body_transform_is_identity']
            or nodes[vb]['stored_entity_id']!=stored_id or initial_nodes[body_id]['stored_entity_id']!=stored_id):
        raise ValueError('Scale reconstruction literal BODY pair changes explicit stored ID/frame')
    graph = graphs[0]
    _whole_prism_topology(graph,nodes)
    view_names,_ = _face_names(blob,view['view_parsed'],graph)
    observations = []
    view_by_face = {r['face_record_index']:r for r in view_names}
    for row in initial_names:
        vf,origin = corresponding(row['face_record_index'],'face')
        if vf not in view_by_face:
            raise ValueError('Scale reconstruction paired FACE leaves explicit literal BODY')
        observations.append(dict(initial_FACE=row,view_FACE=view_by_face[vf],literal_origin_correspondence=origin,
            numeric_component_identity=None,scope='Full signed terms retained on each independently identified cache FACE; no suffix stripped to choose identity'))
    points = []
    for row in vertex_predictions:
        vv,origin = corresponding(row['vertex_index'],'vertex')
        if vv not in graph['vertex_indices']:
            raise ValueError('Scale reconstruction paired VERTEX leaves literal BODY')
        point = nodes[nodes[vv]['point_index']]
        residual = _residual(row['source_position_cm'],point['raw_origin'],'native-derived source position/literal view point')
        points.append(dict(initial_vertex_index=row['vertex_index'],view_vertex_index=vv,
            view_point_index=point['index'],derived_source_position_cm=row['source_position_cm'],
            literal_view_raw_position=point['raw_origin'],residual_raw=residual,
            literal_origin_correspondence=origin))
    if {p['view_vertex_index'] for p in points}!=set(graph['vertex_indices']):
        raise ValueError('Scale reconstruction literal VERTEX aliases do not exhaust source-like BODY')
    provenance = {k:v for k,v in view.items() if k!='view_parsed'}
    return dict(provenance=provenance,qualified_body_view_record_index=vb,qualified_body_origin=body_origin,
        literal_source_body_pair=body_pairs[0],same_stored_BODY_identifier=stored_id,
        full_FACE_name_observations=observations,derived_source_vertex_correspondence=points,
        qualified_historical_state=None,source_before_Scale_identity=None,
        scope='Nonserialized literal slot0/side0 same-ID BODY view; source-like coordinates corroborate native-derived geometry without chronology'),view,viewed,graph


def decode_scale_reconstruction(data,records,features,member,members,body_blob_bindings,body_selections=None):
    """Recompute sources and derive affine prism geometry without mutation."""
    result = dict(decoded=[],unresolved=[],scope=SCOPE)
    candidates = [f for f in features if f.get('class_guid')==SCALE]
    if not candidates:
        return result
    grouped,metadata = {},{}
    for record in records:
        if record.is_primary: grouped.setdefault(record.object_id,[]).append(record)
    for feature in features: metadata.setdefault(feature['object_id'],[]).append(feature)
    joined = None
    cache = {}
    anchors = decode_body_selections(data,records)['body_anchors']
    for feature in candidates:
        fid = feature['object_id']
        try:
            if (len(grouped.get(fid,[]))!=1 or grouped[fid][0].class_guid!=SCALE or len(metadata[fid])!=1):
                raise ValueError('Scale reconstruction receiving metadata/native identity missing or ambiguous')
            source = qualify_scale_reconstruction_sources(data,records,features,member,members,body_blob_bindings,feature)
            if source is None:
                raise ValueError('Scale reconstruction requires observed solid BODY inputs from straight-profile Extrudes')
            if source['feature_object_id']!=fid:
                raise ValueError('Scale reconstruction source factory returned another receiver')
            scale_anchors = [a for a in anchors if a['source_owner_object_id']==fid]
            if scale_anchors:
                raise ValueError('Scale reconstruction observed same-BODY family has no Scale-owned result anchor')
            center,factors = source['settings']['reconstruction_center_cm'],source['settings']['factors_xyz']
            if len(center)!=3 or len(factors)!=3:
                raise ValueError('Scale reconstruction center/factors are not three-vectors')
            _finite(center+factors,'selected Scale center/factors')
            if any(f<=0 for f in factors):
                raise ValueError('Scale reconstruction only observed positive Scale factors supported')
            if joined is None:
                joined = decode_body_asm_identifiers(data,records,member,members,body_blob_bindings)
            groups = []
            for group in source['source_groups']:
                matches = [(m,b) for m in joined['decoded'] for b in m['bindings']
                    if b['native_body_object_id']==group['native_body_object_id']]
                if len(matches)!=1:
                    raise ValueError('Scale reconstruction BODY lacks unique fresh same-asset mapping')
                mapping,binding = matches[0]
                blob_member = mapping['history_blob_member']
                if (binding['asm_body_index']!=group['asm_body_index'] or blob_member!=group['history_blob_member']
                        or binding['stored_handle']!=group['binding']['stored_handle']):
                    raise ValueError('Scale reconstruction fresh mapping disagrees with native source proof')
                if blob_member not in cache:
                    blob = members[blob_member]
                    parsed = inspect_asm(blob)
                    topology = decode_topology(parsed)
                    if topology['unresolved']:
                        raise ValueError('Scale reconstruction initial typed topology/geometry unresolved')
                    cache[blob_member] = blob,parsed,topology
                blob,parsed,topology = cache[blob_member]
                nodes = {n['index']:n for n in topology['nodes']}
                graphs = [g for g in topology['body_graphs'] if g['body_index']==binding['asm_body_index']]
                if len(graphs)!=1:
                    raise ValueError('Scale reconstruction mapped initial BODY graph is missing or ambiguous')
                graph = graphs[0]
                identities = _prism_identities(group,graph,nodes)
                names,_ = _face_names(blob,parsed,graph)
                sketch = group['source_sketch']
                native = {n['object_id']:n for n in sketch['geometry']}
                matrix = rigid_matrix(sketch['placement']['sketch_to_component_matrix'])
                distance = group['extrude_controls']['extent']['side_one']['distance_cm']
                direction = group['extrude_direction_component']
                _finite(direction+[distance],'native Extrude direction/distance')
                translation = [distance*d for d in direction]
                vertices = []
                for native_id,bottom in identities['bottom'].items():
                    base = transform_point(matrix,native[native_id]['position_cm'])
                    for layer,cache_vertex in ((0,bottom),(1,identities['opposite'][native_id])):
                        position = [v+layer*t for v,t in zip(base,translation)]
                        _finite(position,'derived native Sketch/Extrude position')
                        vertices.append(dict(vertex_index=cache_vertex,native_sketch_point_object_id=native_id,
                            layer=layer,derived_position_cm=position))
                derived = derive_scaled_prism(vertices,identities['edge_vertex_pairs'],
                    identities['face_vertex_cycles'],center,factors)
                vertex_rows = []
                for vertex in derived['vertices']:
                    point = nodes[nodes[vertex['vertex_index']]['point_index']]
                    residual = _residual(vertex['scaled_position_cm'],point['raw_origin'],'control-derived affine vertex prediction')
                    vertex_rows.append(dict(vertex,point_index=point['index'],stored_raw_position=point['raw_origin'],
                        residual_raw=residual))
                lines = [_line_geometry(segment,nodes[segment['edge_index']],nodes)
                    for segment in derived['scaled_prism']['segments']]
                planes = [_plane_geometry(boundary,nodes[boundary['face_index']],nodes)
                    for boundary in derived['scaled_prism']['planar_quadrilateral_boundaries']]
                literal,view,view_topology,view_graph = _literal_view(blob,parsed,topology,
                    graph['body_index'],binding['stored_handle'],derived['vertices'],names)
                center_correspondence = None
                point = source['settings'].get('point')
                if point and point['entity']['kind']=='BRepVertexRecipe' and point['entity']['native_body_object_id']==group['native_body_object_id']:
                    recipe_id = point['entity']['recipe']['object_id']
                    recipe_records = grouped.get(recipe_id,[])
                    if len(recipe_records)!=1 or recipe_records[0].class_guid!='7ACC2A03-0261-4879-A14A-A93D661A5BDC':
                        raise ValueError('Scale vertex center counted recipe native record is ambiguous')
                    recipe = decode_counted_recipe(data,recipe_records[0])
                    operand = decode_pipe_auxiliary_vertex_operand(recipe)
                    view_tags = decode_asm_generic_tags(blob,view['view_parsed'],allow_fpm_tracking=True)
                    matches = match_recipe_tag_names(recipe,view_tags,parsed=view['view_parsed'])
                    face_ids = []
                    for ref in operand['face_name_references']:
                        entries = [r for r in matches['name_entries'] if r['name_table_index']==ref['name_table_index']]
                        if len(entries)!=1 or entries[0]['candidate_count']!=1:
                            raise ValueError('Scale vertex center complete FACE name absent/ambiguous in literal view')
                        candidate = entries[0]['candidates'][0]
                        if candidate['owner_kind']!='face' or candidate['body_graph_membership']!=[view_graph['body_index']]:
                            raise ValueError('Scale vertex center complete FACE name leaves paired literal BODY')
                        face_ids.append(candidate['owner_record_index'])
                    view_nodes = {n['index']:n for n in view_topology['nodes']}
                    candidates = []
                    for vertex_id in view_graph['vertex_indices']:
                        incident = {view_nodes[view_nodes[c]['loop_index']]['face_index'] for c in view_graph['coedge_indices']
                            if vertex_id in (view_nodes[view_nodes[c]['edge_index']]['start_vertex_index'],
                                             view_nodes[view_nodes[c]['edge_index']]['end_vertex_index'])}
                        if incident==set(face_ids): candidates.append(vertex_id)
                    if len(set(face_ids))!=3 or len(candidates)!=1:
                        raise ValueError('Scale vertex center three complete FACEs do not fix one literal-view VERTEX')
                    selected = candidates[0]
                    coordinate = view_nodes[view_nodes[selected]['point_index']]['raw_origin']
                    residual = _residual(center,coordinate,'selected vertex backend center/literal named-view point')
                    origins = [v for v in literal['derived_source_vertex_correspondence'] if v['view_vertex_index']==selected]
                    if len(origins)!=1:
                        raise ValueError('Scale vertex center lacks one literal alias to a native-derived source point')
                    derived_centers = [v for v in derived['vertices'] if v['vertex_index']==origins[0]['initial_vertex_index']]
                    if len(derived_centers)!=1:
                        raise ValueError('Scale vertex center native-derived source position is ambiguous')
                    derived_center = derived_centers[0]
                    native_center_residual = _residual(center,derived_center['source_position_cm'],
                        'selected vertex backend center/native Sketch-Extrude derived source point')
                    _residual(coordinate,derived_center['source_position_cm'],
                        'named literal-view vertex/native-derived source center')
                    center_correspondence = dict(complete_recipe=recipe,operation_operand=operand,
                        naming_correspondence=matches,view_FACE_indices=face_ids,view_vertex_index=selected,
                        view_point_index=view_nodes[selected]['point_index'],literal_view_raw_position=coordinate,
                        independently_selected_backend_center_cm=center,residual_raw=residual,
                        independently_derived_source_center_cm=derived_center['source_position_cm'],
                        source_native_sketch_point_object_id=derived_center['native_sketch_point_object_id'],
                        source_extrude_layer=derived_center['layer'],
                        initial_cache_vertex_literal_correspondence=origins[0],
                        native_source_center_residual_raw=native_center_residual,
                        affine_center_input_scope='Selected native backend coordinate independently corroborated by native Sketch/Extrude source geometry after whole-name and literal-alias identity; no ASM coordinate constructs the prism',
                        view_vertex_origin=next(o for o in view['origin_map'] if o['view_record_index']==selected),
                        API_handle_identity=None,initial_selected_vertex_identity=None,
                        qualified_historical_state=None,scope='Three exact full FACE names in the explicit literal BODY view select a cache vertex before center coordinates are compared')
                groups.append(dict(source_native_body_object_id=group['native_body_object_id'],
                    source_feature_object_id=group['source_feature_object_id'],body_binding=binding,
                    history_blob_member=blob_member,asm_body_index=graph['body_index'],
                    identity_provenance=identities,complete_signed_FACE_naming=names,
                    derived_prism=derived,vertex_correspondence=vertex_rows,
                    native_straight_carrier_correspondence=lines,native_planar_boundary_correspondence=planes,
                    literal_source_like_cache_corroboration=literal,
                    vertex_center_literal_view_correspondence=center_correspondence,
                    maximum_vertex_residual_raw=max(r['residual_raw'] for r in vertex_rows),
                    current_or_historical_or_API_BODY_identity=None,
                    scope='Native-derived source/affine prism versus fixed initial cache, supplemented by separately scoped literal-view corroboration'))
            if not groups:
                raise ValueError('Scale reconstruction source group list is empty')
            result['decoded'].append(dict(feature_object_id=fid,native_source_provenance=source,
                computed_affine_matrix_4x4=groups[0]['derived_prism']['affine_matrix_4x4'],
                derived_prism_groups=groups,scale_owned_result_anchor_object_ids=[],
                same_native_BODY_source_and_cache_route=True,
                source_prism_geometry_status='Derived from native Sketch and untapered Extrude controls, not labeled a historical serialization',
                exact_current_or_historical_state=None,persistent_topology_identity=None,API_handle_identity=None,
                counts=dict(BODY_groups=len(groups),vertices=sum(len(g['vertex_correspondence']) for g in groups),
                    straight_segments=sum(len(g['native_straight_carrier_correspondence']) for g in groups),
                    planar_quadrilateral_boundaries=sum(len(g['native_planar_boundary_correspondence']) for g in groups)),scope=SCOPE))
        except (ValueError,KeyError,IndexError,TypeError,OverflowError,struct.error) as error:
            result['unresolved'].append(dict(feature_object_id=fid,reason=str(error)))
    return result
