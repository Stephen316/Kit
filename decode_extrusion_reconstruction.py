"""Native-profile/control-derived ordinary solid Extrude geometry.

Creator/selection/component/BODY identity is established before geometry. The
bounded cache is corroborated as a complete geometric bundle, without choosing
native entities by coordinate proximity or labeling it final/current/history.
"""
import math
import struct

from asm_records import inspect_asm
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_brep import decode_topology
from decode_circular_extrusion_geometry import derive_circular_extrusion, extrusion_stations
from decode_extrusion_source_operands import EXTRUDE, qualify_extrusion_source_operands
from decode_scale_prism_geometry import derive_scaled_prism
from decode_shell_reconstruction import _geometry_sort_key, _canonical_corner_cycle

TOLERANCE=1e-8
SCOPE=('Derived native complete Circle cylinder/frustum or four-Line rectangular '
       'prism from owned Sketch/frame and ordinary NewBody Distance/start controls. '
       'Complete identity-qualified stored BODY analytic carriers and bounded '
       'topology corroborate the model collectively; no coordinate ENTITY mapping, '
       'fit, native UV, API/current/final/persistent identity or chronological '
       'regeneration is established. Unsupported controls and frames stay explicit.')


def _finite(values,label):
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in values):
        raise ValueError('Extrusion reconstruction nonfinite '+label)


def _near(a,b,label):
    _finite(list(a)+list(b),label)
    if len(a)!=len(b):raise ValueError('Extrusion reconstruction '+label+' extent differs')
    residual=max((abs(x-y) for x,y in zip(a,b)),default=0.)
    if not math.isfinite(residual) or residual>TOLERANCE:
        raise ValueError('Extrusion reconstruction '+label+' corroboration differs')
    return residual


def _dot(a,b):
    value=sum(x*y for x,y in zip(a,b));_finite([value],'dot product');return value


def _cross(a,b):
    result=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
    _finite(result,'cross product');return result


def _point(matrix,point):
    result=[sum(matrix[4*i+j]*point[j] for j in range(3))+matrix[4*i+3] for i in range(3)]
    _finite(result,'native frame point');return result


def _vector(matrix,vector):
    result=[sum(matrix[4*i+j]*vector[j] for j in range(3)) for i in range(3)]
    _finite(result,'native frame vector');return result


def _compare_bundle(left,right,label):
    def recurse(a,b):
        if isinstance(a,(int,float)) and isinstance(b,(int,float)):return _near([a],[b],label)
        if not isinstance(a,(list,tuple)) or not isinstance(b,(list,tuple)) or len(a)!=len(b):
            raise ValueError('Extrusion reconstruction '+label+' nested framing differs')
        return max((recurse(x,y) for x,y in zip(a,b)),default=0.)
    return recurse(sorted(left,key=_geometry_sort_key),sorted(right,key=_geometry_sort_key))


