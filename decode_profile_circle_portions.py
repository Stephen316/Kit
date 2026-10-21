"""Bounded derived Circle/Circle profile portions, not stored trim parameters.

Native full tuples and mapped COEDGE names establish each portion's identity
first. In the observed XY/identity-placement two/three-circle context, selector
b equals the number of proper intersection-defined portions; selector a indexes
those portions, beginning with the one crossing the positive reference axis.
Analytic endpoints/angles are derived from source circles, never read as serialized
parameters, and every named cached candidate must independently corroborate them.
"""
import copy
import math
import struct

from asm_records import inspect_asm
from decode_brep import decode_topology
from decode_profiles import read_loops
from decode_trimmed_profiles import decode_trimmed_profiles

PAIRS = frozenset(((1, 2), (2, 2), (2, 4), (4, 4)))
EPS = 1e-9
SCOPE = 'Observed proper Circle/Circle intersections in identity-placed XY sketches; full native tuple identity precedes bounded derived source portions, with every named result-cache candidate corroborated'


def read_circle_portion_loops(body, descriptor_id, sketch):
    seen = set()
    per_tag = {}

    def details(fields, geometry):
        code, tag, secondary, direction, first, second, opaque = fields
        if geometry['kind'] != 'Circle' or (first, second) not in PAIRS:
            raise ValueError('Uncaptured Circle-only portion selector/source family')
        identity = (tag, secondary, direction, opaque, first, second)
        if identity in seen:
            raise ValueError('Duplicate full native portion tuple is ambiguous')
        seen.add(identity)
        per_tag.setdefault(tag, []).append((first, second))
        return {'stored_tuple_code': code, 'stored_reference_selector_pair': [first, second],
                'stored_opaque_u64': opaque, 'stored_tuple_fields': list(fields),
                'stored_coedge_text_fields': [str(value) for value in identity],
                'geometry_scope': 'Underlying Circle identity plus literal portion selectors; analytic source geometry is derived separately'}

    loops = read_loops(body, descriptor_id, sketch, curve_reference_details=details)
    if len(loops) != 1 or not loops[0]['is_outer']:
        raise ValueError('Only captured single outer Circle/Circle portion loop supported')
    for selectors in per_tag.values():
        if len(selectors) > 1 and sorted(selectors) != [(2, 4), (4, 4)]:
            raise ValueError('Uncaptured repeated-Circle portion selector combination')
    cursor = 25
    for ref in loops[0]['curve_references']:
        if body[cursor:cursor+40] != struct.pack('<IQQIIIQ', *ref['stored_tuple_fields']):
            raise ValueError('Circle portion raw tuple replay disagrees')
        ref['stored_tuple_offset_in_definition'] = cursor
        cursor += 40
    return loops


