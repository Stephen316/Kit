"""Focused native Revolve source/axis identities; no target construction/main/live."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_revolve_source_operands import REVOLVE,qualify_revolve_source_operands
from decode_sketch import attributes,reference
from validate_mesh_remesh import load

ROOT=Path(__file__).resolve().parent
BASELINE=Path('/private/tmp/fusion-revolve-reconstruction-baseline.json')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(zstd):
    baseline=json.loads(BASELINE.read_text());assert baseline['baseline_commit']=='676607d'
    checks,guards,samples=[],[],[]
    counts=dict(qualified_source_owners=0,target_fixture_owners=0,modified_boolean_seed_inputs=0,unsupported_receivers=0,
        outside_archives=0,profile_primitives=0,native_profile_POINTs=0,unwelded_eight_POINT_profiles=0,
        construction_axes=0,sketch_line_axes=0,brep_edge_axes=0)
    saved=custom=brep=None;axis_contrasts={}
    def check(label,condition):
        if not condition:raise AssertionError(label)
        checks.append(label)
    for index,(archive,before) in enumerate(zip(baseline['files'],baseline['before'])):
        data,records,features,member,members=load(ROOT,archive,zstd);bindings=before['streams'][0]['body_blob_bindings']
        original=copy.deepcopy((features,bindings));by={r.object_id:r for r in records if r.is_primary};rows,unresolved=[],[]
        candidates=[f for f in features if f.get('class_guid')==REVOLVE]
        for feature in candidates:
            try:row=qualify_revolve_source_operands(data,records,features,member,members,bindings,feature)
            except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error) as error:
                unresolved.append(dict(feature_object_id=feature['object_id'],reason=str(error)));counts['unsupported_receivers']+=1
                continue
            rows.append(row);counts['qualified_source_owners']+=1
            if index<13:counts['target_fixture_owners']+=1
            else:counts['modified_boolean_seed_inputs']+=1
            group=row['source_groups'][0];axis=row['source_axis'];controls=row['original_controls'];mathematical=group['mathematical_inputs']
            check(archive+' original controls separate from source axis '+str(feature['object_id']),controls['revolve']['axis_selection']=='Undecoded'
                and row['effective_axis'] is None and mathematical['controls']==controls
                and mathematical['source_axis']=={k:axis['entity'][k] for k in ('origin_cm','direction')})
            prior=next(f for f in before['streams'][0]['features'] if f['object_id']==feature['object_id'])
            oldrev={k:v for k,v in prior['revolve'].items() if k not in ('axis','axis_selection')}
            newrev={k:v for k,v in controls['revolve'].items() if k!='axis_selection'}
            check(archive+' prior scalar/mode controls exact '+str(feature['object_id']),oldrev==newrev
                and all(prior[k]==controls[k] for k in ('operation','is_solid','is_project_axis')))
            anchor=by[group['body_anchor_object_id']];ab=data[anchor.body:anchor.end]
            check(archive+' own anchor/BODY/mapping identity '+str(feature['object_id']),reference(ab,80)==group['native_body_object_id']
                and reference(ab,91)==feature['object_id'] and group['binding']['stored_handle']==group['binding']['asm_stored_entity_id']
                and group['binding']['previous_ordinal_candidate'] is None)
            selection=group['native_profile_selection'];dr=by[selection['profile_descriptor_object_id']];db=data[dr.body:dr.end]
            check(archive+' explicit profile descriptor/loop/Sketch '+str(feature['object_id']),reference(db,len(db)-11)==feature['object_id']
                and reference(db,2)==selection['profile_loop_definition_object_id']
                and selection['native_sketch_object_id']==group['source_sketch']['sketch_object_id'])
            for p in group['native_profile_points']:
                r=by[p['point_object_id']];pb=data[r.body:r.end];props,cursor=attributes(pb,2)
                check(archive+' native POINT coefficients '+str(r.object_id),props['pt_tag']==p['entity_tag']
                    and list(struct.unpack_from('<3d',pb,cursor+19))==p['position_cm']
                    and reference(pb,len(pb)-11)==selection['native_sketch_object_id'])
                counts['native_profile_POINTs']+=1
            for p in group['profile_primitives']:
                counts['profile_primitives']+=1;r=by[p['source_primitive_id']];pb=data[r.body:r.end];props,cursor=attributes(pb,2)
                check(archive+' native whole primitive '+str(r.object_id),props['crv_primary_id']==p['entity_tag']
                    and reference(pb,len(pb)-11)==selection['native_sketch_object_id'] and p['native_record']['payload_hex']==pb.hex())
                if p['kind']=='Line':
                    check(archive+' explicit Line endpoint identities '+str(r.object_id),reference(pb,cursor+107)==p['native_point_object_ids'][0]
                        and reference(pb,cursor+96)==p['native_point_object_ids'][1])
                else:
                    check(archive+' explicit Circle/Arc centre/radius '+str(r.object_id),reference(pb,cursor+96)==p['native_point_object_ids'][0]
                        and struct.unpack_from('<d',pb,cursor+72)[0]==p['source_geometry']['radius_cm'])
            if len(group['native_profile_points'])==8:
                counts['unwelded_eight_POINT_profiles']+=1
                observations=group['mathematical_vertex_native_POINT_observations']
                check(archive+' source-only math joins retain eight native POINTs '+str(feature['object_id']),group['native_POINT_welding'] is None
                    and len(observations)==4 and len({i for r in observations for i in r['native_POINT_ids']})==8
                    and len(group['mathematical_profile']['points_cm'])==4)
            kind=axis['entity']['kind'];counts[{'ConstructionAxis':'construction_axes','SketchLine':'sketch_line_axes','BRepEdge':'brep_edge_axes'}[kind]]+=1
            for raw in row['source_axis_provenance']['native_records']:
                r=by[raw['object_id']]
                check(archive+' raw axis record '+str(r.object_id),raw['class_guid']==r.class_guid and raw['payload_hex']==data[r.body:r.end].hex())
            if kind=='BRepEdge':
                proof=row['source_axis_provenance']['source_recipe_incidence'];carrier=row['source_axis_provenance']['source_line_coefficient_corroboration']
                check(archive+' named source EDGE precedes context geometry',proof['owner_object_id']==feature['object_id']
                    and proof['cached_source']['kind']=='Edge' and proof['native_body_object_id']!=group['native_body_object_id']
                    and len(proof['endpoint_operand_associations'])==2 and max(carrier['endpoint_residuals_cm'])<1e-10)
                if brep is None:brep=(data,records,features,member,members,bindings,feature,row)
            if 'construction_definition' in row['source_axis_provenance']:
                check(archive+' custom axis native POINT definition retained',len(row['source_axis_provenance']['native_defining_points'])==2)
                custom=(data,records,features,member,members,bindings,feature,row)
            if archive.endswith('/sketch_line.f3d') or archive.endswith('/sketch_line_reversed.f3d'):axis_contrasts[Path(archive).stem]=row
            check(archive+' no lifecycle/API identity assignment '+str(feature['object_id']),row['qualified_historical_state'] is None
                and row['exact_API_handle_identity'] is None and row['persistent_identity'] is None)
            if saved is None:saved=(data,records,features,member,members,bindings,feature,row)
        if not candidates:counts['outside_archives']+=1
        check(archive+' caller metadata/bindings pure',(features,bindings)==original)
        samples.append(dict(archive=archive,archive_sha256=sha(ROOT/archive),expected_sources=rows,expected_unresolved=unresolved))
    forward=axis_contrasts['sketch_line'];reverse=axis_contrasts['sketch_line_reversed']
    check('Native selected-axis reversal preserved without choosing effective sign',math.isclose(sum(a*b for a,b in zip(forward['source_axis']['entity']['direction'],reverse['source_axis']['entity']['direction'])),-1.,abs_tol=1e-10)
        and forward['original_controls']['revolve']['angle_radians']==reverse['original_controls']['revolve']['angle_radians']
        and forward['effective_axis'] is None and reverse['effective_axis'] is None)
    check('All fifteen requested source owners qualify',counts['target_fixture_owners']==15)
    def reject(label,context,changes=None,rs=None,fs=None,bs=None):
        data,records,features,member,members,bindings,feature,row=context
        if changes:
            payload=bytearray(data)
            for offset,value in changes:payload[offset:offset+len(value)]=value
            data=bytes(payload);members=dict(members);members[member]=data
        if fs is not None:features=fs;feature=next(f for f in fs if f['object_id']==feature['object_id'])
        try:qualify_revolve_source_operands(data,rs or records,features,member,members,bs or bindings,feature)
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error,ArithmeticError) as error:guards.append(dict(name=label,rejected=True,reason=str(error)))
        else:raise AssertionError(label+' accepted')
    data,records,features,member,members,bindings,feature,row=saved;by={r.object_id:r for r in records if r.is_primary};group=row['source_groups'][0]
    reject('Duplicate native profile Line primary',saved,rs=records+[by[group['profile_primitives'][0]['source_primitive_id']]])
    altered=copy.deepcopy(features);next(f for f in altered if f['object_id']==feature['object_id'])['parameters'][0]['raw_float64']+=.1
    reject('Supplied angular parameter differs from fresh native binding',saved,fs=altered)
    definition=by[group['native_profile_selection']['profile_loop_definition_object_id']]
    reject('Whole profile curve tag unresolved',saved,[(definition.body+29,struct.pack('<Q',999999))])
    ref=lambda i:b'\1'+struct.pack('<Q',i)+bytes(2)
    anchor=by[group['body_anchor_object_id']];reject('Creator anchor owner differs',saved,[(anchor.body+91,ref(1))])
    leaf=by[row['source_axis']['terminal_object_id']]
    reject('Selected origin axis leaf wrong native kind',saved,[(leaf.body+2,struct.pack('<Q',group['native_body_object_id']))])
    bad=copy.deepcopy(bindings);next(b for m in bad['decoded'] for b in m['bindings'] if b['native_body_object_id']==group['native_body_object_id'])['stored_handle']+=10000
    reject('Explicit same-asset stored BODY identifier differs',saved,bs=bad)
    cd,crs,cfs,cm,cms,cbs,cf,crow=custom;pp=crow['source_axis_provenance']['native_defining_points'][0]['native_point'];pr=next(r for r in crs if r.is_primary and r.object_id==pp['object_id']);_,cursor=attributes(cd[pr.body:pr.end],2)
    reject('Custom-axis native defining POINT differs from cached selected axis',custom,[(pr.body+cursor+19,struct.pack('<d',crow['source_axis_provenance']['native_defining_points'][0]['local_position_cm'][0]+.125))])
    bd,brs,bfs,bm,bms,bbs,bf,brow=brep;context=next(r for r in brs if r.is_primary and r.object_id==brow['source_axis']['context_record_object_id'])
    reject('Identity-qualified source EDGE and separate axis context disagree',brep,[(context.body+2,struct.pack('<d',brow['source_axis']['entity']['origin_cm'][0]+.125))])
    annotated=copy.deepcopy(features)
    for f in annotated:
        f['unrelated_annotation']='ignored'
        if f.get('kind')=='Sketch':f['geometry']=[dict(object_id=-1,kind='Injected')]
    actual=qualify_revolve_source_operands(data,records,annotated,member,members,bindings,next(f for f in annotated if f['object_id']==feature['object_id']))
    check('Source proof independent of unrelated caller geometry/annotations',actual==row)
    return dict(status='pass',interface='qualify_revolve_source_operands(data,records,features,member,members,body_blob_bindings,feature)',
        baseline_commit=baseline['baseline_commit'],baseline_sha256=sha(BASELINE),samples=samples,counts=counts,check_count=len(checks),checks=checks,
        guards=guards,guard_count=len(guards),positive_controls=[dict(name='Caller geometry/annotation independence',accepted=True)],
        source_sha256={name:sha(ROOT/name) for name in ('decode_revolve_source_operands.py','decode_revolve.py','decode_revolve_axes.py','decode_profiles.py',
            'decode_construction_modes.py','decode_selection_recipe_incidence.py','decode_sketch.py','decode_placement.py')},validator_sha256=sha(Path(__file__)),
        source_limits=['Native axis direction is preserved; source-relative effective orientation is separate, never chosen by target cache',
            'Eight separately-created native POINTs remain eight identities; source-only math endpoint joins do not weld native POINTs or assign native VERTEXs',
            'BRep-axis geometry is an explicit recipe-qualified source EDGE plus independent context corroboration, not independently regenerated source history',
            'Three Boolean seed inputs qualify as source primitives but their modified caches are not declared original/current geometry'],
        execution=dict(main_calls=0,live_API_calls=0,target_cache_geometry_identity_selection=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',type=Path,default=ROOT/'revolve-source-operand-decoding.json');args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd);args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status=report['status'],counts=report['counts'],checks=report['check_count'],guards=report['guard_count'],report=str(args.output))))
