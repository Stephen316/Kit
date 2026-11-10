"""Pure native source, result-anchor and component proofs for saved Mirrors.

This factory establishes the identities and selected plane used by a separate
cache-reflection checker. It neither fits geometry nor assigns lifecycle/API IDs.
"""
import copy
import math
import struct

from decode_assembly import decode_assembly
from decode_body_properties import decode_body_properties
from decode_body_selections import ANCHOR, BODY, decode_body_selections
from decode_dependencies import decode_dependencies
from decode_mirror_face_planes import decode_mirror_face_planes
from decode_mirror_modes import MIRROR, decode_mirror_modes
from decode_plane_definitions import decode_plane_definitions
from decode_placement import decode_placement
from decode_selection import known_construction_entities
from decode_sketch import attributes, reference

CONTROL='C444E6AD-33DC-4877-B037-A3A5518856B1'
ELEMENT='AD719C1A-11AF-4537-BB41-030A9091D36B'
COMPONENT='E03784ED-5E19-4E14-B9F2-3B07017018CD'
BODY_COLLECTION='CD57BC48-50EC-47DC-975A-FB6DEA72F4DA'
PLANE='8D424E29-DE23-4B1F-A3AD-84C52A497D1A'
PLANE_COLLECTION='A8635B5F-1E2C-45FD-8BA9-0173B0FEB75E'
ORIGINS='2972A3B8-3627-49BC-8C3D-18707605EC44'
EXTRUDE='DD405BC2-D673-44F0-8833-5CB2A1C186C7'
SCOPE=('Observed noncombine BODY/one-two Extrude Feature Mirror sources, owned result anchors, '
       'literal element/naming pair and selected origin/Offset/planar-face support in one '
       'explicit native component; cache reflection, API/current/history identity and regeneration separate')


