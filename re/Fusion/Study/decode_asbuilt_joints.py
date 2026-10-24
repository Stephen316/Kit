"""Observed root As-built Rigid/Revolute/Slider native associations and caches.

Shared native joint motion semantics stay in decode_joints. Typed feature and
occurrence/context references establish identity before numeric cache checks.
No kinematic solve, general joint geometry or solved world placement is claimed.
"""
from collections import Counter
import math
import struct
import uuid

from decode_assembly import OCCURRENCE_GUID, occurrence, collection as occurrence_collection
from decode_dependencies import decode_dependencies
from decode_extrude import optional_reference
from decode_joints import JOINT, COLLECTION, FRAME, ROUTE, ROUTE_WRAPPER, parse_native_joint_motion
from decode_parameters import read_string
from decode_placement import IDENTITY, rigid_matrix, transform_point
from decode_selection import native_origin_entities
from decode_sketch import numbers, reference, same

ASBUILT='AA8B3D40-B67D-4AF1-B3CF-E1E00279B5F0'
GEOMETRY='7B6C3C2D-4096-4E6D-B225-699E8C2D9355'
POINT='69EE2FA7-BCC7-449E-9CA9-976CEFDFED44'
DESCRIPTOR='5A1BF548-241F-46FD-9FB5-E4B05126EB9D'
FRAME_LINK='549FBB80-B890-473E-A5C0-415D3D9BF4E6'
MATRIX1_PREFIX=bytes.fromhex('00000000030100000002000000010200000000000000000101000000010300000000000000000000')
SCOPE='Observed same-root As-built rigid/revolute/slider occurrence associations, native motion/limit bindings and point-origin geometry caches; no joint solve or world-placement claim'


def _matrix_variant(payload,marker_offset):
    if payload[marker_offset:marker_offset+1]!=b'\1' or payload[marker_offset+1:marker_offset+41]!=MATRIX1_PREFIX:
        raise ValueError('Unsupported As-built native joint matrix marker/prefix')
    start=marker_offset+41
    matrix=rigid_matrix(numbers(payload,start,16))
    footer=start+128
    name,end=read_string(payload,footer+39)
    if end+12!=len(payload):
        raise ValueError('As-built marker1 matrix/footer extent does not meet counted name')
    return dict(stored_context_matrix=matrix,footer_offset=footer,
        matrix_layout_details=dict(stored_marker=1,stored_opaque_prefix_hex=MATRIX1_PREFIX.hex(),
            stored_matrix_relative_offset=start,stored_opaque_footer_byte_count=39,
            prefix_scope='Exact captured forty-byte prefix retained; no semantics assigned to embedded numeric coincidences'))


