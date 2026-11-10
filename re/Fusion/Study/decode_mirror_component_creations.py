"""Mirror-owned CreateComponent correspondence without fictitious snapshots.

The creation and scope point to MirrorComponent, whose owned DerivedInstance
and occurrence datum identify the created occurrence. Saved transform caches
are retained separately from normal creation snapshots and solved placements.
"""

import struct

from decode_assembly import (OCCURRENCE_GUID,OCCURRENCE_COLLECTION_GUID,
                             occurrence,collection)
from decode_component_creation import CREATE_COMPONENT,OCCURRENCE_DATUM,BOOKKEEPING,NIL_UUID
from decode_dependencies import SCOPE_GUID,scope_datum
from decode_parameters import read_string
from decode_placement import rigid_matrix
from decode_sketch import numbers,reference,same
from decode_timeline_state_details import decode_feature_state_footer

MIRROR = '71BBEDD5-81F8-4585-816B-05908C207204'
DERIVED = '66E375EA-40F1-4115-8D83-0F23DD30593E'
FRAME = '2E3AC990-483D-4A55-8662-C064B976A957'
COMPONENT = 'E03784ED-5E19-4E14-B9F2-3B07017018CD'
SCOPE = 'Observed Mirror-owned CreateComponent -> component scope and Mirror backlinks -> DerivedInstance -> reciprocal datum -> created native occurrence; no Snapshot or solved placement inferred'