def _circle_partitions(sketch, sources):
    curves = [geometry for geometry in sketch['geometry'] if geometry['kind'] != 'Point']
    if not 2 <= len(curves) <= 3 or any(curve['kind'] != 'Circle' for curve in curves):
        raise ValueError('Only captured two/three-Circle source context supported')
    if {curve['object_id'] for curve in curves} != {source['native_entity_object_id'] for source in sources}:
        raise ValueError('Every source Circle must have independently qualified native/cache membership')
    expected_matrix = [1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.]
    matrix = sketch.get('placement', {}).get('sketch_to_component_matrix')
    if matrix is None or len(matrix) != 16 or any(not math.isclose(a,b,abs_tol=EPS) for a,b in zip(matrix,expected_matrix)):
        raise ValueError('Circle portion source placement is outside observed identity context')
    for curve in curves:
        if (curve.get('entity_genesis') != 2 or curve.get('is_construction') is not False
                or math.dist(curve['normal'], [0.,0.,1.]) > EPS
                or math.dist(curve['reference_axis'], [1.,0.,0.]) > EPS
                or abs(curve['center_cm'][2]) > EPS
                or not all(math.isfinite(value) for value in (*curve['center_cm'],curve['radius_cm']))
                or curve['radius_cm'] <= EPS):
            raise ValueError('Circle portion source frame/primitive outside observed XY context')
    result = {}
    for curve in curves:
        cx,cy,_ = curve['center_cm']; radius = curve['radius_cm']; cuts = []
        for other in curves:
            if other['object_id'] == curve['object_id']:
                continue
            ox,oy,_ = other['center_cm']; other_radius = other['radius_cm']
            dx,dy = ox-cx,oy-cy; distance = math.hypot(dx,dy)
            if distance <= EPS:
                raise ValueError('Coincident/concentric Circle partition unsupported')
            if distance > radius+other_radius+EPS:
                continue  # Captured disjoint cutters create no intersection cuts.
            if not abs(radius-other_radius)+EPS < distance < radius+other_radius-EPS:
                raise ValueError('Tangent/contained/ambiguous Circle partition unsupported')
            cosine = (radius*radius+distance*distance-other_radius*other_radius)/(2*radius*distance)
            if not -1. < cosine < 1.:
                raise ValueError('Non-proper Circle intersection angle')
            center_angle = math.atan2(dy,dx); spread = math.acos(cosine)
            for angle in (center_angle-spread,center_angle+spread):
                angle %= 2*math.pi
                if angle < EPS or 2*math.pi-angle < EPS:
                    raise ValueError('Intersection on reference-axis seam is not captured')
                cuts.append({'angle_radians':angle,'other_native_circle_object_id':other['object_id'],
                             'other_native_circle_tag':other['entity_tag']})
        cuts.sort(key=lambda item:item['angle_radians'])
        if len(cuts) not in (2,4) or any(b['angle_radians']-a['angle_radians'] < EPS for a,b in zip(cuts,cuts[1:])):
            raise ValueError('Uncaptured or coincident Circle intersection partition')
        result[curve['entity_tag']] = {'source':curve,'derived_intersections':cuts}
    return result


def _point(source, angle):
    cx,cy,cz = source['center_cm']; radius=source['radius_cm']
    return [cx+radius*math.cos(angle),cy+radius*math.sin(angle),cz]


def _cached_samples(candidate):
    curve=candidate['stored_curve_geometry']
    if curve['kind'] != 'ellipse-curve' or not math.isclose(curve['stored_axis_ratio'],1.,abs_tol=EPS):
        raise ValueError('Named cached portion is not the observed circular primitive')
    normal,major=curve['normal'],curve['stored_reference_axis']
    minor=[normal[1]*major[2]-normal[2]*major[1],normal[2]*major[0]-normal[0]*major[2],normal[0]*major[1]-normal[1]*major[0]]
    start,end=candidate['stored_edge_parameter_interval']
    if not all(math.isfinite(value) for value in (start,end)) or not 0 < end-start < 2*math.pi:
        raise ValueError('Named cached circular portion interval outside observed bounded family')
    return [[origin+a*math.cos(parameter)+b*math.sin(parameter)
             for origin,a,b in zip(curve['raw_origin'],major,minor)]
            for parameter in (start,(start+end)/2,end)]


