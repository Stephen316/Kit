"""Observed native type11 rigid-group membership and stored relative matrices.

RigidGroup shares As-built/JOINT classes with other constraints. Only explicit
native type11 qualifies this reader. No API JointType or solved placements are
invented, and includeChildren/suppression controls remain unresolved.
"""
import struct
import uuid

from decode_asbuilt_joints import ASBUILT, make_asbuilt_context_readers
from decode_assembly import collection as occurrence_collection
from decode_dependencies import decode_dependencies
from decode_extrude import optional_reference
from decode_joints import JOINT, COLLECTION
from decode_parameters import read_string
from decode_placement import IDENTITY,rigid_matrix
from decode_sketch import numbers,reference,same

MATRIX_TRAILER_SUFFIX=bytes.fromhex('0102000000000000000001010000000103000000000000000000')
SCOPE='Observed native type11 RigidGroup expanded occurrence membership, typed parent/child routes and copied relative matrix caches; includeChildren/suppression encoding and assembly solve unresolved'


def decode_rigid_groups(data,records,assembly,features):
    records=list(records)
    result=dict(decoded=[],unresolved=[],scope=SCOPE,
        placement_limitation='Stored occurrence/group context matrices are not joint-solved world placements; no kinematic solve applied')
    candidates=[r for r in records if r.is_primary and r.class_guid==ASBUILT]
    if not candidates:return result
    readers=make_asbuilt_context_readers(data,records,assembly,allow_nested=True)
    typed,frame,text_uuid=readers['typed'],readers['frame'],readers['text_uuid']
    native_occurrence=readers['native_occurrence'];primary=readers['primary']
    features_by={f['object_id']:f for f in features}
    for record in candidates:
        is_group=False
        try:
            if primary.get(record.object_id) is not record:raise ValueError('RigidGroup As-built identity ambiguous')
            body=data[record.body:record.end]
            if body[:2]!=bytes(2):raise ValueError('Unobserved RigidGroup As-built prefix')
            geometry_id,cursor=optional_reference(body,2)
            if geometry_id is not None:continue
            root_frame_id=reference(body,cursor);cursor+=11
            limits_count=struct.unpack_from('<I',body,cursor)[0];cursor+=4
            if limits_count!=0:continue
            count=struct.unpack_from('<I',body,cursor)[0];cursor+=4
            if not 1<=count<=1024:raise ValueError('RigidGroup context count exceeds framing bounds')
            context_ids=[reference(body,cursor+11*i) for i in range(count)];cursor+=11*count
            joint_id=reference(body,cursor);cursor+=11
            _,joint=typed(joint_id,JOINT)
            n=struct.unpack_from('<I',joint,1)[0]
            if not 1<=n<=1024 or len(joint)<5+15*n+1+28:
                raise ValueError('RigidGroup common member count exceeds framing bounds')
            code_offset=5+15*n+1+24
            code=struct.unpack_from('<I',joint,code_offset)[0]
            if code!=11:continue
            is_group=True
            if count!=n or n not in(2,3) or joint[0]!=1:
                raise ValueError('Unobserved RigidGroup feature/context/member count combination')
            feature=features_by.get(record.object_id)
            if feature is None or feature['record_offset']!=record.start or feature['class_guid']!=ASBUILT:
                raise ValueError('RigidGroup feature identity absent or stale')
            nil,cursor=text_uuid(body,cursor)
            if nil!=str(uuid.UUID(int=0)) or body[cursor:cursor+7]!=bytes(7):
                raise ValueError('RigidGroup nonempty repeated input list/UUID separator')
            cursor+=7
            if body[cursor:cursor+4]!=b'\xff'*4:raise ValueError('Unobserved RigidGroup As-built label prefix')
            label,end=read_string(body,cursor+4);index=struct.unpack_from('<Q',body,end)[0];name,tail=read_string(body,end+8)
            if label!='As-built' or index!=feature['stored_index'] or name or len(body)-tail!=76:
                raise ValueError('Unobserved RigidGroup feature label/footer extent')
            members=[reference(joint,5+15*i) for i in range(n)]
            member_fields=[struct.unpack_from('<I',joint,16+15*i)[0] for i in range(n)]
            if len(set(members))!=n or joint[5+15*n:code_offset]!=bytes(25):
                raise ValueError('RigidGroup native members duplicate or nonempty motion slots')
            prefix=struct.pack('<I',11)+bytes.fromhex('000100000000')+struct.pack('<I',n)+b'\0'
            if joint[code_offset:code_offset+15]!=prefix:
                raise ValueError('Unobserved RigidGroup native type/member-count prefix')
            pos=code_offset+15;matrices=[];trailers=[]
            for i in range(n-1):
                matrices.append(rigid_matrix(numbers(joint,pos,16)));pos+=128
                trailer=bytes(4)+b'\3'+struct.pack('<I',1)+struct.pack('<I',i+1)+MATRIX_TRAILER_SUFFIX+bytes([int(i==n-2)])
                if len(trailer)!=40 or joint[pos:pos+40]!=trailer:
                    raise ValueError('Unobserved RigidGroup matrix-copy trailer')
                trailers.append(joint[pos:pos+40].hex());pos+=40
            table_start=pos
            table=bytes(4)+b'\3'+struct.pack('<I',n-1)+b''.join(struct.pack('<I',i) for i in range(2,n+1))+MATRIX_TRAILER_SUFFIX
            if joint[pos:pos+len(table)]!=table:
                raise ValueError('Unobserved RigidGroup terminal counted matrix table')
            pos+=len(table);group_name,end=read_string(joint,pos)
            if end+12!=len(joint) or joint[end]!=0:
                raise ValueError('RigidGroup native name/collection footer extent differs')
            collection_id=reference(joint,end+1);_,listing=typed(collection_id,COLLECTION)
            if (len(listing)!=38 or listing[:6]!=bytes(6) or listing[10:12]!=b'\1\0'
                    or struct.unpack_from('<I',listing,6)[0]!=1 or struct.unpack_from('<I',listing,12)[0]!=1
                    or reference(listing,16)!=joint_id):
                raise ValueError('RigidGroup common joint collection membership differs')
            component_id=reference(listing,27);typed(component_id,'E03784ED-5E19-4E14-B9F2-3B07017018CD')
            contexts=[frame(i,record.object_id,2) for i in context_ids]
            if [c['native_occurrence_object_id'] for c in contexts]!=members:
                raise ValueError('RigidGroup ordered contexts differ from explicit expanded native members')
            if (n==2 and [c['stored_route_mode'] for c in contexts]!=[1,1]) or (n==3 and [c['stored_route_mode'] for c in contexts]!=[1,1,2]):
                raise ValueError('Unobserved RigidGroup member route shape')
            if n==3 and contexts[2]['native_occurrence_object_id_path']!=members[1:]:
                raise ValueError('RigidGroup nested child route does not match explicitly included parent')
            root=frame(root_frame_id,record.object_id,0)
            if root['stored_route_mode']!=0 or root['component_object_id']!=component_id or not same(root['stored_context_matrix'],IDENTITY):
                raise ValueError('RigidGroup parent frame differs from owned root component')
            for context in contexts[:2]:
                member=native_occurrence(context['native_occurrence_object_id'])
                owner=member['parent_collection_object_id'];r,_=typed(owner,'904F885E-D859-4755-A7EF-6EBED8732FAD')
                collection=occurrence_collection(data[r.body:r.end],owner)
                if collection['component_object_id']!=component_id or member['object_id'] not in collection['occurrence_object_ids']:
                    raise ValueError('RigidGroup direct occurrence lacks reciprocal parent component membership')
            scopes=[{'object_id':record.object_id}];decode_dependencies(data,records,scopes,assembly)
            if scopes[0].get('component_object_id')!=component_id or 'component_scope_object_id' not in scopes[0]:
                raise ValueError('RigidGroup native feature dependency scope differs from parent component')
            if (any(not same(m,c['stored_context_matrix']) for m,c in zip(matrices,contexts[:-1]))
                    or not same(contexts[-1]['stored_context_matrix'],IDENTITY)):
                raise ValueError('RigidGroup matrix list/ordered context copies disagree')
            result['decoded'].append(dict(feature_object_id=record.object_id,feature_class_guid=ASBUILT,
                object_id=joint_id,name=group_name,collection_object_id=collection_id,component_object_id=component_id,
                component_scope_object_id=scopes[0]['component_scope_object_id'],stored_constraint_type_code=11,
                occurrence_count=n,stored_occurrence_member_object_ids=members,stored_occurrence_member_fields=member_fields,
                ordered_occurrence_contexts=contexts,root_context=root,stored_relative_matrices=matrices,
                stored_matrix_trailers_hex=trailers,stored_terminal_matrix_table_hex=joint[table_start:pos].hex(),
                stored_terminal_matrix_table_count=n-1,stored_terminal_matrix_table_values=list(range(2,n+1)),
                matrix_scope='Exact copied group/context matrices; terminal table literals retained without claiming historical state, solved placement or general basis semantics',
                include_children=None,include_children_status='Expanded membership is explicit; add includeChildren request has no public getter and its native control encoding is not identified',
                is_suppressed=None,suppression_status='Requested True capture still returns actualFalse; no true/false native suppression contrast established',
                opaque_feature_state_footer_hex=body[tail:].hex(),scope=SCOPE,
                placement_limitation=result['placement_limitation']))
        except (ValueError,IndexError,KeyError,UnicodeError,struct.error) as error:
            if is_group:result['unresolved'].append(dict(feature_object_id=record.object_id,class_guid=ASBUILT,reason=str(error)))
    return result
