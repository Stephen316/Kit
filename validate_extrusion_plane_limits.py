"""Focused selected-plane native proofs and complete prior source defaults."""
import argparse
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct

from decode_extrude import decode_extrude
from decode_extrusion_source_operands import EXTRUDE,qualify_extrusion_source_operands
from decode_sketch import reference
from validate_mesh_remesh import load

ROOT=Path(__file__).resolve().parent
BASELINE=Path('/private/tmp/fusion-plane-extrusion-reconstruction-baseline.json')
OLD_BASELINE=Path('/private/tmp/fusion-extrusion-reconstruction-baseline.json')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(zstd):
    checks,guards,samples,defaults=[],[],[],[]
    def check(label,value):
        if not value:raise AssertionError(label)
        checks.append(label)
    old_report=json.loads((ROOT/'extrusion-source-operand-decoding.json').read_text())
    old_baseline=json.loads(OLD_BASELINE.read_text())
    old_by={r['archive']:r for r in old_report['samples']}
    for archive,before in zip(old_baseline['files'],old_baseline['before']):
        data,records,features,member,members=load(ROOT,archive,zstd)
        bindings=before['streams'][0]['body_blob_bindings']
        rows,unresolved=[],[]
        for feature in features:
            if feature.get('class_guid')!=EXTRUDE:continue
            try:rows.append(qualify_extrusion_source_operands(data,records,features,member,members,bindings,feature))
            except (ValueError,KeyError,TypeError,IndexError,UnicodeError,struct.error) as error:
                unresolved.append(dict(feature_object_id=feature['object_id'],reason=str(error)))
        prior=old_by[archive]
        check(archive+' complete prior source defaults and errors EXACT',rows==prior['expected_sources'] and unresolved==prior['expected_unresolved'])
        defaults.append(dict(archive=archive,expected_default_sources=prior['expected_sources'],expected_default_unresolved=prior['expected_unresolved']))
    baseline=json.loads(BASELINE.read_text());saved=None;count=0
    for archive,before in zip(baseline['files'],baseline['before']):
        data,records,features,member,members=load(ROOT,archive,zstd)
        bindings=before['streams'][0]['body_blob_bindings'];original=copy.deepcopy((features,bindings))
        by={r.object_id:r for r in records if r.is_primary};rows=[]
        for feature in features:
            if feature.get('class_guid')!=EXTRUDE:continue
            native_record=by[feature['object_id']]
            controls,_=decode_extrude(data[native_record.body:native_record.end],feature,allow_surface=True)
            if controls['start']['kind']!='FromEntity' and controls['extent']['side_one']['condition']!='ToEntity':continue
            row=qualify_extrusion_source_operands(data,records,features,member,members,bindings,feature,allow_plane_limits=True)
            rows.append(row);count+=1
            proof=row['plane_limit_provenance'];limit=proof['limits'][0]
            check(archive+' native controls untouched',row['settings']==controls and row['source_groups'][0]['extrude_controls']==controls
                and proof['native_controls_unchanged'] is True and proof['derived_distance_controls'] is None)
            check(archive+' full source and group selected-plane proof exact',row['source_groups'][0]['plane_limit_provenance']==proof)
            selected=limit['selection'];proxy=by[selected['selection_object_id']];p=data[proxy.body:proxy.end]
            descriptor=by[selected['descriptor_object_id']];d=data[descriptor.body:descriptor.end]
            leaf=by[selected['terminal_object_id']];l=data[leaf.body:leaf.end]
            check(archive+' explicit receiving selection chain',reference(p,6)==descriptor.object_id and reference(p,94)==feature['object_id']
                and reference(d,2)==leaf.object_id and reference(d,252)==feature['object_id']
                and struct.unpack_from('<Q',l,2)[0]==limit['plane_native_geometry']['plane_object_id'])
            definition=limit['plane_definition'];support=definition['support_inputs'][0]['entity']['native_entity'];scalar=definition['scalar_parameters'][0]
            expected=[o+scalar['value']*n for o,n in zip(support['origin_cm'],support['normal'])]
            check(archive+' input plane derived from typed origin support and scalar',limit['plane_native_geometry']['origin_cm']==expected
                and limit['stored_plane_geometry']['origin_cm']==expected
                and limit['plane_native_geometry']['normal']==support['normal'])
            for raw in limit['native_records']+[limit['proxy_support'],limit['descriptor_support']]:
                r=by[raw['object_id']]
                check(archive+' literal native record '+str(r.object_id),raw['class_guid']==r.class_guid and raw['payload_hex']==data[r.body:r.end].hex())
            check(archive+' same native component proof',proof['component_provenance']['component_object_id']==row['component_provenance']['component_object_id'])
            check(archive+' opaque raw flag retained',limit['raw_extent_flags']==controls['extent']['side_one']['uninterpreted_flags'])
            api=next(r for r in json.loads((ROOT/Path(archive).parent/'ground_truth.json').read_text())['samples'] if r['file']==Path(archive).name)
            if limit['operand_scope']=='side_one':
                check(archive+' actual API ToEntity entity/offset/chain',api['extent_one']['kind']=='ToEntityExtentDefinition'
                    and api['extent_one']['entity_name']==limit['plane_native_geometry']['name']
                    and api['extent_one']['offset']==limit['native_selected_offset_cm'] and api['extent_one']['isChained'] is False)
            else:
                check(archive+' actual API FromEntity entity/offset/distance',api['start']['kind']=='FromEntityStartDefinition'
                    and api['start']['entity_name']==limit['plane_native_geometry']['name']
                    and api['start']['offset']==limit['native_selected_offset_cm']
                    and api['extent_one']['distance']==controls['extent']['side_one']['distance_cm'])
            if saved is None:saved=(data,records,features,member,members,bindings,feature,row)
        check(archive+' caller source metadata and bindings pure',(features,bindings)==original)
        samples.append(dict(archive=archive,archive_sha256=sha(ROOT/archive),expected_sources=rows,expected_unresolved=[]))
    check('Exactly three existing native plane fixtures qualified',count==3)
    data,records,features,member,members,bindings,feature,row=saved
    by={r.object_id:r for r in records if r.is_primary};limit=row['plane_limit_provenance']['limits'][0]
    def reject(label,d=data,rs=records,fs=features,ms=members,f=feature):
        try:qualify_extrusion_source_operands(d,rs,fs,member,ms,bindings,f,allow_plane_limits=True)
        except (ValueError,KeyError,TypeError,IndexError,UnicodeError,struct.error) as error:
            guards.append(dict(name=label,rejected=True,reason=str(error)))
        else:raise AssertionError(label+' accepted')
    def changed(label,changes):
        payload=bytearray(data)
        for offset,value in changes:payload[offset:offset+len(value)]=value
        altered=bytes(payload);altered_members=dict(members);altered_members[member]=altered
        reject(label,d=altered,ms=altered_members)
    def ref(identity):return b'\1'+struct.pack('<Q',identity)+bytes(2)
    selection=limit['selection'];descriptor=by[selection['descriptor_object_id']];proxy=by[selection['selection_object_id']]
    reject('Duplicate selected descriptor primary',rs=records+[descriptor])
    changed('Proxy receiving owner mismatch',[(proxy.body+94,ref(1))])
    support=by[limit['descriptor_support']['object_id']]
    changed('Selected plane definition support owner mismatch',[(support.body+12,ref(33))])
    context=by[limit['context_object_id']]
    changed('Context plane normal/frame differs from actual selected plane',[(context.body+59,struct.pack('<d',0.)),(context.body+67,struct.pack('<d',1.))])
    leaf=by[selection['terminal_object_id']]
    changed('Direct selected plane and context leaf disagree',[(leaf.body+2,struct.pack('<Q',42))])
    collection=by[row['plane_limit_provenance']['component_provenance']['plane_collection_object_id']]
    changed('Repeated selected plane membership differs',[(collection.body+51,ref(42))])
    # Change both reciprocal numeric records, leaving all cached/context geometry
    # unchanged: this specifically tests independent support+scalar derivation.
    from decode_basics import named_features,attach_parameters
    from decode_parameters import decode_stream
    fresh=named_features(data,records);parameters,_=decode_stream(data,records);attach_parameters(data,records,fresh,parameters)
    owner=limit['plane_definition']['feature_object_id'];pf=next(f for f in fresh if f['object_id']==owner)
    scalar=next(p for p in pf['parameters'] if p['role']=='AlongDistance');binding=by[scalar['binding_object_id']]
    changed('Finite reciprocal Offset scalar differs from stored plane geometry',[(scalar['value_offset'],struct.pack('<d',scalar['raw_float64']+.25)),(binding.body+21,struct.pack('<d',scalar['raw_float64']+.25))])
    changed('Unsupported literal ToEntity flag retained as unsupported',[(by[feature['object_id']].body+103,struct.pack('<I',2))])
    annotated=copy.deepcopy(features)
    for f in annotated:
        f['unrelated_annotation']='ignored'
        if f.get('kind')=='Sketch':f['geometry']=[dict(kind='Injected',object_id=-1)]
    result=qualify_extrusion_source_operands(data,records,annotated,member,members,bindings,
        next(f for f in annotated if f['object_id']==feature['object_id']),allow_plane_limits=True)
    check('New plane source proof independent of caller annotations and geometry',result==row)
    return dict(status='pass',interface='qualify_extrusion_source_operands(..., *, allow_plane_limits=False)',
        baseline_commit=baseline['baseline_commit'],baseline_sha256=sha(BASELINE),prior_full_default_report_sha256=sha(ROOT/'extrusion-source-operand-decoding.json'),
        source_sha256={name:sha(ROOT/name) for name in ('decode_extrusion_plane_limits.py','decode_extrusion_source_operands.py','decode_plane_definitions.py','decode_extrude.py')},
        validator_sha256=sha(Path(__file__)),samples=samples,default_controls=defaults,counts=dict(plane_source_owners=count,complete_prior_default_archives=len(defaults)),
        check_count=len(checks),checks=checks,guard_count=len(guards),guards=guards,
        positive_controls=[dict(name='Caller metadata independence',accepted=True)],
        evidence_limits=['Only three saved native plane extent fixtures; no independent Extrude plane holdout found in focused reports',
            'All selected planes parallel/co-directed with source Sketch and stored direction; negative offset/reversed/oblique conventions unproved',
            'Opaque native flags and numeric trailer slots retained without semantics; no native Distance normalization',
            'Derived plane input is origin support plus reciprocal Offset scalar; stored selected plane/context independently corroborate'],
        execution=dict(main_calls=0,live_API_calls=0,geometry_identity_selection=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',type=Path,default=ROOT/'extrusion-plane-limit-source-decoding.json');args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd);args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status=report['status'],checks=report['check_count'],guards=report['guard_count'],counts=report['counts'],report=str(args.output))))