def make_asbuilt_context_readers(data,records,assembly,*,allow_nested=False):
    """Shared typed readers; two-level occurrence routes require explicit opt-in."""
    records=list(records)
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    primary={i:rs[0] for i,rs in grouped.items() if len(rs)==1}
    occurrences=assembly['native_occurrences']
    def typed(identity,guid):
        record=primary.get(identity)
        if record is None or record.class_guid!=guid:
            raise ValueError('As-built typed reference missing/ambiguous/wrong class: '+str(identity))
        return record,data[record.body:record.end]
    def text_uuid(payload,cursor):
        value,end=read_string(payload,cursor)
        if len(value)!=36:raise ValueError('Unsupported As-built route UUID length')
        uuid.UUID(value);return value,end
    def native_occurrence(identity):
        record,_=typed(identity,OCCURRENCE_GUID)
        matches=[o for o in occurrences if o['object_id']==identity]
        if record.payload_start is None or len(matches)!=1:
            raise ValueError('As-built native occurrence summary absent or ambiguous')
        actual=occurrence(data[record.payload_start:record.end],identity)
        if any(matches[0].get(k)!=v for k,v in actual.items()):
            raise ValueError('As-built typed occurrence disagrees with assembly summary')
        return actual
    def frame(identity,owner,footer_mode):
        _,payload=typed(identity,FRAME)
        if (len(payload) not in (78,206) or payload[:20]!=bytes(20)
                or payload[20:37]!=struct.pack('<I',3)+bytes(13)):
            raise ValueError('Unsupported As-built frame prefix/extent')
        link_id=reference(payload,37);typed(link_id,FRAME_LINK)
        if payload[48]==1 and len(payload)==78:matrix,cursor=list(IDENTITY),49
        elif payload[48]==0 and len(payload)==206:matrix,cursor=rigid_matrix(numbers(payload,49,16)),177
        else:raise ValueError('Unsupported As-built frame matrix encoding')
        if (payload[cursor]!=0 or reference(payload,cursor+1)!=owner
                or payload[cursor+23:]!=struct.pack('<I',footer_mode)+bytes(2)):
            raise ValueError('As-built frame owner/footer differs')
        wrapper_id=reference(payload,cursor+12);_,wrapper=typed(wrapper_id,ROUTE_WRAPPER)
        expected_wrapper=bytes.fromhex('00000101000000' if footer_mode==2 else '00000001000000')
        if len(wrapper)!=18 or wrapper[:7]!=expected_wrapper:
            raise ValueError('Unsupported As-built one-route wrapper')
        route_id=reference(wrapper,7);_,route=typed(route_id,ROUTE)
        if route[:2]!=bytes(2):raise ValueError('Unsupported As-built route prefix')
        mode=struct.unpack_from('<I',route,2)[0]
        instance,cursor=text_uuid(route,6)
        context_namespace=context_entity=None
        nested_path=None
        if mode==1 and len(route)==406:
            context_namespace,cursor=text_uuid(route,cursor);context_entity,cursor=text_uuid(route,cursor)
            if route[cursor:cursor+8]!=struct.pack('<Q',2):raise ValueError('Unsupported As-built populated route marker')
            cursor+=8
            matches=[o for o in occurrences if o['instance_guid_text']==instance]
        elif mode==2 and len(route)==482 and allow_nested and footer_mode==2:
            child_instance,cursor=text_uuid(route,cursor)
            context_namespace,cursor=text_uuid(route,cursor);context_entity,cursor=text_uuid(route,cursor)
            if route[cursor:cursor+8]!=struct.pack('<Q',2):
                raise ValueError('Unsupported nested As-built route marker')
            cursor+=8
            parents=[o for o in occurrences if o['instance_guid_text']==instance]
            matches=[o for o in occurrences if o['instance_guid_text']==child_instance]
            if len(parents)!=1 or len(matches)!=1:
                raise ValueError('Nested As-built occurrence UUID path is absent or ambiguous')
            parent=native_occurrence(parents[0]['object_id']);child=native_occurrence(matches[0]['object_id'])
            parent_collection_id=child['parent_collection_object_id']
            listing_record,_=typed(parent_collection_id,'904F885E-D859-4755-A7EF-6EBED8732FAD')
            listing=occurrence_collection(data[listing_record.body:listing_record.end],parent_collection_id)
            if (listing['component_object_id']!=parent['component_object_id']
                    or child['object_id'] not in listing['occurrence_object_ids']):
                raise ValueError('Nested As-built child does not belong to explicitly routed parent component')
            nested_path=dict(stored_occurrence_uuid_path=[instance,child_instance],
                native_occurrence_object_id_path=[parent['object_id'],child['object_id']],
                parent_occurrence_collection_object_id=parent_collection_id)
        elif mode==0 and len(route)==258:
            if instance!=str(uuid.UUID(int=0)) or route[cursor:cursor+12]!=struct.pack('<IQ',0,1):
                raise ValueError('Unsupported As-built root route marker')
            cursor+=12
            matches=[o for o in occurrences if o['parent_collection_object_id'] is None]
        else:raise ValueError('Unsupported As-built route mode/extent')
        namespace,cursor=text_uuid(route,cursor);endpoint,cursor=text_uuid(route,cursor)
        if (route[cursor:]!=struct.pack('<QI',2,0) or (mode and context_namespace!=namespace)
                or len(matches)!=1):
            raise ValueError('As-built route namespace/occurrence/footer ambiguous')
        occurrence_row=native_occurrence(matches[0]['object_id'])
        result=dict(object_id=identity,frame_link_object_id=link_id,route_wrapper_object_id=wrapper_id,
            route_object_id=route_id,stored_route_mode=mode,stored_occurrence_uuid_text=instance,
            context_namespace_text=context_namespace,context_entity_guid_text=context_entity,
            terminal_namespace_text=namespace,terminal_entity_guid_text=endpoint,
            native_occurrence_object_id=occurrence_row['object_id'],component_object_id=occurrence_row['component_object_id'],
            stored_context_matrix=matrix,stored_footer_mode=footer_mode,
            association='Owned typed frame/route with unique native occurrence UUID (or explicit null root route) with internally repeated route namespace; other UUID fields retained literal')
        if nested_path is not None:
            result.update(nested_path)
            result['association']='Owned typed two-level UUID route with independently framed parent/child occurrences and reciprocal child collection membership; other UUID fields remain literal'
        return result

    return dict(primary=primary,typed=typed,native_occurrence=native_occurrence,frame=frame,text_uuid=text_uuid)


