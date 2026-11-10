"""Observed nested MirrorComponent source/derived occurrence route provenance.

Typed reference chains establish identity and component ownership. Composed
occurrence/context matrices are stored-cache evidence, not reflection replay,
current solved placement, or token-derived identity.
"""

import argparse
import json
from pathlib import Path
import struct
import uuid

from decode_assembly import (OCCURRENCE_GUID,OCCURRENCE_COLLECTION_GUID,
                             occurrence as read_occurrence,collection as read_collection,multiply)
from decode_parameters import read_string
from decode_placement import IDENTITY,rigid_matrix
from decode_remaining_body_inputs import MIRROR_COMPONENT,_access,_known_descriptor
from decode_selection import known_construction_entities
from decode_sketch import numbers,reference,same


def decode_mirror_nested_occurrences(data,records,body,feature,known,assembly):
    primary,typed=_access(data,records)
    owner=feature['object_id']
    if (feature['class_guid']!=MIRROR_COMPONENT or len(body)!=544 or body[:2]!=bytes(2)
            or body[13:20]!=bytes.fromhex('00000101000000') or body[31:35]!=bytes(4)
            or struct.unpack_from('<I',body,60)[0]!=1):
        raise ValueError('Unsupported observed nested MirrorComponent layout/count')
    components={c['object_id']:c for c in assembly['components']}
    occurrences={o['object_id']:o for o in assembly['native_occurrences']}
    roots=[o for o in occurrences.values() if o['parent_collection_object_id'] is None]
    if len(roots)!=1:raise ValueError('Nested Mirror root occurrence ambiguous')
    if not same(roots[0]['local_transform'],IDENTITY):
        raise ValueError('Unobserved nonidentity document-root occurrence cache')
    root_component=roots[0]['component_object_id']

    def native_occurrence(identity):
        record,_=typed(identity,OCCURRENCE_GUID)
        item=read_occurrence(data[record.payload_start:record.end],identity)
        if identity not in occurrences or item['instance_guid_text']!=occurrences[identity]['instance_guid_text']:
            raise ValueError('Nested Mirror native occurrence and assembly index disagree')
        if item['component_object_id'] not in components:
            raise ValueError('Nested Mirror occurrence component unresolved')
        collection_record,_=typed(item['parent_collection_object_id'],OCCURRENCE_COLLECTION_GUID)
        collection=read_collection(data[collection_record.body:collection_record.end],collection_record.object_id)
        if identity not in collection['occurrence_object_ids']:
            raise ValueError('Nested Mirror occurrence/parent collection membership not reciprocal')
        return item,collection

    def route(identity,expected_count):
        _,payload=typed(identity,'96CBEA21-17E0-4BCB-BA77-04EA87B47934')
        if (len(payload)!=330+76*expected_count or payload[:2]!=bytes(2)
                or struct.unpack_from('<I',payload,2)[0]!=expected_count):
            raise ValueError('Nested Mirror occurrence route count/size unsupported')
        ids=[];cursor=6
        for _ in range(expected_count):
            text,cursor=read_string(payload,cursor)
            if len(text)!=36:raise ValueError('Nested route instance UUID length unsupported')
            uuid.UUID(text)
            matches=[o['object_id'] for o in occurrences.values() if o['instance_guid_text']==text]
            if len(matches)!=1:raise ValueError('Nested route UUID does not select one native occurrence')
            ids.append(matches[0])
        namespace,cursor=read_string(payload,cursor)
        entity,cursor=read_string(payload,cursor)
        if len(namespace)!=36 or len(entity)!=36:
            raise ValueError('Nested route source UUID lengths unsupported')
        uuid.UUID(namespace);uuid.UUID(entity)
        if payload[cursor:cursor+8]!=struct.pack('<Q',2):
            raise ValueError('Nested route endpoint marker unsupported')
        repeated,cursor=read_string(payload,cursor+8)
        endpoint,cursor=read_string(payload,cursor)
        if len(endpoint)!=36:raise ValueError('Nested route endpoint UUID length unsupported')
        uuid.UUID(endpoint)
        if namespace!=repeated or payload[cursor:]!=struct.pack('<QI',2,0):
            raise ValueError('Nested route namespace/footer mismatch')
        parent_component=root_component;cache=list(IDENTITY);chain=[]
        for identity in ids:
            occurrence,collection=native_occurrence(identity)
            if collection['component_object_id']!=parent_component:
                raise ValueError('Nested route ancestor order and native parent collections disagree')
            cache=multiply(cache,occurrence['local_transform'])
            chain.append({'native_occurrence_object_id':identity,'instance_guid_text':occurrence['instance_guid_text'],
                          'component_object_id':occurrence['component_object_id'],
                          'component_name':components[occurrence['component_object_id']]['name'],
                          'parent_collection_object_id':collection['object_id'],
                          'parent_component_object_id':parent_component,
                          'stored_local_transform':occurrence['local_transform']})
            parent_component=occurrence['component_object_id']
        return {'occurrence_object_ids':ids,'chain':chain,'namespace_text':namespace,'entity_guid_text':entity,
                'endpoint_guid_text':endpoint,'composed_stored_occurrence_cache_matrix':cache}

    def frame(identity,parent):
        _,payload=typed(identity,'2E3AC990-483D-4A55-8662-C064B976A957')
        length=206 if parent else 196
        if (len(payload)!=length or payload[:20]!=bytes(20)
                or struct.unpack_from('<I',payload,20)[0]!=3 or payload[24:37]!=bytes(13)):
            raise ValueError('Nested Mirror context frame framing unsupported')
        if parent:
            link_id=reference(payload,37)
            typed(link_id,'549FBB80-B890-473E-A5C0-415D3D9BF4E6')
            marker,matrix_offset,owner_offset,wrapper_offset,tail=48,49,178,189,200
        else:
            if payload[37]!=0:raise ValueError('Nested source frame optional link encoding unsupported')
            link_id=None
            marker,matrix_offset,owner_offset,wrapper_offset,tail=38,39,168,179,190
        if (payload[marker]!=0 or payload[owner_offset-1]!=0 or reference(payload,owner_offset)!=owner
                or payload[tail:]!=bytes(6)):
            raise ValueError('Nested Mirror context frame reciprocal owner/footer unsupported')
        cache=rigid_matrix(numbers(payload,matrix_offset,16))
        wrapper_id=reference(payload,wrapper_offset)
        _,wrapper=typed(wrapper_id,'FF415D89-A1DB-44AC-B824-E9A772B86ED4')
        if len(wrapper)!=18 or wrapper[:7]!=bytes.fromhex('00000001000000'):
            raise ValueError('Nested context route wrapper count unsupported')
        route_id=reference(wrapper,7)
        selected=route(route_id,1 if parent else 2)
        selected['route_object_id']=route_id
        if not same(cache,selected['composed_stored_occurrence_cache_matrix']):
            raise ValueError('Nested frame cache and explicit native route composition disagree')
        return {'frame_object_id':identity,'context_link_object_id':link_id,'route_wrapper_object_id':wrapper_id,
                'route':selected,'stored_context_matrix':cache,
                'link_scope':'Typed context link retained; its ownership/field meanings are not inferred'}

    parent_context=frame(reference(body,35),True)
    source_context=frame(reference(body,171),False)
    if source_context['route']['occurrence_object_ids'][:1]!=parent_context['route']['occurrence_object_ids']:
        raise ValueError('Nested source route does not extend parent context route')
    source_id=reference(body,64)
    source,source_collection=native_occurrence(source_id)
    if source_context['route']['occurrence_object_ids'][-1]!=source_id or reference(body,186)!=source['component_object_id']:
        raise ValueError('Nested Mirror direct source/route/component identity copies disagree')
    parent_id=parent_context['route']['occurrence_object_ids'][-1]
    parent,_=native_occurrence(parent_id)
    owner_component=parent['component_object_id']
    if source_collection['component_object_id']!=owner_component or feature.get('component_object_id',owner_component)!=owner_component:
        raise ValueError('Nested Mirror feature/source collection and parent context ownership disagree')
    derived_id=reference(body,20)
    _,derived=typed(derived_id,'66E375EA-40F1-4115-8D83-0F23DD30593E')
    if len(derived)!=563 or derived[:2]!=bytes(2) or reference(derived,2)!=owner:
        raise ValueError('Nested Mirror derived-instance reciprocal owner unsupported')
    link_id=reference(derived,17)
    _,link=typed(link_id,'2D6E13A1-BBEF-4FB3-9277-00D99F634136')
    if len(link)!=39 or link[:2]!=bytes(2) or reference(link,28)!=derived_id:
        raise ValueError('Nested Mirror derived occurrence-link reciprocal owner unsupported')
    target_id=reference(link,2)
    target,target_collection=native_occurrence(target_id)
    if target_collection['object_id']!=source_collection['object_id']:
        raise ValueError('Observed nested Mirror source/output must share parent collection')
    descriptor_id=reference(body,315)
    geometry_id=reference(body,2)
    _,geometry=typed(geometry_id,'7B6C3C2D-4096-4E6D-B225-699E8C2D9355')
    if len(geometry)!=322 or reference(geometry,223)!=descriptor_id or reference(geometry,311)!=owner:
        raise ValueError('Nested Mirror support geometry/descriptor reciprocal owner unsupported')
    mirror_plane=_known_descriptor(typed,descriptor_id,owner,known,263)
    _,descriptor=typed(descriptor_id,'5A1BF548-241F-46FD-9FB5-E4B05126EB9D')
    namespace,cursor=read_string(descriptor,17);endpoint,cursor=read_string(descriptor,cursor)
    for context in (parent_context,source_context):
        if context['route']['namespace_text']!=namespace or context['route']['endpoint_guid_text']!=endpoint:
            raise ValueError('Nested context routes and owned mirror-plane descriptor UUIDs disagree')
    def occurrence_summary(item,cache):
        paths=[p['path'] for p in assembly['occurrence_paths'] if p['native_occurrence_object_id']==item['object_id']]
        return {'native_occurrence_object_id':item['object_id'],'component_object_id':item['component_object_id'],
                'component_name':components[item['component_object_id']]['name'],'occurrence_paths':paths,
                'stored_local_transform':item['local_transform'],'composed_stored_occurrence_cache_matrix':cache}
    target_cache=multiply(parent_context['stored_context_matrix'],target['local_transform'])
    return {'feature_object_id':owner,'feature_class_guid':MIRROR_COMPONENT,'status':'ObservedNestedOccurrenceMirrorProvenance',
            'owner_component_object_id':owner_component,'owner_component_name':components[owner_component]['name'],
            'parent_context':parent_context,'source_context':source_context,
            'source_occurrence':occurrence_summary(source,source_context['stored_context_matrix']),
            'derived_occurrence':occurrence_summary(target,target_cache),
            'source_and_output_parent_collection_object_id':source_collection['object_id'],
            'derived_instance_feature_object_id':derived_id,'derived_occurrence_link_object_id':link_id,
            'mirror_plane':mirror_plane,
            'association':'Owned parent/source frames carry exact one-/two-level UUID routes; direct source occurrence agrees; source/output reciprocal collection owner is the parent component; derived-instance link explicitly selects output occurrence',
            'placement_scope':'Composed stored occurrence-cache and context matrices only; no reflection regeneration, joint solving or current grounding state inferred',
            'unresolved_controls':['General MirrorComponent operation/lifecycle replay','Compute/combine/tolerance semantics outside feature inputs','Native proxy tokens unavailable and never used for native ID associations']}


