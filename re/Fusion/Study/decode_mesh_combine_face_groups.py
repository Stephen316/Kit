"""Observed CombineFaceGroups selections in the selected asset's label namespace."""
import lzma
import struct
import uuid

from decode_mesh_contents import _protobuf, _require
from decode_mesh_geometry_variants import decode_mesh_asset, decode_mesh_contents_variants
from decode_mesh_selections import decode_mesh_selection
from decode_mesh_face_group_caches import decode_mesh_face_group_cache
from decode_parameters import read_string
from decode_sketch import reference

COMBINE_GROUPS='8136D47E-3955-4682-8BD7-B353B7B45624'
SCOPE=('Observed CombineFaceGroups ordered2/3 asset-group UUID keys, typed selected current mesh/asset '
       'ownership, exact metadata label/UUID table and current ordered triangle temporary labels. UUIDs '
       'qualify only this stored asset namespace; persistent face identity, handle stability across rollback, '
       'additional asset temporal role, lifecycle and regeneration remain unresolved.')


def _ascii_uuid(body,cursor):
    _require(struct.unpack_from('<I',body,cursor)[0]==36,'CombineFaceGroups UUID string extent differs')
    text=body[cursor+4:cursor+40].decode('ascii')
    _require(len(text)==36 and str(uuid.UUID(text))==text and uuid.UUID(text).int!=0,
             'CombineFaceGroups UUID is not canonical/nonzero')
    return text,cursor+40


def _asset_group_names(asset):
    metadata=bytes.fromhex(asset['geometry']['stored_metadata_hex'])
    outer=_protobuf(metadata)
    _require([(n,w) for n,w,_,_,_ in outer]==[(4,2),(5,2),(7,2),(8,2),(9,0),(12,2),(21,2),(22,2)],
             'CombineFaceGroups asset metadata framing differs')
    payload=outer[1][2];fields=_protobuf(payload)
    _require([(n,w) for n,w,_,_,_ in fields]==[(5,2)]+[(6,2)]*8
             and fields[0][2]==bytes.fromhex('080712027232'),
             'CombineFaceGroups eight-entry asset label namespace differs')
    entries=[]
    for _,_,raw,_,_ in fields[1:]:
        pair=_protobuf(raw)
        _require([(n,w) for n,w,_,_,_ in pair]==[(1,0),(2,2)],
                 'CombineFaceGroups metadata label/UUID pair framing differs')
        label,text=pair[0][2],pair[1][2].decode('ascii')
        _require(isinstance(label,int) and 1<=label<=8 and len(text)==36
                 and str(uuid.UUID(text))==text and uuid.UUID(text).int!=0,
                 'CombineFaceGroups metadata label/UUID outside observed namespace')
        entries.append(dict(stored_asset_group_label=label,stored_asset_group_uuid=text))
    _require({x['stored_asset_group_label'] for x in entries}==set(range(1,9))
             and len({x['stored_asset_group_uuid'] for x in entries})==8,
             'CombineFaceGroups metadata label/UUID identities duplicate or absent')
    replay=bytes.fromhex('2a06080712027232')+b''.join(
        bytes.fromhex('322808')+bytes([row['stored_asset_group_label']])+bytes.fromhex('1224')
        +row['stored_asset_group_uuid'].encode('ascii') for row in entries)
    _require(replay==payload,'CombineFaceGroups full metadata namespace byte replay disagrees')
    return dict(asset_object_id=asset['asset_object_id'],asset_member=asset['asset_member'],
        asset_fusion_uuid=asset['asset_fusion_uuid'],metadata_field_number=5,
        stored_namespace_descriptor_hex=fields[0][2].hex(),stored_payload_hex=payload.hex(),entries=entries,
        identity_scope='Label/UUID pairs scoped to this explicit native asset. Table presence does not imply current triangle use or persistent geometry identity')