def decode_asbuilt_joints(data,records,assembly,features):
    records=list(records)
    candidates=[r for r in records if r.is_primary and r.class_guid==ASBUILT]
    output=dict(decoded=[],unresolved=[],scope=SCOPE,
        placement_limitation='Native occurrence/context/geometry caches do not establish joint-solved placement; no kinematic solve applied')
    if not candidates:return output
    readers=make_asbuilt_context_readers(data,records,assembly)
    primary,typed=readers['primary'],readers['typed']
    native_occurrence,frame,text_uuid=readers['native_occurrence'],readers['frame'],readers['text_uuid']
    feature_map={f['object_id']:f for f in features}
    known=native_origin_entities(data,records)
    for record in candidates:
        try:
            if primary.get(record.object_id) is not record:raise ValueError('As-built feature primary identity ambiguous')
            feature=feature_map.get(record.object_id)
            if feature is None or feature['record_offset']!=record.start or feature['class_guid']!=ASBUILT:
                raise ValueError('As-built caller feature identity missing or stale')
            owner=record.object_id;body=data[record.body:record.end]
            if body[:2]!=bytes(2):raise ValueError('Unsupported As-built feature prefix')
            geometry_id,cursor=optional_reference(body,2)
            root_frame_id=reference(body,cursor);cursor+=11
            limit_count=struct.unpack_from('<I',body,cursor)[0];cursor+=4
            if limit_count>2:raise ValueError('Unsupported As-built enabled limit count')
            limit_ids=[reference(body,cursor+11*i) for i in range(limit_count)];cursor+=11*limit_count
            if len(set(limit_ids))!=limit_count or struct.unpack_from('<I',body,cursor)[0]!=2:
                raise ValueError('As-built requires exactly two ordered context frames')
            context_ids=[reference(body,cursor+4+11*i) for i in range(2)];cursor+=26
            joint_id=reference(body,cursor);cursor+=11
            nil,cursor=text_uuid(body,cursor)
            if nil!=str(uuid.UUID(int=0)) or body[cursor:cursor+3]!=bytes(3):
                raise ValueError('Unsupported As-built explicit UUID/separator')
            cursor+=3;count=struct.unpack_from('<I',body,cursor)[0];cursor+=4
            if count>5:raise ValueError('Unsupported As-built repeated input count')
            repeated=[reference(body,cursor+11*i) for i in range(count)];cursor+=11*count
            if body[cursor:cursor+4]!=b'\xff'*4:raise ValueError('Unsupported As-built feature label prefix')
            label,end=read_string(body,cursor+4);index=struct.unpack_from('<Q',body,end)[0];name,tail=read_string(body,end+8)
            if label!='As-built' or index!=feature['stored_index'] or name or len(body)-tail!=76:
                raise ValueError('Unsupported As-built feature label/footer extent')
            _,joint=typed(joint_id,JOINT)
            if joint[:5]!=bytes.fromhex('0102000000') or joint[35]!=0:
                raise ValueError('Unsupported As-built common native joint prefix')
            member_ids=[reference(joint,5),reference(joint,20)]
            if len(set(member_ids))!=2:raise ValueError('As-built native joint member identities coincide')
            member_fields=[struct.unpack_from('<I',joint,p)[0] for p in(16,31)]
            members=[native_occurrence(i) for i in member_ids]
            motion=parse_native_joint_motion(joint,joint_id,matrix_decoder=_matrix_variant)
            kind=motion['joint_type']
            if kind not in ('Rigid','Revolute','Slider') or (geometry_id is None)!=(kind=='Rigid'):
                raise ValueError('Unobserved As-built motion/optional geometry combination')
            footer=motion['footer_offset'];footer_size=39 if 'matrix_layout_details' in motion else 79
            joint_name,end=read_string(joint,footer+footer_size)
            if end+12!=len(joint) or joint[end]!=0:
                raise ValueError('As-built common joint name/footer extent disagrees')
            collection_id=reference(joint,end+1);_,collection=typed(collection_id,COLLECTION)
            if (len(collection)!=38 or collection[:6]!=bytes(6) or collection[10:12]!=b'\1\0'
                    or struct.unpack_from('<I',collection,6)[0]!=1
                    or struct.unpack_from('<I',collection,12)[0]!=1 or reference(collection,16)!=joint_id):
                raise ValueError('As-built native joint collection membership differs')
            component_id=reference(collection,27)
            typed(component_id,'E03784ED-5E19-4E14-B9F2-3B07017018CD')
            contexts=[frame(i,owner,2) for i in context_ids]
            if any(c['stored_route_mode']!=1 for c in contexts) or set(c['native_occurrence_object_id'] for c in contexts)!=set(member_ids):
                raise ValueError('As-built ordered context routes differ from explicit native joint members')
            root_frame=frame(root_frame_id,owner,0)
            if root_frame['stored_route_mode']!=0 or root_frame['component_object_id']!=component_id or not same(root_frame['stored_context_matrix'],IDENTITY):
                raise ValueError('As-built parent frame is not the observed root identity route')
            parent_ids=[]
            for member in members:
                parent_id=member['parent_collection_object_id'];pr,_=typed(parent_id,'904F885E-D859-4755-A7EF-6EBED8732FAD')
                parent=occurrence_collection(data[pr.body:pr.end],parent_id)
                if parent['component_object_id']!=component_id or member['object_id'] not in parent['occurrence_object_ids']:
                    raise ValueError('As-built occurrence is not explicitly in same parent component collection')
                parent_ids.append(parent_id)
            if len(set(parent_ids))!=1:raise ValueError('As-built occurrences have different parent collections')
            scope_owners=[{'object_id':owner}];decode_dependencies(data,records,scope_owners,assembly)
            if scope_owners[0].get('component_object_id')!=component_id or 'component_scope_object_id' not in scope_owners[0]:
                raise ValueError('As-built feature dependency scope differs from joint parent component')
            parameters={p['binding_object_id']:p for p in feature['parameters']}
            limits=[]
            for identity in limit_ids:
                _,binding=typed(identity,'D91D429C-1BB5-4640-B49F-69AF14F463E9');parameter=parameters.get(identity)
                if (len(binding)!=85 or reference(binding,5)!=owner or reference(binding,48)!=owner
                        or reference(binding,74)!=owner or parameter is None
                        or not math.isclose(numbers(binding,21,1)[0],parameter['raw_float64'],abs_tol=1e-12)):
                    raise ValueError('As-built enabled limit binding owner/value disagrees')
                limits.append(dict(binding_object_id=identity,role=parameter['role'],value=parameter['raw_float64']))
            expected=[]
            for item in motion['motion_limits']:
                prefix='Rotate' if item['limit_kind']=='rotationLimits' else 'Slide'
                for field,suffix in(('minimum','Minimum'),('maximum','Maximum'),('rest','Rest')):
                    if item[field+'_enabled']:expected.append((prefix+suffix,item[field+'_value']))
            if Counter((p['role'],p['value']) for p in limits)!=Counter(expected):
                raise ValueError('As-built enabled native limit bindings differ from shared motion cache')
            geometry=None
            if geometry_id is None:
                if repeated or not same(contexts[0]['stored_context_matrix'],motion['stored_context_matrix']) or not same(contexts[1]['stored_context_matrix'],IDENTITY):
                    raise ValueError('As-built Rigid repeated inputs/context cache copies differ')
            else:
                _,g=typed(geometry_id,GEOMETRY)
                if (len(g)!=332 or g[:37]!=bytes(36)+b'\1' or g[48:57]!=bytes(9)
                        or g[185:233]!=bytes(35)+struct.pack('<Q',20)+bytes(1)+struct.pack('<I',1)
                        or reference(g,321)!=owner):
                    raise ValueError('Unsupported As-built point geometry backend framing/owner')
                method_id=reference(g,37);_,method=typed(method_id,'0F38E3C4-2E39-470B-A4FD-D3187224FB9F')
                if method!=bytes(7):raise ValueError('Unsupported As-built point geometry method literal')
                transform=rigid_matrix(numbers(g,57,16));point_id=reference(g,233);_,point=typed(point_id,POINT)
                if (len(point)!=198 or point[:47]!=bytes(47) or struct.unpack_from('<I',point,47)[0]!=10
                        or numbers(point,51,3)!=[-1.,-1.,-1.] or struct.unpack_from('<I',point,75)[0]!=1
                        or struct.unpack_from('<I',point,112)[0]!=1 or reference(point,187)!=owner):
                    raise ValueError('Unsupported As-built point-provider198 framing/owner')
                descriptor_id=reference(point,79);_,descriptor=typed(descriptor_id,DESCRIPTOR)
                if (len(descriptor)!=263 or descriptor[:2]!=bytes(2) or struct.unpack_from('<I',descriptor,13)[0]!=1
                        or reference(descriptor,252)!=owner):
                    raise ValueError('As-built point descriptor owner/count differs')
                namespace,c=text_uuid(descriptor,17);entity_guid,c=text_uuid(descriptor,c)
                leaf_id=reference(descriptor,2);_,leaf=typed(leaf_id,'90055C05-546C-4EE7-B3C9-3DD922AD0C9C')
                if len(leaf)!=10 or leaf[:2]!=bytes(2):raise ValueError('Unsupported As-built point native leaf')
                point_native_id=struct.unpack_from('<Q',leaf,2)[0];native=known.get(point_native_id)
                if native is None or native['kind']!='ConstructionPoint':raise ValueError('As-built selected native origin point unresolved')
                container_id=native['origin_container_object_id'];_,container=typed(container_id,'2972A3B8-3627-49BC-8C3D-18707605EC44')
                n=struct.unpack_from('<I',container,4)[0]
                if (container[:4]!=bytes(4) or n!=7 or len(container)!=19+11*n
                        or [reference(container,8+11*i) for i in range(n)].count(point_native_id)!=1):
                    raise ValueError('As-built source point native component-origin membership differs')
                point_component=reference(container,len(container)-11)
                point_root=frame(reference(point,90),owner,0);point_source=frame(reference(point,101),owner,0)
                if (point_root['stored_route_mode']!=0 or point_root['component_object_id']!=component_id
                        or point_source['stored_route_mode']!=1 or point_source['component_object_id']!=point_component
                        or point_source['native_occurrence_object_id']!=contexts[0]['native_occurrence_object_id']
                        or point_source['context_namespace_text']!=namespace or point_source['context_entity_guid_text']!=entity_guid
                        or point_root['terminal_namespace_text']!=root_frame['terminal_namespace_text']
                        or point_root['terminal_entity_guid_text']!=root_frame['terminal_entity_guid_text']
                        or not same(point_root['stored_context_matrix'],IDENTITY)
                        or not same(point_source['stored_context_matrix'],transform)):
                    raise ValueError('As-built geometry source point/context/parent route association differs')
                if (repeated!=[geometry_id,point_id,descriptor_id]+limit_ids
                        or not same(contexts[0]['stored_context_matrix'],IDENTITY)
                        or not same(contexts[1]['stored_context_matrix'],motion['stored_context_matrix'])):
                    raise ValueError('As-built nonrigid repeated inputs/context cache copies differ')
                geometry=dict(backend_object_id=geometry_id,method_object_id=method_id,point_provider_object_id=point_id,
                    descriptor_object_id=descriptor_id,terminal_object_id=leaf_id,native_origin_point=native,
                    component_object_id=point_component,origin_container_object_id=container_id,
                    namespace_text=namespace,entity_guid_text=entity_guid,
                    stored_geometry_transform=transform,stored_source_point_context=point_source,stored_parent_point_context=point_root,
                    cached_origin_from_source_point=transform_point(transform,native['position_cm']),
                    stored_point_provider_mode=10,uninterpreted_point_provider_vector=[-1.,-1.,-1.],
                    opaque_geometry_backend_tail_hex=g[244:321].hex(),opaque_point_provider_tail_hex=point[112:187].hex(),
                    geometry_scope='Typed native point source and owned context/backend transform cache; provider sentinel vector is not the source point position, API JointGeometry axis conventions and general origins are not inferred')
            output['decoded'].append(dict(feature_object_id=owner,feature_class_guid=ASBUILT,object_id=joint_id,name=joint_name,
                collection_object_id=collection_id,component_object_id=component_id,
                component_scope_object_id=scope_owners[0]['component_scope_object_id'],
                joint_type=kind,api_joint_type_code=motion['api_joint_type_code'],stored_joint_type_code=motion['stored_joint_type_code'],
                motion_limits=motion['motion_limits'],direction_codes=motion['direction_codes'],
                enabled_limit_bindings=limits,enabled_limit_binding_object_ids=limit_ids,
                ordered_occurrence_contexts=contexts,root_context=root_frame,
                stored_occurrence_member_object_ids=member_ids,stored_occurrence_member_fields=member_fields,
                stored_context_matrix=motion['stored_context_matrix'],
                stored_matrix_layout_details=motion.get('matrix_layout_details'),
                stored_opaque_joint_footer_hex=joint[footer:footer+footer_size].hex(),
                stored_repeated_input_object_ids=repeated,source_geometry=geometry,
                is_suppressed=None,suppression_scope='Actual API captures are unsuppressed; native As-built suppression encoding is not qualified by this stage',
                opaque_feature_state_footer_hex=body[tail:].hex(),scope=SCOPE,
                placement_limitation=output['placement_limitation']))
        except (ValueError,UnicodeError,IndexError,KeyError,struct.error) as error:
            output['unresolved'].append(dict(feature_object_id=record.object_id,class_guid=ASBUILT,reason=str(error)))
    return output