def _closed_body(graph,nodes,kind):
    expected=dict(lump=1,shell=1,face=3,loop=4,coedge=4,edge=2,vertex=2) if kind=='Circle' else dict(lump=1,shell=1,face=6,loop=6,coedge=24,edge=12,vertex=8)
    if graph['body_transform_is_identity'] is not True:
        raise ValueError('Extrusion reconstruction requires the observed identity BODY cache frame')
    for name,count in expected.items():
        identities=graph[name+'_indices']
        if len(identities)!=count or len(set(identities))!=count or any(nodes[i]['kind']!=name for i in identities):
            raise ValueError('Extrusion reconstruction complete '+kind+' BODY topology counts/types differ')
    body=nodes[graph['body_index']];lump=nodes[graph['lump_indices'][0]];shell=nodes[graph['shell_indices'][0]]
    if (body['first_lump_index']!=lump['index'] or body['first_wire_index'] is not None
            or lump['body_index']!=body['index'] or lump['next_lump_index'] is not None
            or lump['first_shell_index']!=shell['index'] or shell['lump_index']!=lump['index']
            or shell['next_shell_index'] is not None or shell['subshell_index'] is not None or shell['first_wire_index'] is not None):
        raise ValueError('Extrusion reconstruction reciprocal single lump/shell/no-wire framing differs')
    seen=set();current=shell['first_face_index']
    while current is not None:
        if current not in graph['face_indices'] or current in seen or nodes[current]['shell_index']!=shell['index']:
            raise ValueError('Extrusion reconstruction complete FACE chain differs')
        seen.add(current);current=nodes[current]['next_face_index']
    if seen!=set(graph['face_indices']):raise ValueError('Extrusion reconstruction FACE chain incomplete')
    loops=[]
    for face_id in graph['face_indices']:
        face=nodes[face_id];owned={i for i in graph['loop_indices'] if nodes[i]['face_index']==face_id}
        visited=set();current=face['first_loop_index']
        while current is not None:
            if current not in owned or current in visited:raise ValueError('Extrusion reconstruction FACE loop chain differs')
            visited.add(current);current=nodes[current]['next_loop_index']
        if not owned or visited!=owned:raise ValueError('Extrusion reconstruction FACE loop ownership incomplete')
        for loop_id in owned:
            loop=nodes[loop_id];cycle=[];pairs=[];current=loop['first_coedge_index']
            limit=1 if kind=='Circle' else 4
            while current not in cycle:
                if current not in graph['coedge_indices'] or len(cycle)>=limit:
                    raise ValueError('Extrusion reconstruction bounded loop cycle differs')
                coedge=nodes[current]
                if (coedge['loop_index']!=loop_id or coedge['edge_index'] not in graph['edge_indices']
                        or coedge['next_coedge_index'] not in graph['coedge_indices']
                        or coedge['previous_coedge_index'] not in graph['coedge_indices']
                        or nodes[coedge['next_coedge_index']]['previous_coedge_index']!=current
                        or nodes[coedge['previous_coedge_index']]['next_coedge_index']!=current):
                    raise ValueError('Extrusion reconstruction coedge cycle reciprocity differs')
                edge=nodes[coedge['edge_index']];pair=[edge['start_vertex_index'],edge['end_vertex_index']]
                if coedge['is_reversed']:pair.reverse()
                if pairs and pairs[-1][1]!=pair[0]:raise ValueError('Extrusion reconstruction loop endpoint continuity differs')
                cycle.append(current);pairs.append(pair);current=coedge['next_coedge_index']
            if current!=cycle[0] or len(cycle)!=limit or pairs[-1][1]!=pairs[0][0]:
                raise ValueError('Extrusion reconstruction complete loop endpoint closure differs')
            loops.append(dict(loop_index=loop_id,face_index=face_id,coedge_cycle=cycle,
                edge_indices=[nodes[i]['edge_index'] for i in cycle],vertex_cycle=[p[0] for p in pairs],
                native_LOOP=loop))
    if sum(len(l['coedge_cycle']) for l in loops)!=len(graph['coedge_indices']):
        raise ValueError('Extrusion reconstruction loop cycles do not exhaust BODY coedges')
    for edge_id in graph['edge_indices']:
        edge=nodes[edge_id];uses=[nodes[c] for c in graph['coedge_indices'] if nodes[c]['edge_index']==edge_id]
        if (len(uses)!=2 or edge['first_coedge_index'] not in {c['index'] for c in uses}
                or len({nodes[c['loop_index']]['face_index'] for c in uses})!=2
                or any(c['partner_index']!=other['index'] for c,other in ((uses[0],uses[1]),(uses[1],uses[0])))):
            raise ValueError('Extrusion reconstruction EDGE head/two-FACE/other-use partner reciprocity differs')
        if (edge['start_vertex_index'] not in graph['vertex_indices'] or edge['end_vertex_index'] not in graph['vertex_indices']
                or (edge['start_vertex_index']==edge['end_vertex_index']) != (kind=='Circle')):
            raise ValueError('Extrusion reconstruction bounded EDGE endpoint topology differs')
    for vertex_id in graph['vertex_indices']:
        vertex=nodes[vertex_id];incident={e for e in graph['edge_indices'] if vertex_id in (nodes[e]['start_vertex_index'],nodes[e]['end_vertex_index'])}
        if len(incident)!=(1 if kind=='Circle' else 3) or vertex['first_edge_index'] not in incident or nodes[vertex['point_index']]['kind']!='point':
            raise ValueError('Extrusion reconstruction VERTEX degree/head/typed POINT differs')
        _finite(nodes[vertex['point_index']]['raw_origin'],'cache POINT')
    return loops


