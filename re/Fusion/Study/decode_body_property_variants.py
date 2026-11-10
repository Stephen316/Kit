"""Observed optional empty attributes on native body collections.

Repeated membership and reciprocal body/mapping/context/component references
establish ownership. Stored body geometry/material/lifecycle are not interpreted.
"""

import argparse
import json
from pathlib import Path
import struct

from decode_body_properties import BODY,COLLECTION
from decode_extrude import optional_reference
from decode_sketch import attributes,reference


def decode_body_collection_attribute_variants(data,records,assembly,body_properties=None):
    groups={}
    for r in records:
        if r.is_primary:groups.setdefault(r.object_id,[]).append(r)
    primary={i:items[0] for i,items in groups.items() if len(items)==1}
    components={c['object_id']:c for c in assembly['components']}
    existing={b['object_id']:b for b in (body_properties or {}).get('bodies',[])}
    decoded,updates,unresolved=[],[],[]
    def typed(identity,guid):
        record=primary.get(identity)
        if record is None or record.class_guid!=guid:
            raise ValueError('Body collection variant typed reference missing, ambiguous or wrong class')
        return record,data[record.body:record.end]
    for record in records:
        if not record.is_primary or record.class_guid!=COLLECTION:continue
        body=data[record.body:record.end]
        if body[:2]!=b'\0\1':continue
        try:
            props,cursor=attributes(body,2)
            if props or cursor!=6 or body[cursor]!=0:
                raise ValueError('Only observed optional empty collection attribute table supported')
            stored_field=struct.unpack_from('<I',body,cursor+1)[0]
            count=struct.unpack_from('<I',body,cursor+5)[0]
            if count>100000 or cursor+9+11*count>len(body):
                raise ValueError('Body collection attributed member count exceeds bounds')
            members=[reference(body,cursor+9+11*i) for i in range(count)]
            repeated=len(body)-15-11*count
            if (repeated<cursor+9+11*count or struct.unpack_from('<I',body,repeated)[0]!=count
                    or [reference(body,repeated+4+11*i) for i in range(count)]!=members
                    or len(set(members))!=count):
                raise ValueError('Attributed body collection repeated count/membership disagrees')
            component=reference(body,len(body)-11)
            typed(component,'E03784ED-5E19-4E14-B9F2-3B07017018CD')
            if component not in components:raise ValueError('Attributed body collection component unresolved')
            for identity in members:
                native,native_body=typed(identity,BODY)
                if reference(native_body,len(native_body)-11)!=record.object_id:
                    raise ValueError('Attributed collection and native body ownership not reciprocal')
            middle=cursor+9+11*count
            if body[middle]!=1:raise ValueError('Attributed collection mapping prefix unsupported')
            auxiliary,mapping_offset=optional_reference(body,middle+1)
            if auxiliary is not None:typed(auxiliary,'E55D0457-898F-4A8E-B1A5-C85BDBA8794F')
            mapping_id=reference(body,mapping_offset)
            _,mapping=typed(mapping_id,'74CA4562-59F8-4C97-8AD1-F8297C21F9AA')
            if mapping[:2]!=bytes(2) or len(mapping)<22:raise ValueError('Attributed collection mapping framing unsupported')
            map_count=struct.unpack_from('<I',mapping,2)[0]
            if map_count>100000 or 6+16*map_count+16>len(mapping):raise ValueError('Attributed collection mapping count exceeds bounds')
            map_ids=[struct.unpack_from('<Q',mapping,14+16*i)[0] for i in range(map_count)]
            if reference(mapping,6+16*map_count)!=record.object_id or set(map_ids)!=set(members) or len(set(map_ids))!=map_count:
                raise ValueError('Attributed collection and mapping membership/owner disagree')
            context_offset=mapping_offset+11
            if body[context_offset]!=1:raise ValueError('Attributed collection context marker unsupported')
            context_id=reference(body,context_offset+1)
            _,context=typed(context_id,'372234A0-2A6C-4122-8047-E74DBA04F326')
            if len(context)!=23 or context[:12]!=bytes(12) or reference(context,12)!=component:
                raise ValueError('Attributed collection context/component references disagree')
            if body[context_offset+12:repeated]!=b'\0':raise ValueError('Attributed collection middle footer unsupported')
            collection={'object_id':record.object_id,'class_guid':COLLECTION,'component_object_id':component,
                'component_name':components[component]['name'],'body_object_ids':members,
                'attribute_table_present':True,'attributes':props,'attributes_end_relative_offset':cursor,
                'stored_header_field':stored_field,'stored_header_field_relative_offset':cursor+1,
                'mapping_record_object_id':mapping_id,'context_record_object_id':context_id,
                'auxiliary_record_object_id':auxiliary,'repeated_count_relative_offset':repeated,
                'ownership_evidence':'Bounded optional empty attributes; repeated member lists; reciprocal typed native body/mapping collection owners; typed context/component agreement'}
            decoded.append(collection)
            for identity in members:
                update={**existing.get(identity,{'object_id':identity,'class_guid':BODY}),
                    'collection_object_id':record.object_id,'component_object_id':component,
                    'component_name':components[component]['name'],'ownership_evidence':collection['ownership_evidence']}
                update.pop('ownership_status',None)
                updates.append(update)
        except (ValueError,UnicodeError,KeyError,IndexError,struct.error) as error:
            unresolved.append({'object_id':record.object_id,'kind':'BodyCollection','reason':str(error)})
    return {'decoded_collections':decoded,'body_ownership_updates':updates,'unresolved':unresolved,
            'scope':'Observed optional empty collection attributes and explicit native ownership only; no material or final-body state inferred'}


