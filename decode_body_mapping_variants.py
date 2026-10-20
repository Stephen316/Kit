"""Explicit empty body tables and passive-reference body/name mapping variants.

Empty tables bind no bodies and no blob. Passive body links remain typed stored
references between distinct native bodies; PM/DM keys are retained without final
lifecycle or ASM-root identity claims.
"""

import argparse
import json
import math
from pathlib import Path
import re
import struct
import uuid

from decode_body_properties import BODY,COLLECTION,NAME_HELPER
from decode_extrude import optional_reference
from decode_parameters import read_string
from decode_sketch import ascii_string,reference

MAPPING='74CA4562-59F8-4C97-8AD1-F8297C21F9AA'
PASSIVE_KEYS={'BASEFEAT_PM_BODY_REF','BASEFEAT_DM_BODY_REF'}


def _records(data,records):
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    primary={identity:items[0] for identity,items in grouped.items() if len(items)==1}
    def typed(identity,guid):
        record=primary.get(identity)
        if record is None or record.class_guid!=guid:
            raise ValueError('Body mapping variant typed reference missing, ambiguous or wrong class')
        return record,data[record.body:record.end]
    return primary,typed


def passive_body_header(body):
    """Frame only observed body prefix and exactly one typed passive reference."""
    if len(body)<6 or body[:2]!=b'\0\1' or struct.unpack_from('<I',body,2)[0]!=1:
        raise ValueError('Not observed one-attribute passive native body')
    key,cursor=ascii_string(body,6)
    kind,cursor=ascii_string(body,cursor)
    if key not in PASSIVE_KEYS or kind!='PassiveRefMetaType':
        raise ValueError('Unsupported passive body attribute key/type')
    target=reference(body,cursor)
    cursor+=11
    tag,end=read_string(body,cursor)
    return {'key':key,'type':kind,'referenced_body_object_id':target,'stored_body_tag':tag,
            'attribute_value_relative_offset':cursor-11,'tag_relative_offset':cursor},end


def _collection_members(typed,identity):
    _,body=typed(identity,COLLECTION)
    if len(body)<26 or body[:3]!=bytes(3):raise ValueError('Unsupported mapping owner body collection')
    count=struct.unpack_from('<I',body,7)[0]
    if count>100000 or 11+11*count>len(body):raise ValueError('Body collection member count exceeds bounds')
    ids=[reference(body,11+11*i) for i in range(count)]
    repeated=len(body)-15-11*count
    if (repeated<11+11*count or struct.unpack_from('<I',body,repeated)[0]!=count
            or [reference(body,repeated+4+11*i) for i in range(count)]!=ids or len(set(ids))!=count):
        raise ValueError('Body collection repeated native membership disagrees')
    component=reference(body,len(body)-11)
    typed(component,'E03784ED-5E19-4E14-B9F2-3B07017018CD')
    return body,ids,component,repeated


def _body_name(data,record,body,typed,tag):
    owner=reference(body,len(body)-11)
    marker=b'\1'+struct.pack('<Q',owner)+bytes(2)
    choices=[]
    for match in re.finditer(re.escape(marker),body):
        cursor=match.start()
        if cursor+23>len(body)-11 or body[cursor+11]!=0:continue
        try:
            helper_id=reference(body,cursor+12)
            typed(helper_id,NAME_HELPER)
            name,end=read_string(body,cursor+23)
            if end+18>len(body)-11:continue
            colors=struct.unpack_from('<4f',body,end)
            if not all(math.isfinite(v) and 0<=v<=1 for v in colors):continue
            if body[end+16] not in (0,1) or body[end+17] not in (0,1):continue
            choices.append({'name':name or None,'name_helper_object_id':helper_id,'name_field_offset':record.body+cursor+23,
                            'name_status':'Stored custom name recovered' if name else 'Stored name empty; default UI label not inferred',
                            'stored_body_tag':tag,'name_evidence':'Unique owner reference + typed helper reference + bounded UTF-16 field and observed trailer'})
        except (ValueError,UnicodeError,IndexError,struct.error):continue
    if len(choices)!=1:raise ValueError('Passive body typed name anchor missing or ambiguous')
    return choices[0]


