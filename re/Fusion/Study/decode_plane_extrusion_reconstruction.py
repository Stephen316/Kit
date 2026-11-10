"""Selected native construction-plane limits for bounded solid Extrudes.

Native ToEntity/FromEntity controls are never rewritten. A separate mathematical
station adapter consumes fresh selected-plane provenance before the unchanged
complete Circle/prism cache corroborators inspect geometry.
"""
import copy
import struct

from asm_records import inspect_asm
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_brep import decode_topology
from decode_extrude import decode_extrude
from decode_extrusion_source_operands import EXTRUDE, qualify_extrusion_source_operands
from decode_extrusion_reconstruction import (_point, _vector, _near, _circle_cache,
    _rectangle_model, _rectangle_cache)
from decode_parameters import decode_stream
from decode_plane_extrusion_geometry import (plane_extrusion_stations,
    derive_plane_limited_circular_extrusion)

SCOPE=('Native owned construction-plane ToEntity/ProfilePlane or FromEntity/Distance '
       'zero-taper one-sided NewBody Extrude, in the observed co-directed +Z '
       'component family with nonnegative selected-plane offsets. Original '
       'control kinds/flags remain literal; separate mathematical stations '
       'derive complete circular or rectangular material corroborated against '
       'the identity-qualified stored BODY. No general reversed/oblique offset '
       'convention, selected BRep target, native UV, ENTITY/API/current/persistent '
       'identity, chronology or general regeneration is established.')


def _eligible(controls):
    extent=controls['extent']
    return (controls['start']['kind']=='FromEntity'
        or extent['side_one']['condition']=='ToEntity'
        or extent.get('side_two',{}).get('condition')=='ToEntity')


def decode_plane_extrusion_reconstruction(data,records,features,member,members,
        body_blob_bindings,body_selections=None):
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    candidates=[f for f in features if f.get('class_guid')==EXTRUDE]
    if not candidates:return result
    # The candidate gate also uses fresh native parameters. Caller annotations,
    # including prior tool settings, cannot invent or suppress selected limits.
    from decode_basics import named_features, attach_parameters
    private=named_features(data,records)
    parameters,_=decode_stream(data,records)
    attach_parameters(data,records,private,parameters)
    primary={};metadata={}
    for record in records:
        if record.is_primary:primary.setdefault(record.object_id,[]).append(record)
    for feature in private:metadata.setdefault(feature['object_id'],[]).append(feature)
    joined=None;cache={}
    for feature in candidates:
        identity=feature['object_id']
        try:
            rows=primary.get(identity,[]);fresh=metadata.get(identity,[])
            if len(rows)!=1 or rows[0].class_guid!=EXTRUDE or len(fresh)!=1:
                raise ValueError('Plane extrusion native receiving identity/metadata missing or ambiguous')
            record=rows[0]
            controls,_=decode_extrude(data[record.body:record.end],fresh[0],allow_surface=True)
            if not _eligible(controls):continue
            source=qualify_extrusion_source_operands(data,records,features,member,members,
                body_blob_bindings,feature,allow_plane_limits=True)
            if source is None or source['feature_object_id']!=identity or len(source['source_groups'])!=1:
                raise ValueError('Plane extrusion requires one freshly qualified native source BODY')
            group=source['source_groups'][0]
            if source['settings']!=controls or group['extrude_controls']!=controls:
                raise ValueError('Plane extrusion original native controls changed during qualification')
            provenance=source.get('plane_limit_provenance')
            if not provenance or provenance!=group.get('plane_limit_provenance'):
                raise ValueError('Plane extrusion fresh selected-plane provenance missing or inconsistent')
            planes={}
            for limit in provenance['limits']:
                role=limit['operand_scope'];geometry=limit['plane_native_geometry']
                if role in planes:raise ValueError('Plane extrusion repeated selected-plane operand role')
                planes[role]=dict(origin_cm=geometry['origin_cm'],normal=geometry['normal'])
            if joined is None:
                native=dict(decoded=[dict(mapping_record_object_id=m['mapping_record_object_id'],
                    owner_object_id=m['owner_object_id'],history_blob_member=m['history_blob_member'],body_count=m['body_count'],
                    bindings=[dict(stored_handle=b['stored_handle'],native_body_object_id=b['native_body_object_id'])
                        for b in m['bindings']]) for m in body_blob_bindings.get('decoded',[])])
                joined=decode_body_asm_identifiers(data,records,member,members,native)
            bindings=[(m,b) for m in joined['decoded'] for b in m['bindings']
                if b['native_body_object_id']==group['native_body_object_id']]
            if (len(bindings)!=1 or bindings[0][1]!=group['binding']
                    or bindings[0][0]['history_blob_member']!=group['history_blob_member']):
                raise ValueError('Plane extrusion fresh same-asset native BODY mapping differs')
            matrix=group['source_sketch']['placement']['sketch_to_component_matrix']
            axis=group['sketch_normal_component']
            _near(group['stored_direction_vector'],axis,'selected-plane native direction/component frame')
            _near(axis,[0.,0.,1.],'selected-plane observed positive component Z family')
            name=group['history_blob_member'];blob=members[name]
            if name not in cache:
                parsed=inspect_asm(blob);topology=decode_topology(parsed);cache[name]=(parsed,topology)
            parsed,topology=cache[name];nodes={n['index']:n for n in topology['nodes']}
            graphs=[g for g in topology['body_graphs'] if g['body_index']==group['asm_body_index']]
            if len(graphs)!=1:raise ValueError('Plane extrusion explicitly mapped BODY graph absent or ambiguous')
            graph=graphs[0]
            if group['native_profile_kind']=='Circle':
                circle=group['native_profile_circles'][0]
                derived=derive_plane_limited_circular_extrusion(_point(matrix,circle['center_cm']),axis,
                    _vector(matrix,circle['reference_axis']),circle['radius_cm'],controls,planes)
                corroboration=_circle_cache(graph,nodes,derived)
            elif group['native_profile_kind']=='FourLine':
                plane_origin=_point(matrix,[0.,0.,0.])
                station_proof=plane_extrusion_stations(plane_origin,axis,controls,planes)
                mathematical_group=copy.deepcopy(group)
                mathematical_group['extrude_controls']=station_proof['mathematical_equivalent_distance_controls']
                derived=_rectangle_model(mathematical_group,matrix,axis)
                derived.update(plane_limit_derivation=station_proof['plane_limit_derivation'],
                    mathematical_equivalent_distance_controls=station_proof['mathematical_equivalent_distance_controls'])
                corroboration=_rectangle_cache(graph,nodes,derived)
            else:raise ValueError('Plane extrusion complete native profile family unsupported')
            result['decoded'].append(dict(feature_object_id=identity,native_source_provenance=source,
                original_native_control_kinds=dict(start=controls['start']['kind'],side_one=controls['extent']['side_one']['condition']),
                source_native_body_object_id=group['native_body_object_id'],binding=group['binding'],
                history_blob_member=name,asm_body_index=group['asm_body_index'],derived_geometry=derived,
                native_cache_geometry_corroboration=corroboration,
                mathematical_effective_controls_scope='Constructed equivalent Distance inputs exist only in derived geometry; original native settings/provenance are unchanged',
                source_to_cache_entity_mapping=None,exact_API_handle_identity=None,
                qualified_historical_state=None,current_or_final_geometry_identity=None,scope=SCOPE))
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error,OverflowError) as error:
            result['unresolved'].append(dict(feature_object_id=identity,reason=str(error)))
    return result
