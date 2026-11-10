"""Observed public body/occurrence RemoveFeature target provenance.

BoundaryFill-owned RemoveBody children remain with decode_direct_body_features.
Stored target references, historical creation snapshots and current collection
membership are distinct facts; no final visibility/lifecycle is reconstructed.
"""
import struct
import uuid

from decode_asbuilt_joints import make_asbuilt_context_readers
from decode_assembly import collection as occurrence_collection
from decode_body_properties import decode_body_properties
from decode_body_selections import decode_body_selections,PROXY,DESCRIPTOR
from decode_boundary_fill import BOUNDARY_FILL_GUID
from decode_component_creation import decode_component_creation,OCCURRENCE_DATUM,SNAPSHOT,BOOKKEEPING
from decode_dependencies import decode_dependencies
from decode_direct_body_features import REMOVE_BODY
from decode_parameters import read_string
from decode_selection import native_proxy_references
from decode_sketch import reference,same
from decode_timeline import feature_state

REMOVE_INSTANCE='D3DC9613-9714-4DBE-99C4-0A76DB3327F1'
SCOPE='Observed ordinary public RemoveBody/RemoveInstance typed target, native component scope and historical source provenance; current visibility, feature replay and regeneration unresolved'


def decode_remove_features(data,records,features,assembly,*,body_selections=None,component_creations=None):
    records=list(records)
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    candidates=[r for r in records if r.is_primary and r.class_guid in(REMOVE_BODY,REMOVE_INSTANCE)]
    if not candidates:return result
    readers=make_asbuilt_context_readers(data,records,assembly)
    typed,primary,native_occurrence=readers['typed'],readers['primary'],readers['native_occurrence']
    features_by={f['object_id']:f for f in features}
    components={c['object_id']:c for c in assembly['components']}
    fresh_selections=None;creations=None
    def owned_component(identity):
        rows=[{'object_id':identity}];decode_dependencies(data,records,rows,assembly)
        if 'component_scope_object_id' not in rows[0] or rows[0].get('component_object_id') not in components:
            raise ValueError('RemoveFeature native dependency component scope unresolved')
        return rows[0]
    def stored_route(target):
        # The target may be deliberately absent from the current parent list.
        # Follow its explicit declared collection/owner chain without restoring it.
        chain=[];seen=set();cursor=target
        for _ in range(3):
            if cursor['object_id'] in seen:raise ValueError('Removed occurrence declared-parent route cycles')
            seen.add(cursor['object_id'])
            if cursor['parent_collection_object_id'] is None:
                if cursor['component_object_id'] not in components:raise ValueError('Removed occurrence root component unresolved')
                return list(reversed(chain))
            collection_id=cursor['parent_collection_object_id'];r,_=typed(collection_id,'904F885E-D859-4755-A7EF-6EBED8732FAD')
            collection=occurrence_collection(data[r.body:r.end],collection_id)
            owner=collection['component_object_id']
            if cursor['component_object_id'] not in components or owner not in components:
                raise ValueError('Removed occurrence declared-parent component missing')
            chain.append(dict(native_occurrence_object_id=cursor['object_id'],component_object_id=cursor['component_object_id'],
                component_name=components[cursor['component_object_id']]['name'],instance_number=cursor['instance_number'],
                declared_parent_collection_object_id=collection_id,declared_parent_component_object_id=owner,
                is_listed_in_stored_parent_collection=cursor['object_id'] in collection['occurrence_object_ids']))
            matches=[o for o in assembly['native_occurrences'] if o['component_object_id']==owner]
            if len(matches)!=1:raise ValueError('Removed occurrence declared parent has ambiguous occurrence context')
            cursor=native_occurrence(matches[0]['object_id'])
        raise ValueError('Removed occurrence declared-parent route deeper than observed root/child cases')
    for record in candidates:
        try:
            if primary.get(record.object_id) is not record:raise ValueError('RemoveFeature primary identity ambiguous')
            body=data[record.body:record.end]
            if record.class_guid==REMOVE_BODY:
                # Existing BoundaryFill child route owns its explicit typed parent.
                try:parent=primary.get(reference(body,len(body)-12))
                except (ValueError,IndexError,struct.error):parent=None
                if parent is not None and parent.class_guid==BOUNDARY_FILL_GUID:continue
            feature=features_by.get(record.object_id)
            if feature is None or feature['class_guid']!=record.class_guid or feature['record_offset']!=record.start:
                raise ValueError('RemoveFeature caller identity absent or stale')
            owner=record.object_id;scope=owned_component(owner)
            component_id=scope['component_object_id'];component_name=components[component_id]['name']
            if record.class_guid==REMOVE_BODY:
                if body[:2]!=bytes(2):raise ValueError('Unsupported public RemoveBody prefix')
                proxy_id=reference(body,2);nil,cursor=read_string(body,13)
                if (nil!=str(uuid.UUID(int=0)) or cursor!=89 or body[89:96]!=bytes.fromhex('00000002000000')
                        or reference(body,96)!=proxy_id or body[118:122]!=b'\xff'*4):
                    raise ValueError('Public RemoveBody repeated input framing differs')
                descriptor_id=reference(body,107)
                proxy_record,proxy=typed(proxy_id,PROXY);ids,props=native_proxy_references(data,proxy_record)
                _,descriptor_payload=typed(descriptor_id,DESCRIPTOR)
                if ids!=[descriptor_id] or props or reference(proxy,len(proxy)-11)!=owner or reference(descriptor_payload,len(descriptor_payload)-11)!=owner:
                    raise ValueError('Public RemoveBody proxy/descriptor reciprocal owner differs')
                if fresh_selections is None:
                    fresh_selections=decode_body_selections(data,records,decode_body_properties(data,records,assembly))
                selected=[s for s in fresh_selections['body_descriptors'] if s['object_id']==descriptor_id]
                if len(selected)!=1 or selected[0]['owner_object_id']!=owner:
                    raise ValueError('Public RemoveBody existing typed descriptor/anchor source unresolved')
                selected=selected[0]
                if body_selections is not None:
                    passed=[s for s in body_selections['body_descriptors'] if s['object_id']==descriptor_id]
                    keys=('object_id','owner_object_id','native_body_object_id','body_anchor_object_id','source_owner_object_id')
                    if len(passed)!=1 or any(passed[0][k]!=selected[k] for k in keys):
                        raise ValueError('Public RemoveBody supplied selection differs from fresh source framing')
                creator=owned_component(selected['source_owner_object_id'])
                if creator['component_object_id']!=component_id:
                    raise ValueError('Public RemoveBody target creator and removal component scopes differ')
                target=dict(kind='Body',native_body_object_id=selected['native_body_object_id'],
                    source_owner_object_id=selected['source_owner_object_id'],body_anchor_object_id=selected['body_anchor_object_id'],
                    selection_record_object_id=proxy_id,descriptor_object_id=descriptor_id,body_descriptor=selected,
                    creator_component_scope_object_id=creator['component_scope_object_id'],
                    geometry_scope='Explicit historical native BODY/anchor and creator component scope; no exact persistent topology or current body membership inferred')
                label_offset=122;expected_label='RemoveBody';kind='RemoveBody'
            else:
                if body[:14]!=bytes(14):raise ValueError('Unsupported public RemoveInstance prefix')
                datum_id=reference(body,14);nil,cursor=read_string(body,25)
                if nil!=str(uuid.UUID(int=0)) or cursor!=101 or body[101:112]!=bytes(7)+b'\xff'*4:
                    raise ValueError('Public RemoveInstance metadata UUID/list framing differs')
                _,datum=typed(datum_id,OCCURRENCE_DATUM)
                if (len(datum)!=39 or datum[:2]!=bytes(2) or datum[13:16]!=b'\1\0\0' or datum[27]!=0):
                    raise ValueError('Public RemoveInstance target datum framing differs')
                occurrence_id=reference(datum,2);snapshot_id=reference(datum,28);bookkeeping_id=reference(datum,16)
                typed(snapshot_id,SNAPSHOT);_,bookkeeping=typed(bookkeeping_id,BOOKKEEPING)
                if len(bookkeeping)!=39 or reference(bookkeeping,12)!=datum_id:
                    raise ValueError('Public RemoveInstance target datum bookkeeping is not reciprocal')
                if creations is None:creations=decode_component_creation(data,records,features,assembly)
                selected=[c for c in creations['decoded'] if c['occurrence_datum_object_id']==datum_id]
                if len(selected)!=1:raise ValueError('Public RemoveInstance target lacks one independently decoded creation/snapshot route')
                creation=selected[0]
                if (creation['native_occurrence_object_id']!=occurrence_id or creation['snapshot_object_id']!=snapshot_id
                        or creation['datum_bookkeeping_object_id']!=bookkeeping_id):
                    raise ValueError('Public RemoveInstance target datum and creation identities differ')
                if component_creations is not None:
                    supplied=[c for c in component_creations['decoded'] if c['occurrence_datum_object_id']==datum_id]
                    if len(supplied)!=1 or supplied[0]!=creation:
                        raise ValueError('Public RemoveInstance supplied creation route differs from fresh framing')
                native=native_occurrence(occurrence_id)
                route=stored_route(native)
                if not route or route[-1]['declared_parent_component_object_id']!=component_id:
                    raise ValueError('Public RemoveInstance feature is not scoped to target declared parent component')
                if native['component_object_id']!=creation['component_object_id'] or not same(native['local_transform'],creation['snapshot_transform']):
                    raise ValueError('Public RemoveInstance target component/local cache differs from historical creation snapshot')
                target=dict(kind='Occurrence',native_occurrence_object_id=occurrence_id,
                    occurrence_datum_object_id=datum_id,snapshot_object_id=snapshot_id,datum_bookkeeping_object_id=bookkeeping_id,
                    source_creation=creation,component_object_id=native['component_object_id'],
                    component_name=components[native['component_object_id']]['name'],instance_number=native['instance_number'],
                    stored_native_occurrence=native,declared_parent_route=route,
                    declared_parent_path_label='+'.join(c['component_name']+':'+str(c['instance_number']) for c in route),
                    path_scope='Uniquely framed declared-parent chain for source provenance; not a restored final occurrence path or collection membership',
                    is_listed_in_stored_parent_collection=route[-1]['is_listed_in_stored_parent_collection'])
                label_offset=112;expected_label='RemoveInstance';kind='RemoveInstance'
            label,cursor=read_string(body,label_offset);index=struct.unpack_from('<Q',body,cursor)[0];name,tail=read_string(body,cursor+8)
            if label!=expected_label or index!=feature['stored_index'] or len(body)-tail!=66:
                raise ValueError('Public removal label/index/shared footer extent differs')
            state=feature_state(body)
            result['decoded'].append(dict(feature_object_id=owner,feature_class_guid=record.class_guid,kind=kind,name=name,
                stored_index=index,component_object_id=component_id,component_name=component_name,
                component_scope_object_id=scope['component_scope_object_id'],target=target,state=state,
                action_scope='Typed removal target and component owner; current collections and historical source identity remain separate. Final visibility, lifecycle replay and regeneration unresolved',scope=SCOPE))
        except (ValueError,UnicodeError,IndexError,KeyError,struct.error) as error:
            result['unresolved'].append(dict(feature_object_id=record.object_id,class_guid=record.class_guid,reason=str(error)))
    return result
