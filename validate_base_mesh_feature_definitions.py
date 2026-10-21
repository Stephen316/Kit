"""Bounded BaseMeshFeature definition proofs, with mesh lifecycle left separate."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
from unittest.mock import patch

from decode_base_mesh_feature_definitions import (decode_base_mesh_feature_definitions,
    decode_base_mesh_feature_definition,MESH_FEATURE,MESH,CONTROLLER,BOOKKEEPING,OWNER_LINK,COLLECTION_MEMBERS)
from decode_parameters import read_string
from decode_sketch import reference
from decode_timeline import HISTORY_GUID
from validate_mesh_remesh import load

ROOT=Path(__file__).resolve().parent
FILES=('meshconverts-4b42d39fb1d5/faceted_closed.f3d','meshconverts-4b42d39fb1d5/faceted_open.f3d',
 'meshcombines-541ebb6cc93f/cut.f3d','meshcombines-541ebb6cc93f/intersect.f3d','meshcombines-541ebb6cc93f/join.f3d',
 'meshseparates-41126250c03f/connected_shell_control.f3d','meshseparates-41126250c03f/two_face_groups.f3d','meshseparates-41126250c03f/two_shells.f3d',
 'meshremoves-8b2188cd274d/one_remove_one.f3d','meshremoves-8b2188cd274d/two_remove_both.f3d','meshremoves-8b2188cd274d/two_remove_first.f3d',
 'meshconvertoperations-5af73924aa60/two_mesh_parametric.f3d',
 'meshcontrasts-10c2557c91a3/stl_centimeter.f3d','meshcontrasts-10c2557c91a3/stl_millimeter.f3d','meshcontrasts-10c2557c91a3/triangle_data_centimeter.f3d',
 'patchcontinuity-b9b0be85a281/brep_tangent.f3d')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(zstd):
    samples=[];checks=[];guards=[];api_observations=[];contexts=[];total=0;replayed=0
    def check(label,value,**evidence):
        if not value:raise AssertionError(label)
        checks.append(dict(check=label,**evidence))
    for archive in FILES:
        d,rs,fs,member,members=load(ROOT,archive,zstd);before=copy.deepcopy(fs)
        # An accidental mesh-asset call must fail this isolated definition reader.
        with patch('decode_mesh_geometry_variants.decode_mesh_asset',side_effect=AssertionError('Asset decode forbidden in BaseMesh definition')):
            result=decode_base_mesh_feature_definitions(d,rs,fs)
        check(archive+' no asset access or feature mutation',before==fs)
        check(archive+' every native BaseMesh definition qualified',not result['unresolved'] and {r['feature_object_id'] for r in result['partial']}=={r.object_id for r in rs if r.is_primary and r.class_guid==MESH_FEATURE})
        by={r.object_id:r for r in rs if r.is_primary}
        for row in result['partial']:
            total+=1;identity=row['feature_object_id'];record=by[identity];body=d[record.body:record.end]
            feature=next(f for f in fs if f['object_id']==identity)
            check(archive+' feature'+str(identity)+' exact single/direct helper equality',row==decode_base_mesh_feature_definition(d,rs,feature))
            check(archive+' feature'+str(identity)+' complete263 byte replay',row['stored_payload']['exact_full_payload_replay'] is True and bytes.fromhex(row['stored_payload']['hex'])==body and len(body)==263)
            replayed+=len(body)
            check(archive+' feature'+str(identity)+' native label/name/index exact',read_string(body,147)==('Base Mesh Feature',185) and struct.unpack_from('<Q',body,185)[0]==row['stored_index']==feature['stored_index'] and read_string(body,193)==('',197) and row['name'] is None)
            mesh_id,=row['stored_mesh_object_ids'];mesh=by[mesh_id]
            check(archive+' feature'+str(identity)+' typed forward mesh only',reference(body,6)==mesh_id and mesh.class_guid==MESH and row['stored_mesh_records']==[dict(object_id=mesh_id,class_guid=MESH,record_offset=mesh.start,body_offset=mesh.body,end_offset=mesh.end)] and row['mesh_owner_backlink_qualified'] is False and row['current_mesh_membership'] is row['mesh_assets'] is row['API_BaseFeature_owner'] is None)
            controller=row['controller'];cr=by[controller['object_id']];cb=d[cr.body:cr.end]
            check(archive+' feature'+str(identity)+' reciprocal controller/native copies',reference(body,22)==reference(body,132)==controller['object_id'] and cr.class_guid==CONTROLLER and reference(cb,14)==reference(cb,60)==identity)
            br=by[controller['bookkeeping_object_id']];bb=d[br.body:br.end]
            check(archive+' feature'+str(identity)+' typed controller bookkeeping backlink',br.class_guid==BOOKKEEPING and reference(cb,48)==br.object_id and reference(bb,12)==cr.object_id and bb.hex()==controller['bookkeeping_payload_hex'])
            ownership=row['ownership'];owned=ownership['counted_member_object_ids']
            check(archive+' feature'+str(identity)+' unique collection feature/controller membership',len(owned)==len(set(owned)) and owned.count(identity)==owned.count(cr.object_id)==1)
            history=row['history'];hr=by[history['object_id']];hb=d[hr.body:hr.end]
            check(archive+' feature'+str(identity)+' explicit typed native history position',hr.class_guid==HISTORY_GUID and reference(hb,2)==history['owner_object_id']==ownership['native_history_container_object_id'] and history['ordered_native_entry_object_ids'][history['native_entry_index']]==identity and hb.hex()==history['payload_hex'])
            check(archive+' feature'+str(identity)+' existing kind and warnings not promoted',feature['kind']=='UnsupportedFeature' and 'tool_settings' not in feature and 'base_mesh_feature_definition' not in feature)
        samples.append(dict(archive=archive,archive_sha256=sha(ROOT/archive),expected_partial=result,existing_discovered_kinds={str(f['object_id']):f['kind'] for f in fs if f['class_guid']==MESH_FEATURE},native_definition_count=len(result['partial']),no_asset_decoding=True,no_feature_mutation=True))
        contexts.append((archive,d,rs,fs,result))
    # Actual API BaseFeature observations are negative ownership evidence only.
    # They do not identify the private native99F BaseMesh definitions.
    for folder in ('meshconverts-4b42d39fb1d5','meshremoves-8b2188cd274d'):
        truth=json.loads((ROOT/folder/'ground_truth.json').read_text())
        for sample in truth['samples']:
            archive=folder+'/'+sample['file']
            if archive not in FILES:continue
            phases=[]
            for phase in ('base_after_edit','base_after_convert','base_after_remove'):
                if phase not in sample:continue
                base=sample[phase]
                check(archive+' '+phase+' APIBaseFeature does not supply mesh ownership',base['objectType']=='adsk::fusion::BaseFeature' and base['mesh_bodies']==base['brep_source_bodies']==base['brep_bodies']==[] and not base['base_getter_errors'])
                phases.append(dict(phase=phase,actual_type=base['objectType'],mesh_bodies=[],brep_source_bodies=[],brep_bodies=[]))
            api_observations.append(dict(archive=archive,ground_truth_sha256=sha(ROOT/folder/'ground_truth.json'),phases=phases,native_BaseMesh_to_API_BaseFeature_assignment=None))
    archive,d,rs,fs,result=next(c for c in contexts if c[0].endswith('/two_remove_first.f3d'))
    row=result['partial'][0];identity=row['feature_object_id'];by={r.object_id:r for r in rs if r.is_primary};record=by[identity]
    def guard(label,offset=None,payload=b'',alter_features=None,alter_records=None):
        changed=bytearray(d);features=copy.deepcopy(fs);records=list(rs)
        if offset is not None:changed[offset:offset+len(payload)]=payload
        if alter_features:alter_features(features)
        if alter_records:alter_records(records)
        answer=decode_base_mesh_feature_definitions(bytes(changed),records,features)
        check(label,identity not in {r['feature_object_id'] for r in answer['partial']} and any(r['feature_object_id']==identity for r in answer['unresolved']))
        guards.append(dict(guard=label,absolute_mutation_offset=offset,reason=next(r['reason'] for r in answer['unresolved'] if r['feature_object_id']==identity)))
    def ref(value):return b'\1'+struct.pack('<Q',value)+bytes(2)
    guard('Reject unsupported count2 definition',record.body+2,struct.pack('<I',2))
    guard('Reject nonmesh typed source reference',record.body+6,ref(row['controller']['object_id']))
    guard('Reject controller feature backlink mismatch',by[row['controller']['object_id']].body+14,ref(identity+1))
    guard('Reject controller bookkeeping backlink mismatch',by[row['controller']['bookkeeping_object_id']].body+12,ref(identity))
    guard('Reject repeated controller reference mismatch',record.body+132,ref(identity))
    owner=next(r for r in rs if not r.is_primary and r.object_id==row['controller']['object_id'] and r.class_guid==OWNER_LINK)
    guard('Reject controller inherited collection mismatch',owner.body,ref(row['ownership']['collection_object_id']+1))
    membership=next(r for r in rs if not r.is_primary and r.object_id==row['ownership']['collection_object_id'] and r.class_guid==COLLECTION_MEMBERS)
    pos=row['ownership']['counted_member_object_ids'].index(identity)
    guard('Reject missing feature in counted collection',membership.body+4+11*pos,ref(row['controller']['object_id']))
    history=by[row['history']['object_id']];hpos=row['history']['native_entry_index']
    guard('Reject native history reference alias',history.body+17+11*hpos,ref(row['controller']['object_id']))
    guard('Reject stale discovered stored index',alter_features=lambda values:next(f for f in values if f['object_id']==identity).__setitem__('stored_index',row['stored_index']+1))
    return dict(interface='decode_base_mesh_feature_definitions(data,records,features)->partial/unresolved/scope; single decode_base_mesh_feature_definition(data,records,feature)',integration=dict(stream='base_mesh_feature_definitions',feature_attachment='base_mesh_feature_definition',classification_or_warning_changes=False),samples=samples,actual_API_negative_ownership_evidence=api_observations,checks=checks,malformed_guards=guards,validation=dict(saved_archives=len(samples),partial_native_definitions=total,full_definition_bytes_replayed=replayed,check_count=len(checks),malformed_guards=len(guards),no_asset_decoding=True,no_classification_changes=True,no_live_calls=True,no_main_calls=True),source_sha256={p:sha(ROOT/p) for p in ('decode_base_mesh_feature_definitions.py','validate_base_mesh_feature_definitions.py','decode_base_feature_empty_lists.py','decode_mesh_contents.py','decode_timeline.py','decode_parameters.py')},limitations=['The singleton stored feature→mesh pointer is typed, not evidence of current membership or a reciprocal mesh owner. Separate current/retained source readers qualify backlinks and assets.','These remain partial native definitions; no new feature kind/tool settings, geometry, asset or current state is assigned by this reader.','Public API BaseFeature mesh/BRep collections are observed empty and do not identify native BaseMesh owners. No API BaseFeature parent is inferred.','Controller and native feature/history collection references are reciprocal; explicit sequence position is not general lifecycle replay.','Opaque bookkeeping bytes, related-object semantics and literal signed table metadata -1 remain unassigned; exact bytes are preserved.'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--zstd');p.add_argument('--output',default='base-mesh-feature-definition-decoding.json');a=p.parse_args()
    z=a.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(z);Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['validation'],sort_keys=True))
