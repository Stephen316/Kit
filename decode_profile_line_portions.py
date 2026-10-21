"""Bounded derived Line/Line source-profile fractions, not stored parameters.

Full native tuple/cache-name identity is established before geometric checks.
The observed context is two axis-aligned four-Line cycles in an identity XY
Sketch. Source endpoint references qualify shared corners; proper intersections
partition each selected source Line in its explicit native start/end direction.
"""
import copy
import math
import struct

from asm_records import inspect_asm
from decode_brep import decode_topology
from decode_parameters import read_string
from decode_profiles import PROFILE_DESCRIPTOR_GUID
from decode_sketch import attributes, numbers, reference
from decode_trimmed_profiles import decode_trimmed_profiles, read_trimmed_profile_loops

LINE='DCA267ED-D615-4934-B64F-AD805E8003E2'
SKETCH='44A64366-4BD3-4B24-881A-F94C206E8F2D'
EPS=1e-9
SCOPE='Observed identity-XY two-rectangle Line profiles; complete native six-literal/cache identity precedes derived source fractions from proper Line intersections; no serialized/API parameter equivalence'


def _eligible_features(data,records,features):
    """Typed owned descriptors gate Line-only contexts; Circle cases stay empty."""
    groups={}
    for record in records:
        if record.is_primary:groups.setdefault(record.object_id,[]).append(record)
    primary={identity:rows[0] for identity,rows in groups.items() if len(rows)==1}
    selected=set()
    for record in records:
        if not record.is_primary or record.class_guid!=PROFILE_DESCRIPTOR_GUID:continue
        try:
            body=data[record.body:record.end]
            _,cursor=read_string(body,17);sketch_text,_=read_string(body,cursor)
            if not sketch_text.isascii() or not sketch_text.isdecimal():continue
            sketch_id=int(sketch_text)
            if sketch_id not in primary or primary[sketch_id].class_guid!=SKETCH:continue
            sketches=[feature for feature in features if feature['kind']=='Sketch' and feature['sketch_object_id']==sketch_id]
            if len(sketches)!=1:continue
            curves=[geometry for geometry in sketches[0]['geometry'] if geometry['kind']!='Point']
            if curves and all(geometry['kind']=='Line' for geometry in curves):
                selected.add(reference(body,len(body)-11))
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error):continue
    return [feature for feature in features if feature['kind']!='Extrude' or feature['object_id'] in selected],selected


def read_line_portion_loops(body,descriptor_id,sketch):
    loops=read_trimmed_profile_loops(body,descriptor_id,sketch)
    if len(loops)!=1 or not loops[0]['is_outer'] or len(loops[0]['curve_references'])!=4:
        raise ValueError('Only captured single four-Line outer profile supported')
    if any(ref['entity_kind']!='Line' or ref['stored_reference_selector_pair'] not in ([1,2],[2,2])
           for ref in loops[0]['curve_references']):
        raise ValueError('Uncaptured Line-only source/reference selector family')
    return loops


def _cross(a,b):
    return a[0]*b[1]-a[1]*b[0]


