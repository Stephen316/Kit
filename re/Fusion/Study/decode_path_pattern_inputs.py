"""Observed Feature/Occurrence PathPattern inputs and stored assembly results.

Common scalar/path/element/suppression controls are parsed once by the shared
reader. Typed input leaves and occurrence datums establish associations before
cache comparisons. No feature regeneration or solved assembly state is implied.
"""
import math
import struct
import uuid

from decode_asbuilt_joints import make_asbuilt_context_readers
from decode_assembly import collection as occurrence_collection, multiply
from decode_body_selections import decode_body_selections
from decode_component_creation import OCCURRENCE_DATUM, BOOKKEEPING
from decode_parameters import read_string
from decode_path_patterns import parse_path_pattern_controls
from decode_placement import IDENTITY, rigid_matrix
from decode_selection import native_proxy_references
from decode_sketch import numbers, reference, same

FEATURE='B0B3D9E5-1C25-47BC-ABCD-E723F193DF1B'
OCCURRENCE_PATTERN='EBCDE6CC-CA52-44AD-A6B0-76265794E4BD'
CONTROL='BE1FB171-D98A-4A4D-99C2-3738627CF79C'
DESCRIPTOR='5A1BF548-241F-46FD-9FB5-E4B05126EB9D'
LEAF='90055C05-546C-4EE7-B3C9-3DD922AD0C9C'
ANCHOR='D26351F0-5940-4D23-AA20-2C35475A6D9E'
ELEMENT='414A485F-2F33-4B4F-9641-B6D824E214AF'
SCOPE='Observed single Extrude Feature Optimized/Identical or same-root Occurrence PathPattern, straight sketch line, spacing, zero start and no flip/symmetry/suppression; typed input/result associations and stored matrices only, no regeneration or solved assembly placement'


