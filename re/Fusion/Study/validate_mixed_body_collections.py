"""Two strict mixed CD57 collection roles; typed BODY-only ownership hydration."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from decode_assembly import decode_assembly
from decode_body_properties import decode_body_properties,BODY,COLLECTION
from decode_mixed_body_collections import decode_mixed_body_collections
from decode_sketch import reference
from validate_mesh_remesh import load

ROOT=Path(__file__).resolve().parent
FILES=('meshconverts-4b42d39fb1d5/faceted_closed.f3d',
 'meshconverts-4b42d39fb1d5/faceted_open.f3d',
 'meshcombines-541ebb6cc93f/cut.f3d',
 'meshcombines-541ebb6cc93f/intersect.f3d',
 'meshcombines-541ebb6cc93f/join.f3d',
 'meshseparates-41126250c03f/connected_shell_control.f3d',
 'meshseparates-41126250c03f/two_face_groups.f3d',
 'meshseparates-41126250c03f/two_shells.f3d',
 'meshremoves-8b2188cd274d/one_remove_one.f3d',
 'meshremoves-8b2188cd274d/two_remove_both.f3d',
 'meshremoves-8b2188cd274d/two_remove_first.f3d',
 'meshconvertoperations-5af73924aa60/two_mesh_parametric.f3d',
 'meshcontrasts-10c2557c91a3/stl_centimeter.f3d',
 'meshcontrasts-10c2557c91a3/stl_millimeter.f3d',
 'meshcontrasts-10c2557c91a3/triangle_data_centimeter.f3d',
 'patchcontinuity-b9b0be85a281/brep_tangent.f3d',
 'meshconverts-4b42d39fb1d5/prismatic_closed.f3d',
 'meshconvertoperations-5af73924aa60/base_feature_closed.f3d',
 'meshconvertoperations-5af73924aa60/base_feature_open.f3d',
 'namedbodies-3c7c11fc2924/namedbodies.f3d',
 'advanced-627f7fe095f4/advanced.f3d',
 'assembly-acc48a9dc05d/assembly.f3d')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def hydrate(original,summary):
    result=copy.deepcopy(original)
    for row in summary['decoded']:
        assert row['collection']['object_id'] not in {r['object_id'] for r in result['collections']}
        result['collections'].append(copy.deepcopy(row['collection']))
        for update in row['body_ownership_updates']:
            body=next(r for r in result['bodies'] if r['object_id']==update['object_id'])
            body.update(update);body.pop('ownership_status',None)
        result['unresolved']=[r for r in result['unresolved'] if not(r['object_id']==row['object_id'] and r['kind']=='BodyCollection' and r['reason'] in ('Body collection repeated count disagrees','Body collection repeated membership disagrees'))]
    return result


def validate(zstd):
    checks=[];samples=[];guards=[];contexts={};totals=dict(collections=0,history_roles=0,alternate_roles=0,typed_BRep_ownership_updates=0,mixed_mesh_memberships=0,full_payload_bytes_replayed=0)
    def check(label,value,**fields):
        if not value:raise AssertionError(label)
        checks.append(dict(check=label,**fields))
    for archive in FILES:
        d,rs,fs,member,members=load(ROOT,archive,zstd)
        assembly=decode_assembly(d,rs,copy.deepcopy(fs));properties=decode_body_properties(d,rs,assembly)
        before_assembly,before_props=copy.deepcopy(assembly),copy.deepcopy(properties)
        decoded=decode_mixed_body_collections(d,rs,assembly,properties)
        check(archive+' no native inputs mutated',assembly==before_assembly and properties==before_props)
        check(archive+' summary independent of optional properties',decoded==decode_mixed_body_collections(d,rs,assembly))
        check(archive+' all admitted mixed frames resolved',not decoded['unresolved'])
        after=hydrate(properties,decoded);by={r.object_id:r for r in rs if r.is_primary};updates=[]
        for row in decoded['decoded']:
            totals['collections']+=1;totals['history_roles' if row['role']=='StoredHistoryMapping74CA' else 'alternate_roles']+=1
            collection=row['collection'];identity=row['object_id'];record=by[identity];raw=d[record.body:record.end]
            body_ids=row['body_member_object_ids'];mesh_ids=row['mesh_member_object_ids'];all_ids=row['mixed_member_object_ids']
            check(archive+' collection'+str(identity)+' complete CD57 byte replay',row['stored_payload']['exact_full_payload_replay'] is True and bytes.fromhex(row['stored_payload']['hex'])==raw and collection['class_guid']==COLLECTION)
            totals['full_payload_bytes_replayed']+=len(raw);totals['mixed_mesh_memberships']+=len(mesh_ids)
            check(archive+' collection'+str(identity)+' mixed list and BODY-only tail agree by types',body_ids==[i for i in all_ids if by[i].class_guid==BODY] and collection['body_object_ids']==body_ids and mesh_ids==[i for i in all_ids if by[i].class_guid=='EA90DA22-556C-4C61-89BB-20C2681B7A9D'] and len(body_ids)+len(mesh_ids)==len(all_ids) and bool(mesh_ids))
            first_count=struct.unpack_from('<I',raw,7)[0];tail_count=struct.unpack_from('<I',raw,row['tail_count_relative_offset'])[0]
            check(archive+' collection'+str(identity)+' independent counts and literal BODY-count field',first_count==len(all_ids)>tail_count==len(body_ids)==struct.unpack_from('<I',raw,3)[0])
            check(archive+' collection'+str(identity)+' exact old same-ID failure qualified',any(e['object_id']==identity and e['kind']=='BodyCollection' and e['reason'] in ('Body collection repeated count disagrees','Body collection repeated membership disagrees') for e in properties['unresolved']))
            backend=row['backend'];check(archive+' collection'+str(identity)+' backend reciprocal BODY identity table',backend['native_body_object_ids']==body_ids and backend['owner_collection_object_id']==identity and backend['exact_full_payload_replay'] is True and bytes.fromhex(backend['payload_hex'])==d[by[backend['object_id']].body:by[backend['object_id']].end])
            proof=row['component_reference'];component=row['component_object_id']
            check(archive+' collection'+str(identity)+' explicit typed component pointer agrees',reference(d,proof['reference_offset'])==identity and reference(raw,len(raw)-11)==component and collection['component_object_id']==component)
            check(archive+' collection'+str(identity)+' no mesh/render/final-state semantics',row['mesh_native_owner_assignment'] is row['rendering_semantics'] is row['current_final_lifecycle'] is None and {u['object_id'] for u in row['body_ownership_updates']}==set(body_ids))
            if row['auxiliary']:
                auxiliary=row['auxiliary'];check(archive+' collection'+str(identity)+' opaque auxiliary uint64 retained independently',auxiliary['stored_count']==len(auxiliary['stored_uint64_values']) and 'stored_uint64_at_6' in auxiliary)
            for patch in row['body_ownership_updates']:
                totals['typed_BRep_ownership_updates']+=1
                native=by[patch['object_id']]
                check(archive+' BODY'+str(native.object_id)+' reciprocal owner and minimal patch',native.class_guid==BODY and reference(d[native.body:native.end],native.end-native.body-11)==identity and set(patch)=={'object_id','collection_object_id','component_object_id','component_name','ownership_evidence'})
                before=next(b for b in properties['bodies'] if b['object_id']==native.object_id);current=next(b for b in after['bodies'] if b['object_id']==native.object_id)
                check(archive+' BODY'+str(native.object_id)+' name/tag states exact after hydration',all(current.get(k)==before.get(k) for k in ('name','name_status','stored_body_tag','name_helper_object_id','name_field_offset','name_evidence')) and 'ownership_status' not in current)
                normalized=copy.deepcopy(current)
                for key in patch:
                    if key=='object_id':continue
                    if key in before:normalized[key]=before[key]
                    else:normalized.pop(key,None)
                if 'ownership_status' in before:normalized['ownership_status']=before['ownership_status']
                check(archive+' BODY'+str(native.object_id)+' only qualified ownership fields changed',normalized==before)
                updates.append(current)
        old_ids={r['object_id'] for r in properties['collections']}
        check(archive+' all prior homogeneous collection dictionaries exact',all(next(c for c in after['collections'] if c['object_id']==old['object_id'])==old for old in properties['collections']) and not old_ids.intersection(r['object_id'] for r in decoded['decoded']))
        check(archive+' revalidation stable after ownership merge',decoded==decode_mixed_body_collections(d,rs,assembly,after))
        samples.append(dict(archive=archive,archive_sha256=sha(ROOT/archive),expected_decoded=decoded,expected_fresh_body_properties=properties,expected_hydrated_body_properties=after,expected_hydrated_BRep_rows=updates,prior_homogeneous_collections_exact=True))
        contexts[archive]=(d,rs,assembly,properties,decoded)
    d,rs,assembly,properties,result=contexts['meshconvertoperations-5af73924aa60/base_feature_closed.f3d'];by={r.object_id:r for r in rs if r.is_primary};h=next(r for r in result['decoded'] if r['role']=='StoredHistoryMapping74CA');a=next(r for r in result['decoded'] if r['role']=='StoredBodyContext40D')
    def ref(i):return b'\1'+struct.pack('<Q',i)+bytes(2)
    def guard(label,collection_id,offset,payload):
        changed=bytearray(d);changed[offset:offset+len(payload)]=payload
        answer=decode_mixed_body_collections(bytes(changed),rs,assembly,properties)
        check(label,collection_id not in {r['object_id'] for r in answer['decoded']} and any(e['object_id']==collection_id for e in answer['unresolved']))
        guards.append(dict(guard=label,absolute_mutation_offset=offset,reason=next(e['reason'] for e in answer['unresolved'] if e['object_id']==collection_id)))
    guard('Reject BODY tail counted extent mismatch',h['object_id'],by[h['object_id']].body+h['tail_count_relative_offset'],struct.pack('<I',2))
    guard('Reject Mesh substituted into typed BODY tail',h['object_id'],by[h['object_id']].body+h['tail_count_relative_offset']+4,ref(h['mesh_member_object_ids'][0]))
    body=by[h['body_member_object_ids'][0]]
    guard('Reject native BODY reciprocal collection mismatch',h['object_id'],body.end-11,ref(a['object_id']))
    guard('Reject inherited COMPONENT collection slot mismatch',h['object_id'],h['component_reference']['reference_offset'],ref(a['object_id']))
    guard('Reject primary COMPONENT alternate collection mismatch',a['object_id'],a['component_reference']['reference_offset'],ref(h['object_id']))
    mapping=by[h['mapping_record_object_id']]
    guard('Reject history mapping collection owner mismatch',h['object_id'],mapping.body+6+16*len(h['body_member_object_ids']),ref(a['object_id']))
    context=by[a['context_record_object_id']]
    guard('Reject alternate context BODY namespace alias',a['object_id'],context.body+25,struct.pack('<Q',h['body_member_object_ids'][0]))
    guard('Reject non-BODY/non-Mesh first member class',h['object_id'],by[h['object_id']].body+22,ref(h['mapping_record_object_id']))
    duplicated=rs+[copy.copy(by[a['object_id']])]
    duplicate_result=decode_mixed_body_collections(d,duplicated,assembly,properties)
    label='Reject duplicate primary alternate CD57 identity'
    check(label,a['object_id'] not in {r['object_id'] for r in duplicate_result['decoded']} and any(e['object_id']==a['object_id'] for e in duplicate_result['unresolved']))
    guards.append(dict(guard=label,reason=next(e['reason'] for e in duplicate_result['unresolved'] if e['object_id']==a['object_id'])))
    return dict(interface='decode_mixed_body_collections(data,records,assembly,body_properties=None)->decoded/unresolved/scope; decoded rows collection/body_ownership_updates plus typed role proofs',integration=dict(stream='mixed_body_collections',compatible_collection_key='collection',minimal_BRep_patch_key='body_ownership_updates',clear_only_same_ID_reasons=['Body collection repeated count disagrees','Body collection repeated membership disagrees'],preserve_name_tag_fields_and_all_mesh_ownership=True),samples=samples,checks=checks,malformed_guards=guards,validation=dict(saved_archives=len(samples),**totals,check_count=len(checks),malformed_guards=len(guards),no_live_calls=True,no_main_calls=True),source_sha256={p:sha(ROOT/p) for p in ('decode_mixed_body_collections.py','validate_mixed_body_collections.py','decode_body_properties.py','decode_assembly.py','decode_component_display_colors.py','decode_extrude.py')},limitations=['First Mesh/BRep stored memberships and trailing native BODY members are independently framed. Forward Mesh membership does not establish Mesh native ownership.','Both roles are component-related stored collections; auxiliary40D/BREP.smb and history74CA/BREP.smbh roles are kept separate. No rendering or general current/final lifecycle meaning is assigned.','Only reciprocally owned typed native BODY members receive component/collection patches. Names, tags, Mesh ownership, ASM/body identity and geometry stay separate.','Auxiliary E55 leading uint64 and counted array values are literal opaque fields; the leading uint64 is demonstrably not the array count in all captures.','Old homogeneous equal-count/list successes are skipped and their complete dictionaries preserved. Unknown member classes, component layouts or backend framing retain explicit failures.'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--zstd');p.add_argument('--output',default='mixed-body-collection-decoding.json');a=p.parse_args()
    z=a.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(z);Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['validation'],sort_keys=True))
