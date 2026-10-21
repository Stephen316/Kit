"""Native-profile/axis/angular Revolve construction and complete analytic cache proof.

Only mathematical source inputs construct geometry. Native owned BODY identity is
fixed before comparing complete nested carrier/boundary bundles. Geometry never
assigns model roles to native entities, and smooth closed surfaces retain their
actual zero-edge topology rather than invented seams.
"""
import math
import struct

from asm_records import inspect_asm
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_brep import decode_topology
from decode_extrusion_reconstruction import _near,_finite,_dot,_cross,_compare_bundle
from decode_shell_reconstruction import _geometry_sort_key

SCOPE=('Native NewBody solid angular Revolve construction from owned selected '
    'profile primitives, rigid Sketch frame and explicit axis. Effective angular '
    'orientation is derived from source geometry before cache inspection. Complete '
    'analytic carrier equations and bounded topology corroborate independently '
    'derived geometry as nested unordered bundles; no fit or coordinate ENTITY '
    'assignment, native UV/traversal, persistent/API/current identity, chronology '
    'or general Boolean regeneration is established.')


def _canonical_axis(axis):
    _finite(axis,'Revolve axis');_near([_dot(axis,axis)],[1.],'Revolve unit axis')
    first=next((x for x in axis if abs(x)>1e-10),None)
    if first is None:raise ValueError('Revolve axis is zero')
    return [x if first>0 else -x for x in axis]


def _axis_line(origin,axis):
    _finite(origin,'Revolve axis origin');a=_canonical_axis(axis);height=_dot(origin,a)
    return a,[x-height*y for x,y in zip(origin,a)]


def _plane_signature(origin,normal):
    n=_canonical_axis(normal);_finite(origin,'Revolve Plane origin')
    return ['Plane',n,_dot(n,origin)]


def _cylinder_signature(origin,axis,radius):
    _finite([radius],'Revolve Cylinder radius')
    if radius<=0:raise ValueError('Revolve Cylinder radius is nonpositive')
    a,o=_axis_line(origin,axis);return ['Cylinder',a,o,radius]


def _cone_signature(origin,axis,radius,slope):
    _finite([radius,slope],'Revolve Cone radial coefficients')
    a,o=_axis_line(origin,axis);m=slope*_dot(axis,a);b=radius-m*_dot(origin,a)
    if abs(m)<1e-10:raise ValueError('Revolve Cone slope degenerates')
    return ['Cone',a,o,m,b]


def _carrier(surface):
    kind=surface['kind']
    if kind=='plane-surface':
        _finite(surface['stored_reference_axis'],'Revolve Plane reference axis')
        return _plane_signature(surface['raw_origin'],surface['normal'])
    a=surface.get('analytic_surface',{});kind=a.get('kind')
    if kind=='Cylinder':return _cylinder_signature(a['raw_origin'],a['axis'],a['raw_radius'])
    if kind=='Cone':return _cone_signature(a['raw_origin'],a['axis'],a['raw_radius'],math.tan(a['stored_signed_half_angle_radians']))
    if kind=='Sphere':
        _finite(a['raw_origin']+[a['raw_radius']]+a['stored_axis_one']+a['stored_axis_two'],'Revolve Sphere coefficients')
        if a['raw_radius']<=0:raise ValueError('Revolve Sphere radius nonpositive')
        return ['Sphere',a['raw_origin'],a['raw_radius']]
    if kind=='Torus':
        _finite(a['raw_origin']+[a['raw_major_radius'],a['raw_minor_radius']]+a['stored_reference_axis'],'Revolve Torus coefficients')
        axis=_canonical_axis(a['axis']);major=a['raw_major_radius'];minor=abs(a['raw_minor_radius'])
        if not 0<minor<major:raise ValueError('Revolve ring Torus radius family differs')
        return ['Torus',a['raw_origin'],axis,major,minor]
    raise ValueError('Revolve cache carrier family unsupported')