def qualify_mirror_cache_sources(data,records,features,member,members,body_blob_bindings,feature):
    """Return a qualified native route, or None for recognized nontarget families.

    Attempted BODY/Feature routes raise ValueError when malformed. Caller metadata
    is copied before fresh placement/assembly/plane/dependency readers run.
    """
    if feature.get('class_guid')!=MIRROR:
        return None
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)

    def typed(identity,guid=None):
        values=grouped.get(identity,[])
        if len(values)!=1 or guid is not None and values[0].class_guid!=guid:
            raise ValueError('Mirror cache source native identity missing, duplicate or wrong class')
        record=values[0]
        return record,data[record.body:record.end]

    def raw(record):
        return dict(object_id=record.object_id,class_guid=record.class_guid,record_offset=record.start,
            body_offset=record.body,end_offset=record.end,payload_hex=data[record.body:record.end].hex())

    receiver=feature['object_id'];rec,body=typed(receiver,MIRROR)
    if body[0]!=0 or body[1] not in (0,1):
        raise ValueError('Mirror cache source common feature prefix differs')
    props,cursor=attributes(body,2) if body[1] else ({},2)
    if props:raise ValueError('Mirror cache source feature attributes outside observed family')
    control_id=reference(body,cursor);control_record,control=typed(control_id,CONTROL)
    if len(control)!=133:
        raise ValueError('Mirror cache source control extent differs')
    compute,entity_type=struct.unpack_from('<II',control,37)
    if entity_type==0:
        return None  # Face-input Mirrors retain their existing unsupported scope.
    if entity_type not in (1,2):
        raise ValueError('Mirror cache source input kind outside BODY/Feature family')
    # Existing aggregate ownership readers use primary-ID maps. Prove that their
    # full namespace is unique first, rather than letting a duplicate overwrite.
    if any(len(values)!=1 for values in grouped.values()):
        raise ValueError('Mirror cache source duplicate primary namespace prevents ownership qualification')
    if member not in members or members[member]!=data or not member.endswith('/FusionDesignSegmentType1/BulkStream.dat'):
        raise ValueError('Mirror cache source Design member/bytes scope differs')
    metadata=[f for f in features if f['object_id']==receiver]
    if (len(metadata)!=1 or feature.get('record_offset')!=rec.start or metadata[0].get('record_offset')!=rec.start
            or metadata[0].get('class_guid')!=MIRROR or metadata[0].get('kind')!='Mirror'):
        raise ValueError('Mirror cache source receiving feature metadata missing or ambiguous')
    private=copy.deepcopy(features)
    decode_placement(data,records,private)
    assembly=decode_assembly(data,records,private)
    properties=decode_body_properties(data,records,assembly)
    definitions=decode_plane_definitions(data,records,private)
    known=known_construction_entities(data,records,private)
    fresh_feature=next(f for f in private if f['object_id']==receiver)
    settings=decode_mirror_modes(data,records,body,fresh_feature,known,private,allowed_feature_counts=(1,2))
    if (settings['is_combine'] is not False or settings['input_kind'] not in ('Body','Feature')
            or not math.isfinite(settings['stitch_tolerance_cm']) or settings['stitch_tolerance_cm']<0):
        raise ValueError('Mirror cache source requires observed noncombine BODY/Feature controls')
    if (settings['input_kind']=='Body' and compute!=2 or settings['input_kind']=='Feature' and compute not in (0,1,2)):
        raise ValueError('Mirror cache source active/inactive compute scope disagrees')
    if (control[:2]!=bytes(2) or control[2]!=0 or reference(control,107)!=receiver
            or control[45:50]!=b'\xff'*4+b'\1' or struct.unpack_from('<I',control,50)[0]!=1
            or struct.unpack_from('<I',control,70)[0]!=2):
        raise ValueError('Mirror cache source literal controller pair/header differs')
    pair=list(struct.unpack_from('<QQ',control,54))
    if pair[0]!=2 or pair[1]<=0:
        raise ValueError('Mirror cache source native element/opaque naming pair differs')
    element_records=[]
    for at in (74,85):
        identity=reference(control,at);record,payload=typed(identity,ELEMENT)
        if len(payload)!=17 or payload[:2]!=bytes(2) or reference(payload,6)!=control_id:
            raise ValueError('Mirror cache source typed element/controller backlink differs')
        element_records.append(dict(object_id=identity,stored_element_key=struct.unpack_from('<I',payload,2)[0],
            control_record_object_id=control_id,native_record=raw(record)))
    if ({e['stored_element_key'] for e in element_records}!={1,2}
            or len({e['object_id'] for e in element_records})!=2):
        raise ValueError('Mirror cache source element/key coverage is not a bijection')
    selections=decode_body_selections(data,records)
    anchor_rows={}
    for anchor in selections['body_anchors']:anchor_rows.setdefault(anchor['object_id'],[]).append(anchor)

    def anchor(identity,owner):
        record,payload=typed(identity,ANCHOR);matches=anchor_rows.get(identity,[])
        if (len(payload)!=102 or reference(payload,91)!=owner or len(matches)!=1
                or matches[0]['source_owner_object_id']!=owner
                or reference(payload,80)!=matches[0]['native_body_object_id']):
            raise ValueError('Mirror cache source owned anchor/BODY/owner copies disagree')
        typed(matches[0]['native_body_object_id'],BODY)
        return matches[0]

    sources=[];source_provenance=[];source_owner_ids=[]
    selected=settings['input_selections']
    if len(selected)!=settings['input_count'] or not 1<=len(selected)<=2:
        raise ValueError('Mirror cache source input count outside captured singleton/two-source family')
    for item in selected:
        descriptor_record,_=typed(item['descriptor_object_id'],
            '9716F783-676D-42E0-93F9-EBF273E7C035' if settings['input_kind']=='Body'
            else '5A1BF548-241F-46FD-9FB5-E4B05126EB9D')
        association_record,_=typed(item['association_record_object_id'],'C46D3EEB-40E1-43FA-83DC-9CB204335417')
        if settings['input_kind']=='Body':
            source_owner=item['source_owner_object_id']
            source_anchor=anchor(item['body_anchor_object_id'],source_owner)
            if source_anchor['native_body_object_id']!=item['native_body_object_id']:
                raise ValueError('Mirror cache BODY descriptor differs from independently decoded anchor')
            extra=[]
        else:
            source_owner=item['source_feature_object_id']
            leaf_record,_=typed(item['terminal_object_id'],'90055C05-546C-4EE7-B3C9-3DD922AD0C9C')
            owned=[a for a in selections['body_anchors'] if a['source_owner_object_id']==source_owner]
            if len(owned)!=1:
                raise ValueError('Mirror cache Feature source does not own one unique BODY anchor')
            source_anchor=anchor(owned[0]['object_id'],source_owner)
            extra=[leaf_record]
        source_record,_=typed(source_owner,EXTRUDE)
        if source_owner==receiver:
            raise ValueError('Mirror cache source is self-referential')
        native=source_anchor['native_body_object_id'];native_record,_=typed(native,BODY)
        source_owner_ids.append(source_owner);sources.append(native)
        source_provenance.append(dict(input_descriptor=item,source_anchor=source_anchor,
            native_records=[raw(r) for r in (descriptor_record,association_record,*extra,source_record,
                typed(source_anchor['object_id'],ANCHOR)[0],native_record)]))
    if len(set(sources))!=len(sources):
        raise ValueError('Mirror cache source BODY identities overlap')
    if body[cursor+22:cursor+26]!=bytes(4):
        raise ValueError('Mirror cache source result-list separator differs')
    count=struct.unpack_from('<I',body,cursor+26)[0]
    if count!=len(sources):
        raise ValueError('Mirror cache source result count must equal explicit source count')
    result_ids=[reference(body,cursor+30+11*i) for i in range(count)]
    if len(set(result_ids))!=count:
        raise ValueError('Mirror cache source result anchor list repeats')
    results=[anchor(identity,receiver) for identity in result_ids]
    result_bodies=[a['native_body_object_id'] for a in results]
    if len(set(result_bodies))!=count or set(sources)&set(result_bodies):
        raise ValueError('Mirror cache source/result BODY identities overlap or repeat')
    selected_plane=settings['plane']
    support_bodies=[];support_owners=[]
    if selected_plane is None:
        proof=decode_mirror_face_planes(data,records,private,member,members,body_blob_bindings)
        matches=[r for r in proof['decoded'] if r['feature_object_id']==receiver]
        if len(matches)!=1 or any(r['feature_object_id']==receiver for r in proof['unresolved']):
            raise ValueError('Mirror cache source planar-face support proof unresolved')
        face=matches[0];cp=face['cache_plane'];support_bodies=[face['source_body_binding']['native_body_object_id']]
        support_owners=[face['support_provenance']['historical_anchor_source_owner_object_id'],
            *face['support_provenance']['support_source_record_object_ids']]
        plane=dict(kind='NamedBRepFaceCache',origin=cp['raw_origin'],unit_normal=cp['normalized_unit_normal'],
            native_proof=face,history_blob_member=face['history_blob_member'],
            source_body_binding=face['source_body_binding'],native_body_object_id=support_bodies[0])
        plane_component_proof=None
    else:
        entity=selected_plane['entity'];plane_id=entity['object_id'];plane_record,plane_body=typed(plane_id,PLANE)
        if entity['kind']!='ConstructionPlane':
            raise ValueError('Mirror cache source selected support is not a captured plane kind')
        if 'origin_container_object_id' in entity:
            container_id=entity['origin_container_object_id'];container_record,container=typed(container_id,ORIGINS)
            n=struct.unpack_from('<I',container,4)[0]
            if container[:4]!=bytes(4) or n!=7 or len(container)!=19+11*n:
                raise ValueError('Mirror cache source origin container framing differs')
            ids=[reference(container,8+11*i) for i in range(n)]
            if len(set(ids))!=n or ids.count(plane_id)!=1 or reference(plane_body,len(plane_body)-11)!=container_id:
                raise ValueError('Mirror cache source origin plane/container membership differs')
            component=reference(container,len(container)-11)
            plane_component_proof=dict(kind='OriginContainer',component_object_id=component,
                container_object_id=container_id,origin_member_object_ids=ids,
                native_records=[raw(plane_record),raw(container_record)])
            plane=dict(kind='OriginConstructionPlane',origin=entity['origin_cm'],unit_normal=entity['normal'],
                native_plane_object_id=plane_id,native_proof=dict(selection=selected_plane,component_route=plane_component_proof))
        else:
            definitions_for_plane=[d for d in definitions['definitions'] if d['plane_object_id']==plane_id]
            if len(definitions_for_plane)!=1 or definitions_for_plane[0]['definition_kind']!='Offset':
                raise ValueError('Mirror cache source custom plane requires one freshly qualified Offset definition')
            definition=definitions_for_plane[0];geometry=definition['cached_geometry'];owner=definition['feature_object_id']
            if entity.get('feature_object_id')!=owner or entity['origin_cm']!=geometry['origin_cm'] or entity['normal']!=geometry['normal']:
                raise ValueError('Mirror cache source selected custom plane/cache definition differs')
            collection_id=reference(plane_body,len(plane_body)-11);collection_record,collection=typed(collection_id,PLANE_COLLECTION)
            n=struct.unpack_from('<I',collection,2)[0];repeat=len(collection)-15-11*n
            if collection[:2]!=bytes(2) or n!=1 or len(collection)!=51+22*n:
                raise ValueError('Mirror cache source custom plane collection framing differs')
            ids=[reference(collection,6+11*i) for i in range(n)]
            if ids!=[plane_id] or struct.unpack_from('<I',collection,repeat)[0]!=n or [reference(collection,repeat+4+11*i) for i in range(n)]!=ids:
                raise ValueError('Mirror cache source custom plane repeated membership differs')
            component=reference(collection,len(collection)-11);support_owners=[owner]
            plane_component_proof=dict(kind='StoredPlaneCollection',component_object_id=component,
                collection_object_id=collection_id,stored_member_object_ids=ids,repeated_member_object_ids=ids,
                native_records=[raw(plane_record),raw(collection_record),raw(typed(owner,'D869265F-F339-4751-A066-91D30F81FF08')[0])])
            plane=dict(kind='StoredConstructionPlane',origin=geometry['origin_cm'],unit_normal=geometry['normal'],
                native_plane_object_id=plane_id,native_proof=dict(selection=selected_plane,definition=definition,
                    component_route=plane_component_proof))
    origin,normal=plane['origin'],plane['unit_normal']
    length=math.hypot(*normal)
    if (len(origin)!=3 or len(normal)!=3 or any(not math.isfinite(v) for v in origin+normal)
            or not math.isfinite(length) or length<=0):
        raise ValueError('Mirror cache source selected plane frame is not finite/nondegenerate')
    plane['unit_normal']=[v/length for v in normal]
    required_bodies=list(dict.fromkeys(sources+result_bodies+support_bodies))
    body_proofs=[];components=set()
    for identity in required_bodies:
        matches=[b for b in properties['bodies'] if b['object_id']==identity]
        if len(matches)!=1 or 'collection_object_id' not in matches[0] or 'component_object_id' not in matches[0]:
            raise ValueError('Mirror cache source BODY has no repeated reciprocal component ownership')
        prop=matches[0];collections=[c for c in properties['collections'] if c['object_id']==prop['collection_object_id']]
        if len(collections)!=1 or identity not in collections[0]['body_object_ids']:
            raise ValueError('Mirror cache source BODY/collection identity differs')
        collection=collections[0];crecord,cb=typed(collection['object_id'],BODY_COLLECTION)
        body_record,bb=typed(identity,BODY)
        if reference(bb,len(bb)-11)!=crecord.object_id or reference(cb,len(cb)-11)!=prop['component_object_id']:
            raise ValueError('Mirror cache source BODY/collection/component reciprocal references differ')
        typed(prop['component_object_id'],COMPONENT);components.add(prop['component_object_id'])
        body_proofs.append(dict(native_body_object_id=identity,body_properties=prop,collection=collection,
            native_records=[raw(body_record),raw(crecord)]))
    if len(components)!=1:
        raise ValueError('Mirror cache source/result/support BODYs do not share one native component')
    component=next(iter(components))
    if plane_component_proof is not None and plane_component_proof['component_object_id']!=component:
        raise ValueError('Mirror cache source selected plane belongs to a different component')
    owner_ids=list(dict.fromkeys([receiver]+source_owner_ids+support_owners))
    dependency_owners=[dict(object_id=identity) for identity in owner_ids]
    for identity in owner_ids:typed(identity)
    decode_dependencies(data,records,dependency_owners,assembly)
    if any(o.get('component_object_id')!=component or 'component_scope_object_id' not in o for o in dependency_owners):
        raise ValueError('Mirror cache source/receiver/plane-support fresh dependency scopes disagree')
    return dict(feature_object_id=receiver,input_kind=settings['input_kind'],source_native_body_object_ids=sources,
        source_provenance=source_provenance,result_anchors=results,selected_plane=plane,
        stored_instance_key_pair=pair,element_records=element_records,native_controller_proof=raw(control_record),
        native_feature_proof=raw(rec),component_provenance=dict(component_object_id=component,
            body_ownership=body_proofs,selected_plane_component_route=plane_component_proof,
            dependency_scopes=dependency_owners,assembly_scope=assembly['scope'],
            scope='Fresh repeated BODY collections/reciprocal BODY links and native dependency datums share the selected support component; no occurrence solving'),
        settings=settings,API_handle_identity=None,current_source_identity=None,persistent_source_identity=None,
        qualified_historical_state=None,scope=SCOPE)
