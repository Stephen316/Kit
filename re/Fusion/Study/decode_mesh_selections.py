"""Bounded native mesh selection proxies, typed mesh pointers and identity leaves.

Only explicit variable references are interpreted. The invariant native mesh
prefix bytes that can resemble ref257 are deliberately outside this reader.
"""
import struct
import uuid

from decode_parameters import read_string
from decode_sketch import reference

PROXY='22975A91-16AD-4CC9-A5E4-B4F8B4C27881'
DESCRIPTOR='1AA9CC7B-5C34-45DA-AE14-0444E7F966F2'
MESH='EA90DA22-556C-4C61-89BB-20C2681B7A9D'
LEAF='90055C05-546C-4EE7-B3C9-3DD922AD0C9C'
SECONDARY='2DF7DA30-A4E4-4260-AFD1-D9C7154CB44B'


def decode_mesh_selection(data,records,proxy_id,feature_id):
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    def typed(identity,guid):
        rows=grouped.get(identity,[])
        if len(rows)!=1 or rows[0].class_guid!=guid:
            raise ValueError('Mesh selection typed reference missing, ambiguous or wrong class')
        record=rows[0];return record,data[record.body:record.end]
    _,proxy=typed(proxy_id,PROXY)
    if (len(proxy) not in(94,105) or proxy[:6]!=bytes(2)+struct.pack('<I',1)
            or proxy[17:19]!=bytes(2) or reference(proxy,len(proxy)-11)!=feature_id):
        raise ValueError('Unobserved mesh singleton proxy framing/owner')
    count=struct.unpack_from('<I',proxy,19)[0]
    if count not in(0,1) or len(proxy)!=94+11*count:
        raise ValueError('Unobserved mesh proxy secondary count/extent')
    secondary_id=reference(proxy,23) if count else None
    if count:
        _,secondary=typed(secondary_id,SECONDARY)
        if secondary!=bytes.fromhex('0000010100'):
            raise ValueError('Unobserved mesh proxy secondary literal payload')
    typed(reference(proxy,len(proxy)-37),'5FBE538E-139B-46D4-BCAF-CC796D1E1F78')
    typed(reference(proxy,len(proxy)-23),'6CCF41D5-40BE-48ED-A834-18F3EAED6C57')
    descriptor_id=reference(proxy,6);_,descriptor=typed(descriptor_id,DESCRIPTOR)
    if (len(descriptor)!=263 or descriptor[:2]!=bytes(2)
            or struct.unpack_from('<I',descriptor,24)[0]!=1
            or descriptor[180:196]!=struct.pack('<QII',2,0,0)
            or reference(descriptor,252)!=feature_id):
        raise ValueError('Unobserved mesh descriptor count/context/owner framing')
    mesh_id,leaf_id=reference(descriptor,2),reference(descriptor,13)
    typed(mesh_id,MESH);_,leaf=typed(leaf_id,LEAF)
    if len(leaf)!=10 or leaf[:2]!=bytes(2) or struct.unpack_from('<Q',leaf,2)[0]!=mesh_id:
        raise ValueError('Mesh descriptor direct pointer and typed identity leaf disagree')
    namespace,cursor=read_string(descriptor,28);identity,cursor=read_string(descriptor,cursor)
    if cursor!=180 or len(namespace)!=36 or len(identity)!=36:
        raise ValueError('Unobserved mesh descriptor counted namespace lengths')
    uuid.UUID(namespace);uuid.UUID(identity)
    typed(reference(descriptor,226),'5FBE538E-139B-46D4-BCAF-CC796D1E1F78')
    typed(reference(descriptor,240),'6CCF41D5-40BE-48ED-A834-18F3EAED6C57')
    return dict(proxy_object_id=proxy_id,descriptor_object_id=descriptor_id,mesh_object_id=mesh_id,leaf_object_id=leaf_id,
        owner_feature_object_id=feature_id,namespace_text=namespace,entity_guid_text=identity,
        stored_secondary_count=count,secondary_record_object_id=secondary_id,
        secondary_payload_hex=secondary.hex() if count else None,stored_descriptor_context_counts=[0,0],
        stored_proxy_trailer_hex=proxy[23+11*count:len(proxy)-11].hex(),
        stored_descriptor_trailer_hex=descriptor[196:252].hex(),
        association='Owned typed proxy/descriptor and matching direct mesh pointer plus bounded90055 mesh identity leaf',
        scope='Explicit native mesh selection identity only; optional secondary literal/context fields carry no geometry, lifecycle or solved-ownership semantics. Invariant mesh prefix numeric coincidences are not object links')
