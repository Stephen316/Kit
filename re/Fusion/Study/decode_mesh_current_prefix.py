"""Literal alternate mesh prefix, admitted only by reciprocal current membership."""
import struct

from decode_mesh_contents import MESH,COLLECTION,COLLECTION_BASE,OWNER_BASE,COMPONENT_BASE,MESH_FEATURE,_require
from decode_sketch import reference

PREFIX=bytes.fromhex('00000100000000000000000100010000000000000000')


def decode_mesh_current_prefix(data,records,mesh_id,prefix):
    """Return opt-in prefix fields; retained/noncurrent sources keep the old error."""
    try:
        _require(prefix==PREFIX,'prefix')
        def typed(identity,guid,primary=True):
            rows=[r for r in records if r.object_id==identity and r.is_primary==primary and r.class_guid==guid]
            if primary:
                _require(len([r for r in records if r.object_id==identity and r.is_primary])==1,'identity')
            _require(len(rows)==1,'typed')
            record=rows[0];return record,data[record.body:record.end]
        mesh,body=typed(mesh_id,MESH)
        _require(body[:22]==prefix,'stored prefix')
        _,owner=typed(mesh_id,OWNER_BASE,False)
        _require(len(owner)==11,'owner fragment')
        collection_id=reference(owner,0)
        typed(collection_id,COLLECTION)
        _,collection=typed(collection_id,COLLECTION_BASE,False)
        _require(len(collection)==27 and collection[:5]==bytes(1)+struct.pack('<I',1)
                 and reference(collection,5)==mesh_id,'current counted membership')
        component_id=reference(collection,16)
        typed(component_id,'E03784ED-5E19-4E14-B9F2-3B07017018CD')
        typed(component_id,COMPONENT_BASE,False)
        feature_id=reference(body,489)
        _,feature=typed(feature_id,MESH_FEATURE)
        _require(feature[:6]==bytes(2)+struct.pack('<I',1) and reference(feature,6)==mesh_id,
                 'reciprocal native BaseMesh owner')
        return dict(stored_mesh_index=1,stored_prefix_11_22_hex=prefix[11:].hex(),
            prefix_scope='Literal alternate stored index1 prefix; current membership independently proven, no flag/visibility meanings',
            native_current_prefix_membership=dict(mesh_object_id=mesh_id,mesh_collection_object_id=collection_id,
                stored_current_collection_member_ids=[mesh_id],component_object_id=component_id,
                reciprocal_base_mesh_feature_object_id=feature_id,reciprocal_base_mesh_feature_class_guid=MESH_FEATURE,
                stored_prefix_hex=prefix.hex(),source_record_offset=mesh.start,
                association='Typed singleton counted current collection, component and reciprocal BaseMesh membership; no BaseFeature-to-source identity or lifecycle inference'))
    except (ValueError,KeyError,IndexError,struct.error,TypeError):
        raise ValueError('Unobserved opt-in native mesh prefix') from None