def _point(vertex,nodes):
    point=nodes[vertex['point_index']]
    if point['kind']!='point':raise ValueError('Revolve VERTEX lacks typed POINT')
    _finite(point['raw_origin'],'Revolve cache POINT');return point['raw_origin']


def _curve_signature(edge,nodes):
    ends=[_point(nodes[edge[k]],nodes) for k in ('start_vertex_index','end_vertex_index')]
    if edge['curve_index'] is None:
        if edge['start_vertex_index']!=edge['end_vertex_index']:raise ValueError('Revolve singular EDGE endpoints differ')
        return ['PointSingularity',ends[0]],dict(native_EDGE=edge,native_POINT=nodes[nodes[edge['start_vertex_index']]['point_index']],scope='Typed null-curve singular EDGE; stored parameter literals have no inferred evaluator meaning')
    curve=nodes[edge['curve_index']];parameters=[edge['start_parameter'],edge['end_parameter']]
    _finite(parameters,'Revolve finite EDGE domain')
    if curve['kind']=='straight-curve':
        origin,direction=curve['raw_origin'],curve['direction'];_finite(origin+direction,'Revolve Line coefficients')
        _near([_dot(direction,direction)],[1.],'Revolve Line unit direction')
        evaluated=[[o+t*d for o,d in zip(origin,direction)] for t in parameters]
        residual=_compare_bundle(evaluated,ends,'Revolve complete native Line domain endpoints')
        if edge['start_vertex_index']==edge['end_vertex_index']:raise ValueError('Revolve straight EDGE degenerates')
        signature=['LineSegment',sorted(evaluated,key=_geometry_sort_key)]
    elif curve['kind']=='ellipse-curve':
        c,n,ref=curve['raw_origin'],curve['normal'],curve['stored_reference_axis'];radius=curve['raw_major_radius']
        _finite(c+n+ref+[radius,curve['raw_minor_radius']],'Revolve circle coefficients')
        if radius<=0:raise ValueError('Revolve ellipse radius nonpositive')
        _near([radius],[curve['raw_minor_radius']],'Revolve complete circle radii')
        u=[x/radius for x in ref];v=_cross(n,u)
        _near([_dot(n,n),_dot(u,u),_dot(u,n)],[1.,1.,0.],'Revolve circular frame')
        span=abs(parameters[1]-parameters[0]);_finite([span],'Revolve circular span')
        if not 1e-10<span<=2*math.pi+1e-8:raise ValueError('Revolve bounded circular span outside observed family')
        evaluated=[[o+radius*(math.cos(t)*x+math.sin(t)*y) for o,x,y in zip(c,u,v)] for t in parameters]
        residual=_compare_bundle(evaluated,ends,'Revolve complete circular domain endpoints')
        normal=_canonical_axis(n)
        if abs(span-2*math.pi)<=1e-8:
            if edge['start_vertex_index']!=edge['end_vertex_index']:raise ValueError('Revolve closed-circle EDGE must have one seam VERTEX')
            signature=['Circle',c,radius,normal]
        else:
            if edge['start_vertex_index']==edge['end_vertex_index']:raise ValueError('Revolve bounded arc endpoints not distinct')
            mid=sum(parameters)/2;middle=[o+radius*(math.cos(mid)*x+math.sin(mid)*y) for o,x,y in zip(c,u,v)]
            signature=['CircleArc',c,radius,normal,span,middle]
    else:raise ValueError('Revolve cache bounded curve family unsupported')
    return signature,dict(native_EDGE=edge,native_curve=curve,native_endpoint_positions_cm=ends,
        native_endpoint_evaluations_cm=evaluated,complete_endpoint_residual_raw=residual,
        scope='Complete typed Line or circular carrier plus finite interval; arc signature retains full span and midpoint phase, not merely endpoint samples')


