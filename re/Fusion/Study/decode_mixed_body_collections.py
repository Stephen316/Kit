"""Typed BODY subsets of observed mixed Mesh/BRep CD57 collection tables.

Both stored collection roles remain component-related. Forward mesh membership
is not a mesh owner, render list, visibility or lifecycle assignment.
"""
import struct

from decode_body_properties import BODY, COLLECTION
from decode_component_display_colors import PREFIX_REFERENCE_CLASSES
from decode_extrude import optional_reference
from decode_mesh_contents import MESH, COMPONENT_BASE
from decode_parameters import read_string
from decode_sketch import reference

COMPONENT='E03784ED-5E19-4E14-B9F2-3B07017018CD'
MAPPING='74CA4562-59F8-4C97-8AD1-F8297C21F9AA'
HISTORY_CONTEXT='372234A0-2A6C-4122-8047-E74DBA04F326'
BODY_CONTEXT='40DCC3F41D-E94F-B3B1-3E95-9B6ABE572C'
AUXILIARY='E55D0457-898F-4A8E-B1A5-C85BDBA8794F'
SCOPE=('Observed mixed Mesh/BRep CD57 first-member tables and independently counted typed BODY tails, '
       'qualified by native component reference, role-specific mapping/context backlinks and reciprocal '
       'BODY ownership. Mesh entries remain forward memberships only; no rendering, current/final '
       'visibility, mesh ownership, geometry or lifecycle inference.')