def _circle_cache(graph,nodes,model):
    loops=_closed_body(graph,nodes,'Circle');source=model['source_circle'];axis=source['unit_axis'];center=source['center_cm']
    cap_faces=[nodes[i] for i in graph['face_indices'] if nodes[nodes[i]['surface_index']]['kind']=='plane-surface']
    side_faces=[nodes[i] for i in graph['face_indices'] if nodes[nodes[i]['surface_index']]['kind']=='cone-surface']
    if len(cap_faces)!=2 or len(side_faces)!=1:raise ValueError('Extrusion reconstruction circular BODY requires two Plane caps and one circular analytic carrier')
    edge_rows=[];circle_bundles=[]
    for edge_id in graph['edge_indices']:
        edge=nodes[edge_id];curve=nodes[edge['curve_index']]
        if curve['kind']!='ellipse-curve':raise ValueError('Extrusion reconstruction circular boundary is not a typed ellipse')
        origin,normal,reference=curve['raw_origin'],curve['normal'],curve['stored_reference_axis']
        radius=curve['raw_major_radius'];minor=curve['raw_minor_radius']
        _finite(origin+normal+reference+[radius,minor,edge['start_parameter'],edge['end_parameter']],'circle carrier/domain')
        if radius<=0:raise ValueError('Extrusion reconstruction cache circle radius is not positive')
        # ASM ellipse reference vectors encode the major-radius magnitude.
        u=[v/radius for v in reference]
        _near([radius],[minor],'circular major/minor radii')
        _near([_dot(normal,normal),_dot(u,u),_dot(normal,u)],[1.,1.,0.],'circle orthonormal frame')
        _near([abs(_dot(normal,axis))],[1.],'complete circular normal coefficients up to sign')
        normal_sign=1 if _dot(normal,axis)>=0 else -1
        _near(normal,[normal_sign*n for n in axis],'complete circular normal vector coefficients up to sign')
        _near([abs(edge['end_parameter']-edge['start_parameter'])],[2*math.pi],'complete closed-circle finite EDGE domain')
        uses=[nodes[c] for c in graph['coedge_indices'] if nodes[c]['edge_index']==edge_id]
        incident={nodes[c['loop_index']]['face_index'] for c in uses}
        caps=[f for f in cap_faces if f['index'] in incident]
        if len(caps)!=1 or side_faces[0]['index'] not in incident:
            raise ValueError('Extrusion reconstruction circle boundary lacks exactly one cap and lateral FACE')
        cap=caps[0];plane=nodes[cap['surface_index']]
        _finite(plane['raw_origin']+plane['normal']+plane['stored_reference_axis'],'cap Plane')
        _near([_dot(plane['normal'],plane['normal']),abs(_dot(plane['normal'],normal))],[1.,1.],'complete cap Plane normal coefficients')
        plane_sign=1 if _dot(plane['normal'],normal)>=0 else -1
        _near(plane['normal'],[plane_sign*n for n in normal],'complete cap Plane normal vector coefficients up to sign')
        cap_residual=_near([_dot(plane['normal'],[x-o for x,o in zip(origin,plane['raw_origin'])])],[0.],'cap Plane contains whole circular boundary')
        cap_loops=[l for l in loops if l['face_index']==cap['index']]
        if len(cap_loops)!=1 or cap_loops[0]['edge_indices']!=[edge_id]:
            raise ValueError('Extrusion reconstruction cap does not own exactly its singleton circular loop')
        vertex=nodes[edge['start_vertex_index']];point=nodes[vertex['point_index']];v=_cross(normal,u)
        evaluations=[]
        for parameter in (edge['start_parameter'],edge['end_parameter']):
            evaluated=[o+radius*(math.cos(parameter)*a+math.sin(parameter)*b) for o,a,b in zip(origin,u,v)]
            residual=_near(evaluated,point['raw_origin'],'closed-circle native endpoint evaluation')
            evaluations.append(dict(parameter=parameter,evaluated_position_cm=evaluated,
                native_POINT=point,residual_raw=residual))
        circle_bundles.append(origin+[radius])
        edge_rows.append(dict(native_EDGE=edge,native_Circle=curve,native_cap_FACE=cap,native_cap_Plane=plane,
            endpoint_evaluations=evaluations,cap_plane_constant_residual_raw=cap_residual,
            native_COEDGEs=uses,cap_loop=cap_loops[0],native_traversal_semantics=None))
    circle_error=_compare_bundle(circle_bundles,[s['center_cm']+[s['radius_cm']] for s in model['axial_stations']],
        'complete unordered cap-circle bundle')
    side=side_faces[0];carrier=nodes[side['surface_index']];analytic=carrier.get('analytic_surface',{})
    if analytic.get('kind') not in ('Cylinder','Cone'):raise ValueError('Extrusion reconstruction lateral carrier is not canonical circular Cylinder/Cone')
    origin,a=analytic['raw_origin'],analytic['axis'];radius=analytic['raw_radius']
    _finite(origin+a+[radius],'lateral analytic coefficients')
    _near([_dot(a,a)],[1.],'lateral unit axis')
    orientation=_dot(a,axis);_near([abs(orientation)],[1.],'complete lateral axis linear coefficients up to sign')
    axis_sign=1 if orientation>=0 else -1
    _near(a,[axis_sign*n for n in axis],'complete lateral axis vector coefficients up to sign')
    delta=[x-y for x,y in zip(origin,center)];height=_dot(delta,axis)
    radial=[x-height*n for x,n in zip(delta,axis)];axis_error=_near(radial,[0.,0.,0.],'complete lateral axis line')
    native_slope=math.tan(analytic.get('stored_signed_half_angle_radians',0.))
    slope=native_slope*orientation
    model_carrier=model['lateral_carrier']
    slope_error=_near([slope],[model_carrier['radial_slope']],'complete lateral radial-slope coefficient')
    intercept=radius-slope*height
    radius_error=_near([intercept],[model_carrier['radial_intercept_cm']],'complete lateral radial-intercept coefficient')
    side_loops=[l for l in loops if l['face_index']==side['index']]
    if len(side_loops)!=2 or {e for l in side_loops for e in l['edge_indices']}!=set(graph['edge_indices']):
        raise ValueError('Extrusion reconstruction complete lateral boundary loops differ')
    return dict(kind='CompleteCappedCircularCache',counts=graph['counts'],native_boundary_circles=edge_rows,
        native_lateral_FACE=side,native_lateral_carrier=carrier,lateral_boundary_loops=side_loops,
        complete_coefficient_residuals_raw=dict(cap_circle_bundle=circle_error,lateral_axis_line=axis_error,
            lateral_radial_slope=slope_error,lateral_radial_intercept=radius_error),
        bounded_axial_domain_from_derived_caps_cm=model_carrier['axial_domain_cm'],
        semantic_cap_to_native_ENTITY_mapping=None,API_handle_identity=None,qualified_historical_state=None,
        scope='Complete analytic carrier equations and full two-circle/Plane cap boundary after native BODY identity; unordered model corroboration, no coordinate-selected cap identity or native UV')