def validate_fixtures(root,zstd_library):
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records
    folder=root/'mirrorassemblydatum-700af16e9fc6';truth=json.loads((folder/'ground_truth.json').read_text())
    assert len(truth['samples'])==2 and not truth['errors'] and (folder/'complete.txt').is_file()
    report={'api_version':truth['fusion_version'],'samples':[],'negative_checks':[],
            'interface':'decode_mirror_nested_occurrences(data,records,body,feature,known,assembly)',
            'validation_command':'python3 decode_mirror_nested_occurrences.py --validate --zstd-library <local libzstd path>'}
    for sample in truth['samples']:
        assert sample['getter_errors'] and all(e['field']=='occurrence.nativeObject.entityToken' for e in sample['getter_errors'])
        archive=folder/sample['file'];stream=decode_basics(archive,zstd_library)['streams'][0]
        members=read_members(archive,zstd_library);data=members[stream['member']]
        records,_=design_records(data,members.get(stream['member'].replace('BulkStream.dat','MetaStream.dat')))
        by={r.object_id:r for r in records if r.is_primary};feature=next(f for f in stream['features'] if f.get('name')=='ProbeMirrorAssemblyDatum')
        record=by[feature['object_id']];known=known_construction_entities(data,records,stream['features'])
        result=decode_mirror_nested_occurrences(data,records,data[record.body:record.end],feature,known,stream['assembly_decoding'])
        actual=sample['actual_inputs'][0];source=result['source_occurrence'];target=result['derived_occurrence']
        actual_target=[o for o in sample['all_occurrences_after'] if o['component_name']==target['component_name']]
        checks={'explicit_source_path_matches_actual':source['occurrence_paths']==[actual['full_path_name']],
                'source_component_name_matches_actual':source['component_name']==actual['component_name'],
                'source_stored_context_composition_matches_actual':same(source['composed_stored_occurrence_cache_matrix'],actual['transform']),
                'parent_context_cache_matches_actual_request':same(result['parent_context']['stored_context_matrix'],sample['requested_parent']['transform']),
                'owner_is_parent_component_not_document_root':result['owner_component_name']==sample['requested_parent']['component_name'],
                'two_level_source_route_extends_one_level_parent_route':len(result['source_context']['route']['chain'])==2 and len(result['parent_context']['route']['chain'])==1,
                'derived_path_matches_independent_actual_collection':len(actual_target)==1 and target['occurrence_paths']==[actual_target[0]['full_path_name']],
                'derived_stored_composition_matches_actual_collection':len(actual_target)==1 and same(target['composed_stored_occurrence_cache_matrix'],actual_target[0]['transform']),
                'actual_resultFeatures_returns_null':sample['api_result_features']['status']=='returned_null',
                'unavailable_native_tokens_not_used':actual['native_object_token'] is None,
                'mirror_plane_matches_actual_getter':sample['mirror_plane_getter_status']=='returned_entity' and result['mirror_plane']['entity']['name']==sample['actual_mirror_plane']['name']}
        assert all(checks.values()),(sample['file'],checks)
        report['samples'].append({'archive':str(archive.relative_to(root)),'checks':checks,'decoded':result,
            'actual_source_input':actual,'independent_actual_target_occurrences':actual_target,'actual_getter_errors':sample['getter_errors'],
            'actual_resultFeatures':sample['api_result_features']})
        negative_case=data,records,feature,known,stream,by,result
    data,records,feature,known,stream,by,result=negative_case
    route_id=result['source_context']['route']['route_object_id'];route_record=by[route_id]
    body=data[route_record.body:route_record.end];guid,end=read_string(body,6)
    changed_guid=('0' if guid[0]!='0' else '1')+guid[1:]
    mutations=[('Nested source-frame reciprocal Mirror owner mismatch',result['source_context']['frame_object_id'],169,struct.pack('<Q',999999)),
               ('Nested source-route count unsupported',route_id,2,struct.pack('<I',3)),
               ('Nested ancestor valid UUID absent from native occurrences',route_id,10,changed_guid.encode('utf-16le')),
               ('Derived link reciprocal owner mismatch',result['derived_occurrence_link_object_id'],29,struct.pack('<Q',999999))]
    for label,identity,offset,replacement in mutations:
        record=by[identity];changed=bytearray(data);changed[record.body+offset:record.body+offset+len(replacement)]=replacement
        record=by[feature['object_id']]
        try:decode_mirror_nested_occurrences(bytes(changed),records,data[record.body:record.end],feature,known,stream['assembly_decoding'])
        except (ValueError,KeyError,IndexError,struct.error) as error:report['negative_checks'].append({'check':label,'passed':True,'reason':str(error)})
        else:raise AssertionError(label)
    report['limitations']=['Exact native source/output and parent ownership come from typed identities, UUID routes and reciprocal collection membership; no token or geometry-derived ID associations.',
                           'Only captured two-level source routes, one-level parent contexts and same-parent derived occurrences supported; deeper/repeated-context paths remain unsupported.',
                           'Matrices are stored occurrence/context caches corroborated by actual getters, including rotated parent; no general reflection, assembly solving or lifecycle replay.',
                           'Optional native proxy token getters fail as expected and are preserved; actual resultFeatures returnedNone in both captures.']
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate',required=True,action='store_true');parser.add_argument('--zstd-library',required=True,type=Path)
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('mirror-nested-occurrence-decoding.json'))
    args=parser.parse_args();report=validate_fixtures(Path(__file__).resolve().parent,args.zstd_library)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'samples':len(report['samples']),'negative_checks':len(report['negative_checks']),'output':str(args.output)}))
