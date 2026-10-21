"""Observed CloseHoles/StitchAndRemove controls with typed mesh/asset routes.

Inactive Density/Offset remain explicit stored ModelParameters, not active Repair
settings or proof of Rebuild behavior. Additional asset lifecycle is unassigned.
"""
import lzma
import math
import struct
import uuid

from decode_mesh_contents import MESH, MESH_FEATURE, _require
from decode_mesh_geometry_variants import decode_mesh_asset, decode_mesh_contents_variants
from decode_mesh_selections import decode_mesh_selection
from decode_parameters import decode_stream, read_string
from decode_sketch import reference
from decode_timeline import feature_state

REPAIR='68691143-5EE3-428E-9CD3-F728E4718559'
INTEGER_BINDING='A085449A-5144-4B2B-B455-7F7035A40559'
FLOAT_BINDING='D91D429C-1BB5-4640-B49F-69AF14F463E9'
PARAMETER='7A6A3D31-BE74-4E19-9115-20642944C2E4'
METHODS={0:'CloseHoles',1:'StitchAndRemove'}
SCOPE=('Observed MeshRepair CloseHoles/StitchAndRemove method, owned inactive Density/Offset ModelParameter '
       'bindings, current selected MeshBody and two typed assets. Rebuild mode/flags, additional methods, '
       'additional asset temporal role, general topology/lifecycle and procedural regeneration unresolved.')


