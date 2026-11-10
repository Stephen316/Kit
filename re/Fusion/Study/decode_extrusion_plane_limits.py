"""Owned native Extrude construction-plane limits in the captured parallel family.

Native FromEntity/ToEntity controls remain literal. This proves selected plane
identity/component/definition/frame, without normalizing native controls into a
Distance feature or assigning general offset, chain or direction flag semantics.
"""
import copy
import math
import struct
import uuid

from decode_assembly import decode_assembly
from decode_dependencies import decode_dependencies
from decode_extrude import decode_extrude
from decode_parameters import decode_stream,read_string
from decode_placement import decode_placement
from decode_plane_definitions import decode_plane_definitions
from decode_selection import native_proxy_references,known_construction_entities,resolve_native_selection
from decode_sketch import decode_sketches,numbers,reference

EXTRUDE='DD405BC2-D673-44F0-8833-5CB2A1C186C7'
PROXY='2CA5A1CD-C99B-4C9B-91AF-57989148E841'
DESCRIPTOR='5A1BF548-241F-46FD-9FB5-E4B05126EB9D'
LEAF='90055C05-546C-4EE7-B3C9-3DD922AD0C9C'
PLANE='8D424E29-DE23-4B1F-A3AD-84C52A497D1A'
PLANE_FEATURE='D869265F-F339-4751-A066-91D30F81FF08'
HELPER='5FBE538E-139B-46D4-BCAF-CC796D1E1F78'
SUPPORT='6CCF41D5-40BE-48ED-A834-18F3EAED6C57'
COMPONENT='E03784ED-5E19-4E14-B9F2-3B07017018CD'
SCOPE=('Observed owned solid NewBody OneSided Extrude ToEntity/ProfilePlane or FromEntity/Distance '
    'selection of a same-component Offset construction plane, parallel/co-directed with native '
    'Sketch frame and stored extrusion vector. Native controls, opaque flags and contexts remain '
    'literal; analytic station derivation is separate and no general sign/chain/lifecycle/API identity is inferred.')