def decode_path_pattern_inputs(data,records,features,assembly,*,body_selections=None):
    records=list(records)
    readers=make_asbuilt_context_readers(data,records,assembly)
    typed,primary,frame=readers['typed'],readers['primary'],readers['frame']
    native_occurrence,text_uuid=readers['native_occurrence'],readers['text_uuid']
    named={f['object_id']:f for f in features}
    components={c['object_id']:c for c in assembly['components']}
    bodies=body_selections if body_selections is not None else decode_body_selections(data,records)
    anchors={a['object_id']:a for a in bodies['body_anchors']}
    result=dict(decoded=[],unresolved=[],scope=SCOPE)

    def anchor(identity,owner):
        _,body=typed(identity,ANCHOR)
        item=anchors.get(identity)
        if (len(body)!=102 or reference(body,91)!=owner or item is None
                or item['source_owner_object_id']!=owner):
            raise ValueError('PathPattern typed result/source anchor owner mismatch')
        return item

    def identity_leaf(identity):
        _,payload=typed(identity,LEAF)
        if len(payload)!=10 or payload[:2]!=bytes(2):
            raise ValueError('PathPattern source identity leaf framing mismatch')
        return struct.unpack_from('<Q',payload,2)[0]

    def bounded_controls(control_id,feature,**kwargs):
        settings=parse_path_pattern_controls(data,records,control_id,feature,features,**kwargs)
        if (settings['quantity']!=3 or not math.isfinite(settings['distance_cm'])
                or settings['is_flipped'] or settings['is_symmetric']
                or settings['orientation_along_path'] or settings['stored_start_fraction']!=0
                or settings['distance_type']!='Spacing' or settings['suppressed_element_ids']
                or settings['path'].get('kind')!='Line'):
            raise ValueError('Unobserved Feature/Occurrence PathPattern control combination')
        settings.update(start_fraction_scope='Captured zero start, unflipped and nonsymmetric straight sketch-line cases only',
            path_traversal_status='Source sketch line identity/natural endpoints decoded; Path opposed flag remains unresolved',
            geometry_status='No persistent result topology, solid/feature replay or joint-solved placement reconstructed')
        return settings

    def feature_input(body,feature):
        owner=feature['object_id']
        if body[:6]!=bytes.fromhex('000100000000') or body[28:32]!=bytes(4):
            raise ValueError('Unobserved Feature PathPattern prefix')
        control_id,collection_id=reference(body,6),reference(body,17)
        _,controls=typed(control_id,CONTROL)
        compute,entity=struct.unpack_from('<II',controls,125)
        if (compute,entity) not in ((0,1),(1,1)):
            raise ValueError('Unobserved Feature PathPattern compute/entity modes')
        settings=bounded_controls(control_id,feature,allowed_type_codes=((0,1),(1,1)))
        _,collection=typed(collection_id,'8DB90DAE-3FF5-4E01-BACC-00AAA3EBB3EF')
        if (len(collection)!=100 or collection[:10]!=bytes(6)+struct.pack('<I',1)
                or struct.unpack_from('<I',collection,21)[0]!=1
                or reference(collection,36)!=owner or reference(collection,89)!=owner):
            raise ValueError('Feature PathPattern singleton input collection/count/owner mismatch')
        descriptor_id,association_id=reference(collection,10),reference(collection,25)
        if settings['auxiliary_descriptor_object_ids']!=[descriptor_id]:
            raise ValueError('Feature PathPattern input collection/proxy copies disagree')
        _,descriptor=typed(descriptor_id,DESCRIPTOR)
        if (len(descriptor)!=263 or descriptor[:2]!=bytes(2)
                or struct.unpack_from('<I',descriptor,13)[0]!=1
                or reference(descriptor,252)!=owner):
            raise ValueError('Feature PathPattern source descriptor framing/owner mismatch')
        namespace,cursor=text_uuid(descriptor,17);entity_text,cursor=text_uuid(descriptor,cursor)
        if descriptor[cursor:cursor+16]!=struct.pack('<QII',2,0,1):
            raise ValueError('Feature PathPattern descriptor context/anchor counts unsupported')
        leaf_id=reference(descriptor,2);source_id=identity_leaf(leaf_id)
        source=named.get(source_id)
        typed(source_id,'DD405BC2-D673-44F0-8833-5CB2A1C186C7')
        if source is None or source['class_guid']!='DD405BC2-D673-44F0-8833-5CB2A1C186C7' or source_id==owner:
            raise ValueError('Feature PathPattern explicit source Extrude absent or self-referential')
        anchor_id=reference(descriptor,cursor+16);source_anchor=anchor(anchor_id,source_id)
        _,association=typed(association_id,'C46D3EEB-40E1-43FA-83DC-9CB204335417')
        if len(association)!=181 or association[:10]!=bytes.fromhex('00000a00000000000000'):
            raise ValueError('Feature PathPattern association framing unsupported')
        ans,cursor=text_uuid(association,10);aid,cursor=text_uuid(association,cursor)
        if (ans,aid)!=(namespace,entity_text) or association[cursor:cursor+8]!=struct.pack('<Q',2):
            raise ValueError('Feature PathPattern association descriptor namespace differs')
        bridge_id=reference(association,cursor+8)
        _,bridge=typed(bridge_id,'CB4F4CC2-9D6F-48BA-9B1F-20C1992C9C9C')
        if len(bridge)!=14 or bridge[:2]!=bytes(2) or bridge[13]!=0:
            raise ValueError('Feature PathPattern association anchor bridge framing unsupported')
        second_leaf=reference(bridge,2)
        if identity_leaf(second_leaf)!=anchor_id:
            raise ValueError('Feature PathPattern association/source-anchor leaf copies disagree')
        count=struct.unpack_from('<I',body,32)[0]
        if count!=settings['quantity']-1:
            raise ValueError('Feature PathPattern generated result count mismatch')
        result_ids=[reference(body,36+11*i) for i in range(count)]
        if len(set(result_ids))!=count:raise ValueError('Feature PathPattern result anchors duplicated')
        for identity in result_ids:anchor(identity,owner)
        cursor=36+11*count
        if body[cursor:cursor+8]!=bytes(8):raise ValueError('Feature PathPattern result separator mismatch')
        nil,cursor=text_uuid(body,cursor+8)
        if nil!=str(uuid.UUID(int=0)) or body[cursor:cursor+3]!=bytes(3):
            raise ValueError('Feature PathPattern nil UUID/repeated-source separator mismatch')
        cursor+=3
        if struct.unpack_from('<I',body,cursor)[0]!=9:raise ValueError('Feature PathPattern dependency count mismatch')
        repeated=[reference(body,cursor+4+11*i) for i in range(9)];cursor+=103
        path_proxy_id=reference(controls,64);path_descriptors,_=native_proxy_references(data,primary[path_proxy_id])
        aux_id=reference(controls,94);_,aux=typed(aux_id,'69EE2FA7-BCC7-449E-9CA9-976CEFDFED44')
        if len(aux)!=178 or reference(aux,167)!=owner:raise ValueError('Feature PathPattern auxiliary provider owner mismatch')
        if repeated!=[collection_id,settings['auxiliary_selection_record_object_id'],descriptor_id,
                settings['quantity_binding_object_id'],path_proxy_id,*path_descriptors,settings['distance_binding_object_id'],
                aux_id,reference(aux,79)]:
            raise ValueError('Feature PathPattern explicit dependency copies disagree')
        if struct.unpack_from('<I',body,cursor)[0]!=8:raise ValueError('Feature PathPattern label marker mismatch')
        label,cursor=read_string(body,cursor+4);index=struct.unpack_from('<Q',body,cursor)[0]
        name,cursor=read_string(body,cursor+8)
        if label!='PathPattern' or index!=feature['stored_index'] or name!=feature.get('name') or len(body)-cursor!=66:
            raise ValueError('Feature PathPattern feature name/index/footer framing mismatch')
        settings.update(pattern_entity_type='Features',pattern_entity_type_api_value=1,
            stored_entity_type_code=entity,stored_compute_option_code=compute,
            pattern_compute_option={0:'Optimized',1:'Identical'}[compute],
            compute_option_status='Active Feature compute option contrasted by actual Optimized/Identical getters',
            input_entity_count=1,input_entity_collection_object_id=collection_id,
            input_descriptors=[dict(descriptor_object_id=descriptor_id,terminal_object_id=leaf_id,
                association_record_object_id=association_id,association_bridge_object_id=bridge_id,
                association_terminal_object_id=second_leaf,source_feature_object_id=source_id,
                source_feature_class_guid=source['class_guid'],source_feature_name=source.get('name'),
                source_body_anchor_object_id=anchor_id,source_native_body_object_id=source_anchor['native_body_object_id'],
                namespace_text=namespace,entity_guid_text=entity_text)],
            result_record_object_ids=result_ids,generated_result_reference_count=count,
            input_selection_status='Typed descriptor leaf selects Extrude; matching association UUIDs and second typed leaf corroborate its owned body anchor',
            compute_status='Observed Feature Optimized/Identical controls only; no feature regeneration')
        return settings

    def occurrence_input(body,feature):
        owner=feature['object_id']
        if body[:7]!=bytes(3)+struct.pack('<I',3):
            raise ValueError('Unobserved Occurrence PathPattern member count/prefix')
        datum_ids=[reference(body,7)]
        if body[18]!=1:raise ValueError('Occurrence PathPattern generated-list marker mismatch')
        stored_matrices=[];cursor=19
        for _ in range(2):
            datum_ids.append(reference(body,cursor));cursor+=11
            if body[cursor]!=0:raise ValueError('Occurrence PathPattern explicit result matrix marker mismatch')
            cursor+=1;stored_matrices.append(rigid_matrix(numbers(body,cursor,16)));cursor+=128
        if struct.unpack_from('<I',body,cursor)[0]!=3:
            raise ValueError('Occurrence PathPattern UUID table count mismatch')
        cursor+=4;table=[]
        for ordinal in range(3):
            index=struct.unpack_from('<Q',body,cursor)[0];flag=struct.unpack_from('<I',body,cursor+8)[0];cursor+=12
            instance,cursor=text_uuid(body,cursor);source_instance,cursor=text_uuid(body,cursor)
            if index!=ordinal or flag!=1:raise ValueError('Occurrence PathPattern UUID table ordinal/flag mismatch')
            table.append(dict(ordinal=ordinal,instance_guid_text=instance,source_instance_guid_text=source_instance))
        control_id=reference(body,cursor);cursor+=11
        nil,cursor=text_uuid(body,cursor)
        if nil!=str(uuid.UUID(int=0)) or body[cursor:cursor+3]!=bytes(3):
            raise ValueError('Occurrence PathPattern repeated-source UUID separator mismatch')
        cursor+=3
        if struct.unpack_from('<I',body,cursor)[0]!=9:raise ValueError('Occurrence PathPattern repeated reference count mismatch')
        repeated=[reference(body,cursor+4+11*i) for i in range(9)];cursor+=103
        if body[cursor:cursor+4]!=b'\xff'*4:raise ValueError('Occurrence PathPattern feature label prefix mismatch')
        label,cursor=read_string(body,cursor+4);index=struct.unpack_from('<Q',body,cursor)[0]
        name,cursor=read_string(body,cursor+8)
        if (label!='PathPattern' or index!=feature['stored_index'] or name!=feature.get('name')
                or len(body)-cursor!=76):
            raise ValueError('Occurrence PathPattern feature name/index/footer framing mismatch')
        occurrences=[]
        for i,identity in enumerate(datum_ids):
            _,datum=typed(identity,OCCURRENCE_DATUM)
            if (len(datum)!=39 or datum[:2]!=bytes(2) or datum[13:16]!=b'\1\0\0' or datum[27]!=0):
                raise ValueError('Occurrence PathPattern datum framing mismatch')
            if i and reference(datum,28)!=owner:raise ValueError('Occurrence PathPattern created datum owner mismatch')
            book_id=reference(datum,16);_,book=typed(book_id,BOOKKEEPING)
            if len(book)!=39 or book[:12]!=bytes(12) or reference(book,12)!=identity or book[31:]!=bytes(8):
                raise ValueError('Occurrence PathPattern datum bookkeeping backlink mismatch')
            occurrence=native_occurrence(reference(datum,2))
            if (table[i]['instance_guid_text']!=occurrence['instance_guid_text']
                    or table[i]['source_instance_guid_text']!=table[0]['instance_guid_text']):
                raise ValueError('Occurrence PathPattern UUID table differs from typed datum occurrences')
            occurrences.append(occurrence)
        if len({o['object_id'] for o in occurrences})!=3 or len({o['component_object_id'] for o in occurrences})!=1:
            raise ValueError('Occurrence PathPattern distinct same-definition membership mismatch')
        source=occurrences[0];source_id=source['object_id']
        if len({o['parent_collection_object_id'] for o in occurrences})!=1:
            raise ValueError('Occurrence PathPattern source/results have different parent collections')
        collection_id=source['parent_collection_object_id']
        collection_record,listing=typed(collection_id,'904F885E-D859-4755-A7EF-6EBED8732FAD')
        listing=occurrence_collection(listing,collection_id);component_id=listing['component_object_id']
        typed(component_id,'E03784ED-5E19-4E14-B9F2-3B07017018CD')
        roots=[o for o in assembly['native_occurrences'] if o['parent_collection_object_id'] is None]
        if (len(roots)!=1 or roots[0]['component_object_id']!=component_id
                or any(o['object_id'] not in listing['occurrence_object_ids'] for o in occurrences)):
            raise ValueError('Occurrence PathPattern reciprocal root collection membership unsupported')
        component=components.get(source['component_object_id'])
        if component is None:raise ValueError('Occurrence PathPattern source component summary missing')
        for matrix,o in zip(stored_matrices,occurrences[1:]):
            if not same(matrix,o['local_transform']):raise ValueError('Occurrence PathPattern result datum/native occurrence matrices differ')

        def auxiliary(_data,_records,identity,requested_owner,_features):
            _,proxy=typed(identity,'2CA5A1CD-C99B-4C9B-91AF-57989148E841')
            if (requested_owner!=owner or len(proxy)!=114 or proxy[:6]!=bytes(6)
                    or proxy[28:32]!=struct.pack('<I',1) or reference(proxy,103)!=owner):
                raise ValueError('Occurrence PathPattern input context proxy framing/owner mismatch')
            root_frame=frame(reference(proxy,6),owner,0);source_frame=frame(reference(proxy,17),owner,0)
            if (root_frame['stored_route_mode']!=0 or source_frame['stored_route_mode']!=1
                    or root_frame['native_occurrence_object_id']!=roots[0]['object_id']
                    or source_frame['native_occurrence_object_id']!=source_id
                    or (root_frame['terminal_namespace_text'],root_frame['terminal_entity_guid_text'])
                        !=(source_frame['terminal_namespace_text'],source_frame['terminal_entity_guid_text'])
                    or not same(source_frame['stored_context_matrix'],source['local_transform'])
                    or not same(root_frame['stored_context_matrix'],IDENTITY)):
                raise ValueError('Occurrence PathPattern input source/root context copies disagree')
            flags_id=reference(proxy,32);_,flags=typed(flags_id,'2DF7DA30-A4E4-4260-AFD1-D9C7154CB44B')
            if len(flags)!=133 or flags[:3]!=bytes(3) or flags[131:]!=b'\1\0':
                raise ValueError('Occurrence PathPattern copied context flag/matrix framing mismatch')
            copied=rigid_matrix(numbers(flags,3,16))
            if not same(copied,source_frame['stored_context_matrix']):
                raise ValueError('Occurrence PathPattern secondary context matrix copy differs')
            return dict(selection_record_object_id=identity,descriptor_object_ids=[],
                root_context=root_frame,source_context=source_frame,
                copied_context_record_object_id=flags_id,stored_copied_source_matrix=copied,
                source_native_occurrence_object_id=source_id,
                scope='Explicit root/source UUID routes select native occurrence; copied historical local matrices are not solved placements')

        def element(_data,_records,identity,ordinal,requested_control,requested_owner):
            _,payload=typed(identity,ELEMENT)
            if (len(payload)!=32 or payload[:6]!=bytes(2)+struct.pack('<I',1)
                    or reference(payload,6)!=datum_ids[ordinal]
                    or struct.unpack_from('<I',payload,17)[0]!=ordinal
                    or reference(payload,21)!=requested_control or requested_owner!=owner):
                raise ValueError('Occurrence PathPattern element ordinal/datum/controller mismatch')
            return dict(element_record_object_id=identity,stored_ordinal=ordinal,
                occurrence_datum_object_id=datum_ids[ordinal],native_occurrence_object_id=occurrences[ordinal]['object_id'])
        settings=bounded_controls(control_id,feature,allowed_type_codes=((2,0),),allow_empty_ordinal_pairs=True,
            auxiliary_resolver=auxiliary,element_resolver=element)
        _,controls=typed(control_id,CONTROL)
        if struct.unpack_from('<I',controls,138)[0]!=0:
            raise ValueError('Occurrence PathPattern only observed empty ordinal-pair table supported')
        path_proxy_id=reference(controls,64);_,path_proxy=typed(path_proxy_id,'2CA5A1CD-C99B-4C9B-91AF-57989148E841')
        path_descriptors,props=native_proxy_references(data,primary[path_proxy_id])
        if props or len(path_descriptors)!=1:raise ValueError('Occurrence PathPattern path descriptor count/attributes unsupported')
        aux_id=reference(controls,94);_,aux=typed(aux_id,'69EE2FA7-BCC7-449E-9CA9-976CEFDFED44')
        # The point provider's explicit descriptor is a repeated dependency; no coordinate role is inferred.
        if (len(aux)!=178 or struct.unpack_from('<I',aux,75)[0]!=1 or reference(aux,167)!=owner):
            raise ValueError('Occurrence PathPattern auxiliary provider count/owner framing unsupported')
        aux_descriptor=reference(aux,79)
        _,aux_definition=typed(aux_descriptor,DESCRIPTOR)
        if len(aux_definition)!=263 or reference(aux_definition,252)!=owner:
            raise ValueError('Occurrence PathPattern repeated auxiliary descriptor owner mismatch')
        if repeated!=[settings['auxiliary_selection_record_object_id'],settings['quantity_binding_object_id'],
            path_proxy_id,path_descriptors[0],settings['distance_binding_object_id'],aux_id,aux_descriptor,*datum_ids[1:]]:
            raise ValueError('Occurrence PathPattern explicit dependency list copies disagree')
        source_matrix=source['local_transform']
        settings.update(pattern_entity_type='Occurrences',pattern_entity_type_api_value=3,
            stored_entity_type_code=0,stored_compute_option_code=2,pattern_compute_option=None,
            compute_option_status='Stored code2 matches inactive API getter; feature-only compute option has no occurrence replay semantics assigned',
            compute_status='Occurrence source/results and local matrix caches decoded; assembly solving and pattern regeneration unresolved',
            input_entity_count=1,source_native_occurrence_object_id=source_id,
            source_component_object_id=source['component_object_id'],source_component_name=component['name'],
            owner_component_object_id=component_id,occurrence_collection_object_id=collection_id,
            source_occurrence_datum_object_id=datum_ids[0],created_occurrence_datum_object_ids=datum_ids[1:],
            created_native_occurrence_object_ids=[o['object_id'] for o in occurrences[1:]],
            stored_source_local_matrix=source_matrix,stored_created_local_matrices=stored_matrices,
            stored_instance_uuid_table=table,
            relative_instance_matrix_caches=[multiply(matrix,_inverse_rigid(source_matrix)) for matrix in [source_matrix,*stored_matrices]],
            relative_matrix_scope='Algebraic created local matrix times inverse source local matrix; actual API element matrices agree only in these captured translated cases, no general solver mapping',
            input_selection_status='Owned source/root context routes, typed occurrence datums, UUID table and element backlinks independently agree',
            matrix_scope='Historical native local/copy matrices in cm; no current visibility, joint-solved world placement or general PathPattern transform evaluation')
        return settings

    for record in records:
        if not record.is_primary or record.class_guid not in(FEATURE,OCCURRENCE_PATTERN):continue
        body=data[record.body:record.end]
        try:
            if primary.get(record.object_id) is not record:raise ValueError('PathPattern feature identity ambiguous')
            if record.class_guid==FEATURE:
                if body[:6]!=bytes.fromhex('000100000000'):continue
                _,controls=typed(reference(body,6),CONTROL)
                if len(controls)>133 and struct.unpack_from('<II',controls,125)==(2,2):continue
            feature=named.get(record.object_id)
            if feature is None or feature['class_guid']!=record.class_guid or feature['record_offset']!=record.start:
                raise ValueError('PathPattern named feature missing/stale')
            settings=feature_input(body,feature) if record.class_guid==FEATURE else occurrence_input(body,feature)
            result['decoded'].append(dict(feature_object_id=record.object_id,kind='PathPattern',name=feature.get('name'),settings=settings))
        except (ValueError,KeyError,IndexError,struct.error,UnicodeError,TypeError) as error:
            result['unresolved'].append(dict(feature_object_id=record.object_id,class_guid=record.class_guid,reason=str(error)))
    return result


def _inverse_rigid(matrix):
    inverse=[matrix[0],matrix[4],matrix[8],0.,matrix[1],matrix[5],matrix[9],0.,matrix[2],matrix[6],matrix[10],0.,0.,0.,0.,1.]
    for row in range(3):inverse[4*row+3]=-sum(inverse[4*row+j]*matrix[4*j+3] for j in range(3))
    return rigid_matrix(inverse)