def decode_mesh_repair(data,records,features,member,members,mesh_contents=None):
    """Return decoded/unresolved/scope; successful rows feature_object_id/kind/name/settings."""
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    candidates=[r for r in records if r.is_primary and r.class_guid==REPAIR]
    if not candidates:return result
    grouped,named={},{}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    for feature in features:named.setdefault(feature['object_id'],[]).append(feature)
    def typed(identity,guid):
        rows=grouped.get(identity,[])
        _require(len(rows)==1 and rows[0].class_guid==guid,'MeshRepair typed reference missing, ambiguous or wrong class')
        record=rows[0]
        return record,data[record.body:record.end]
    parameters,_=decode_stream(data,records)
    meshes=mesh_contents if mesh_contents is not None else decode_mesh_contents_variants(data,records,member,members)
    for record in candidates:
        try:
            typed(record.object_id,REPAIR)
            rows=named.get(record.object_id,[])
            _require(len(rows)==1 and rows[0].get('class_guid')==REPAIR and rows[0].get('record_offset')==record.start
                and rows[0].get('native_kind_label')=='MeshRepair','MeshRepair discovery metadata differs')
            feature=rows[0];owner=record.object_id
            body=data[record.body:record.end]
            _require(body[:2]==bytes(2) and body[24:28]==bytes(4) and body[54:58]==bytes(4)
                and body[69:70]==bytes(1),'Unobserved MeshRepair prefix/opaque controls/separators')
            method=struct.unpack_from('<I',body,28)[0]
            _require(method in METHODS,'Unsupported MeshRepair method code')
            bindings={'Density':reference(body,2),'Offset':reference(body,13)}
            _require(len(set(bindings.values()))==2,'MeshRepair inactive roles share a binding')
            scalars={}
            for role,binding_id in bindings.items():
                integer=role=='Density'
                binding,payload=typed(binding_id,INTEGER_BINDING if integer else FLOAT_BINDING)
                _require(len(payload)==(82 if integer else 85) and payload[:6]==bytes.fromhex('010100000001')
                    and all(reference(payload,offset)==owner for offset in (5,45 if integer else 48,len(payload)-11)),
                    'MeshRepair inactive scalar binding owner/framing differs: '+role)
                parameter_id=reference(payload,26 if integer else 29)
                parameter_record,_=typed(parameter_id,PARAMETER)
                if integer:_require(payload[21]==1,'MeshRepair Density integer tag differs')
                value=struct.unpack_from('<I',payload,22)[0] if integer else struct.unpack_from('<d',payload,21)[0]
                parsed=[p for p in parameters if p['role']==role and p.get('declared_binding_object_id')==binding_id
                    and p.get('parameter_object_id')==parameter_id and parameter_record.body<=p['role_offset']<parameter_record.end]
                attached=[p for p in feature.get('parameters',[]) if p.get('binding_object_id')==binding_id and p.get('role')==role]
                _require(len(parsed)==len(attached)==1 and math.isfinite(value) and parsed[0]['raw_float64']==value
                    and attached[0].get('parameter_object_id')==parameter_id and attached[0].get('raw_float64')==value,
                    'MeshRepair native/attached role/parameter/binding value copies disagree: '+role)
                p=parsed[0]
                _require((role,value,p['display_units']) in (('Density',128,''),('Offset',0.,'mm')),
                    'Unobserved inactive MeshRepair parameter family')
                scalars[role]=dict(binding_object_id=binding_id,parameter_object_id=parameter_id,
                    parameter_name=p['parameter_name'],stored_value=value,display_units=p['display_units'],
                    internal_units=p['internal_units'],value_representation='tagged_uint32' if integer else 'float64',
                    is_active=False,applicability='NotApplicable',
                    applicability_scope='Stored ModelParameter exists, but documented control only applies to Rebuild mode; no Rebuild property getter/setter called in captured modes',
                    stored_binding_payload_hex=payload.hex())
            selection=decode_mesh_selection(data,records,reference(body,58),owner)
            current_id,additional_id=reference(body,32),reference(body,43)
            _require(current_id!=additional_id,'MeshRepair current/additional asset references alias')
            matches=[m for m in meshes['decoded'] if m['mesh_object_id']==selection['mesh_object_id']]
            _require(len(matches)==1,'MeshRepair selected mesh lacks one strict current native geometry/owner route')
            mesh=matches[0]
            _require(mesh['asset_object_id']==current_id and mesh['native_feature_class_guid']==MESH_FEATURE
                and mesh['feature_object_id']!=owner and mesh['collection_mesh_object_ids']==[selection['mesh_object_id']]
                and {r.object_id for r in records if r.is_primary and r.class_guid==MESH}=={selection['mesh_object_id']},
                'MeshRepair current asset/owner outside observed singleton native BaseMesh family')
            current=decode_mesh_asset(data,records,current_id,member,members)
            additional=decode_mesh_asset(data,records,additional_id,member,members)
            _require(current['asset_member']==mesh['asset_member']
                and (current['geometry']['node_count'],current['geometry']['triangle_count'])==(4,4)
                and (additional['geometry']['node_count'],additional['geometry']['triangle_count']) in ((4,3),(4,4)),
                'MeshRepair stored current/additional cache dimensions or asset route differ')
            nil,cursor=read_string(body,70)
            _require(nil==str(uuid.UUID(int=0)) and cursor==146 and body[146:149]==bytes(3)
                and struct.unpack_from('<I',body,149)[0]==4,'MeshRepair nil UUID/dependency framing differs')
            repeated=[reference(body,153+11*i) for i in range(4)]
            _require(repeated==[selection['proxy_object_id'],selection['descriptor_object_id'],bindings['Density'],bindings['Offset']]
                and body[197:201]==b'\xff'*4,'MeshRepair repeated input/control dependency table differs')
            label,cursor=read_string(body,201)
            index=struct.unpack_from('<Q',body,cursor)[0]
            name,tail=read_string(body,cursor+8)
            _require(label=='MeshRepair' and index==feature.get('stored_index') and name==feature.get('name')
                and len(body)-tail==66,'MeshRepair counted label/index/name/shared footer differs')
            state=feature_state(body)
            state_id=reference(body,tail+7)
            _,state_body=typed(state_id,'B7F34D7B-DAC4-41A5-B67D-D672537C3BFA')
            _require(state_body==bytes.fromhex('0000000000000100000000000000'),'Unobserved MeshRepair stored state payload')
            def ref(identity):return b'\1'+struct.pack('<Q',identity)+bytes(2)
            def text(value):return struct.pack('<I',len(value))+value.encode('utf-16le')
            replay=(bytes(2)+ref(bindings['Density'])+ref(bindings['Offset'])+bytes(4)+struct.pack('<I',method)
                +ref(current_id)+ref(additional_id)+bytes(4)+ref(selection['proxy_object_id'])+bytes(1)+text(nil)
                +bytes(3)+struct.pack('<I',4)+b''.join(ref(i) for i in repeated)+b'\xff'*4+text(label)
                +struct.pack('<Q',index)+text(name)+body[tail:])
            _require(replay==body,'MeshRepair complete feature payload replay differs')
            settings=dict(method=METHODS[method],stored_method_code=method,stored_uninterpreted_uint32_at_24=0,
                mesh_repair_rebuild_type=None,rebuild_type_scope='Invariant native uint32@24 remains literal zero; inactive SDK getter was not called and no Rebuild enum mapping inferred',
                scalar_bindings=scalars,input_selection=selection,native_mesh_object_id=selection['mesh_object_id'],mesh_name=mesh['name'],
                component_object_id=mesh['component_object_id'],mesh_collection_object_id=mesh['mesh_collection_object_id'],
                current_mesh_native_feature_owner_object_id=mesh['feature_object_id'],current_mesh_native_owner_class_guid=mesh['native_feature_class_guid'],
                mesh_repair_owns_current_mesh=None,
                owner_scope='Owned input selection/current asset and independent reciprocal native BaseMeshFeature owner; Repair is not promoted to native mesh owner or API baseOrFormFeature',
                stored_current_asset_field_relative_offset=32,current_mesh_asset=current,
                stored_additional_asset_field_relative_offset=43,additional_stored_asset=additional,additional_asset_temporal_role=None,
                asset_scope='Current asset agrees with selected native mesh pointer/UUID/same-asset filename. Additional asset is explicitly referenced; rolled getter array equality is corroboration, not persistent source state or temporal role.',
                current_cache_node_count=len(mesh['geometry']['stored_node_coordinates_float32']),current_cache_triangle_count=mesh['geometry']['triangle_count'],
                repeated_dependency_object_ids=repeated,
                layout=dict(feature_body_offset=record.body,feature_body_end_offset=record.end,feature_body_hex=body.hex(),
                    method_body_relative_offset=28,dependency_table_body_relative_offset=153,
                    shared_footer_hex=body[tail:].hex(),shared_feature_state=state,
                    stored_state_object_id=state_id,stored_state_payload_hex=state_body.hex(),exact_full_payload_replay=True))
            result['decoded'].append(dict(feature_object_id=owner,kind='MeshRepair',name=name,settings=settings))
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error,lzma.LZMAError) as error:
            result['unresolved'].append(dict(feature_object_id=record.object_id,class_guid=REPAIR,reason=str(error)))
    return result