def decode_passive_body_names(data,records,body_properties):
    primary,typed=_records(data,records)
    properties={b['object_id']:b for b in body_properties['bodies']}
    decoded,unresolved=[],[]
    for record in records:
        if not record.is_primary or record.class_guid!=BODY:continue
        body=data[record.body:record.end]
        # Only named observed keys trigger this pass; other attribute layouts
        # retain their original decoder status.
        if not any(key.encode('ascii') in body[:100] for key in PASSIVE_KEYS):continue
        try:
            attr,_=passive_body_header(body)
            partner_id=attr['referenced_body_object_id']
            partner_record,partner=typed(partner_id,BODY)
            partner_attr,_=passive_body_header(partner)
            if (partner_id==record.object_id or partner_attr['referenced_body_object_id']!=record.object_id
                    or partner_attr['key']==attr['key'] or {attr['key'],partner_attr['key']}!=PASSIVE_KEYS):
                raise ValueError('Passive PM/DM body references are not distinct reciprocal typed links')
            owner=reference(body,len(body)-11)
            _,members,component,_=_collection_members(typed,owner)
            partner_owner=reference(partner,len(partner)-11)
            _,partner_members,partner_component,_=_collection_members(typed,partner_owner)
            if (record.object_id not in members or partner_id not in partner_members or component!=partner_component):
                raise ValueError('Passive linked bodies lack reciprocal same-component collection ownership')
            prop=properties.get(record.object_id)
            if prop is None or prop.get('collection_object_id')!=owner or prop.get('component_object_id')!=component:
                raise ValueError('Passive body and independently decoded body-property ownership disagree')
            name=_body_name(data,record,body,typed,attr['stored_body_tag'])
            decoded.append({**prop,**name,'passive_reference_attribute':attr,
                            'passive_partner_body_object_id':partner_id,'passive_partner_collection_object_id':partner_owner,
                            'passive_reference_scope':'Explicit reciprocal PM/DM-key stored body links; distinct native bodies/collections retained, final lifecycle meaning unresolved'})
        except (ValueError,UnicodeError,KeyError,IndexError,struct.error) as error:
            unresolved.append({'object_id':record.object_id,'kind':'PassiveBodyName','reason':str(error)})
    return {'decoded':decoded,'unresolved':unresolved,
            'scope':'Only observed one-entry PassiveRefMetaType body attributes and reciprocal links; no general attribute/lifecycle interpretation'}