def _closed_topology(graph,nodes,expected):
    if graph['body_transform_is_identity'] is not True:raise ValueError('Revolve cache BODY frame is not identity')
    for kind,count in expected.items():
        ids=graph[kind+'_indices']
        if len(ids)!=count or len(set(ids))!=count or any(nodes[i]['kind']!=kind for i in ids):raise ValueError('Revolve complete topology count/type differs: '+kind)
    body=nodes[graph['body_index']];lump=nodes[graph['lump_indices'][0]];shell=nodes[graph['shell_indices'][0]]
    if (body['first_lump_index']!=lump['index'] or body['first_wire_index'] is not None or lump['body_index']!=body['index']
            or lump['next_lump_index'] is not None or lump['first_shell_index']!=shell['index'] or shell['lump_index']!=lump['index']
            or shell['next_shell_index'] is not None or shell['subshell_index'] is not None or shell['first_wire_index'] is not None):
        raise ValueError('Revolve reciprocal single lump/shell/no-wire framing differs')
    seen=set();current=shell['first_face_index']
    while current is not None:
        if current in seen or current not in graph['face_indices'] or nodes[current]['shell_index']!=shell['index'] or nodes[current]['subshell_index'] is not None:
            raise ValueError('Revolve FACE owner/chain differs')
        seen.add(current);current=nodes[current]['next_face_index']
    if seen!=set(graph['face_indices']):raise ValueError('Revolve FACE chain incomplete')
    loops=[];all_coedges=set()
    for face_id in graph['face_indices']:
        loop_ids=set();current=nodes[face_id]['first_loop_index']
        while current is not None:
            if current not in graph['loop_indices'] or current in loop_ids or nodes[current]['face_index']!=face_id:raise ValueError('Revolve FACE/LOOP chain differs')
            loop_ids.add(current);current=nodes[current]['next_loop_index']
        for loop_id in sorted(loop_ids):
            cycle=[];pairs=[];current=nodes[loop_id]['first_coedge_index']
            while current not in cycle:
                if current not in graph['coedge_indices'] or current in all_coedges or len(cycle)>=64:raise ValueError('Revolve loop cycle framing differs')
                coedge=nodes[current];next_id=coedge['next_coedge_index'];previous=coedge['previous_coedge_index']
                if (coedge['loop_index']!=loop_id or next_id not in graph['coedge_indices'] or previous not in graph['coedge_indices']
                        or nodes[next_id]['previous_coedge_index']!=current or nodes[previous]['next_coedge_index']!=current
                        or coedge['edge_index'] not in graph['edge_indices']):raise ValueError('Revolve reciprocal COEDGE loop differs')
                edge=nodes[coedge['edge_index']];pair=[edge['start_vertex_index'],edge['end_vertex_index']]
                if coedge['is_reversed']:pair.reverse()
                if pairs and pairs[-1][1]!=pair[0]:raise ValueError('Revolve loop endpoint continuity differs')
                cycle.append(current);pairs.append(pair);current=next_id
            if current!=cycle[0] or pairs[-1][1]!=pairs[0][0]:raise ValueError('Revolve complete loop closure differs')
            all_coedges.update(cycle);loops.append(dict(face_index=face_id,loop_index=loop_id,coedge_cycle=cycle,
                edge_indices=[nodes[c]['edge_index'] for c in cycle],vertex_cycle=[p[0] for p in pairs],
                native_LOOP=nodes[loop_id],native_COEDGEs=[nodes[c] for c in cycle]))
    if {l['loop_index'] for l in loops}!=set(graph['loop_indices']) or all_coedges!=set(graph['coedge_indices']):raise ValueError('Revolve LOOP/COEDGE exhaustion differs')
    for e in graph['edge_indices']:
        edge=nodes[e];uses=[nodes[c] for c in all_coedges if nodes[c]['edge_index']==e]
        if edge['first_coedge_index'] not in {c['index'] for c in uses}:raise ValueError('Revolve EDGE head incidence differs')
        if edge['curve_index'] is None:
            if (len(uses)!=1 or uses[0]['partner_index'] is not None or edge['start_vertex_index']!=edge['end_vertex_index']):raise ValueError('Revolve singular EDGE/COEDGE framing differs')
        elif (len(uses)!=2 or len({nodes[c['loop_index']]['face_index'] for c in uses})!=2
                or any(a['partner_index']!=b['index'] for a,b in ((uses[0],uses[1]),(uses[1],uses[0])))):
            raise ValueError('Revolve reciprocal other-use partner/two-FACE incidence differs')
        if any(v not in graph['vertex_indices'] for v in (edge['start_vertex_index'],edge['end_vertex_index'])):raise ValueError('Revolve EDGE vertex membership differs')
    for v in graph['vertex_indices']:
        vertex=nodes[v];incident={e for e in graph['edge_indices'] if v in (nodes[e]['start_vertex_index'],nodes[e]['end_vertex_index'])}
        if vertex['first_edge_index'] not in incident:raise ValueError('Revolve VERTEX head incidence differs')
        _point(vertex,nodes)
    return loops


