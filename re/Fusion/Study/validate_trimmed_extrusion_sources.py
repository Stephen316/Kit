"""Fresh trimmed source operands; independent native math and prior defaults."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_extrusion_source_operands import EXTRUDE,qualify_extrusion_source_operands
from decode_placement import transform_point
from decode_sketch import attributes,reference
from validate_mesh_remesh import load

ROOT=Path(__file__).resolve().parent
BASELINE=Path('/private/tmp/fusion-trimmed-extrusion-reconstruction-baseline.json')
OLD_BASELINE=Path('/private/tmp/fusion-extrusion-reconstruction-baseline.json')
PLANE_BASELINE=Path('/private/tmp/fusion-plane-extrusion-reconstruction-baseline.json')


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def validate(zstd):
    checks,guards,samples,defaults,plane_defaults=[],[],[],[],[]
    def check(label,value):
        if not value:raise AssertionError(label)
        checks.append(label)
    prior=json.loads((ROOT/'extrusion-source-operand-decoding.json').read_text())
    cache=json.loads(OLD_BASELINE.read_text())
    by_archive={s['archive']:s for s in prior['samples']}
    for archive,before in zip(cache['files'],cache['before']):
        data,records,features,member,members=load(ROOT,archive,zstd);bindings=before['streams'][0]['body_blob_bindings']
        rows,unresolved=[],[]
        for feature in features:
            if feature.get('class_guid')!=EXTRUDE:continue
            try:rows.append(qualify_extrusion_source_operands(data,records,features,member,members,bindings,feature))
            except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error) as error:
                unresolved.append(dict(feature_object_id=feature['object_id'],reason=str(error)))
        expected=by_archive[archive]
        check(archive+' full prior default source dictionaries/errors EXACT',rows==expected['expected_sources'] and unresolved==expected['expected_unresolved'])
        defaults.append(dict(archive=archive,expected_sources=rows,expected_unresolved=unresolved))
    plane=json.loads((ROOT/'extrusion-plane-limit-source-decoding.json').read_text());pcache=json.loads(PLANE_BASELINE.read_text())
    contexts=dict(zip(pcache['files'],pcache['before']))
    for sample in plane['samples']:
        if not sample['expected_sources']:continue
        archive=sample['archive'];data,records,features,member,members=load(ROOT,archive,zstd)
        bindings=contexts[archive]['streams'][0]['body_blob_bindings'];ids={r['feature_object_id'] for r in sample['expected_sources']}
        rows=[qualify_extrusion_source_operands(data,records,features,member,members,bindings,f,allow_plane_limits=True)
            for f in features if f['object_id'] in ids]
        check(archive+' full prior plane opt-in source dictionaries EXACT',rows==sample['expected_sources'])
        plane_defaults.append(dict(archive=archive,expected_sources=rows))
    baseline=json.loads(BASELINE.read_text());assert baseline['baseline_commit']=='d5f29a9'
    counts=dict(owners=0,portions=0,circle_arcs=0,line_segments=0,native_circles=0,native_lines=0,native_points=0,
        cached_coedge_candidates=0,outside_controls=0)
    saved=placed=line_saved=None
    for index,(archive,before) in enumerate(zip(baseline['files'],baseline['before'])):
        data,records,features,member,members=load(ROOT,archive,zstd);bindings=before['streams'][0]['body_blob_bindings']
        original=copy.deepcopy((features,bindings));by={r.object_id:r for r in records if r.is_primary};rows=[]
        if index<15:
            for feature in features:
                if feature.get('class_guid')!=EXTRUDE:continue
                row=qualify_extrusion_source_operands(data,records,features,member,members,bindings,feature,allow_trimmed_profiles=True)
                rows.append(row);group=row['source_groups'][0];counts['owners']+=1
                counts['native_circles']+=len(group['native_profile_circles']);counts['native_lines']+=len(group['native_profile_lines']);counts['native_points']+=len(group['native_profile_points'])
                proof=group['profile_portion_cache_corroboration'];qualified=proof['qualified_profile_cache']
                check(archive+' selected profile full tuple/cache and BODY routes',qualified['profile_loops']==group['native_profile_selection']['profile_loops']
                    and qualified['native_body_object_id']==group['native_body_object_id'] and qualified['asm_body_index']==group['asm_body_index'])
                portion_by={p['role_key']:p for p in group['derived_source_portions']}
                refs=[r for loop in group['native_profile_selection']['profile_loops'] for r in loop['curve_references']]
                keys=[str(r['entity_id'])+':'+':'.join(map(str,r['stored_tuple_fields'])) for r in refs]
                check(archive+' every selected tuple unique mathematical role',len(set(keys))==len(keys) and set(keys)==set(portion_by)
                    and set(keys)=={p['role_key'] for p in group['mathematical_inputs']})
                definition=by[group['native_profile_selection']['profile_loop_definition_object_id']]
                for ref in refs:
                    check(archive+' full native tuple replay '+str(ref['stored_tuple_offset_in_definition']),
                        data[definition.body+ref['stored_tuple_offset_in_definition']:definition.body+ref['stored_tuple_offset_in_definition']+40]==struct.pack('<IQQIIIQ',*ref['stored_tuple_fields']))
                primitives={g['object_id']:g for g in group['source_sketch']['geometry'] if g['kind']!='Point'}
                matrix=group['source_sketch']['placement']['sketch_to_component_matrix']
                for p in group['mathematical_inputs']:
                    counts['portions']+=1;part=portion_by[p['role_key']];primitive=primitives[p['source_primitive_id']]
                    check(archive+' mathematical source primitive identity '+p['role_key'],p['source_primitive_id']==part['source_primitive_id']
                        and p['source_primitive_id']==part['stored_profile_reference']['entity_id'])
                    a,b=p['parameter_interval'];evaluated=[]
                    if p['kind']=='CircleArc':
                        counts['circle_arcs']+=1
                        check(archive+' native Circle-only math geometry '+p['role_key'],p['source_geometry']=={k:primitive[k] for k in ('center_cm','radius_cm','normal','reference_axis')})
                        g=p['source_geometry'];axis=g['reference_axis'];normal=g['normal'];cross=[normal[1]*axis[2]-normal[2]*axis[1],normal[2]*axis[0]-normal[0]*axis[2],normal[0]*axis[1]-normal[1]*axis[0]]
                        for t in (a,(a+b)/2,b):evaluated.append([o+g['radius_cm']*(math.cos(t)*u+math.sin(t)*v) for o,u,v in zip(g['center_cm'],axis,cross)])
                    else:
                        counts['line_segments']+=1
                        check(archive+' native Line-only math geometry '+p['role_key'],p['source_geometry']=={k:primitive[k] for k in ('start_cm','end_cm')})
                        g=p['source_geometry']
                        for t in (a,(a+b)/2,b):evaluated.append([x+t*(y-x) for x,y in zip(g['start_cm'],g['end_cm'])])
                    for key,point in zip(('start','midpoint','end'),evaluated):
                        check(archive+' native derived '+key+' '+p['role_key'],math.dist(point,part['derived_sketch_local_points_cm'][key])<1e-10
                            and math.dist(transform_point(matrix,point),part['derived_component_points_cm'][key])<1e-10)
                    check(archive+' cache coordinates excluded from mathematical geometry '+p['role_key'],set(p)=={'role_key','source_primitive_id','kind','source_geometry','parameter_interval'}
                        and 'all_full_tuple_cache_candidates_corroborate' not in part)
                for source in qualified['source_curves']:
                    candidates=source['cached_coedge_candidates'];counts['cached_coedge_candidates']+=len(candidates)
                    expected=[r['stored_coedge_text_fields'] for r in refs if r['entity_id']==source['native_entity_object_id']]
                    check(archive+' all-six-field native/cache portion identity '+str(source['native_entity_object_id']),all(c['stored_decimal_text_fields'] in expected for c in candidates))
                check(archive+' stored membership separate from derived traversal',group['stored_profile_membership_order']==keys and row['qualified_historical_state'] is None)
                if saved is None:saved=(data,records,features,member,members,bindings,feature,row)
                if group['native_profile_kind']=='TrimmedLineLine' and line_saved is None:line_saved=(data,records,features,member,members,bindings,feature,row)
                if archive.startswith('placedprofiletrims') and placed is None:placed=(data,records,features,member,members,bindings,feature,row)
        else:counts['outside_controls']+=1
        check(archive+' caller metadata/native bindings pure',(features,bindings)==original)
        samples.append(dict(archive=archive,archive_sha256=sha(ROOT/archive),expected_sources=rows,expected_unresolved=[]))
    def reject(label,context,changes=None,rs=None,fs=None,bs=None):
        data,records,features,member,members,bindings,feature,row=context
        if changes:
            payload=bytearray(data)
            for offset,value in changes:payload[offset:offset+len(value)]=value
            data=bytes(payload);members=dict(members);members[member]=data
        if fs is not None:features=fs;feature=next(f for f in fs if f['object_id']==feature['object_id'])
        try:qualify_extrusion_source_operands(data,rs or records,features,member,members,bs or bindings,feature,allow_trimmed_profiles=True)
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error,ArithmeticError) as error:guards.append(dict(name=label,rejected=True,reason=str(error)))
        else:raise AssertionError(label+' accepted')
    data,records,features,member,members,bindings,feature,row=saved;by={r.object_id:r for r in records if r.is_primary};group=row['source_groups'][0]
    circle=by[group['native_profile_circles'][0]['circle_object_id']]
    reject('Duplicate underlying native Circle namespace',saved,rs=records+[circle])
    altered=copy.deepcopy(features);next(f for f in altered if f['object_id']==feature['object_id'])['parameters'][0]['raw_float64']+=.5
    reject('Supplied parameter differs from fresh reciprocal native binding',saved,fs=altered)
    definition=by[group['native_profile_selection']['profile_loop_definition_object_id']]
    reject('Uncaptured selected portion count selector',saved,[(definition.body+25+28,struct.pack('<I',3))])
    ref=lambda i:b'\1'+struct.pack('<Q',i)+bytes(2)
    anchor=by[group['body_anchor_object_id']]
    reject('Creator anchor backlink differs',saved,[(anchor.body+91,ref(1))])
    point=by[group['native_profile_points'][0]['point_object_id']];_,cursor=attributes(data[point.body:point.end],2)
    reject('Nonfinite underlying native source POINT',saved,[(point.body+cursor+19,struct.pack('<d',float('nan')))])
    pd,prs,pfs,pm,pms,pbs,pf,prow=placed;pby={r.object_id:r for r in prs if r.is_primary}
    transform=pby[prow['source_groups'][0]['source_sketch_frame_provenance']['transform']['object_id']]
    reject('Nonrigid placed source frame',placed,[(transform.body+3,struct.pack('<d',2.))])
    ld,lrs,lfs,lm,lms,lbs,lf,lrow=line_saved;lby={r.object_id:r for r in lrs if r.is_primary};lg=lrow['source_groups'][0]
    selected_ids={r['entity_id'] for loop in lg['native_profile_selection']['profile_loops'] for r in loop['curve_references']}
    unselected=next(r for r in lg['native_profile_lines'] if r['line_object_id'] not in selected_ids);lr=lby[unselected['line_object_id']]
    reject('Unselected cutting-context native Line owner differs',line_saved,[(lr.end-11,ref(1))])
    changed=copy.deepcopy(bindings);next(b for m in changed['decoded'] for b in m['bindings'] if b['native_body_object_id']==group['native_body_object_id'])['stored_handle']+=10000
    reject('Same-asset stored BODY identifier differs',saved,bs=changed)
    annotated=copy.deepcopy(features)
    for f in annotated:
        f['extra_caller_annotation']='ignored'
        if f.get('kind')=='Sketch':f['geometry']=[dict(kind='Injected',object_id=-1)]
    actual=qualify_extrusion_source_operands(data,records,annotated,member,members,bindings,next(f for f in annotated if f['object_id']==feature['object_id']),allow_trimmed_profiles=True)
    check('Trimmed proof independent of caller geometry/annotations',actual==row)
    return dict(status='pass',interface='qualify_extrusion_source_operands(..., *, allow_trimmed_profiles=False)',baseline_commit=baseline['baseline_commit'],baseline_sha256=sha(BASELINE),
        source_sha256={n:sha(ROOT/n) for n in ('decode_trimmed_extrusion_sources.py','decode_extrusion_source_operands.py',
            'decode_profile_circle_portions.py','decode_profile_line_portions.py','decode_profile_mixed_portions.py','decode_trimmed_profiles.py','decode_placed_profile_portions.py')},
        validator_sha256=sha(Path(__file__)),samples=samples,default_controls=defaults,plane_default_controls=plane_defaults,counts=counts,
        check_count=len(checks),checks=checks,guard_count=len(guards),guards=guards,positive_controls=[dict(name='Caller geometry/annotation independence',accepted=True)],
        scope='Native primitive/POINT/full-tuple/frame/BODY input identity before derived source portions; cache evidence isolated from mathematical inputs',
        limits=['Selected portion parameters are derived native mathematical angles/fractions, not serialized/API parameters',
            'Stored profile membership and native direction flags are not decoded traversal/orientation',
            'Existing portion readers corroborate cached boundaries after native tuple identity; no cache coordinate enters source math',
            'No chronology, persistent entity/API handle identity or general trimmed-profile regeneration'],execution=dict(main_calls=0,live_API_calls=0,geometry_identity_selection=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',type=Path,default=ROOT/'trimmed-extrusion-source-decoding.json');args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(zstd);args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],counts=result['counts'],checks=result['check_count'],guards=result['guard_count'],report=str(args.output))))