def decode_body_mapping_variants(data,records,member,asm_summary,body_properties):
    primary,typed=_records(data,records)
    properties={b['object_id']:b for b in body_properties['bodies']}
    passive_names=decode_passive_body_names(data,records,body_properties)
    names={b['object_id']:b for b in passive_names['decoded']}
    streams={s['member']:s for s in asm_summary['streams']}
    asset=member.rsplit('/FusionDesignSegmentType1/',1)[0]
    decoded,unresolved=[],[]
    for record in records:
        if not record.is_primary or record.class_guid!=MAPPING:continue
        body=data[record.body:record.end]
        try:
            if len(body)<6 or body[:2]!=bytes(2):raise ValueError('Unsupported native mapping variant prefix')
            count=struct.unpack_from('<I',body,2)[0]
            if count>100000 or 6+16*count+16>len(body):raise ValueError('Body mapping variant count exceeds bounded record')
            entries=[struct.unpack_from('<QQ',body,6+16*i) for i in range(count)]
            if count and not any(identity in names for _,identity in entries):continue
            cursor=6+16*count
            owner=reference(body,cursor)
            if body[cursor+11]!=0:raise ValueError('Body mapping filename separator unsupported')
            filename,end=read_string(body,cursor+12)
            if end!=len(body):raise ValueError('Body mapping variant has unconsumed filename/footer bytes')
            collection,members,component,repeated=_collection_members(typed,owner)
            position=11+11*len(members)
            if collection[position]!=1:raise ValueError('Body collection mapping header marker unsupported')
            auxiliary,position=optional_reference(collection,position+1)
            if auxiliary is not None:typed(auxiliary,'E55D0457-898F-4A8E-B1A5-C85BDBA8794F')
            if reference(collection,position)!=record.object_id:
                raise ValueError('Mapping/owner body collection reference is not reciprocal')
            position+=11
            if collection[position]!=1:raise ValueError('Mapping collection context marker unsupported')
            context_id=reference(collection,position+1)
            _,context=typed(context_id,'372234A0-2A6C-4122-8047-E74DBA04F326')
            if len(context)!=23 or context[:12]!=bytes(12) or reference(context,12)!=component:
                raise ValueError('Mapping typed context and collection component references disagree')
            position+=12
            if collection[position:repeated]!=b'\0':raise ValueError('Mapping collection middle/footer framing unsupported')
            if len({a for a,b in entries})!=count or len({b for a,b in entries})!=count:
                raise ValueError('Duplicate mapping opaque handles or native body IDs')
            if {b for a,b in entries}!=set(members):
                raise ValueError('Mapping native body IDs and reciprocal collection members disagree')
            bindings=[]
            for ordinal,(handle,identity) in enumerate(entries):
                native,native_body=typed(identity,BODY)
                if reference(native_body,len(native_body)-11)!=owner:
                    raise ValueError('Mapped native body/collection ownership is not reciprocal')
                prop=names.get(identity,properties.get(identity))
                if prop is None or prop.get('collection_object_id')!=owner or prop.get('component_object_id')!=component:
                    raise ValueError('Mapped native body properties and explicit collection ownership disagree')
                if identity not in names:raise ValueError('Only observed passive-reference populated mapping variant supported')
                attr,_=passive_body_header(native_body)
                bindings.append({'stored_handle':handle,'native_body_object_id':identity,'stored_body_tag':attr['stored_body_tag'],
                    'native_body_record_offset':native.start,'mapping_entry_ordinal':ordinal,
                    'name':prop['name'],'name_status':prop['name_status'],'component_object_id':component,
                    'component_name':prop['component_name'],'passive_partner_body_object_id':prop['passive_partner_body_object_id'],
                    'passive_reference_attribute':attr,'association_status':'ASM root association unresolved',
                    'handle_scope':'Opaque stored handle; never treated as ASM record index'})
            if count==0:
                if filename or len(body)!=22 or members:raise ValueError('Empty mapping must have no native bodies and no filename/blob')
                blob_member=None
            else:
                if not filename.startswith('BREP.') or not filename.endswith('.smbh') or '/' in filename or '\\' in filename:
                    raise ValueError('Unsupported populated mapping history-blob filename')
                uuid.UUID(filename[5:-5])
                blob_member=asset+'/Breps.BlobParts/'+filename
                if blob_member not in streams:raise ValueError('Explicit populated mapping blob absent from same asset ASM summary')
            decoded.append({'mapping_record_object_id':record.object_id,'owner_object_id':owner,
                'component_object_id':component,'context_record_object_id':context_id,
                'body_count':count,'bindings':bindings,'history_blob_member':blob_member,
                'mapping_status':'ExplicitEmptyMappingNoBodiesOrBlob' if not count else 'ExplicitPassiveBodyCollectionContextBlobMapping',
                'scope':'Typed reciprocal native mapping/body collection/context/component joins only; ASM root/final-body lifecycle unresolved'})
        except (ValueError,UnicodeError,KeyError,IndexError,struct.error) as error:
            unresolved.append({'object_id':record.object_id,'reason':str(error)})
    return {'decoded':decoded,'unresolved':unresolved,'passive_body_name_updates':passive_names['decoded'],
            'passive_body_name_unresolved':passive_names['unresolved'],
            'scope':'Recovered observed empty/passive-reference variants only; ordinary positive-count mappings remain in original decoder'}


