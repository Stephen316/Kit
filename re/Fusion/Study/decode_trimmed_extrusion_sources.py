"""Selected native profile portions for bounded NewBody Extrude construction.

Existing Circle/Line/Mixed readers own tuple grammars and native intersection
algorithms. Their cache corroboration is retained separately; only explicitly
native-derived portion parameters/points and source primitives enter mathematical
inputs. Underlying full curves are never substituted for selected portions.
"""
import copy
import math

from decode_profile_circle_portions import read_circle_portion_loops,decode_profile_circle_portions
from decode_profile_line_portions import read_line_portion_loops,decode_profile_line_portions
from decode_profile_mixed_portions import read_mixed_profile_loops,decode_profile_mixed_portions

SCOPE=('Observed selected Circle/Circle, Line/Line and Circle/Line native profile portions, '
    'full native tuple/source identity and rigid Sketch frame, zero-taper NewBody Distance '
    'Extrude; native-primitive-derived portion angles/fractions/points and mathematical '
    'inputs are separate from cache corroboration. Stored membership is not traversal; '
    'serialized/API parameters, lifecycle and persistent identities remain unresolved.')


def read_trimmed_extrusion_profile(body,descriptor_id,sketch):
    kinds=[g['kind'] for g in sketch['geometry'] if g['kind']!='Point']
    if kinds and all(k=='Circle' for k in kinds):
        loops=read_circle_portion_loops(body,descriptor_id,sketch);family='TrimmedCircleCircle'
    elif kinds and all(k=='Line' for k in kinds):
        loops=read_line_portion_loops(body,descriptor_id,sketch);family='TrimmedLineLine'
    elif sorted(kinds)==['Circle','Line']:
        loops=read_mixed_profile_loops(body,descriptor_id,sketch);family='TrimmedCircleLine'
    else:
        raise ValueError('Trimmed extrusion source primitive family is unsupported')
    return loops,family