def _rectangular_stations(controls):
    stations=extrusion_stations(controls)
    if any(s['taper_angle_radians'] for s in stations):
        raise ValueError('Extrusion reconstruction rectangular taper has no saved complete-profile proof')
    return [s['axial_distance_cm'] for s in stations]


def _rectangle_model(group,matrix,axis):
    points={p['point_object_id']:p['position_cm'] for p in group['native_profile_points']}
    lines=group['native_profile_lines'];adjacency={i:[] for i in points}
    for line in lines:
        adjacency[line['start_point_id']].append(line['end_point_id']);adjacency[line['end_point_id']].append(line['start_point_id'])
    start=min(points);cycle=[start];previous=None
    while len(cycle)<4:
        choices=[i for i in adjacency[cycle[-1]] if i!=previous and i not in cycle]
        if not choices:raise ValueError('Extrusion reconstruction native rectangle endpoint cycle incomplete')
        previous,current=cycle[-1],min(choices);cycle.append(current)
    if start not in adjacency[cycle[-1]]:raise ValueError('Extrusion reconstruction native rectangle cycle does not close')
    corners=[points[i] for i in cycle]
    vectors=[[b-a for a,b in zip(corners[i],corners[(i+1)%4])] for i in range(4)]
    lengths=[_dot(v,v) for v in vectors]
    if min(lengths)<=TOLERANCE:raise ValueError('Extrusion reconstruction native rectangular side degenerates')
    for i in range(4):_near([_dot(vectors[i],vectors[(i+1)%4])],[0.],'native rectangular perpendicular adjacent sides')
    _near(vectors[0],[-v for v in vectors[2]],'native rectangular opposite side coefficients')
    _near(vectors[1],[-v for v in vectors[3]],'native rectangular opposite side coefficients')
    stations=_rectangular_stations(group['extrude_controls']);vertices=[]
    for layer,height in enumerate(stations):
        for ordinal,identity in enumerate(cycle):
            base=_point(matrix,points[identity]);position=[x+height*v for x,v in zip(base,axis)]
            vertices.append(dict(vertex_index=4*layer+ordinal,native_sketch_point_object_id=identity,
                layer=layer,derived_position_cm=position))
    edges=[]
    for layer in range(2):
        for i in range(4):edges.append(dict(edge_index=4*layer+i,vertex_indices=[4*layer+i,4*layer+(i+1)%4]))
    for i in range(4):edges.append(dict(edge_index=8+i,vertex_indices=[i,4+i]))
    faces=[dict(face_index=0,vertex_cycle=list(range(4))),dict(face_index=1,vertex_cycle=list(range(4,8)))]
    faces.extend(dict(face_index=2+i,vertex_cycle=[i,(i+1)%4,4+(i+1)%4,4+i]) for i in range(4))
    prism=derive_scaled_prism(vertices,edges,faces,[0.,0.,0.],[1.,1.,1.])['source_prism']
    return dict(kind='RectangularPrism',native_profile_point_cycle=cycle,axial_stations_cm=stations,
        constructed_vertices=vertices,prism=prism,
        constructed_identifier_scope='Small integer vertex/edge/face indices identify constructed semantic roles only; no native ASM ENTITY assignments',
        source_to_cache_entity_mapping=None)