def decode_mirror_component_creations(data,records,features,assembly):
    """Return decoded/unresolved/scope without feature or summary mutation.

    Keep successes separate from canonical snapshot creations. Successful IDs
    alone may clear the corresponding base-reader unresolved entries.
    """
    groups={}
    for r in records:
        if r.is_primary:
            groups.setdefault(r.object_id,[]).append(r)
    primary={i:rs[0] for i,rs in groups.items() if len(rs)==1}
    components={c['object_id']:c for c in assembly['components']}
    occurrences={o['object_id']:o for o in assembly['native_occurrences']}
    decoded,unresolved=[],[]

    def typed(identity,guid):
        r=primary.get(identity)
        if r is None or r.class_guid!=guid:
            raise ValueError('Mirror creation typed reference missing, ambiguous or wrong class')
        return r,data[r.body:r.end]

    def bookkeeping(identity,owner):
        _,b=typed(identity,BOOKKEEPING)
        if len(b)!=39 or reference(b,12)!=owner:
            raise ValueError('Mirror creation bookkeeping owner backlink disagrees')

    def native_occurrence(identity):
        r,_=typed(identity,OCCURRENCE_GUID)
        if r.payload_start is None:
            raise ValueError('Mirror creation occurrence has no indexed raw payload')
        result=occurrence(data[r.payload_start:r.end],identity)
        index=occurrences.get(identity)
        if index is None or any(result[k]!=index[k] for k in ('component_object_id','parent_collection_object_id','instance_guid_text','local_transform')):
            raise ValueError('Mirror creation native occurrence and assembly index disagree')
        if result['parent_collection_object_id'] is None:
            raise ValueError('Mirror creation cannot select document root occurrence')
        cr,cb=typed(result['parent_collection_object_id'],OCCURRENCE_COLLECTION_GUID)
        parent=collection(cb,cr.object_id)
        if identity not in parent['occurrence_object_ids'] or parent['component_object_id'] not in components:
            raise ValueError('Mirror creation occurrence/parent collection ownership is not reciprocal')
        return result,parent

    for feature in features:
        r=primary.get(feature['object_id'])
        if r is None or r.class_guid!=CREATE_COMPONENT:
            continue
        b=data[r.body:r.end]
        try:
            owner_id=reference(b,210)
        except (ValueError,IndexError,struct.error):
            continue
        if primary.get(owner_id) is None or primary[owner_id].class_guid!=MIRROR:
            continue
        try:
            namespace,end=read_string(b,13);label,label_end=read_string(b,100)
            if (len(b)!=222 or b[:2]!=bytes(2) or namespace!=NIL_UUID or end!=89
                    or b[89:100]!=bytes(7)+b'\xff'*4 or label!='CreateComponent' or label_end!=134
                    or struct.unpack_from('<Q',b,134)[0]!=feature['stored_index'] or b[-1:]!=b'\0'
                    or r.start!=feature['record_offset']):
                raise ValueError('Unobserved Mirror-owned CreateComponent header')
            creation_state=decode_feature_state_footer(data,r,primary)
            if (creation_state.get('related_feature_reference') or {}).get('object_id')!=owner_id:
                raise ValueError('Mirror creation typed footer owner disagrees')
            scope_id=reference(b,2);_,scope_body=typed(scope_id,SCOPE_GUID)
            scope=scope_datum(scope_body,scope_id,components)
            if scope['optional_related_object_id']!=owner_id:
                raise ValueError('Mirror creation scope and direct owner disagree')
            bookkeeping(scope['anchor_object_id'],scope_id)
            component_id=scope['component_object_id'];typed(component_id,COMPONENT)
            mirror_record,mirror=typed(owner_id,MIRROR)
            if (len(mirror) not in (542,544) or mirror[:2]!=bytes(2)
                    or mirror[13:20]!=bytes.fromhex('00000101000000') or mirror[31:35]!=bytes(4)
                    or struct.unpack_from('<I',mirror,60)[0]!=1 or reference(mirror,197)!=r.object_id
                    or struct.unpack_from('<I',mirror,len(mirror)-109)[0]!=3
                    or [reference(mirror,len(mirror)-105+11*i) for i in range(3)]!=[owner_id,r.object_id,scope_id]):
                raise ValueError('Mirror creation direct/repeated Mirror backreferences disagree')
            mirror_state=decode_feature_state_footer(data,mirror_record,primary)
            if (mirror_state.get('related_feature_reference') or {}).get('object_id')!=owner_id:
                raise ValueError('Mirror creation owner footer is not self-related')
            derived_id=reference(mirror,20);derived_record,derived=typed(derived_id,DERIVED)
            if (len(derived)!=563 or derived[:2]!=bytes(2) or reference(derived,2)!=owner_id
                    or struct.unpack_from('<I',derived,13)[0]!=1 or derived[28]!=0
                    or struct.unpack_from('<I',derived,157)[0]!=1):
                raise ValueError('Unobserved Mirror derived-instance header/owner/matrix layout')
            datum_id=reference(derived,17)
            if any(reference(derived,offset)!=datum_id for offset in (172,187,202,426)):
                raise ValueError('Mirror derived-instance repeated occurrence datum references disagree')
            frame_id=reference(derived,161);typed(frame_id,FRAME)
            decode_feature_state_footer(data,derived_record,primary)
            matrix=rigid_matrix(numbers(derived,29,16))
            _,datum=typed(datum_id,OCCURRENCE_DATUM)
            if (len(datum)!=39 or datum[:2]!=bytes(2) or datum[13:16]!=b'\1\0\0'
                    or datum[27]!=0 or reference(datum,28)!=derived_id):
                raise ValueError('Mirror creation occurrence datum owner disagrees with derived instance')
            book_id=reference(datum,16);bookkeeping(book_id,datum_id)
            target_id=reference(datum,2);target,parent=native_occurrence(target_id)
            if target['component_object_id']!=component_id:
                raise ValueError('Mirror creation component scope disagrees with derived occurrence')
            source_id=reference(mirror,64);source,source_parent=native_occurrence(source_id)
            if (reference(mirror,186)!=source['component_object_id'] or source_id==target_id
                    or source_parent['object_id']!=parent['object_id']):
                raise ValueError('Mirror creation source/component/parent copies disagree')
            if not same(matrix,target['local_transform']):
                raise ValueError('Mirror derived-instance transform disagrees with saved native occurrence cache')
            paths=[p for p in assembly['occurrence_paths'] if p['native_occurrence_object_id']==target_id]
            decoded.append({'feature_object_id':r.object_id,'kind':'MirrorOwnedComponentCreation',
                'component_object_id':component_id,'component_name':components[component_id]['name'],
                'component_scope_object_id':scope_id,'scope_bookkeeping_object_id':scope['anchor_object_id'],
                'owning_mirror_feature_object_id':owner_id,'source_native_occurrence_object_id':source_id,
                'derived_instance_feature_object_id':derived_id,'derived_context_frame_object_id':frame_id,
                'occurrence_datum_object_id':datum_id,'datum_bookkeeping_object_id':book_id,
                'native_occurrence_object_id':target_id,'occurrence_paths':[p['path'] for p in paths],
                'parent_collection_object_id':parent['object_id'],
                'parent_component_object_id':parent['component_object_id'],
                'parent_component_name':components[parent['component_object_id']]['name'],
                'stored_derived_instance_transform':matrix,'stored_occurrence_local_transform':target['local_transform'],
                'derived_instance_transform_matches_occurrence_cache':True,
                'stored_occurrence_path_transforms':[{'path':p['path'],'matrix':p.get('world_transform',p.get('stored_occurrence_cache_transform'))} for p in paths],
                'snapshot_status':'No Snapshot record in this correspondence: CreateComponent and scope explicitly reference MirrorComponent',
                'transform_scope':'Stored derived-feature and occurrence caches; not an initial snapshot timestamp guarantee, reflection replay, grounding or solved joint placement',
                'uninterpreted_derived_middle_hex':derived[157:426].hex(),
                'association':'CreateComponent/scope/Mirror reciprocal links, repeated derived datum, datum bookkeeping owner, typed occurrence component and parent membership all agree',
                'remaining_scope':'Existing separate Mirror provenance owns plane/source routes and general Mirror controls remain partial'})
        except (ValueError,KeyError,IndexError,UnicodeError,struct.error) as error:
            unresolved.append({'feature_object_id':r.object_id,'kind':'MirrorOwnedComponentCreation','reason':str(error)})
    return {'decoded':decoded,'unresolved':unresolved,'scope':SCOPE,
            'limitations':'Only captured one-output Mirror-owned component creation association; no canonical snapshot fields, full Mirror regeneration, external component resolution or solved assembly placement'}