def _partition_lines(data,records,sketch,sources):
    curves=[geometry for geometry in sketch['geometry'] if geometry['kind']!='Point']
    if len(curves)!=8 or any(curve['kind']!='Line' for curve in curves) or len(sources)!=4:
        raise ValueError('Only captured two-four-Line-cycle source context supported')
    if not {source['native_entity_object_id'] for source in sources}<={curve['object_id'] for curve in curves}:
        raise ValueError('Qualified source Line is absent from explicit source Sketch')
    identity=[1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.]
    matrix=sketch.get('placement',{}).get('sketch_to_component_matrix')
    if matrix is None or len(matrix)!=16 or any(not math.isclose(a,b,abs_tol=EPS) for a,b in zip(matrix,identity)):
        raise ValueError('Derived Line source placement outside observed identity context')
    groups={}
    for record in records:
        if record.is_primary:groups.setdefault(record.object_id,[]).append(record)
    primary={identity:rows[0] for identity,rows in groups.items() if len(rows)==1}
    endpoint_graph={};by_id={curve['object_id']:curve for curve in curves}
    for curve in curves:
        record=primary.get(curve['object_id'])
        if record is None or record.class_guid!=LINE:
            raise ValueError('Source Line typed native identity missing/ambiguous')
        body=data[record.body:record.end]
        props,cursor=attributes(body,2)
        if (body[:2]!=b'\0\1' or props.get('EntityGenesis')!=2 or props.get('crv_primary_id')!=curve['entity_tag']
                or props.get('crv_secondary_id')!=0 or reference(body,len(body)-11)!=sketch['sketch_object_id']
                or len(body)-cursor!=171 or reference(body,cursor+107)!=curve['start_point_id']
                or reference(body,cursor+96)!=curve['end_point_id']):
            raise ValueError('Native Line owner/tags/endpoint references disagree')
        values=numbers(body,cursor,12)
        if (math.dist(values[:3],curve['start_cm'])>EPS
                or math.dist([a+b for a,b in zip(values[:3],values[3:6])],curve['end_cm'])>EPS):
            raise ValueError('Canonical Line geometry differs from typed native endpoint representation')
        start,end=curve['start_cm'],curve['end_cm'];delta=[b-a for a,b in zip(start,end)]
        if (curve.get('entity_genesis')!=2 or curve.get('is_construction') is not False
                or not all(math.isfinite(value) for value in (*start,*end))
                or abs(start[2])>EPS or abs(end[2])>EPS or math.hypot(*delta[:2])<=EPS
                or (abs(delta[0])>EPS)==(abs(delta[1])>EPS)):
            raise ValueError('Source Line frame/axis alignment outside captured XY family')
        for point_id in (curve['start_point_id'],curve['end_point_id']):
            endpoint_graph.setdefault(point_id,[]).append(curve['object_id'])
    if len(endpoint_graph)!=8 or any(len(lines)!=2 for lines in endpoint_graph.values()):
        raise ValueError('Native Line endpoints do not form the captured disjoint cycles')
    remaining=set(by_id);components=[]
    while remaining:
        pending=[next(iter(remaining))];component=set()
        while pending:
            identity=pending.pop()
            if identity in component:continue
            component.add(identity);curve=by_id[identity]
            for point_id in (curve['start_point_id'],curve['end_point_id']):
                pending.extend(endpoint_graph[point_id])
        remaining-=component;components.append(component)
    if sorted(map(len,components))!=[4,4]:
        raise ValueError('Expected two explicit native four-Line cycles')
    partitions={}
    for curve in curves:
        p=curve['start_cm'];r=[b-a for a,b in zip(p,curve['end_cm'])];cuts=[]
        for other in curves:
            if other['object_id']==curve['object_id']:continue
            q=other['start_cm'];s=[b-a for a,b in zip(q,other['end_cm'])];qp=[b-a for a,b in zip(p,q)]
            denominator=_cross(r,s)
            if abs(denominator)<=EPS:
                if abs(_cross(qp,r))<=EPS:
                    raise ValueError('Collinear source Lines outside captured proper-intersection context')
                continue
            t=_cross(qp,s)/denominator;u=_cross(qp,r)/denominator
            if not -EPS<=t<=1+EPS or not -EPS<=u<=1+EPS:continue
            if EPS<t<1-EPS and EPS<u<1-EPS:
                cuts.append({'derived_fraction':t,'other_native_line_object_id':other['object_id'],
                             'other_native_line_tag':other['entity_tag']})
            else:
                shared={curve['start_point_id'],curve['end_point_id']}&{other['start_point_id'],other['end_point_id']}
                if len(shared)!=1 or EPS<t<1-EPS or EPS<u<1-EPS:
                    raise ValueError('Non-proper Line touch without explicit shared native corner')
        cuts.sort(key=lambda item:item['derived_fraction'])
        if any(b['derived_fraction']-a['derived_fraction']<=EPS for a,b in zip(cuts,cuts[1:])):
            raise ValueError('Coincident Line cuts need an unsupported multiway partition')
        partitions[curve['entity_tag']]={'source':curve,'derived_intersections':cuts}
    return partitions


def _point(line,fraction):
    return [a+fraction*(b-a) for a,b in zip(line['start_cm'],line['end_cm'])]


