"""Captured Circle/Circle tangent-distance geometry caches, without side enums.

Structured copies and contact/projection coordinates are checked against explicit
source roles. Native selector bytes remain opaque; no nearest/farthest API flag
mapping or general tangent-dimension solver is inferred from invariant settings.
"""

import math
import struct

from decode_dimension_controls import TANGENT, decode_dimension_controls
from decode_sketch import constraint_prefix, numbers, same

CIRCLE = 'F0130424-8B7E-4092-93C9-1CA807482534'
HEADER = struct.pack('<IddI',2,0.,1.,2)
SCOPE = 'Observed separated horizontal XY Circle/Circle TangentDistance source copies, stored contact/projection points, repeated anchor and distance cache; native side flags unresolved'


def decode_tangent_dimension_caches(data, records, features, dimension_controls=None):
    """Return decoded/unresolved without mutation; call after annotation reader.

    Pass the existing dimension_controls summary to avoid repeating its binding,
    expression, target and owner validation. Only successfully decoded matching
    annotations are eligible; new output adds geometry-cache details alone.
    """
    if dimension_controls is None:
        dimension_controls=decode_dimension_controls(data,records,features)
    grouped={}
    for r in records:
        if r.is_primary:
            grouped.setdefault(r.object_id,[]).append(r)
    primary={i:rs[0] for i,rs in grouped.items() if len(rs)==1}
    annotation_groups={}
    for a in dimension_controls['decoded']:
        annotation_groups.setdefault(a['object_id'],[]).append(a)
    annotations={i:rs[0] for i,rs in annotation_groups.items() if len(rs)==1}
    decoded,unresolved=[],[]
    for sketch in features:
        if sketch['kind']!='Sketch':
            continue
        geometry={g['object_id']:g for g in sketch.get('geometry',[])}
        for dimension in sketch.get('dimensions',[]):
            r=primary.get(dimension['object_id'])
            if r is None or r.class_guid!=TANGENT:
                continue
            try:
                identity=r.object_id;a=annotations.get(identity)
                if (dimension['kind']!='TangentDistance' or a is None or a['class_guid']!=TANGENT
                        or a['binding_object_id']!=dimension['binding_object_id']
                        or a['entity_ids']!=dimension['entity_ids']
                        or a['sketch_object_id']!=sketch['sketch_object_id']):
                    raise ValueError('Tangent cache requires validated matching annotation/binding/owner/target roles')
                b=data[r.body:r.end];inputs,props,c=constraint_prefix(b)
                targets=dimension['entity_ids']
                if (props!={'EntityGenesis':0} or len(inputs)!=3 or inputs[0]!=0 or inputs[1:]!=targets
                        or len(targets)!=2 or len(set(targets))!=2
                        or [struct.unpack_from('<I',b,16+15*i)[0] for i in range(3)] not in ([4,0,0],[12,0,0])):
                    raise ValueError('Unsupported tangent cache dependency/attribute framing')
                if b[c:c+24]!=HEADER or b[c+216:c+218]!=b'\0\1' or b[c+314]!=0:
                    raise ValueError('Unobserved tangent geometry cache header/control bytes')
                if a['value_expression_offset']-r.body < c+366:
                    raise ValueError('Tangent geometry block overlaps bounded annotation expression')
                sources=[]
                copies=[]
                for index,source_id in enumerate(targets):
                    source=geometry.get(source_id);typed=primary.get(source_id)
                    if (source is None or source['kind']!='Circle' or typed is None or typed.class_guid!=CIRCLE
                            or source['sketch_object_id']!=sketch['sketch_object_id']):
                        raise ValueError('Only captured explicit same-sketch Circle/Circle tangent inputs supported')
                    values=numbers(b,c+24+96*index,12)
                    expected=(source['center_cm']+source['normal']+source['reference_axis']
                              +[source['radius_cm'],0.,2*math.pi])
                    if (not same(values,expected) or source['radius_cm']<=0
                            or not same(source['normal'],[0.,0.,1.])
                            or not same(source['reference_axis'],[1.,0.,0.])
                            or not math.isclose(source['center_cm'][2],0.,abs_tol=1e-9)):
                        raise ValueError('Tangent ordered full-circle copy disagrees with explicit source or XY scope')
                    sources.append(source)
                    copies.append({'source_entity_object_id':source_id,'source_role_index':index,
                        'body_relative_offset':c+24+96*index,'kind':'FullCircle',
                        'center_cm':values[:3],'normal':values[3:6],'reference_axis':values[6:9],
                        'radius_cm':values[9],'start_angle_radians':values[10],'end_angle_radians':values[11]})
                first,second=sources
                center_distance=second['center_cm'][0]-first['center_cm'][0]
                if (center_distance<=first['radius_cm']+second['radius_cm']
                        or not math.isclose(first['center_cm'][1],second['center_cm'][1],abs_tol=1e-9)):
                    raise ValueError('Only captured separated horizontal positively ordered circle centers supported')
                projection_points=[numbers(b,c+218+24*i,3) for i in range(2)]
                contact_points=[numbers(b,c+266+24*i,3) for i in range(2)]
                distance=numbers(b,c+315,1)[0];anchor=numbers(b,c+323,3)
                expected_contacts=[
                    [second['center_cm'][0]+second['radius_cm'],second['center_cm'][1],0.],
                    [first['center_cm'][0]-first['radius_cm'],first['center_cm'][1],0.]]
                if not all(same(x,y) for x,y in zip(contact_points,expected_contacts)) or not same(anchor,contact_points[1]):
                    raise ValueError('Tangent stored contact/anchor points disagree with captured source-role geometry')
                actual_distance=math.dist(contact_points[0],contact_points[1])
                if (distance<=0 or not math.isclose(distance,dimension['value_cm'],abs_tol=1e-9)
                        or not math.isclose(actual_distance,distance,abs_tol=1e-9)):
                    raise ValueError('Tangent contact distance disagrees with native cache/bound parameter')
                annotation=a['annotation_position_cm']
                expected_projection=[[p[0],annotation[1],0.] for p in contact_points]
                if not all(same(x,y) for x,y in zip(projection_points,expected_projection)):
                    raise ValueError('Tangent stored projection points disagree with contacts and annotation line')
                decoded.append({'object_id':identity,'kind':'TangentDistanceGeometryCache',
                    'sketch_object_id':sketch['sketch_object_id'],'binding_object_id':dimension['binding_object_id'],
                    'entity_ids':targets,'stored_dependency_extras':[struct.unpack_from('<I',b,16+15*i)[0] for i in range(3)],
                    'dependency_extra_scope':'Raw captured values only; first placeholder slot meaning unresolved',
                    'coordinate_system':'sketch-local','coordinate_units':'cm',
                    'source_geometry_copies':copies,
                    'stored_contact_points_cm':contact_points,
                    'stored_contact_source_entity_ids':[targets[1],targets[0]],
                    'stored_measurement_line_points_cm':projection_points,
                    'stored_repeated_anchor_cm':anchor,'cached_distance_cm':distance,
                    'uninterpreted_header_hex':b[c:c+24].hex(),
                    'uninterpreted_pre_contact_control_hex':b[c+216:c+218].hex(),
                    'uninterpreted_post_contact_control_byte':b[c+314],
                    'side_selector_status':'All captured API creation side arguments are False/False; native byte-to-side mapping unproven and deliberately not returned',
                    'geometry_consistency':{'ordered_circle_copies_match_explicit_sources':True,
                        'stored_contacts_on_their_source_circles':True,
                        'contact_distance_matches_bound_parameter':True,
                        'projection_points_match_contacts_and_annotation_line':True,
                        'identity_scope':'IDs assigned from explicit ordered dimension inputs before geometry validation; no coordinate-based source assignment'},
                    'scope':SCOPE})
            except (ValueError,KeyError,IndexError,struct.error) as error:
                unresolved.append({'object_id':r.object_id,'kind':'TangentDimensionGeometryCache','reason':str(error)})
    return {'decoded':decoded,'unresolved':unresolved,'scope':SCOPE,
            'limitations':'No new tangent-side enum, driving/annotation flag decoding, rotated/overlapping circle support, line/point/arc input variants or solver regeneration'}