def validate_fixtures(root,zstd_library):
    from decode_basics import decode_basics
    from decode_body_bindings import decode_body_bindings
    from fusion_archive import read_members
    from fusion_metadata import design_records
    files=('advanced-627f7fe095f4/advanced.f3d','assembly-acc48a9dc05d/assembly.f3d',
           'namedbodies-3c7c11fc2924/namedbodies.f3d',
           'remainingbodyinputs-7b3357274e85/mirror_occurrence.f3d',
           'mirrorassemblydatum-700af16e9fc6/nested_occurrence_yz.f3d',
           'mirrorassemblydatum-700af16e9fc6/nested_occurrence_rotated_parent_xz.f3d')
    report={'samples':[],'negative_checks':[],
            'interface':'decode_body_mapping_variants(data,records,member,asm_summary,body_properties)',
            'body_name_interface':'decode_passive_body_names(data,records,body_properties)',
            'integration':'Merge recovered mapping IDs into original result and remove only their original rejections. Apply passive_body_name_updates to matching body_properties IDs and remove only their recovered BodyName rejections. Leave original positive-count mappings/root-candidate policy unchanged.',
            'finding':'Audited Unsupported native body mapping count examples are exactly zero-entry tables with empty filename, not an unsupported positive multi-count format.',
            'validation_command':'python3 decode_body_mapping_variants.py --validate --zstd-library <local libzstd path>'}
    for filename in files:
        archive=root/filename;main=decode_basics(archive,zstd_library);stream=main['streams'][0]
        members=read_members(archive,zstd_library);data=members[stream['member']]
        records,_=design_records(data,members.get(stream['member'].replace('BulkStream.dat','MetaStream.dat')))
        by={r.object_id:r for r in records if r.is_primary}
        original=decode_body_bindings(data,records,stream['member'],main['asm_decoding'],stream['body_properties'])
        recovered=decode_body_mapping_variants(data,records,stream['member'],main['asm_decoding'],stream['body_properties'])
        old=stream['body_blob_bindings']
        checks={'original_positive_mapping_output_unchanged':original['decoded']==old['decoded'],
                'new_pass_has_no_unresolved_observed_candidates':not recovered['unresolved'] and not recovered['passive_body_name_unresolved'],
                'recovered_mapping_ids_do_not_duplicate_original_positive_ids':not ({m['mapping_record_object_id'] for m in original['decoded']} & {m['mapping_record_object_id'] for m in recovered['decoded']}),
                'empty_tables_have_no_bodies_bindings_or_blob':all(m['bindings']==[] and m['history_blob_member'] is None and m['mapping_status']=='ExplicitEmptyMappingNoBodiesOrBlob' for m in recovered['decoded'] if m['body_count']==0),
                'passive_mappings_have_explicit_blob_and_no_ASM_root_guess':all(m['history_blob_member'] is not None and all('candidate_asm_body_index' not in b and b['association_status']=='ASM root association unresolved' for b in m['bindings']) for m in recovered['decoded'] if m['body_count'])}
        if 'namedbodies-' in filename:
            truth=json.loads((archive.parent/'ground_truth.json').read_text())
            actual_names={b['name'] for b in truth['bodies']}
            checks['positive_multi_count_already_supported']=any(m['body_count']==2 for m in original['decoded'])
            checks['original_named_mapping_names_match_actual_API']=all(b.get('name') in actual_names for m in original['decoded'] for b in m['bindings'])
        if recovered['passive_body_name_updates']:
            truth=json.loads((archive.parent/'ground_truth.json').read_text())
            sample=next(s for s in truth['samples'] if s['file']==archive.name)
            actual_occurrences=sample.get('all_occurrences_after',sample.get('root_occurrences_after',[]))
            name_checks=[]
            for prop in recovered['passive_body_name_updates']:
                actual=[o for o in actual_occurrences if o['component_name']==prop['component_name']]
                actual_names={b['name'] for o in actual for b in o['bodies']}
                name_checks.append(prop['name'] in actual_names and prop['passive_partner_body_object_id']!=prop['object_id'])
            checks['stored_passive_names_and_components_match_independent_actual_API']=all(name_checks)
            checks['both_PM_and_DM_links_preserved_without_alias_collapse']=len(recovered['passive_body_name_updates'])==2 and {b['passive_reference_attribute']['key'] for b in recovered['passive_body_name_updates']}==PASSIVE_KEYS
            passive_case=data,records,stream,main,by,recovered
        assert all(checks.values()),(filename,checks)
        report['samples'].append({'archive':filename,'checks':checks,'recovered':recovered,
             'unchanged_original_positive_mapping_ids':[m['mapping_record_object_id'] for m in original['decoded']],
             'original_rejections':original['unresolved'],
             'scope':'Only explicit native body/collection/context/blob references and stored names validated; no ASM-root, canonical/final body or geometry association inferred'})
        if filename.startswith('advanced-'):empty_case=data,records,stream,main,by,recovered
    data,records,stream,main,by,recovered=empty_case
    empty=next(m for m in recovered['decoded'] if m['body_count']==0);record=by[empty['mapping_record_object_id']]
    for label,offset,replacement in [('Empty mapping owner points to another collection',7,struct.pack('<Q',22)),
                                      ('Empty mapping count contradicts exact record size',2,struct.pack('<I',1))]:
        changed=bytearray(data);changed[record.body+offset:record.body+offset+len(replacement)]=replacement
        out=decode_body_mapping_variants(bytes(changed),records,stream['member'],main['asm_decoding'],stream['body_properties'])
        assert not any(m['mapping_record_object_id']==record.object_id for m in out['decoded']) and any(e['object_id']==record.object_id for e in out['unresolved'])
        report['negative_checks'].append({'check':label,'passed':True,'reason':next(e['reason'] for e in out['unresolved'] if e['object_id']==record.object_id)})
    data,records,stream,main,by,recovered=passive_case
    mapping=next(m for m in recovered['decoded'] if m['body_count'])
    prop=next(b for b in recovered['passive_body_name_updates'] if b['object_id']==mapping['bindings'][0]['native_body_object_id'])
    record=by[prop['object_id']];attr=prop['passive_reference_attribute']
    other_body=next(b['object_id'] for b in stream['body_properties']['bodies'] if b['object_id'] not in {p['object_id'] for p in recovered['passive_body_name_updates']})
    changed=bytearray(data);offset=record.body+attr['attribute_value_relative_offset']+1
    changed[offset:offset+8]=struct.pack('<Q',other_body)
    out=decode_passive_body_names(bytes(changed),records,stream['body_properties'])
    assert not any(b['object_id']==record.object_id for b in out['decoded']) and any(e['object_id']==record.object_id for e in out['unresolved'])
    report['negative_checks'].append({'check':'Passive linked-body reference loses reciprocal PM/DM typed partner','passed':True,
         'reason':next(e['reason'] for e in out['unresolved'] if e['object_id']==record.object_id)})
    context=by[mapping['context_record_object_id']]
    changed=bytearray(data);changed[context.body+13:context.body+21]=struct.pack('<Q',3)
    out=decode_body_mapping_variants(bytes(changed),records,stream['member'],main['asm_decoding'],stream['body_properties'])
    assert not any(m['mapping_record_object_id']==mapping['mapping_record_object_id'] for m in out['decoded']) and any(e['object_id']==mapping['mapping_record_object_id'] for e in out['unresolved'])
    report['negative_checks'].append({'check':'Typed collection context points to a different component','passed':True,
         'reason':next(e['reason'] for e in out['unresolved'] if e['object_id']==mapping['mapping_record_object_id'])})
    report['coverage']={'focused_archives':len(files),'recovered_empty_mappings':sum(m['body_count']==0 for s in report['samples'] for m in s['recovered']['decoded']),
        'recovered_passive_populated_mappings':sum(m['body_count']>0 for s in report['samples'] for m in s['recovered']['decoded']),
        'recovered_passive_body_names':sum(len(s['recovered']['passive_body_name_updates']) for s in report['samples']),
        'malformed_guards':len(report['negative_checks'])}
    report['limitations']=['Zero-entry records explicitly contain no body IDs and an empty filename; no blob or geometry is invented.',
        'PassiveRefMetaType support is bounded to one observed PM/DM key and a reciprocal typed D393 body reference; no general attribute grammar or PM/DM lifecycle meaning assigned.',
        'Native body identities, owner collections and context/component/blob links are explicit. Opaque handles remain opaque, and populated ASM root/final-body identity remains unresolved.',
        'Positive multi-count tables were already supported by the original decoder; existing output/experimental root-candidate behavior is preserved separately.',
        'No broad audit sweep performed; six targeted archives include empty-root, assembly, multi-count named bodies and three actual mirrored-component controls.']
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate',required=True,action='store_true');parser.add_argument('--zstd-library',required=True,type=Path)
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('body-mapping-variant-decoding.json'))
    args=parser.parse_args();report=validate_fixtures(Path(__file__).resolve().parent,args.zstd_library)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'samples':len(report['samples']),'negative_checks':len(report['negative_checks']),'coverage':report['coverage'],'output':str(args.output)}))