def decode_mixed_body_collections(data,records,assembly,body_properties=None):
    """Return decoded/unresolved/scope; compatible BODY-tail-only collection plus patches.

    body_properties is accepted for caller compatibility; output does not depend
    on names, prior errors or whether qualified ownership patches were applied.
    """
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    components={}
    for component in assembly['components']:
        components.setdefault(component['object_id'],[]).append(component)
    def typed(identity,guid=None):
        rows=grouped.get(identity,[])
        if len(rows)!=1 or (guid is not None and rows[0].class_guid!=guid):
            raise ValueError('Mixed collection typed identity missing, ambiguous or wrong class')
        record=rows[0];return record,data[record.body:record.end]
    def ref(value):return b'\1'+struct.pack('<Q',value)+bytes(2)
    def text(value):return struct.pack('<I',len(value))+value.encode('utf-16le')
    def optional_auxiliary(identity,owner):
        if identity is None:return None
        record,payload=typed(identity,AUXILIARY)
        if len(payload)<30 or payload[:6]!=bytes(6) or payload[25]!=0:
            raise ValueError('Mixed collection auxiliary counted framing unsupported')
        stored_literal=struct.unpack_from('<Q',payload,6)[0]
        count=struct.unpack_from('<I',payload,26)[0]
        if count>100000 or len(payload)!=30+8*count or reference(payload,14)!=owner:
            raise ValueError('Mixed collection auxiliary count/owner backlink disagrees')
        return dict(object_id=identity,class_guid=AUXILIARY,record_offset=record.start,
            stored_count=count,stored_uint64_at_6=stored_literal,stored_uint64_values=list(struct.unpack_from('<'+str(count)+'Q',payload,30)) if count else [],
            payload_hex=payload.hex(),scope='Bounded counted array and owner only; leading uint64 and array values carry no assigned identity meaning')
    def mapping_fields(identity,owner,body_ids,alternate=False):
        record,payload=typed(identity,BODY_CONTEXT if alternate else MAPPING)
        start=17 if alternate else 6
        if payload[:2]!=bytes(2) or len(payload)<start+16:
            raise ValueError('Mixed collection mapping/context prefix unsupported')
        leading=None
        if alternate:
            leading_id=reference(payload,2);leading_record,leading_payload=typed(leading_id,AUXILIARY)
            if leading_payload!=bytes(20):
                raise ValueError('Mixed body context leading typed auxiliary framing unsupported')
            leading=dict(object_id=leading_id,record_offset=leading_record.start,payload_hex=leading_payload.hex())
        count=struct.unpack_from('<I',payload,start-4)[0]
        if count>100000 or start+16*count+16>len(payload):
            raise ValueError('Mixed collection mapping/context count exceeds bounds')
        pairs=[struct.unpack_from('<QQ',payload,start+16*i) for i in range(count)]
        cursor=start+16*count
        if (reference(payload,cursor)!=owner or payload[cursor+11]!=0
                or len({a for a,b in pairs})!=count or len({b for a,b in pairs})!=count
                or {b for a,b in pairs}!=set(body_ids) or count!=len(body_ids)):
            raise ValueError('Mixed collection mapping/context BODY IDs or owner disagree')
        filename,end=read_string(payload,cursor+12)
        suffix='.smb' if alternate else '.smbh'
        if (end!=len(payload) or (count==0 and filename!='') or (count>0 and
                (not filename.startswith('BREP.') or not filename.endswith(suffix) or '/' in filename or '\\' in filename))):
            raise ValueError('Mixed collection mapping/context filename extent unsupported')
        replay=(bytes(2)+(ref(leading['object_id']) if alternate else b'')+struct.pack('<I',count)
            +b''.join(struct.pack('<QQ',*pair) for pair in pairs)+ref(owner)+b'\0'+text(filename))
        if replay!=payload:raise ValueError('Mixed collection mapping/context byte replay disagrees')
        return dict(object_id=identity,class_guid=record.class_guid,record_offset=record.start,
            native_body_object_ids=[b for a,b in pairs],stored_uint64_body_pairs=[list(pair) for pair in pairs],
            owner_collection_object_id=owner,stored_filename=filename,leading_auxiliary=leading,
            payload_hex=payload.hex(),exact_full_payload_replay=True,
            scope='Explicit typed BODY IDs and collection backlink only; no ASM root, asset existence, stored-handle namespace or lifecycle assignment')
    def component_reference(component_id,collection_id,alternate):
        record,payload=typed(component_id,COMPONENT)
        rows=components.get(component_id,[])
        if len(rows)!=1:raise ValueError('Mixed collection assembly component absent or ambiguous')
        if alternate:
            if len(payload)<228 or payload[:11]!=bytes.fromhex('000100000000010000803f'):
                raise ValueError('Mixed alternate collection component primary prefix unsupported')
            preceding_id=reference(payload,195);following_id=reference(payload,217)
            preceding_record,preceding=typed(preceding_id,'AD3F9695-7FDF-4708-AE05-B21309CDE969')
            typed(following_id,'91461D14-4F77-44B2-9E79-8B052566D9CE')
            if len(preceding)!=23 or reference(preceding,12)!=component_id or reference(payload,206)!=collection_id:
                raise ValueError('Mixed alternate collection component primary reference/backlink disagrees')
            if payload[195:228]!=ref(preceding_id)+ref(collection_id)+ref(following_id):
                raise ValueError('Mixed alternate component three-reference replay disagrees')
            return dict(method='Typed primary COMPONENT observed reference206 with typed adjacent references and owner backlink',
                component_record_offset=record.start,reference_relative_offset=206,reference_offset=record.body+206,
                framed_prefix_hex=payload[:11].hex(),typed_reference_run_offset=record.body+195,
                typed_reference_run_hex=payload[195:228].hex(),preceding_record_object_id=preceding_id,
                following_record_object_id=following_id,preceding_owner_backlink_offset=preceding_record.body+12)
        bases=[r for r in records if not r.is_primary and r.object_id==component_id and r.class_guid==COMPONENT_BASE]
        if len(bases)!=1:raise ValueError('Mixed history collection inherited COMPONENT definition ambiguous')
        base=bases[0];body=data[base.body:base.end]
        if base.payload_start is None or base.body!=base.payload_start+4 or data[base.payload_start:base.body]!=bytes(4):
            raise ValueError('Mixed history collection indexed COMPONENT prefix unsupported')
        cursor=0;links=[]
        for slot in range(5):
            if slot==2:
                if list(struct.unpack_from('<4d',body,cursor))!=[-1.]*4:
                    raise ValueError('Mixed history collection COMPONENT scalar prefix unsupported')
                cursor+=32
            target=reference(body,cursor);target_record,target_body=typed(target,PREFIX_REFERENCE_CLASSES[slot])
            if reference(target_body,len(target_body)-11)!=component_id:
                raise ValueError('Mixed history collection COMPONENT reference owner backlink disagrees')
            links.append(dict(slot=slot,object_id=target,class_guid=target_record.class_guid,reference_relative_offset=cursor))
            cursor+=11
        if cursor!=87 or links[-1]['object_id']!=collection_id:
            raise ValueError('Mixed history collection COMPONENT slot76 reference differs')
        return dict(method='Framed inherited COMPONENT typed slot4 reference76 and reciprocal owner',
            component_base_record_offset=base.start,reference_relative_offset=76,reference_offset=base.body+76,
            framed_prefix_offset=base.payload_start,framed_prefix_hex=data[base.payload_start:base.body+cursor].hex(),
            prefix_references=links)

    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    for record in records:
        if not record.is_primary or record.class_guid!=COLLECTION:continue
        candidate=False
        try:
            body=data[record.body:record.end]
            if len(body)<11 or body[:3]!=bytes(3):continue
            count=struct.unpack_from('<I',body,7)[0]
            if count>100000 or 11+11*count>len(body):continue
            member_ids=[reference(body,11+11*i) for i in range(count)]
            candidate=any(len(grouped.get(i,[]))==1 and grouped[i][0].class_guid==MESH for i in member_ids)
            if not candidate:continue
            self_record,_=typed(record.object_id,COLLECTION)
            if (self_record.start,self_record.body,self_record.end)!=(record.start,record.body,record.end):
                raise ValueError('Mixed collection indexed record identity disagrees')
            if len(set(member_ids))!=count:raise ValueError('Mixed collection first membership repeats identity')
            mesh_ids=[];body_ids=[]
            for identity in member_ids:
                member,_=typed(identity)
                if member.class_guid==BODY:body_ids.append(identity)
                elif member.class_guid==MESH:mesh_ids.append(identity)
                else:raise ValueError('Mixed collection member has unsupported native class')
            cursor=11+11*count;middle_start=cursor
            if body[cursor]!=1:raise ValueError('Mixed collection middle marker unsupported')
            auxiliary_id,cursor=optional_reference(body,cursor+1)
            auxiliary=optional_auxiliary(auxiliary_id,record.object_id)
            backend_id=reference(body,cursor);backend,_=typed(backend_id);cursor+=11
            if backend.class_guid==MAPPING:
                alternate=False;role='StoredHistoryMapping74CA';mapping_id=backend_id
                if body[cursor]!=1:raise ValueError('Mixed history collection context marker unsupported')
                context_id=reference(body,cursor+1);cursor+=12
                context_record,context=typed(context_id,HISTORY_CONTEXT)
                if len(context)!=23 or context[:12]!=bytes(12):
                    raise ValueError('Mixed history collection typed context framing unsupported')
                context_component=reference(context,12)
                if body[cursor]!=0:raise ValueError('Mixed history collection tail separator unsupported')
                cursor+=1
            elif backend.class_guid==BODY_CONTEXT:
                alternate=True;role='StoredBodyContext40D';mapping_id=None;context_id=backend_id;context_component=None
                if body[cursor:cursor+3]!=bytes.fromhex('010000'):
                    raise ValueError('Mixed alternate collection tail separator unsupported')
                cursor+=3
            else:raise ValueError('Mixed collection backend has unsupported typed role')
            tail_start=cursor;tail_count=struct.unpack_from('<I',body,cursor)[0];cursor+=4
            if tail_count>100000 or len(body)!=cursor+11*tail_count+11:
                raise ValueError('Mixed collection BODY tail counted extent unsupported')
            tail_ids=[reference(body,cursor+11*i) for i in range(tail_count)];cursor+=11*tail_count
            component_id=reference(body,cursor);cursor+=11
            if tail_ids!=body_ids or len(set(tail_ids))!=tail_count or struct.unpack_from('<I',body,3)[0]!=tail_count:
                raise ValueError('Mixed collection typed BODY subset/count copies disagree')
            if member_ids==tail_ids:continue
            component_proof=component_reference(component_id,record.object_id,alternate)
            if not alternate and context_component!=component_id:
                raise ValueError('Mixed history context component backlink disagrees')
            backend_proof=mapping_fields(backend_id,record.object_id,body_ids,alternate)
            for identity in body_ids:
                native,payload=typed(identity,BODY)
                if reference(payload,len(payload)-11)!=record.object_id:
                    raise ValueError('Mixed collection native BODY owner backlink disagrees')
            middle=(b'\1'+(ref(auxiliary_id) if auxiliary_id is not None else b'\0')+ref(backend_id)
                +(bytes.fromhex('010000') if alternate else b'\1'+ref(context_id)+b'\0'))
            replay=(bytes(3)+struct.pack('<II',tail_count,count)+b''.join(ref(i) for i in member_ids)
                +middle+struct.pack('<I',tail_count)+b''.join(ref(i) for i in tail_ids)+ref(component_id))
            if replay!=body:raise ValueError('Mixed collection full payload replay disagrees')
            evidence='Typed BODY tail equals BODY subset of mixed stored membership; reciprocal native BODY/CD57 and framed native component references agree'
            component=components[component_id][0]
            collection=dict(object_id=record.object_id,class_guid=COLLECTION,component_object_id=component_id,
                component_name=component['name'],body_object_ids=body_ids,stored_field_at_3=tail_count,
                uninterpreted_middle_hex=body[middle_start:tail_start].hex())
            updates=[dict(object_id=i,collection_object_id=record.object_id,component_object_id=component_id,
                component_name=component['name'],ownership_evidence=evidence) for i in body_ids]
            result['decoded'].append(dict(object_id=record.object_id,class_guid=COLLECTION,role=role,
                collection=collection,body_ownership_updates=updates,component_object_id=component_id,
                mixed_member_object_ids=member_ids,mesh_member_object_ids=mesh_ids,body_member_object_ids=body_ids,
                mapping_record_object_id=mapping_id,context_record_object_id=context_id,
                auxiliary_record_object_id=auxiliary_id,auxiliary=auxiliary,component_reference=component_proof,
                backend=backend_proof,first_count_relative_offset=7,tail_count_relative_offset=tail_start,
                body_member_owner_backlink_offsets={str(i):typed(i,BODY)[0].end-11 for i in body_ids},
                stored_payload=dict(offset=record.body,end_offset=record.end,hex=body.hex(),exact_full_payload_replay=True),
                mesh_native_owner_assignment=None,rendering_semantics=None,current_final_lifecycle=None,scope=SCOPE))
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error) as error:
            if candidate:result['unresolved'].append(dict(object_id=record.object_id,kind='BodyCollection',reason=str(error)))
    return result
