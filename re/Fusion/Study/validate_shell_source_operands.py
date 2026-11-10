"""Focused Shell source identities/controls/recipe replay; no main/live calls."""
import argparse
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct

from decode_one_face_edge_sources import _replay_recipe
from decode_shell_source_operands import qualify_shell_source_operands,SHELL
from decode_sketch import attributes,reference
from validate_mesh_remesh import load

ROOT=Path(__file__).resolve().parent
BASELINE=Path('/private/tmp/fusion-shell-reconstruction-baseline.json')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(zstd,baseline_path=BASELINE):
    baseline=json.loads(baseline_path.read_text())
    assert baseline['baseline_commit']=='ddc57a8'
    samples,checks,guards,positives=[],[],[],[]
    groups=lines=points=coedges=faces=bodies=0
    saved=None

    def check(label,value):
        if not value:
            raise AssertionError(label)
        checks.append(label)

    for archive,before in zip(baseline['files'],baseline['before']):
        data,records,features,member,members=load(ROOT,archive,zstd)
        bindings=before['streams'][0]['body_blob_bindings']
        original=copy.deepcopy((features,bindings))
        candidates=[f for f in features if f.get('class_guid')==SHELL]
        source_rows=[]
        for feature in candidates:
            row=qualify_shell_source_operands(data,records,features,member,members,bindings,feature)
            check(archive+' fresh Shell source qualified',row is not None)
            source_rows.append(row)
        check(archive+' caller metadata and native bindings unchanged',(features,bindings)==original)
        entry=dict(archive=archive,archive_sha256=sha(ROOT/archive),expected_sources=source_rows,expected_unresolved=[])
        samples.append(entry)
        if not candidates:
            check(archive+' outside Shell source family',not source_rows)
            continue
        check(archive+' exactly one Shell native owner',len(source_rows)==1)
        row=source_rows[0]
        by={r.object_id:r for r in records if r.is_primary}
        prior=next(f for f in before['streams'][0]['features'] if f['object_id']==row['feature_object_id'])
        check(archive+' fresh common tool settings match prior dictionary exactly',row['settings']==prior['tool_settings'])
        check(archive+' no invented result anchor or historical/API identity',row['shell_owned_result_anchors']==[]
            and row['source_to_result_pairing'] is None and row['qualified_historical_state'] is None
            and row['API_handle_identity'] is None and row['persistent_identity'] is None)
        covered=[]
        for group in row['source_groups']:
            groups+=1
            anchor=by[group['body_anchor_object_id']]
            anchor_bytes=data[anchor.body:anchor.end]
            check(archive+' unique native source anchor '+str(anchor.object_id),
                reference(anchor_bytes,80)==group['native_body_object_id']
                and reference(anchor_bytes,91)==group['source_feature_object_id']
                and group['source_anchor']['source_owner_object_id']!=row['feature_object_id'])
            check(archive+' source scalar/profile controls '+str(anchor.object_id),
                group['extrude_controls']['operation']['kind']=='NewBody'
                and group['extrude_controls']['start']['kind']=='ProfilePlane'
                and group['extrude_controls']['extent']['mode']=='OneSided'
                and group['extrude_controls']['extent']['side_one']['condition']=='Distance'
                and group['extrude_controls']['extent']['side_one']['taper_angle_radians']==0
                and len(group['profile_cache_correspondence']['source_curves'])==4)
            degree={p['point_object_id']:0 for p in group['native_profile_points']}
            for line in group['native_profile_lines']:
                native=by[line['line_object_id']]
                raw=data[native.body:native.end]
                props,cursor=attributes(raw,2)
                check(archive+' native Line endpoint/tag references '+str(native.object_id),
                    props['crv_primary_id']==line['entity_tag']
                    and reference(raw,cursor+107)==line['start_point_id']
                    and reference(raw,cursor+96)==line['end_point_id']
                    and reference(raw,len(raw)-11)==group['source_sketch']['sketch_object_id'])
                degree[line['start_point_id']]+=1
                degree[line['end_point_id']]+=1
                lines+=1
            for point in group['native_profile_points']:
                native=by[point['point_object_id']]
                raw=data[native.body:native.end]
                props,cursor=attributes(raw,2)
                check(archive+' native POINT payload '+str(native.object_id),
                    props['pt_tag']==point['entity_tag']
                    and list(struct.unpack_from('<3d',raw,cursor+19))==point['position_cm']
                    and reference(raw,len(raw)-11)==group['source_sketch']['sketch_object_id'])
                points+=1
            check(archive+' native POINT incidence cycle '+str(anchor.object_id),len(degree)==4 and set(degree.values())=={2})
            coedges+=sum(len(c['cached_coedge_candidates']) for c in group['profile_cache_correspondence']['source_curves'])
            covered+=group['selected_input_indices']
            check(archive+' group operand membership by explicit BODY/anchor/sourceowner '+str(anchor.object_id),all(
                (row['selected_inputs'][i]['native_body_object_id'],row['selected_inputs'][i]['body_anchor_object_id'],
                    row['selected_inputs'][i]['source_owner_object_id'])
                ==(group['native_body_object_id'],group['body_anchor_object_id'],group['source_feature_object_id'])
                for i in group['selected_input_indices']))
            check(archive+' stored-ID mapping independent of caller ordinal annotations '+str(anchor.object_id),
                group['binding']['previous_ordinal_candidate'] is None
                and group['binding']['stored_handle']==group['binding']['asm_stored_entity_id'])
        check(archive+' source groups exactly partition literal input operands',sorted(covered)==list(range(row['settings']['input_count'])))
        for operand in row['selected_inputs']:
            if operand['kind']=='Body':
                bodies+=1
                continue
            faces+=1
            recipe=operand['counted_recipe']
            native=by[recipe['object_id']]
            check(archive+' complete counted 476-byte recipe replay '+str(native.object_id),
                recipe['payload_length']==476 and operand['exact_counted_recipe_payload_replay'] is True
                and _replay_recipe(recipe)==data[native.body:native.end]
                and operand['removed_face_cache_identity'] is None)
            ctx=operand['typed_context']
            check(archive+' namespace/context/anchored BODY retained '+str(native.object_id),
                ctx['native_body_object_id']==operand['native_body_object_id']
                and ctx['source_owner_object_id']==operand['source_owner_object_id']
                and ctx['body_anchor_object_id']==operand['body_anchor_object_id'])
        check(archive+' shared source/Sketch/receiving dependency component',
            all(f['component_object_id']==row['component_provenance']['component_object_id']
                for f in row['component_provenance']['dependency_scopes']))
        if saved is None:
            saved=data,records,features,member,members,bindings,candidates[0],row

    data,records,features,member,members,bindings,feature,row=saved
    by={r.object_id:r for r in records if r.is_primary}

    def altered(offset,value):
        raw=bytearray(data)
        raw[offset:offset+len(value)]=value
        return bytes(raw)

    def reject(label,changed_data=data,changed_records=records,changed_features=None,changed_bindings=None):
        fs=features if changed_features is None else changed_features
        bs=bindings if changed_bindings is None else changed_bindings
        ms=dict(members)
        ms[member]=changed_data
        try:
            qualify_shell_source_operands(changed_data,changed_records,fs,member,ms,bs,
                next(f for f in fs if f['object_id']==feature['object_id']))
        except ValueError as error:
            guards.append(dict(label=label,reason=str(error)))
        else:
            raise AssertionError(label+' did not reject')

    operand=row['selected_inputs'][0]
    descriptor=by[operand['descriptor_object_id']]
    reject('Duplicate primary selected Face descriptor',changed_records=records+[descriptor])
    reject('Descriptor receiving owner changed',changed_data=altered(descriptor.body+266,struct.pack('<Q',operand['source_owner_object_id'])))
    support=by[operand['descriptor_support']['object_id']]
    reject('Descriptor source-support backlink changed',changed_data=altered(support.body+32,struct.pack('<Q',feature['object_id'])))
    reject('Shell descriptor trailer marker corruption',changed_data=altered(descriptor.body+235,b'\0'))
    group=row['source_groups'][0]
    source=by[group['source_feature_object_id']]
    reject('Source Extrude operation changes to Join',changed_data=altered(source.body+9,struct.pack('<I',1)))
    line=by[group['native_profile_lines'][0]['line_object_id']]
    reject('Source profile Line wrong native class',changed_records=[replace(r,class_guid='F0130424-8B7E-4092-93C9-1CA807482534')
        if r is line else r for r in records])
    fake=copy.deepcopy(features)
    next(f for f in fake if f['object_id']==feature['object_id'])['parameters'][0]['raw_float64']+=.1
    reject('Caller thickness parameter disagrees with native binding',changed_features=fake)
    fake=copy.deepcopy(bindings)
    fake['decoded'][0]['bindings'][0]['stored_handle']+=999
    reject('Forged stored handle cannot choose source BODY',changed_bindings=fake)
    receiver=by[feature['object_id']]
    payload=data[receiver.body:receiver.end]
    label=struct.pack('<I',5)+'Shell'.encode('utf-16le')
    check('Receiving Shell repeated label is uniquely bounded',payload.count(label)==1)
    reject('Missing fresh Shell label is explicit unsupported',changed_data=altered(receiver.body+payload.index(label)+4,b'X'))

    fake_features=copy.deepcopy(features)
    for f in fake_features:
        f['harmless_later_annotation']=True
        if f['kind']=='Sketch':
            f['geometry']=[dict(kind='BogusCallerGeometry',object_id=-1)]
            f['placement']=dict(sketch_to_component_matrix=[999.]*16)
    fake_bindings=copy.deepcopy(bindings)
    for mapping in fake_bindings['decoded']:
        for binding in mapping['bindings']:
            binding.update(candidate_asm_body_index=999999,name='Ignored caller label')
    actual=qualify_shell_source_operands(data,records,fake_features,member,members,fake_bindings,
        next(f for f in fake_features if f['object_id']==feature['object_id']))
    check('Fresh source proof independent of caller geometry/placement/ordinal/display annotations',actual==row)
    positives.append(dict(label='Caller annotations ignored; full native source row exact',passed=True))
    return dict(interface='qualify_shell_source_operands(data,records,features,member,members,body_blob_bindings,feature)',
        scope='Source/control/typed native identity and counted recipe framing; C owns cache FACE/loop incidence and hollow geometry qualification.',
        baseline=dict(commit='ddc57a8',path=str(baseline_path),sha256=sha(baseline_path)),
        samples=samples,guards=guards,positive_controls=positives,checks=checks,
        source_sha256={name:sha(ROOT/name) for name in ('decode_shell_source_operands.py',
            'validate_shell_source_operands.py','decode_body_tools.py','decode_body_tool_selections.py',
            'decode_profile_cache_correspondence.py','decode_extrude.py','decode_sketch.py',
            'decode_placement.py','decode_body_asm_identifiers.py','decode_selection_context_recipes.py')},
        validation=dict(Shell_owners=13,source_BODY_groups=groups,native_profile_lines=lines,native_profile_points=points,
            retained_COEDGE_candidates=coedges,selected_Face_operands=faces,selected_Body_operands=bodies,
            outside_family_controls=2,focused_checks=len(checks),negative_guards=len(guards),positive_controls=len(positives),
            main_reader_calls=0,live_API_calls=0))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--baseline',type=Path,default=BASELINE)
    parser.add_argument('--zstd-library',default=str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))))
    parser.add_argument('--output',type=Path,default=ROOT/'shell-source-operand-decoding.json')
    args=parser.parse_args()
    report=validate(args.zstd_library,args.baseline)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report['validation'],sort_keys=True))