def _key(value):
    if isinstance(value,str):return (0,value)
    if isinstance(value,(int,float)):return (1,round(value,9))
    return (2,tuple(_key(x) for x in value))


def _cycle(curves):
    if not curves:raise ValueError('Revolve empty boundary loop is unsupported')
    variants=[]
    for rows in (curves,list(reversed(curves))):
        variants.extend(rows[i:]+rows[:i] for i in range(len(rows)))
    return min(variants,key=_key)


def _nested(left,right):
    if isinstance(left,str) or isinstance(right,str):
        if left!=right:raise ValueError('Revolve complete carrier/boundary kind differs')
        return 0.
    if isinstance(left,(int,float)) and isinstance(right,(int,float)):
        return _near([left],[right],'Revolve complete carrier/bounded nested geometry')
    if not isinstance(left,(tuple,list)) or not isinstance(right,(tuple,list)) or len(left)!=len(right):
        raise ValueError('Revolve complete carrier/boundary nested framing differs')
    return max((_nested(a,b) for a,b in zip(left,right)),default=0.)


def _model_carrier(carrier):
    kind=carrier['kind']
    if kind=='Plane':return _plane_signature(carrier['origin_cm'],carrier['unit_normal'])
    if kind=='Cylinder':return _cylinder_signature(carrier['axis_origin_cm'],carrier['unit_axis'],carrier['radius_cm'])
    if kind=='Cone':return _cone_signature(carrier['axis_origin_cm'],carrier['unit_axis'],carrier['radial_intercept_cm'],carrier['radial_slope'])
    if kind=='Sphere':return ['Sphere',carrier['center_cm'],carrier['radius_cm']]
    if kind=='Torus':return ['Torus',carrier['center_cm'],_canonical_axis(carrier['unit_axis']),carrier['major_radius_cm'],carrier['minor_radius_cm']]
    raise ValueError('Revolve mathematical carrier kind unsupported')


def _model_curve(curve):
    kind=curve['kind']
    if kind=='PointSingularity':return [kind,curve['point_cm']]
    if kind=='LineSegment':return [kind,sorted([curve['start_cm'],curve['end_cm']],key=_geometry_sort_key)]
    if kind=='CircleArc':
        center,radius=curve['center_cm'],curve['radius_cm'];normal=_canonical_axis(curve['unit_axis'])
        if curve['is_full_circle']:return ['Circle',center,radius,normal]
        a,b=curve['angle_interval_radians'];middle=(a+b)/2
        point=[o+radius*(math.cos(middle)*x+math.sin(middle)*y) for o,x,y in zip(center,curve['reference_u'],curve['reference_v'])]
        return [kind,center,radius,normal,abs(b-a),point]
    raise ValueError('Revolve mathematical boundary curve kind unsupported')