def decode_mesh_combine_face_groups(data,records,features,member,members,mesh_contents=None):
    """Return decoded/unresolved/scope, rows feature_object_id/kind/name/settings."""
    records=list(records);result=dict(decoded=[],unresolved=[],scope=SCOPE)
    targets=[r for r in records if r.is_primary and r.class_guid==COMBINE_GROUPS]
    if not targets:return result
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    def typed(identity,guid):
        rows=grouped.get(identity,[])
        _require(len(rows)==1 and rows[0].class_guid==guid,'CombineFaceGroups typed reference absent/ambiguous/wrong class')
        record=rows[0];return record,data[record.body:record.end]
    named={}
    for feature in features:named.setdefault(feature['object_id'],[]).append(feature)
    meshes=mesh_contents if mesh_contents is not None else decode_mesh_contents_variants(data,records,member,members)
    for record in targets:
        try:
            typed(record.object_id,COMBINE_GROUPS)
            named_rows=named.get(record.object_id,[])
            _require(len(named_rows)==1,'CombineFaceGroups discovery feature identity ambiguous/absent')
            feature=named_rows[0]
            _require(feature['class_guid']==COMBINE_GROUPS
                     and feature['record_offset']==record.start and feature.get('native_kind_label')=='CombineFaceGroups',
                     'CombineFaceGroups discovery class/label/offset differs')
            body=data[record.body:record.end]
            _require(body[:2]==bytes(2),'CombineFaceGroups prefix differs')
            leading,cursor=_ascii_uuid(body,2)
            current_id,additional_id=reference(body,cursor),reference(body,cursor+11);cursor+=22
            _require(current_id!=additional_id,'CombineFaceGroups stored asset slots alias')
            count=struct.unpack_from('<I',body,cursor)[0];cursor+=4
            _require(count in (2,3),'Unobserved CombineFaceGroups selection count')
            keys=[]
            for _ in range(count):
                key,cursor=_ascii_uuid(body,cursor);keys.append(key)
            _require(len(set(keys))==count and leading==keys[-1],
                     'CombineFaceGroups selected UUIDs duplicate or leading key differs from last selection')
            proxy_id=reference(body,cursor);cursor+=11
            selection=decode_mesh_selection(data,records,proxy_id,record.object_id)
            _require(body[cursor]==0,'CombineFaceGroups source/namespace separator differs');cursor+=1
            nil,cursor=read_string(body,cursor)
            _require(nil==str(uuid.UUID(int=0)) and body[cursor:cursor+3]==bytes(3)
                     and struct.unpack_from('<I',body,cursor+3)[0]==2,
                     'CombineFaceGroups nil namespace/dependency framing differs');cursor+=7
            repeated=[reference(body,cursor),reference(body,cursor+11)];cursor+=22
            _require(repeated==[proxy_id,selection['descriptor_object_id']] and body[cursor:cursor+4]==b'\xff'*4,
                     'CombineFaceGroups repeated mesh selection differs');cursor+=4
            label,cursor=read_string(body,cursor);index=struct.unpack_from('<Q',body,cursor)[0]
            name,tail=read_string(body,cursor+8)
            _require(label=='CombineFaceGroups' and index==feature['stored_index'] and name==feature['name']
                     and len(body)-tail==66 and body[tail:tail+7]==bytes(7),
                     'CombineFaceGroups metadata/footer extent differs')
            def ref(identity):return b'\1'+struct.pack('<Q',identity)+bytes(2)
            def ascii_text(value):return struct.pack('<I',len(value))+value.encode('ascii')
            def unicode_text(value):return struct.pack('<I',len(value))+value.encode('utf-16le')
            replay=(bytes(2)+ascii_text(leading)+ref(current_id)+ref(additional_id)+struct.pack('<I',count)
                +b''.join(ascii_text(key) for key in keys)+ref(proxy_id)+bytes(1)+unicode_text(nil)
                +bytes(3)+struct.pack('<I',2)+b''.join(ref(identity) for identity in repeated)+b'\xff'*4
                +unicode_text(label)+struct.pack('<Q',index)+unicode_text(name)+body[tail:])
            _require(replay==body,'CombineFaceGroups complete feature payload replay disagrees')
            state_id=reference(body,tail+7)
            _,state=typed(state_id,'B7F34D7B-DAC4-41A5-B67D-D672537C3BFA')
            _require(state==bytes.fromhex('0000000000000100000000000000'),
                     'CombineFaceGroups state payload outside observed layout')
            matches=[m for m in meshes['decoded'] if m['mesh_object_id']==selection['mesh_object_id']]
            _require(len(matches)==1 and matches[0]['asset_object_id']==current_id,
                     'CombineFaceGroups selected current mesh/asset route unresolved')
            mesh=matches[0];current=decode_mesh_asset(data,records,current_id,member,members)
            additional=decode_mesh_asset(data,records,additional_id,member,members)
            _require(current['asset_member']==mesh['asset_member'],'CombineFaceGroups current asset member differs')
            names=_asset_group_names(current);additional_names=_asset_group_names(additional)
            by_key={x['stored_asset_group_uuid']:x['stored_asset_group_label'] for x in names['entries']}
            other={x['stored_asset_group_uuid']:x['stored_asset_group_label'] for x in additional_names['entries']}
            _require(all(key in by_key and key in other and by_key[key]==other[key] for key in keys),
                     'CombineFaceGroups selected UUID missing/inconsistent in explicit asset namespaces')
            selected_labels=[by_key[key] for key in keys]
            _require(selected_labels in ([1,2],[2,1],[1,2,4]),'Unobserved CombineFaceGroups ordered asset label selection')
            cache=decode_mesh_face_group_cache(mesh)
            _require(len(mesh['geometry']['stored_node_coordinates_float32'])==6 and cache['triangle_label_count']==8,
                     'Unobserved CombineFaceGroups current cache dimensions')
            labels=cache['decoded_triangle_face_group_temporary_ids']
            settings=dict(input_selection=selection,native_mesh_object_id=mesh['mesh_object_id'],
                component_object_id=mesh['component_object_id'],mesh_name=mesh['name'],
                current_mesh_native_feature_owner_object_id=mesh['feature_object_id'],
                current_mesh_native_owner_class_guid=mesh['native_feature_class_guid'],
                stored_selected_asset_group_uuids=keys,stored_leading_asset_group_uuid=leading,
                selected_asset_group_labels=selected_labels,
                selected_current_triangle_label_occurrence_counts=[labels.count(value) for value in selected_labels],
                leading_key_current_triangle_label_occurrence_count=labels.count(by_key[leading]),
                selection_scope='Ordered feature UUIDs resolve through the explicitly selected native mesh current/additional asset metadata tables. Labels remain asset-scoped temporary cache keys; no persistent geometry/handle identity',
                leading_key_scope='Literal leading UUID equals last selected UUID in observed2/3 layouts; no universal merge-survivor or lifecycle semantics',
                current_asset_group_namespace=names,additional_asset_group_namespace=additional_names,
                current_mesh_asset=current,additional_stored_asset=additional,additional_asset_temporal_role=None,
                current_triangle_face_groups=cache,repeated_dependency_object_ids=repeated,
                stored_feature_index=index,stored_state_object_id=state_id,stored_state_payload_hex=state.hex(),
                stored_shared_footer_hex=body[tail:].hex(),
                layout=dict(feature_record_offset=record.start,feature_body_offset=record.body,
                    feature_body_end_offset=record.end,stored_feature_body_hex=body.hex(),exact_full_payload_replay=True),
                source_scope='Typed input proxy/descriptor proves MeshBody selection; independent native BaseMesh owner retained',
                regeneration_scope='Stored selection/control/cache evidence only; no grouping algorithm, history replay or regeneration')
            result['decoded'].append(dict(feature_object_id=record.object_id,kind='MeshCombineFaceGroups',name=name,settings=settings))
        except (ValueError,KeyError,IndexError,UnicodeError,struct.error,TypeError,lzma.LZMAError) as error:
            result['unresolved'].append(dict(feature_object_id=record.object_id,class_guid=COMBINE_GROUPS,reason=str(error)))
    return result