def qualify_trimmed_extrusion_portions(data,records,features,member,members,mappings,group):
    owner=group['source_feature_object_id'];kind=group['native_profile_kind']
    decoder={'TrimmedCircleCircle':decode_profile_circle_portions,'TrimmedLineLine':decode_profile_line_portions,
        'TrimmedCircleLine':decode_profile_mixed_portions}.get(kind)
    if decoder is None:
        raise ValueError('Trimmed extrusion portion family unresolved')
    controls=group['extrude_controls'];extent=controls['extent'];side=extent['side_one']
    if (controls['operation']['kind']!='NewBody' or controls['is_solid'] is not True
            or controls['start']['kind']!='ProfilePlane' or extent['mode']!='OneSided'
            or controls['stored_second_extent_enabled']!=0 or side['condition']!='Distance'
            or side['uninterpreted_flags']!=0 or side.get('taper_angle_radians')!=0
            or not math.isfinite(side['distance_cm']) or side['distance_cm']<=0):
        raise ValueError('Trimmed extrusion requires captured positive untapered OneSided ProfilePlane NewBody Distance')
    sketch=group['source_sketch'];matrix=sketch['placement']['sketch_to_component_matrix']
    normal=[matrix[2],matrix[6],matrix[10]]
    if math.dist(normal,extent['stored_direction_vector'])>1e-10:
        raise ValueError('Trimmed extrusion stored direction differs from native component Sketch normal')
    selection=group['native_profile_selection']
    frame_proof=copy.deepcopy(group['source_sketch_frame_provenance'])
    frame_proof.update(sketch_to_component_matrix=copy.deepcopy(matrix),
        source_feature_object_id=owner,native_body_object_id=group['native_body_object_id'],
        coordinate_scope='Fresh native Sketch parent-component frame; no occurrence/world placement')
    def source_frame(candidate,row):
        if (candidate['object_id']!=sketch['object_id'] or candidate['sketch_object_id']!=selection['native_sketch_object_id']
                or candidate['placement']['sketch_to_component_matrix']!=matrix
                or row['source_feature_object_id']!=owner or row['native_body_object_id']!=group['native_body_object_id']
                or row['body_anchor_object_id']!=group['body_anchor_object_id']
                or row['asm_body_index']!=group['asm_body_index'] or row['history_blob_member']!=group['history_blob_member']
                or row['profile_loops']!=selection['profile_loops']):
            raise ValueError('Trimmed extrusion portion/source native identity or frame differs')
        return frame_proof
    selected=copy.deepcopy([f for f in features if f['kind']!='Extrude' or f['object_id']==owner])
    from decode_basics import sketch_references
    sketch_references(data,records,selected)
    result=decoder(data,records,selected,member,members,mappings,source_frame=source_frame)
    rows=[r for r in result['decoded'] if r['source_feature_object_id']==owner]
    if len(rows)!=1:
        reasons=[r['reason'] for r in result['unresolved'] if r['source_feature_object_id']==owner]
        raise ValueError('Trimmed extrusion complete native tuple/derived portion qualification unresolved: '+'; '.join(reasons))
    qualified=rows[0]
    if qualified['profile_loops']!=selection['profile_loops']:
        raise ValueError('Trimmed extrusion full tuple membership changed during portion derivation')
    primitives={g['object_id']:g for g in sketch['geometry'] if g['kind']!='Point'}
    references=[r for loop in selection['profile_loops'] for r in loop['curve_references']]
    portions,mathematical,cache_evidence=[],[],[]
    allowed=('native_source_circle_object_id','native_source_circle_tag','native_source_line_object_id',
        'native_source_line_tag','native_source_object_id','native_source_tag','native_source_kind',
        'stored_profile_reference','geometry_status','derivation','derived_portion_ordinal','derived_portion_count',
        'derived_reference_axis_angle_interval_radians','derived_native_start_end_fraction_interval',
        'derived_sketch_local_points_cm','derived_component_points_cm','native_line_endpoint_object_ids',
        'native_line_start_end_cm','parameter_status')
    for p in qualified['derived_source_portions']:
        ref=p['stored_profile_reference']
        identity=p.get('native_source_object_id',p.get('native_source_circle_object_id',p.get('native_source_line_object_id')))
        matches=[r for r in references if r['entity_id']==identity and r['stored_tuple_fields']==ref['stored_tuple_fields']]
        if len(matches)!=1:
            raise ValueError('Trimmed extrusion portion full native tuple is missing or ambiguous')
        primitive=primitives.get(identity)
        if primitive is None:
            raise ValueError('Trimmed extrusion derived portion native source identity is absent')
        role_key=str(identity)+':'+':'.join(map(str,ref['stored_tuple_fields']))
        geometry={k:copy.deepcopy(primitive[k]) for k in
            (('center_cm','radius_cm','normal','reference_axis') if primitive['kind']=='Circle' else ('start_cm','end_cm'))}
        interval=p.get('derived_reference_axis_angle_interval_radians',p.get('derived_native_start_end_fraction_interval'))
        if (interval is None or len(interval)!=2 or any(not math.isfinite(v) for v in interval) or interval[1]<=interval[0]
                or any(not math.isfinite(v) for point in p['derived_sketch_local_points_cm'].values() for v in point)
                or any(not math.isfinite(v) for point in p['derived_component_points_cm'].values() for v in point)):
            raise ValueError('Trimmed extrusion native-derived source portion is not finite/nondegenerate')
        if (not p['all_full_tuple_cache_candidates_corroborate'] or any(
                not math.isfinite(e[k]) for e in p['all_full_tuple_cache_candidates_corroborate']
                for k in ('max_endpoint_set_error_cm','midpoint_error_cm'))):
            raise ValueError('Trimmed extrusion cache corroboration residuals are not finite')
        native_portion={k:copy.deepcopy(p[k]) for k in allowed if k in p}
        native_portion.update(role_key=role_key,source_primitive_id=identity,
            geometry_input_scope='Derived only from fresh native primitives and full selector tuple; cached boundary coordinates excluded')
        portions.append(native_portion)
        mathematical.append(dict(role_key=role_key,source_primitive_id=identity,
            kind='CircleArc' if primitive['kind']=='Circle' else 'LineSegment',source_geometry=geometry,
            parameter_interval=copy.deepcopy(interval)))
        cache_evidence.append(dict(role_key=role_key,source_primitive_id=identity,
            all_full_tuple_cache_candidates_corroborate=copy.deepcopy(p['all_full_tuple_cache_candidates_corroborate'])))
    if len({p['role_key'] for p in mathematical})!=len(references) or len(portions)!=len(references):
        raise ValueError('Trimmed extrusion selected tuples do not bijectively cover derived source portions')
    return dict(native_profile_kind=kind,derived_source_portions=portions,mathematical_inputs=mathematical,
        profile_portion_cache_corroboration=dict(qualified_profile_cache=qualified,per_portion=cache_evidence,
            scope='Complete native tuple/name qualification and independent cache corroboration only; not mathematical input coordinates'),
        stored_profile_membership_order=[str(r['entity_id'])+':'+':'.join(map(str,r['stored_tuple_fields'])) for r in references],
        profile_membership_order_scope='Literal native selected reference order, not traversal or loop orientation',scope=SCOPE)