def qualify_extrusion_plane_limits(data,records,features,feature,settings):
    grouped={}
    for r in records:
        if r.is_primary:grouped.setdefault(r.object_id,[]).append(r)
    if any(len(rows)!=1 for rows in grouped.values()):
        raise ValueError('Extrude plane limit duplicate primary namespace')
    def typed(identity,guid):
        rows=grouped.get(identity,[])
        if len(rows)!=1 or rows[0].class_guid!=guid:
            raise ValueError('Extrude plane limit typed reference missing, ambiguous or wrong class')
        r=rows[0];return r,data[r.body:r.end]
    def raw(identity,guid):
        r,p=typed(identity,guid)
        return dict(object_id=identity,class_guid=guid,record_offset=r.start,body_offset=r.body,end_offset=r.end,payload_hex=p.hex())
    receiver=feature['object_id'];record,body=typed(receiver,EXTRUDE)
    from decode_basics import named_features,attach_parameters
    private=named_features(data,records);parameters,_=decode_stream(data,records)
    attach_parameters(data,records,private,parameters)
    decode_sketches(data,records,private);decode_placement(data,records,private)
    assembly=decode_assembly(data,records,private)
    rows=[f for f in private if f['object_id']==receiver]
    supplied=[f for f in features if f['object_id']==receiver]
    if len(rows)!=1 or len(supplied)!=1 or feature.get('record_offset')!=record.start:
        raise ValueError('Extrude plane limit fresh receiving metadata missing or ambiguous')
    fresh=rows[0];native,reasons=decode_extrude(body,fresh,allow_surface=True)
    if native!=settings or reasons!=['Referenced start/end geometry selection not decoded']:
        raise ValueError('Extrude plane limit native controls or expected selection diagnostic differ')
    extent,start=native['extent'],native['start'];one=extent['side_one']
    if (native['operation']['kind']!='NewBody' or native['is_solid'] is not True or extent['mode']!='OneSided'
            or native['stored_second_extent_enabled']!=0 or one.get('taper_angle_radians')!=0
            or any(not math.isfinite(v) for v in extent['stored_direction_vector'])):
        raise ValueError('Extrude plane limit requires solid untapered OneSided NewBody controls')
    if one['condition']=='ToEntity' and start['kind']=='ProfilePlane' and one['uninterpreted_flags']==1:
        operand_scope='side_one';offset=one['offset_cm'];selection_id=one['selection_record_object_id']
    elif (one['condition']=='Distance' and start['kind']=='FromEntity' and one['uninterpreted_flags']==0
            and math.isfinite(one['distance_cm']) and one['distance_cm']>0):
        operand_scope='start';offset=start['offset_cm'];selection_id=start['selection_record_object_id']
    else:
        raise ValueError('Extrude plane limit control combination outside observed family')
    if not math.isfinite(offset) or offset<0:
        raise ValueError('Extrude plane limit requires observed nonnegative selected-plane offset')
    definitions=decode_plane_definitions(data,records,private)
    selected=resolve_native_selection(data,records,selection_id,known_construction_entities(data,records,private))
    if selected is None or selected['entity']['kind']!='ConstructionPlane' or 'feature_object_id' not in selected['entity']:
        raise ValueError('Extrude plane limit must resolve to an owned construction plane')
    plane_id=selected['entity']['object_id'];owner=selected['entity']['feature_object_id']
    defs=[r for r in definitions['definitions'] if r['plane_object_id']==plane_id and r['feature_object_id']==owner]
    if (len(defs)!=1 or defs[0]['definition_kind']!='Offset' or defs[0]['stored_backend_method_code']!=2
            or defs[0]['stored_extra_offset_cm']!=0):
        raise ValueError('Extrude plane limit requires one explicit Offset plane definition with zero ExtraOffset')
    definition=defs[0];geometry=definition['cached_geometry']
    plane_record,plane=typed(plane_id,PLANE);_,plane_feature=typed(owner,PLANE_FEATURE)
    if (reference(plane_feature,19)!=plane_id or selected['entity']['origin_cm']!=geometry['origin_cm']
            or selected['entity']['normal']!=geometry['normal']):
        raise ValueError('Extrude plane limit selected native geometry/creator differs')
    # Complete owned singleton selector framing; opaque numeric trailer bytes are
    # retained without interpreting their values as IDs, time or flags.
    proxy_record,proxy=typed(selection_id,PROXY)
    descriptor_ids,props=native_proxy_references(data,proxy_record)
    if len(proxy)!=105 or props or len(descriptor_ids)!=1 or reference(proxy,94)!=receiver:
        raise ValueError('Extrude plane limit owned singleton proxy differs')
    descriptor_id=descriptor_ids[0];_,descriptor=typed(descriptor_id,DESCRIPTOR)
    if (len(descriptor)!=263 or descriptor[:2]!=bytes(2) or struct.unpack_from('<I',descriptor,13)[0]!=1
            or reference(descriptor,252)!=receiver):
        raise ValueError('Extrude plane limit descriptor prefix/count/owner differs')
    namespace,cursor=read_string(descriptor,17);entity_uuid,cursor=read_string(descriptor,cursor)
    uuid.UUID(namespace);uuid.UUID(entity_uuid)
    if cursor!=169 or len(namespace)!=36 or len(entity_uuid)!=36 or descriptor[169:181]!=struct.pack('<QI',2,1):
        raise ValueError('Extrude plane limit complete descriptor namespace/context frame differs')
    literal=bytes.fromhex('00000000050000000000000000000000000001010000')
    for payload,begin,helper_at,support_at,owner_at in ((proxy,34,68,82,94),(descriptor,192,226,240,252)):
        if (payload[begin:begin+22]!=literal or payload[begin+30:begin+34]!=b'\1\1\0\0'
                or payload[helper_at+11:support_at]!=b'\1\0\0' or payload[support_at+11:owner_at]!=b'\0'):
            raise ValueError('Extrude plane limit complete selector trailer markers differ')
        _,helper=typed(reference(payload,helper_at),HELPER)
        if helper!=bytes.fromhex('0001000000000000000000000000'):
            raise ValueError('Extrude plane limit selector helper payload differs')
    secondary_id=reference(proxy,23);_,secondary=typed(secondary_id,'2DF7DA30-A4E4-4260-AFD1-D9C7154CB44B')
    if secondary!=bytes.fromhex('0000010100'):
        raise ValueError('Extrude plane limit proxy secondary payload differs')
    def support(identity,entries,repeated):
        _,payload=typed(identity,SUPPORT)
        n=len(entries)
        if (len(payload)!=39+19*n or payload[:12]!=bytes(6)+b'\1\1'+struct.pack('<I',n)
                or [reference(payload,12+19*i) for i in range(n)]!=entries
                or reference(payload,12+19*n)!=repeated or payload[-8:]!=bytes(8)):
            raise ValueError('Extrude plane limit support entries/repeated backlink differ')
        return raw(identity,SUPPORT)
    proxy_support=support(reference(proxy,82),[descriptor_id],selection_id)
    descriptor_support=support(reference(descriptor,240),[owner,descriptor_id],descriptor_id)
    leaf_id=reference(descriptor,2);_,leaf=typed(leaf_id,LEAF)
    if len(leaf)!=10 or leaf[:2]!=bytes(2) or struct.unpack_from('<Q',leaf,2)[0]!=plane_id:
        raise ValueError('Extrude plane limit direct typed plane leaf differs')
    context_id=reference(descriptor,181);_,context=typed(context_id,'CC54ECAD-6DE8-4DE1-803D-BBE0E751975B')
    frame=geometry['origin_cm']+geometry['x_axis']+geometry['y_axis']
    if len(context)!=87 or context[:3]!=bytes(3) or numbers(context,3,9)!=frame or context[75]!=1:
        raise ValueError('Extrude plane limit explicit context frame differs from selected native plane')
    link_id=reference(context,76);_,link=typed(link_id,'CB4F4CC2-9D6F-48BA-9B1F-20C1992C9C9C')
    if len(link)!=14 or link[:2]!=bytes(2) or link[-1]!=0:
        raise ValueError('Extrude plane limit context link framing differs')
    context_leaf_id=reference(link,2);_,context_leaf=typed(context_leaf_id,LEAF)
    if context_leaf!=leaf:
        raise ValueError('Extrude plane limit context/direct leaf plane identities differ')
    collection_id=reference(plane,len(plane)-11)
    _,collection=typed(collection_id,'A8635B5F-1E2C-45FD-8BA9-0173B0FEB75E')
    if (len(collection)!=73 or collection[:6]!=bytes(2)+struct.pack('<I',1)
            or reference(collection,6)!=plane_id or collection[17:47]!=bytes.fromhex('000000000100000000000000000000000101011400000000000000000000')
            or struct.unpack_from('<I',collection,47)[0]!=1 or reference(collection,51)!=plane_id
            or reference(plane,181)!=collection_id or reference(plane,201)!=owner):
        raise ValueError('Extrude plane limit repeated plane collection/creator backlinks differ')
    component=reference(collection,62);typed(component,COMPONENT)
    support_input=definition['support_inputs']
    if len(support_input)!=1 or support_input[0]['entity']['kind']!='ConstructionPlane':
        raise ValueError('Extrude plane limit Offset origin-plane support differs')
    origin=support_input[0]['entity']['native_entity'];origin_id=origin['object_id']
    _,origin_plane=typed(origin_id,PLANE)
    container_id=origin['origin_container_object_id'];_,container=typed(container_id,'2972A3B8-3627-49BC-8C3D-18707605EC44')
    if (len(container)!=96 or container[:8]!=bytes(4)+struct.pack('<I',7)
            or len({reference(container,8+11*i) for i in range(7)})!=7
            or [reference(container,8+11*i) for i in range(7)].count(origin_id)!=1
            or reference(origin_plane,len(origin_plane)-11)!=container_id or reference(container,85)!=component):
        raise ValueError('Extrude plane limit origin support/container/component route differs')
    scalar=definition['scalar_parameters']
    if len(scalar)!=1 or scalar[0]['role']!='AlongDistance' or not math.isfinite(scalar[0]['value']):
        raise ValueError('Extrude plane limit Offset definition scalar differs')
    expected=[o+scalar[0]['value']*n for o,n in zip(origin['origin_cm'],origin['normal'])]
    if (any(not math.isfinite(v) for v in expected) or math.dist(expected,geometry['origin_cm'])>1e-10
            or any(math.dist(geometry[k],origin[k])>1e-10 for k in ('normal','x_axis','y_axis'))):
        raise ValueError('Extrude plane limit native Offset scalar/support/frame consistency differs')
    # Match the fresh owned profile Sketch by explicit decimal-ID namespace. No
    # geometry or target-cache surface is used to select this native input.
    profiles=[]
    for rows in grouped.values():
        r=rows[0]
        if r.class_guid=='4BD53E5A-0B3E-45E5-AE8B-02044306485A':
            p=data[r.body:r.end]
            if reference(p,len(p)-11)==receiver:profiles.append(p)
    if len(profiles)!=1:
        raise ValueError('Extrude plane limit source profile descriptor ambiguous')
    _,cursor=read_string(profiles[0],17);sketch_text,_=read_string(profiles[0],cursor)
    sketches=[s for s in private if s['kind']=='Sketch' and str(s['sketch_object_id'])==sketch_text]
    if len(sketches)!=1:
        raise ValueError('Extrude plane limit source Sketch unresolved')
    sketch=sketches[0];matrix=sketch['placement']['sketch_to_component_matrix']
    axis=[matrix[2],matrix[6],matrix[10]];normal=geometry['normal'];direction=extent['stored_direction_vector']
    values=geometry['origin_cm']+normal+direction+axis
    if (any(not math.isfinite(v) for v in values) or not math.isclose(math.hypot(*normal),1.,abs_tol=1e-10)
            or math.dist(axis,normal)>1e-10 or math.dist(axis,direction)>1e-10):
        raise ValueError('Extrude plane limit native planes/vector outside parallel co-directed component frame')
    profile_origin=[matrix[3],matrix[7],matrix[11]]
    separation=sum(n*(p-o) for n,p,o in zip(normal,geometry['origin_cm'],profile_origin))
    if not math.isfinite(separation) or separation<=0:
        raise ValueError('Extrude plane limit selected plane intersection not strictly forward from profile')
    dependencies=[dict(object_id=i) for i in (receiver,owner,sketch['object_id'])]
    decode_dependencies(data,records,dependencies,assembly)
    if (sketch.get('component_object_id')!=component or any(f.get('component_object_id')!=component
            or 'component_scope_object_id' not in f for f in dependencies)):
        raise ValueError('Extrude plane limit receiver/plane/Sketch dependency components differ')
    native_ids=[(selection_id,PROXY),(descriptor_id,DESCRIPTOR),(leaf_id,LEAF),(context_id,'CC54ECAD-6DE8-4DE1-803D-BBE0E751975B'),
        (link_id,'CB4F4CC2-9D6F-48BA-9B1F-20C1992C9C9C'),(context_leaf_id,LEAF),(secondary_id,'2DF7DA30-A4E4-4260-AFD1-D9C7154CB44B'),
        (plane_id,PLANE),(owner,PLANE_FEATURE),(definition['backend_object_id'],'7B6C3C2D-4096-4E6D-B225-699E8C2D9355'),
        (collection_id,'A8635B5F-1E2C-45FD-8BA9-0173B0FEB75E'),(origin_id,PLANE),(container_id,'2972A3B8-3627-49BC-8C3D-18707605EC44')]
    derived_geometry=copy.deepcopy(geometry)
    derived_geometry.update(origin_cm=expected,normal=origin['normal'],x_axis=origin['x_axis'],y_axis=origin['y_axis'],
        input_geometry_scope='Derived native origin-plane frame plus owned Offset AlongDistance scalar; stored selected-plane frame independently corroborated')
    limit=dict(operand_scope=operand_scope,selection=selected,plane_definition=definition,plane_native_geometry=derived_geometry,
        stored_plane_geometry=geometry,
        native_selection_record_object_id=selection_id,descriptor_object_id=descriptor_id,context_object_id=context_id,
        context_identity_link_object_id=link_id,context_identity_leaf_object_id=context_leaf_id,
        proxy_support=proxy_support,descriptor_support=descriptor_support,native_records=[raw(i,g) for i,g in native_ids],
        opaque_proxy_numeric_trailer_hex=proxy[56:64].hex(),opaque_descriptor_numeric_trailer_hex=descriptor[214:222].hex(),
        native_selected_offset_cm=offset,raw_extent_flags=one['uninterpreted_flags'],
        frame_relation=dict(profile_plane_origin_cm=profile_origin,sketch_normal_component=axis,stored_extrusion_direction=direction,
            selected_plane_normal=normal,derived_forward_plane_separation_cm=separation,
            scope='Native component mathematical frame relation after explicit source/plane identity; general offset sign convention not inferred'))
    return dict(feature_object_id=receiver,limits=[limit],component_provenance=dict(component_object_id=component,
        plane_collection_object_id=collection_id,origin_container_object_id=container_id,dependency_scopes=dependencies),
        native_controls_unchanged=True,derived_distance_controls=None,scope=SCOPE)
