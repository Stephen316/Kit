"""Explicit root-context Scale/Mirror/Shell body and face input selections."""

import struct

from decode_body_selections import decode_body_selections
from decode_extrude import optional_reference
from decode_face_selections import resolve_native_faces
from decode_placement import rigid_matrix, transform_point
from decode_selection import native_proxy_references
from decode_sketch import attributes, numbers, reference, same


def decode_body_tool_selections(data, records, features, body_selections=None):
    groups = {}
    for record in records:
        if record.is_primary:
            groups.setdefault(record.object_id, []).append(record)
    primary = {identity: items[0] for identity,items in groups.items() if len(items)==1}
    summary = body_selections if body_selections is not None else decode_body_selections(data,records)
    descriptors = {d['object_id']:d for d in summary['body_descriptors']}

    def typed(identity,guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Body-tool input typed reference missing, ambiguous or wrong class')
        return record,data[record.body:record.end]

    def body_descriptor(identity,owner):
        typed(identity,'9716F783-676D-42E0-93F9-EBF273E7C035')
        selected=descriptors.get(identity)
        if selected is None or selected['owner_object_id']!=owner or selected['context_record_object_ids']:
            raise ValueError('Only observed owned body inputs without instance context supported')
        return {'kind':'Body','descriptor_object_id':identity,
                'native_body_object_id':selected['native_body_object_id'],
                'body_anchor_object_id':selected['body_anchor_object_id'],
                'source_owner_object_id':selected['source_owner_object_id'],
                'identity_scope':'Explicit historical native body; result lifecycle and ASM topology remain separate'}

    def proxy_inputs(identity,owner,allow_faces):
        record,payload=typed(identity,'2CA5A1CD-C99B-4C9B-91AF-57989148E841')
        ids,props=native_proxy_references(data,record)
        if props or reference(payload,len(payload)-11)!=owner:
            raise ValueError('Body-tool input proxy attributes/owner unsupported')
        kinds={primary[i].class_guid for i in ids if i in primary}
        if kinds=={'9716F783-676D-42E0-93F9-EBF273E7C035'}:
            return [body_descriptor(i,owner) for i in ids]
        if allow_faces and kinds=={'5662F619-2281-4AD9-93DC-1FCFDA1062E7'}:
            faces=resolve_native_faces(data,records,identity,owner,summary)
            if faces['attributes']:raise ValueError('Unobserved Shell face proxy attributes')
            return [{'kind':'Face',**face} for face in faces['faces']]
        raise ValueError('Unobserved mixed or non-body/face input descriptor list')

    def sketch_point(identity,owner):
        _,payload=typed(identity,'69EE2FA7-BCC7-449E-9CA9-976CEFDFED44')
        if (len(payload)!=178 or payload[:23]!=bytes(23)
                or struct.unpack_from('<I',payload,47)[0]!=10
                or struct.unpack_from('<I',payload,75)[0]!=1 or reference(payload,167)!=owner):
            raise ValueError('Only observed explicit SketchPoint scale-reference backend supported')
        descriptor_id=reference(payload,79)
        _,descriptor=typed(descriptor_id,'5A1BF548-241F-46FD-9FB5-E4B05126EB9D')
        if (len(descriptor)!=263 or descriptor[:2]!=bytes(2)
                or struct.unpack_from('<I',descriptor,13)[0]!=1 or reference(descriptor,252)!=owner):
            raise ValueError('Unsupported Scale point descriptor framing/owner')
        leaf_id=reference(descriptor,2)
        _,leaf=typed(leaf_id,'D95DBAC0-238B-4429-A0AD-4AE5BEE79ADF')
        if len(leaf)!=18 or leaf[:2]!=bytes(2):raise ValueError('Unsupported Scale point source leaf')
        sketch_id,tag=struct.unpack_from('<QQ',leaf,2)
        matches=[(s,g) for s in features if s['kind']=='Sketch' and s['sketch_object_id']==sketch_id
                 for g in s['geometry'] if g['kind']=='Point' and g['entity_tag']==tag]
        if len(matches)!=1:raise ValueError('Scale point explicit sketch/tag unresolved or ambiguous')
        sketch,point=matches[0]
        position=transform_point(rigid_matrix(sketch['placement']['sketch_to_component_matrix']),point['position_cm'])
        if not same(position,numbers(payload,23,3)):raise ValueError('Scale point source and cached position disagree')
        return {'selection_object_id':identity,'descriptor_object_id':descriptor_id,'terminal_object_id':leaf_id,
                'entity':{'kind':'SketchPoint','object_id':point['object_id'],'sketch_object_id':sketch_id,
                          'sketch_name':sketch['name'],'entity_tag':tag,'position_cm':position},
                'association':'Owned backend/descriptor explicitly selects sketch ID and point tag; cached coordinates corroborate',
                'coordinate_scope':'Parent component coordinates; occurrence transforms unverified'}

    decoded,unresolved=[],[]
    for feature in features:
        kind=feature['kind']
        if kind not in ('Scale','Mirror','Shell') or 'tool_settings' not in feature:continue
        if kind == 'Scale' and feature['tool_settings'].get('input_kind') == 'Sketch':continue
        if kind == 'Mirror' and feature['tool_settings'].get('input_kind') == 'Feature':continue
        owner=feature['object_id']
        record=primary.get(owner)
        if record is None:continue
        body=data[record.body:record.end]
        try:
            proxy_ids=[]
            collection_id=None
            if kind=='Scale':
                factor,cursor=optional_reference(body,21)
                if factor is not None:
                    if body[cursor:cursor+13]!=bytes.fromhex('01000000000100000001000000'):
                        raise ValueError('Unsupported uniform Scale input-list framing')
                    position=cursor+13
                else:
                    if body[cursor:cursor+6]!=bytes.fromhex('010000000000') or body[cursor+39:cursor+43]!=struct.pack('<I',1):
                        raise ValueError('Unsupported nonuniform Scale input-list framing')
                    position=cursor+43
                proxy_ids=[reference(body,position)]
                selected=proxy_inputs(proxy_ids[0],owner,False)
            elif kind=='Mirror':
                props,cursor=attributes(body,2) if body[1] else ({},2)
                if props:raise ValueError('Unobserved Mirror feature attributes')
                collection_id=reference(body,cursor+11)
                _,collection=typed(collection_id,'8DB90DAE-3FF5-4E01-BACC-00AAA3EBB3EF')
                count=struct.unpack_from('<I',collection,6)[0]
                if (collection[:6]!=bytes(6) or not 1<=count<=1024 or len(collection)!=74+26*count
                        or reference(collection,10+26*count)!=owner or reference(collection,len(collection)-11)!=owner):
                    raise ValueError('Unsupported Mirror counted input collection/owner')
                selected=[]
                for index in range(count):
                    position=10+26*index
                    if struct.unpack_from('<I',collection,position+11)[0]!=1:
                        raise ValueError('Unobserved Mirror input association count')
                    association_id=reference(collection,position+15)
                    typed(association_id,'C46D3EEB-40E1-43FA-83DC-9CB204335417')
                    selected.append({**body_descriptor(reference(collection,position),owner),
                                     'association_record_object_id':association_id})
            else:
                _,cursor=optional_reference(body,4)
                _,cursor=optional_reference(body,cursor)
                if body[cursor:cursor+12]!=bytes(12):raise ValueError('Unsupported Shell input-list prefix')
                count=struct.unpack_from('<I',body,cursor+12)[0]
                if not 1<=count<=1024:raise ValueError('Unobserved Shell proxy count')
                proxy_ids=[reference(body,cursor+16+11*i) for i in range(count)]
                selected=[item for identity in proxy_ids for item in proxy_inputs(identity,owner,True)]
            ids=[item['descriptor_object_id'] for item in selected]
            if not selected or len(set(ids))!=len(ids):raise ValueError('Duplicate or empty body-tool input list')
            fields={'input_selections':selected,'input_count':len(selected),
                    'input_body_count':sum(item['kind']=='Body' for item in selected),
                    'input_face_count':sum(item['kind']=='Face' for item in selected),
                    'native_input_body_object_ids':list(dict.fromkeys(item['native_body_object_id'] for item in selected)),
                    'input_selection_record_object_ids':proxy_ids,
                    'input_entity_collection_object_id':collection_id,
                    'input_selection_status':'Explicit input field/counts and owned body descriptors or face recipes; persistent topology unresolved'}
            item={'feature_object_id':owner,'kind':kind,'settings':fields}
            if kind=='Scale' and feature['tool_settings'].get('point') is None:
                try:
                    fields['point']=sketch_point(reference(body,10),owner)
                    fields['point_selection_status']='Observed explicit SketchPoint reference decoded'
                except (ValueError,KeyError,IndexError,struct.error) as error:
                    item['unresolved_point']={'selection_object_id':reference(body,10),'reason':str(error)}
            decoded.append(item)
        except (ValueError,KeyError,IndexError,struct.error) as error:
            unresolved.append({'feature_object_id':owner,'kind':kind,'reason':str(error)})
    return {'decoded':decoded,'unresolved':unresolved,
            'scope':'Observed explicit Scale/Mirror body inputs and Shell body/face inputs; arbitrary instance contexts and persistent face geometry unresolved'}