def validate_fixtures(root,zstd_library):
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records
    files=('constructionmodes-521ce7cdfdbe/axis_perpendicular_at_point.f3d',
           'holeplacements-04adf73afe93/sketch_point.f3d','holeplacements-04adf73afe93/sketch_points.f3d')
    report={'samples':[],'negative_checks':[],
            'interface':'decode_body_collection_attribute_variants(data,records,assembly,body_properties=None)',
            'integration':'Run after base body properties; append recovered collection IDs, merge body_ownership_updates by object_id and remove only matching BodyCollection rejections. Preserve stored name state and mapping/ASM lifecycle scope.',
            'validation_command':'python3 decode_body_property_variants.py --validate --zstd-library <local libzstd path>',
            'finding':'All three prefix failures in the two cited fixture families use an optional, explicitly empty attribute table; the existing collection fields shift by four bytes.'}
    for filename in files:
        archive=root/filename;main=decode_basics(archive,zstd_library);stream=main['streams'][0]
        members=read_members(archive,zstd_library);data=members[stream['member']]
        records,_=design_records(data,members.get(stream['member'].replace('BulkStream.dat','MetaStream.dat')))
        by={r.object_id:r for r in records if r.is_primary}
        out=decode_body_collection_attribute_variants(data,records,stream['assembly_decoding'],stream['body_properties'])
        assert len(out['decoded_collections'])==1 and len(out['body_ownership_updates'])==1 and not out['unresolved']
        collection=out['decoded_collections'][0];body=out['body_ownership_updates'][0]
        original=next(b for b in stream['body_properties']['bodies'] if b['object_id']==body['object_id'])
        checks={'empty_attribute_table_is_explicit':collection['attribute_table_present'] and collection['attributes']=={} and collection['attributes_end_relative_offset']==6,
                'body_member_and_ownership_patch_agree':collection['body_object_ids']==[body['object_id']] and body['collection_object_id']==collection['object_id'],
                'component_owner_is_decoded_root_component':body['component_object_id']==3 and collection['component_object_id']==3,
                'original_stored_name_state_preserved':body['name']==original['name'] and body['name_status']==original['name_status'],
                'mapping_and_context_native_id_fields_retained':collection['mapping_record_object_id']==8 and collection['context_record_object_id']==18,
                'old_collection_prefix_rejection_recovered':any(e['object_id']==collection['object_id'] and e['kind']=='BodyCollection' for e in stream['body_properties']['unresolved'])}
        api_reference=None
        if filename.startswith('constructionmodes'):
            truth=json.loads((archive.parent/'ground_truth.json').read_text());sample=next(s for s in truth['samples'] if s['file']==archive.name)
            api_reference=next(s['entity'] for s in sample['support_inputs'] if s['role']=='face')
            checks['stored_body_name_matches_independent_API_face_body_name']=body['name']==api_reference['body_name']=='SupportBody'
        else:checks['empty_name_not_replaced_by_default_UI_label']=body['name'] is None
        assert all(checks.values()),(filename,checks)
        report['samples'].append({'archive':filename,'checks':checks,'decoded':out,'actual_API_support_face':api_reference,
                                  'scope':'Explicit native membership and source ownership only; neither current geometry/material nor final lifecycle state inferred'})
        negative_case=data,records,stream,by,out
    data,records,stream,by,out=negative_case
    collection=out['decoded_collections'][0];record=by[collection['object_id']]
    native=by[out['body_ownership_updates'][0]['object_id']];context=by[collection['context_record_object_id']]
    mutations=[('Unsupported nonempty collection attribute table',record.body+2,struct.pack('<I',1)),
               ('Repeated native body membership disagrees',record.body+collection['repeated_count_relative_offset']+5,struct.pack('<Q',999999)),
               ('Native body reciprocal collection owner mismatch',native.end-10,struct.pack('<Q',22)),
               ('Typed collection context component mismatch',context.body+13,struct.pack('<Q',999999))]
    for label,offset,replacement in mutations:
        changed=bytearray(data);changed[offset:offset+len(replacement)]=replacement
        result=decode_body_collection_attribute_variants(bytes(changed),records,stream['assembly_decoding'],stream['body_properties'])
        assert not result['decoded_collections'] and not result['body_ownership_updates'] and len(result['unresolved'])==1,(label,result)
        report['negative_checks'].append({'check':label,'passed':True,'reason':result['unresolved'][0]['reason']})
    report['limitations']=['Only observed explicitly empty collection attribute tables are accepted; nonempty/custom attribute types remain unsupported.',
        'Repeated native member lists and reciprocal body/mapping/context/component joins establish source ownership, not current-body lifecycle.',
        'Existing stored custom names or empty-name state are preserved; API default display labels are not inferred.',
        'Material, body topology, ASM root identity, final shape and assembly solving are outside this ownership pass.']
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate',required=True,action='store_true');parser.add_argument('--zstd-library',required=True,type=Path)
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('body-property-variant-decoding.json'))
    args=parser.parse_args();report=validate_fixtures(Path(__file__).resolve().parent,args.zstd_library)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'samples':len(report['samples']),'negative_checks':len(report['negative_checks']),'output':str(args.output)}))