def _rectangle_cache(graph,nodes,model):
    loops=_closed_body(graph,nodes,'FourLine');prism=model['prism']
    positions={i:nodes[nodes[i]['point_index']]['raw_origin'] for i in graph['vertex_indices']}
    vertex_error=_compare_bundle(list(positions.values()),[v['derived_position_cm'] for v in model['constructed_vertices']],
        'complete unordered rectangular POINT bundle')
    segments=[]
    for edge_id in graph['edge_indices']:
        edge=nodes[edge_id];curve=nodes[edge['curve_index']]
        if curve['kind']!='straight-curve':raise ValueError('Extrusion reconstruction rectangular EDGE lacks straight carrier')
        origin,direction=curve['raw_origin'],curve['direction'];norm=_dot(direction,direction)
        _finite(origin+direction,'rectangular Line')
        if norm<=TOLERANCE:raise ValueError('Extrusion reconstruction rectangular Line degenerates')
        parameters=[edge['start_parameter'],edge['end_parameter']];_finite(parameters,'rectangular finite EDGE parameters')
        endpoints=[positions[edge['start_vertex_index']],positions[edge['end_vertex_index']]]
        sign=-1 if edge['is_reversed'] else 1;evaluations=[]
        for point,t in zip(endpoints,parameters):
            evaluated=[o+sign*t*d for o,d in zip(origin,direction)]
            residual=_near(evaluated,point,'rectangular native Line endpoint')
            evaluations.append(dict(raw_parameter=t,observed_parameter_multiplier=sign,
                evaluated_position_cm=evaluated,typed_point_cm=point,residual_raw=residual))
        segments.append(dict(native_EDGE=edge,native_Line=curve,endpoint_positions_cm=endpoints,
            endpoint_evaluations=evaluations,native_traversal_semantics=None))
    segment_error=_compare_bundle([sorted(r['endpoint_positions_cm'],key=_geometry_sort_key) for r in segments],
        [sorted((r['start_position_cm'],r['end_position_cm']),key=_geometry_sort_key) for r in prism['segments']],
        'complete unordered rectangular straight segment bundle')
    faces=[];bundles=[]
    for face_id in graph['face_indices']:
        face=nodes[face_id];plane=nodes[face['surface_index']]
        if plane['kind']!='plane-surface':raise ValueError('Extrusion reconstruction rectangular FACE lacks Plane carrier')
        _finite(plane['raw_origin']+plane['normal']+plane['stored_reference_axis'],'rectangular Plane')
        _near([_dot(plane['normal'],plane['normal'])],[1.],'rectangular Plane unit normal')
        face_loops=[l for l in loops if l['face_index']==face_id]
        if len(face_loops)!=1:raise ValueError('Extrusion reconstruction rectangular FACE must own one loop')
        corners=[positions[i] for i in face_loops[0]['vertex_cycle']]
        for point in corners:_near([_dot(plane['normal'],[x-o for x,o in zip(point,plane['raw_origin'])])],[0.],'rectangular Plane boundary containment')
        bundles.append(_canonical_corner_cycle(corners))
        faces.append(dict(native_FACE=face,native_Plane=plane,loop=face_loops[0],corner_positions_cm=corners,
            native_UV_convention=None,FACE_sense_interpretation=None))
    face_error=_compare_bundle(bundles,[_canonical_corner_cycle(f['corner_positions_cm']) for f in prism['planar_quadrilateral_boundaries']],
        'complete unordered rectangular cyclic boundary bundle')
    return dict(kind='CompleteRectangularPrismCache',counts=graph['counts'],
        native_vertices=[dict(native_VERTEX=nodes[i],native_POINT=nodes[nodes[i]['point_index']]) for i in graph['vertex_indices']],
        native_straight_segments=segments,native_planar_boundaries=faces,
        complete_bundle_residuals_raw=dict(vertices=vertex_error,segments=segment_error,planar_boundaries=face_error),
        semantic_role_to_native_ENTITY_mapping=None,
        scope='Complete planar/straight bounded BODY corroboration after native profile/BODY qualification; coordinate-sorted geometric bundles assign no ENTITY identity')