def decode_profile_circle_portions(data, records, features, member, members, body_identifier_summary):
    base=decode_trimmed_profiles(data,records,features,member,members,body_identifier_summary,
                                 profile_loops_reader=read_circle_portion_loops)
    decoded=[];unresolved=list(base['unresolved'])
    for cached in base['decoded']:
        try:
            row=copy.deepcopy(cached)
            sketches=[feature for feature in features if feature['kind']=='Sketch' and feature['sketch_object_id']==row['native_sketch_object_id']]
            if len(sketches)!=1:
                raise ValueError('Derived Circle source Sketch missing/ambiguous')
            partitions=_circle_partitions(sketches[0],row['source_curves'])
            topology=decode_topology(inspect_asm(members[row['history_blob_member']]))
            graphs=[graph for graph in topology['body_graphs'] if graph['body_index']==row['asm_body_index']]
            if len(graphs)!=1 or graphs[0]['body_transform_is_identity'] is not True:
                raise ValueError('Derived Circle/cache comparison requires observed identity BODY transform')
            portions=[]
            for source in row['source_curves']:
                refs=source.get('stored_profile_references') or [source['stored_profile_reference']]
                partition=partitions[source['native_entity_tag']]
                geometry=partition['source'];cuts=partition['derived_intersections'];count=len(cuts)
                for ref in refs:
                    ordinal,stored_count=ref['stored_reference_selector_pair']
                    if stored_count!=count:
                        raise ValueError('Stored portion-count selector differs from derived proper intersection count')
                    if ordinal==1:
                        start,end=cuts[-1]['angle_radians'],cuts[0]['angle_radians']+2*math.pi
                    else:
                        start,end=cuts[ordinal-2]['angle_radians'],cuts[ordinal-1]['angle_radians']
                    points=[_point(geometry,angle) for angle in (start,(start+end)/2,end)]
                    candidates=[candidate for candidate in source['cached_coedge_candidates']
                                if candidate['stored_decimal_text_fields']==ref['stored_coedge_text_fields']]
                    if not candidates:
                        raise ValueError('Derived portion has no full-tuple qualified cached candidate')
                    evidence=[]
                    for candidate in candidates:
                        observed=_cached_samples(candidate)
                        endpoint_error=max(min(math.dist(point,other) for other in (observed[0],observed[2])) for point in (points[0],points[2]))
                        midpoint_error=math.dist(points[1],observed[1])
                        if endpoint_error>EPS or midpoint_error>EPS:
                            raise ValueError('Derived source Circle portion disagrees with a full-tuple named cached boundary')
                        evidence.append({'coedge_record_index':candidate['coedge_record_index'],
                                         'edge_record_index':candidate['edge_record_index'],
                                         'max_endpoint_set_error_cm':endpoint_error,'midpoint_error_cm':midpoint_error})
                    portions.append({'native_source_circle_object_id':source['native_entity_object_id'],
                                     'native_source_circle_tag':source['native_entity_tag'],
                                     'stored_profile_reference':ref,
                                     'geometry_status':'DerivedAnalyticSourceCirclePortion',
                                     'derivation':'Proper source Circle/Circle intersections, sorted about observed positive reference axis; portion1 crosses that seam, later portions follow increasing angle',
                                     'derived_portion_ordinal':ordinal,'derived_portion_count':count,
                                     'derived_reference_axis_angle_interval_radians':[start,end],
                                     'derived_sketch_local_points_cm':{'start':points[0],'midpoint':points[1],'end':points[2]},
                                     'all_full_tuple_cache_candidates_corroborate':evidence,
                                     'parameter_status':'Derived reference-axis angles; not serialized trim parameters, API Arc parameters or decoded traversal direction'})
            row.update(derived_source_circle_partitions=[{'native_circle_object_id':part['source']['object_id'],
                                                          'native_circle_tag':tag,'derived_intersections':part['derived_intersections']}
                                                         for tag,part in sorted(partitions.items())],
                       derived_source_portions=portions,
                       geometry_status='Bounded derived source Circle portions, independently corroborated by every full-tuple qualified cached boundary',
                       remaining_uncertainty=['General source frames/curve families, tangent/coincident intersections and seam intersections',
                                              'Uncaptured selector combinations/counts and repeated-source arrangements',
                                              'Stored direction flag/API traversal and serialized parameter conversion',
                                              'Historical/current geometry lifecycle, modified cached shape and persistent topology identity'])
            decoded.append(row)
        except (ValueError,KeyError,IndexError,TypeError,ArithmeticError) as error:
            unresolved.append({'source_feature_object_id':cached['source_feature_object_id'],'reason':str(error)})
    return {'decoded':decoded,'unresolved':unresolved,'scope':SCOPE}