def _containment(carrier,curve):
    """Whole coefficient containment, independently of bundle correspondence."""
    kind=carrier[0];curvekind=curve[0]
    if curvekind=='LineSegment':points=curve[1]
    elif curvekind=='PointSingularity':points=[curve[1]]
    else:points=[curve[1]] # circular centre; radial coefficients checked below
    if kind=='Plane':
        normal,constant=carrier[1:]
        for p in points:_near([_dot(normal,p)],[constant],'Revolve Plane complete boundary containment')
        if curvekind in ('Circle','CircleArc'):
            axis=curve[3];sign=1 if _dot(normal,axis)>=0 else -1
            _near(normal,[sign*x for x in axis],'Revolve Plane circle coefficient containment')
    elif kind in ('Cylinder','Cone'):
        axis,origin=carrier[1:3]
        if curvekind in ('Circle','CircleArc'):
            center,radius,normal=curve[1:4];sign=1 if _dot(normal,axis)>=0 else -1
            _near(normal,[sign*x for x in axis],'Revolve lateral circular normal coefficients')
            delta=[x-y for x,y in zip(center,origin)];height=_dot(delta,axis)
            _near([x-height*a for x,a in zip(delta,axis)],[0.,0.,0.],'Revolve lateral circular centre axis line')
            expected=carrier[3] if kind=='Cylinder' else carrier[3]*_dot(center,axis)+carrier[4]
            _near([radius],[expected],'Revolve lateral complete circle radial coefficient')
        elif curvekind=='LineSegment' and kind=='Cylinder':
            p,q=points;direction=[y-x for x,y in zip(p,q)];height=_dot(direction,axis)
            _near([x-height*a for x,a in zip(direction,axis)],[0.,0.,0.],'Revolve Cylinder straight generatrix coefficients')
            delta=[x-y for x,y in zip(p,origin)];height=_dot(delta,axis)
            radius=math.hypot(*[x-height*a for x,a in zip(delta,axis)])
            _near([radius],[carrier[3]],'Revolve Cylinder generatrix radius')
        elif curvekind=='PointSingularity' and kind=='Cone':
            delta=[x-y for x,y in zip(points[0],origin)];height=_dot(delta,axis)
            _near([x-height*a for x,a in zip(delta,axis)],[0.,0.,0.],'Revolve Cone singular point axis')
            _near([carrier[3]*_dot(points[0],axis)+carrier[4]],[0.],'Revolve Cone singular point zero radius')
        else:raise ValueError('Revolve lateral bounded curve/analytic carrier family unsupported')
    elif points:raise ValueError('Revolve smooth closed carrier must have no finite trim boundary')


def _expected_counts(model):
    if model['kind'] in ('Sphere','Torus'):values=(1,0,0,0,0)
    elif model['kind']=='PolygonRevolve' and len(model['meridian_profile']['vertices'])==3:values=(2,3,3,2,2)
    elif model['is_full_turn']:values=(4,8,8,4,4)
    else:values=(6,6,24,12,8)
    return dict(lump=1,shell=1,**dict(zip(('face','loop','coedge','edge','vertex'),values)))


def _corroborate(graph,nodes,model):
    loops=_closed_topology(graph,nodes,_expected_counts(model));curves={};edgeproof=[]
    for edge_id in graph['edge_indices']:
        signature,proof=_curve_signature(nodes[edge_id],nodes);curves[edge_id]=signature
        proof['complete_geometric_signature']=signature;edgeproof.append(proof)
    faces=[];bundle=[]
    for face_id in graph['face_indices']:
        face=nodes[face_id];surface=nodes[face['surface_index']];carrier=_carrier(surface);face_loops=[]
        for loop in loops:
            if loop['face_index']!=face_id:continue
            signatures=[curves[e] for e in loop['edge_indices']]
            for curve in signatures:_containment(carrier,curve)
            face_loops.append(_cycle(signatures))
        signature=[carrier,sorted(face_loops,key=_key)];bundle.append(signature)
        faces.append(dict(native_FACE=face,native_surface=surface,complete_geometric_signature=signature,
            native_boundary_loops=[l for l in loops if l['face_index']==face_id],native_UV_and_FACE_sense=None))
    derived=[]
    for face in model['faces']:
        carrier=_model_carrier(face['carrier']);loopbundles=[]
        for loop in face['boundary_loops']:
            signatures=[_model_curve(c) for c in loop['curves']]
            for curve in signatures:_containment(carrier,curve)
            loopbundles.append(_cycle(signatures))
        derived.append([carrier,sorted(loopbundles,key=_key)])
    residual=_nested(sorted(bundle,key=_key),sorted(derived,key=_key))
    return dict(kind='CompleteAnalyticRevolveCache',counts=graph['counts'],native_bounded_edges=edgeproof,
        native_analytic_faces=faces,complete_native_FACE_loop_curve_bundle=bundle,
        independent_derived_FACE_loop_curve_bundle=derived,complete_bundle_residual_raw=residual,
        native_vertices=[dict(native_VERTEX=nodes[v],native_POINT=nodes[nodes[v]['point_index']]) for v in graph['vertex_indices']],
        mathematical_role_to_native_ENTITY_mapping=None,scope=SCOPE)