def decode_profile_line_portions(data,records,features,member,members,body_identifier_summary):
    selected,owners=_eligible_features(data,records,features)
    if not owners:return {'decoded':[],'unresolved':[],'scope':SCOPE}
    base=decode_trimmed_profiles(data,records,selected,member,members,body_identifier_summary,
                                 profile_loops_reader=read_line_portion_loops)
    decoded=[];unresolved=list(base['unresolved'])
    for cached in base['decoded']:
        try:
            row=copy.deepcopy(cached)
            sketches=[feature for feature in features if feature['kind']=='Sketch' and feature['sketch_object_id']==row['native_sketch_object_id']]
            if len(sketches)!=1:raise ValueError('Derived Line source Sketch missing/ambiguous')
            partitions=_partition_lines(data,records,sketches[0],row['source_curves'])
            topology=decode_topology(inspect_asm(members[row['history_blob_member']]))
            graphs=[graph for graph in topology['body_graphs'] if graph['body_index']==row['asm_body_index']]
            if len(graphs)!=1 or graphs[0]['body_transform_is_identity'] is not True:
                raise ValueError('Derived Line/cache comparison requires identity BODY transform')
            portions=[]
            for source in row['source_curves']:
                ref=source['stored_profile_reference'];ordinal,stored_count=ref['stored_reference_selector_pair']
                partition=partitions[source['native_entity_tag']];line=partition['source'];cuts=partition['derived_intersections']
                if stored_count!=len(cuts)+1 or stored_count!=2:
                    raise ValueError('Stored Line portion count differs from proper source partition')
                bounds=[0.]+[item['derived_fraction'] for item in cuts]+[1.]
                start,end=bounds[ordinal-1:ordinal+1];points=[_point(line,t) for t in (start,(start+end)/2,end)]
                evidence=[]
                for candidate in source['cached_coedge_candidates']:
                    if candidate['stored_decimal_text_fields']!=ref['stored_coedge_text_fields']:
                        raise ValueError('Derived Line candidate lacks complete native tuple identity')
                    curve=candidate['stored_curve_geometry'];a,b=candidate['stored_edge_parameter_interval']
                    if curve['kind']!='straight-curve' or not all(math.isfinite(t) for t in (a,b)) or b<=a:
                        raise ValueError('Named stored Line primitive/interval unsupported')
                    observed=[[origin+t*direction for origin,direction in zip(curve['raw_origin'],curve['direction'])]
                              for t in (a,(a+b)/2,b)]
                    endpoint_error=max(min(math.dist(point,other) for other in (observed[0],observed[2])) for point in (points[0],points[2]))
                    midpoint_error=math.dist(points[1],observed[1])
                    if max(endpoint_error,midpoint_error)>EPS:
                        raise ValueError('Derived source Line portion disagrees with a full-tuple named cached boundary')
                    evidence.append({'coedge_record_index':candidate['coedge_record_index'],
                                     'edge_record_index':candidate['edge_record_index'],
                                     'max_endpoint_set_error_cm':endpoint_error,'midpoint_error_cm':midpoint_error})
                portions.append({'native_source_line_object_id':source['native_entity_object_id'],
                                 'native_source_line_tag':source['native_entity_tag'],'stored_profile_reference':ref,
                                 'native_line_endpoint_object_ids':[line['start_point_id'],line['end_point_id']],
                                 'native_line_start_end_cm':[copy.deepcopy(line['start_cm']),copy.deepcopy(line['end_cm'])],
                                 'geometry_status':'DerivedAnalyticSourceLinePortion',
                                 'derivation':'Proper intersections partition the finite source Line; portion1 starts at its explicit native start endpoint and later portions follow toward its end endpoint',
                                 'derived_portion_ordinal':ordinal,'derived_portion_count':stored_count,
                                 'derived_native_start_end_fraction_interval':[start,end],
                                 'derived_sketch_local_points_cm':{'start':points[0],'midpoint':points[1],'end':points[2]},
                                 'all_full_tuple_cache_candidates_corroborate':evidence,
                                 'parameter_status':'Derived affine fractions between explicit native source endpoints; not serialized trim fields, API evaluator parameters or decoded traversal direction'})
            row.update(derived_source_line_partitions=[{'native_line_object_id':part['source']['object_id'],
                                                       'native_line_tag':tag,'derived_intersections':part['derived_intersections'],
                                                       'derived_portion_count':len(part['derived_intersections'])+1}
                                                      for tag,part in sorted(partitions.items())],
                       derived_source_portions=portions,
                       geometry_status='Bounded derived source Line portions, independently corroborated by every full-tuple qualified cached boundary',
                       remaining_uncertainty=['General non-rectangular/rotated/3D/collinear/touching Line contexts',
                                              'Other selector/count combinations and repeated source Line portions',
                                              'Serialized/native/API parameterization and stored direction flag traversal semantics',
                                              'Modified cached geometry, persistent topology identity and lifecycle'])
            decoded.append(row)
        except (ValueError,KeyError,IndexError,TypeError,ArithmeticError,UnicodeError,struct.error) as error:
            unresolved.append({'source_feature_object_id':cached['source_feature_object_id'],'reason':str(error)})
    return {'decoded':decoded,'unresolved':unresolved,'scope':SCOPE}
