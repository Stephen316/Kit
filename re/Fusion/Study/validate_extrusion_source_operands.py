"""Focused native Extrude input proofs; fixed saved fixtures, no main/live calls."""
import argparse
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct
from unittest.mock import patch

from decode_extrusion_source_operands import qualify_extrusion_source_operands, EXTRUDE
from decode_profiles import PROFILE_DESCRIPTOR_GUID
from decode_sketch import attributes,reference
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
BASELINE = Path('/private/tmp/fusion-extrusion-reconstruction-baseline.json')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(zstd,baseline_path=BASELINE):
    baseline = json.loads(baseline_path.read_text())
    assert baseline['baseline_commit'] == 'b8a24f1'
    checks,guards,positives,samples = [],[],[],[]
    counts = dict(qualified_owners=0,circle_profiles=0,four_line_profiles=0,native_lines=0,native_points=0,
        unsupported_extrudes=0,outside_archives=0,optional_profile_cache_absent=0)
    saved = None

    def check(label,condition):
        if not condition:
            raise AssertionError(label)
        checks.append(label)

    for archive,before in zip(baseline['files'],baseline['before']):
        data,records,features,member,members = load(ROOT,archive,zstd)
        bindings = before['streams'][0]['body_blob_bindings']
        original = copy.deepcopy((features,bindings))
        sources,unresolved = [],[]
        candidates = [f for f in features if f.get('class_guid') == EXTRUDE]
        by = {r.object_id:r for r in records if r.is_primary}
        for feature in candidates:
            try:
                row = qualify_extrusion_source_operands(data,records,features,member,members,bindings,feature)
            except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error) as error:
                unresolved.append(dict(feature_object_id=feature['object_id'],reason=str(error)))
                counts['unsupported_extrudes'] += 1
                continue
            sources.append(row)
            counts['qualified_owners'] += 1
            check(archive+' unique creator/source group '+str(feature['object_id']),row['source_group_count']==1 and len(row['source_groups'])==1)
            group = row['source_groups'][0]
            anchor = by[group['body_anchor_object_id']]
            ab = data[anchor.body:anchor.end]
            check(archive+' native creator-owned BODY anchor '+str(feature['object_id']),
                reference(ab,80)==group['native_body_object_id'] and reference(ab,91)==feature['object_id']
                and group['source_anchor']['source_owner_object_id']==feature['object_id'])
            check(archive+' same-asset stored-ID mapping '+str(feature['object_id']),
                group['binding']['stored_handle']==group['binding']['asm_stored_entity_id']
                and group['binding']['previous_ordinal_candidate'] is None
                and group['history_blob_member'] in members)
            prior = [f for f in before['streams'][0]['features'] if f['object_id']==feature['object_id']]
            controls = copy.deepcopy(row['settings']); controls.pop('is_solid')
            if len(prior)==1 and 'tool_settings' in prior[0]:
                check(archive+' common scalar controls prior-full-dictionary exact '+str(feature['object_id']),controls==prior[0]['tool_settings'])
            sketch = group['source_sketch']
            selection = group['native_profile_selection']
            dr = by[selection['profile_descriptor_object_id']]
            db = data[dr.body:dr.end]
            check(archive+' owned descriptor and loop '+str(feature['object_id']),
                reference(db,len(db)-11)==feature['object_id'] and reference(db,2)==selection['profile_loop_definition_object_id']
                and selection['native_sketch_object_id']==sketch['sketch_object_id'])
            for point in group['native_profile_points']:
                pr = by[point['point_object_id']]; pb = data[pr.body:pr.end]; props,cursor = attributes(pb,2)
                check(archive+' native POINT '+str(pr.object_id),props['pt_tag']==point['entity_tag']
                    and list(struct.unpack_from('<3d',pb,cursor+19))==point['position_cm']
                    and reference(pb,len(pb)-11)==sketch['sketch_object_id'])
                counts['native_points'] += 1
            if group['native_profile_kind']=='Circle':
                counts['circle_profiles'] += 1
                circle = group['native_profile_circles'][0]
                cr = by[circle['circle_object_id']]; cb = data[cr.body:cr.end]; props,cursor = attributes(cb,2)
                values = struct.unpack_from('<12d',cb,cursor)
                check(archive+' native complete Circle centre/radius/frame '+str(cr.object_id),
                    reference(cb,cursor+96)==circle['center_point_id'] and list(values[:3])==circle['center_cm']
                    and values[9]==circle['radius_cm'] and list(values[3:6])==circle['normal']
                    and list(values[6:9])==circle['reference_axis'] and len(cb)-cursor==162)
            else:
                counts['four_line_profiles'] += 1
                degree = {p['point_object_id']:0 for p in group['native_profile_points']}
                for line in group['native_profile_lines']:
                    lr = by[line['line_object_id']]; lb = data[lr.body:lr.end]; props,cursor = attributes(lb,2)
                    check(archive+' native Line endpoint incidence '+str(lr.object_id),
                        reference(lb,cursor+107)==line['start_point_id'] and reference(lb,cursor+96)==line['end_point_id']
                        and props['crv_primary_id']==line['entity_tag'])
                    degree[line['start_point_id']]+=1;degree[line['end_point_id']]+=1
                    counts['native_lines'] += 1
                check(archive+' four distinct POINT degree-two loop '+str(feature['object_id']),len(degree)==4 and set(degree.values())=={2})
            if group['profile_cache_correspondence'] is None:
                counts['optional_profile_cache_absent']+=1
                check(archive+' optional COEDGE evidence absent explicitly '+str(feature['object_id']),bool(group['profile_cache_diagnostics']))
            check(archive+' lifecycle/API identity not invented '+str(feature['object_id']),
                row['API_handle_identity'] is None and row['persistent_identity'] is None and row['qualified_historical_state'] is None)
            if archive.startswith('extents-') and Path(archive).stem in ('distance_positive','distance_negative','offset_positive','offset_negative','taper'):
                truth = json.loads((ROOT/Path(archive).parent/'ground_truth.json').read_text())
                api = next(s for s in truth['samples'] if s['file']==Path(archive).name)
                check(archive+' existing actual API distance/taper',row['settings']['extent']['side_one']['distance_cm']==api['extent_one']['distance']
                    and row['settings']['extent']['side_one']['taper_angle_radians']==api['taper_one'])
                if 'offset' in api['start']:
                    check(archive+' actual API Offset start',row['settings']['start']['offset_cm']==api['start']['offset'])
            if saved is None:
                saved = (data,records,features,member,members,bindings,feature,row)
        if not candidates:
            counts['outside_archives'] += 1
            check(archive+' non-Extrude family empty',not sources and not unresolved)
        check(archive+' caller metadata/bindings unchanged',(features,bindings)==original)
        samples.append(dict(archive=archive,archive_sha256=sha(ROOT/archive),expected_sources=sources,expected_unresolved=unresolved))

    data,records,features,member,members,bindings,feature,row = saved
    by = {r.object_id:r for r in records if r.is_primary}
    group = row['source_groups'][0]

    def reject(label,d=data,rs=records,fs=features,ms=members,bs=bindings,f=feature):
        try:
            qualify_extrusion_source_operands(d,rs,fs,member,ms,bs,f)
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error) as error:
            guards.append(dict(name=label,rejected=True,reason=str(error)))
        else:
            raise AssertionError(label+' accepted')

    reject('Duplicate primary native Circle namespace',rs=records+[by[group['native_profile_circles'][0]['circle_object_id']]])
    changed = copy.deepcopy(features)
    cf = next(f for f in changed if f['object_id']==feature['object_id'])
    cf['parameters'][0]['raw_float64']+=.25
    reject('Supplied receiver parameter differs from fresh reciprocal native binding',fs=changed,f=cf)
    import decode_basics
    original_named = decode_basics.named_features
    with patch('decode_basics.named_features',side_effect=lambda d,rs:[f for f in original_named(d,rs) if f['object_id']!=feature['object_id']]):
        reject('Fresh receiver metadata absent emits explicit unsupported')

    def change(label,identity,offset,raw):
        payload = bytearray(data);record=by[identity];payload[record.body+offset:record.body+offset+len(raw)]=raw
        altered=bytes(payload);altered_members=dict(members);altered_members[member]=altered
        reject(label,d=altered,ms=altered_members)

    descriptor = by[group['native_profile_selection']['profile_descriptor_object_id']]
    change('Profile descriptor receiving owner differs',descriptor.object_id,descriptor.end-descriptor.body-11,bytes.fromhex('01')+struct.pack('<Q',1)+bytes(2))
    definition = by[group['native_profile_selection']['profile_loop_definition_object_id']]
    change('Owned profile tag unresolved',definition.object_id,29,struct.pack('<Q',999999))
    anchor = by[group['body_anchor_object_id']]
    change('Creator anchor source owner differs',anchor.object_id,91,bytes.fromhex('01')+struct.pack('<Q',1)+bytes(2))
    circle=group['native_profile_circles'][0];cr=by[circle['circle_object_id']];cb=data[cr.body:cr.end];_,cursor=attributes(cb,2)
    change('Circle centre typed identity differs',cr.object_id,cursor+96,bytes.fromhex('01')+struct.pack('<Q',feature['object_id'])+bytes(2))
    point=group['native_profile_points'][0];pr=by[point['point_object_id']];pb=data[pr.body:pr.end];_,pc=attributes(pb,2)
    change('Nonfinite native centre POINT',pr.object_id,pc+19,struct.pack('<d',float('nan')))
    altered_bindings=copy.deepcopy(bindings)
    entry=next(b for m in altered_bindings['decoded'] for b in m['bindings'] if b['native_body_object_id']==group['native_body_object_id'])
    entry['stored_handle']+=10000
    reject('Same-asset mapping stored handle differs',bs=altered_bindings)
    annotated=copy.deepcopy(features)
    for f in annotated:
        f['extra_caller_annotation']='irrelevant'
        if f.get('kind')=='Sketch':
            f['geometry']=[dict(object_id=-999,kind='Injected')]
    annotated_bindings=copy.deepcopy(bindings)
    for m in annotated_bindings['decoded']:
        for b in m['bindings']:
            b['candidate_asm_body_index']=99999;b['extra_caller_annotation']='irrelevant'
    actual=qualify_extrusion_source_operands(data,records,annotated,member,members,annotated_bindings,
        next(f for f in annotated if f['object_id']==feature['object_id']))
    check('Fresh native source independent of unrelated caller geometry/ordinal annotations',actual==row)
    positives.append(dict(name='Irrelevant caller geometry/metadata/ordinal annotations do not alter source proof',accepted=True))
    return dict(interface='qualify_extrusion_source_operands(data,records,features,member,members,body_blob_bindings,feature)',
        scope='Independent fresh native input/identity proof only; no main/live API or cached cap assignment',
        baseline_commit=baseline['baseline_commit'],baseline_sha256=sha(baseline_path),
        source_sha256={name:sha(ROOT/name) for name in ('decode_extrusion_source_operands.py','decode_extrude.py',
            'decode_profiles.py','decode_profile_cache_correspondence.py','decode_placement.py','decode_sketch.py',
            'decode_body_asm_identifiers.py')},validator_sha256=sha(Path(__file__)),samples=samples,counts=counts,
        checks=checks,check_count=len(checks),guards=guards,guard_count=len(guards),positive_controls=positives,
        execution=dict(main_calls=0,live_API_calls=0,geometry_identity_selection=False),status='pass')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--baseline',type=Path,default=BASELINE)
    parser.add_argument('--output',type=Path,default=ROOT/'extrusion-source-operand-decoding.json');args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(zstd,args.baseline);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],counts=result['counts'],checks=result['check_count'],guards=result['guard_count'],report=str(args.output))))