def decode_revolve_reconstruction(data,records,features,member,members,body_blob_bindings,body_selections=None):
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    candidates=[f for f in features if f.get('class_guid')=='E3849A15-2FC6-42A0-AF3A-2F1D7273B406']
    if not candidates:return result
    from decode_revolve_source_operands import qualify_revolve_source_operands
    from decode_revolve_geometry import derive_revolve_geometry
    mapping_input=dict(decoded=[dict(mapping_record_object_id=m['mapping_record_object_id'],owner_object_id=m['owner_object_id'],
        history_blob_member=m['history_blob_member'],body_count=m['body_count'],bindings=[dict(stored_handle=b['stored_handle'],
        native_body_object_id=b['native_body_object_id']) for b in m['bindings']]) for m in body_blob_bindings.get('decoded',[])])
    joined=None;cache={}
    for feature in candidates:
        try:
            source=qualify_revolve_source_operands(data,records,features,member,members,body_blob_bindings,feature)
            if source is None or len(source['source_groups'])!=1:raise ValueError('Revolve reconstruction needs one fresh native profile/BODY source')
            group=source['source_groups'][0]
            if joined is None:joined=decode_body_asm_identifiers(data,records,member,members,mapping_input)
            matches=[(m,b) for m in joined['decoded'] for b in m['bindings'] if b['native_body_object_id']==group['native_body_object_id']]
            if len(matches)!=1 or matches[0][1]!=group['binding'] or matches[0][0]['history_blob_member']!=group['history_blob_member']:
                raise ValueError('Revolve reconstruction fresh same-asset BODY mapping differs')
            inputs=group['mathematical_inputs']
            model=derive_revolve_geometry(inputs['profile'],inputs['sketch_to_component_matrix'],
                inputs['source_axis'],inputs['controls'])
            name=group['history_blob_member']
            if name not in cache:
                parsed=inspect_asm(members[name]);cache[name]=decode_topology(parsed)
            topology=cache[name];nodes={n['index']:n for n in topology['nodes']}
            graphs=[g for g in topology['body_graphs'] if g['body_index']==group['asm_body_index']]
            if len(graphs)!=1:raise ValueError('Revolve reconstruction mapped BODY graph missing or ambiguous')
            corroboration=_corroborate(graphs[0],nodes,model)
            result['decoded'].append(dict(feature_object_id=feature['object_id'],native_source_provenance=source,
                source_native_body_object_id=group['native_body_object_id'],binding=group['binding'],history_blob_member=name,
                asm_body_index=group['asm_body_index'],derived_geometry=model,native_cache_geometry_corroboration=corroboration,
                exact_API_handle_identity=None,current_or_final_geometry_identity=None,qualified_historical_state=None,scope=SCOPE))
        except (ValueError,KeyError,IndexError,TypeError,struct.error,OverflowError) as error:
            result['unresolved'].append(dict(feature_object_id=feature['object_id'],reason=str(error)))
    return result