def decode_extrusion_reconstruction(data,records,features,member,members,body_blob_bindings,body_selections=None):
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    candidates=[f for f in features if f.get('class_guid')==EXTRUDE]
    if not candidates:return result
    mapping_input=dict(decoded=[dict(mapping_record_object_id=m['mapping_record_object_id'],owner_object_id=m['owner_object_id'],
        history_blob_member=m['history_blob_member'],body_count=m['body_count'],bindings=[dict(stored_handle=b['stored_handle'],
        native_body_object_id=b['native_body_object_id']) for b in m['bindings']]) for m in body_blob_bindings.get('decoded',[])])
    joined=None;cache={}
    for feature in candidates:
        try:
            source=qualify_extrusion_source_operands(data,records,features,member,members,body_blob_bindings,feature)
            if source is None or source['feature_object_id']!=feature['object_id'] or len(source['source_groups'])!=1:
                raise ValueError('Extrusion reconstruction needs one freshly owned native profile/BODY source')
            group=source['source_groups'][0]
            if joined is None:joined=decode_body_asm_identifiers(data,records,member,members,mapping_input)
            matches=[(m,b) for m in joined['decoded'] for b in m['bindings'] if b['native_body_object_id']==group['native_body_object_id']]
            if len(matches)!=1 or matches[0][1]!=group['binding'] or matches[0][0]['history_blob_member']!=group['history_blob_member']:
                raise ValueError('Extrusion reconstruction fresh same-asset source BODY mapping differs')
            matrix=group['source_sketch']['placement']['sketch_to_component_matrix'];axis=group['sketch_normal_component']
            _near(group['stored_direction_vector'],axis,'stored direction/component Sketch normal frame relation unsupported')
            _near([_dot(axis,axis)],[1.],'native component extrusion axis')
            name=group['history_blob_member'];blob=members[name]
            if name not in cache:
                parsed=inspect_asm(blob);topology=decode_topology(parsed);cache[name]=(parsed,topology)
            parsed,topology=cache[name];nodes={n['index']:n for n in topology['nodes']}
            graphs=[g for g in topology['body_graphs'] if g['body_index']==group['asm_body_index']]
            if len(graphs)!=1:raise ValueError('Extrusion reconstruction explicitly mapped BODY graph absent or ambiguous')
            graph=graphs[0]
            if group['native_profile_kind']=='Circle':
                circle=group['native_profile_circles'][0]
                model=derive_circular_extrusion(_point(matrix,circle['center_cm']),axis,
                    _vector(matrix,circle['reference_axis']),circle['radius_cm'],group['extrude_controls'])
                corroboration=_circle_cache(graph,nodes,model)
            elif group['native_profile_kind']=='FourLine':
                model=_rectangle_model(group,matrix,axis);corroboration=_rectangle_cache(graph,nodes,model)
            else:raise ValueError('Extrusion reconstruction complete native profile family unsupported')
            result['decoded'].append(dict(feature_object_id=feature['object_id'],native_source_provenance=source,
                source_native_body_object_id=group['native_body_object_id'],history_blob_member=name,
                asm_body_index=group['asm_body_index'],binding=group['binding'],derived_geometry=model,
                native_cache_geometry_corroboration=corroboration,
                source_to_cache_entity_mapping=None,exact_API_handle_identity=None,
                qualified_historical_state=None,current_or_final_geometry_identity=None,scope=SCOPE))
        except (ValueError,KeyError,IndexError,TypeError,struct.error,OverflowError) as error:
            result['unresolved'].append(dict(feature_object_id=feature['object_id'],reason=str(error)))
    return result
