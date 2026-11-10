"""Focused saved-output integration for parting Draft, BRep Patch and mesh."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from decode_basics import decode_basics
from decode_parting_line_drafts import decode_parting_line_drafts
from decode_patch_continuity import decode_patch_continuity
from decode_mesh_contents import decode_mesh_contents
from fusion_archive import read_members
from fusion_metadata import design_records
from validate_history_cache_integration import baseline_outputs, differences

ROOT=Path(__file__).resolve().parent
BASELINE='cd4cad1'
FILES=('meshcontrasts-10c2557c91a3/stl_centimeter.f3d',
 'meshcontrasts-10c2557c91a3/stl_millimeter.f3d',
 'meshcontrasts-10c2557c91a3/triangle_data_centimeter.f3d',
 'partinglinedrafts-c4d07c76fcd5/fixed_seven.f3d',
 'partinglinedrafts-c4d07c76fcd5/fixed_three.f3d',
 'partinglinedrafts-c4d07c76fcd5/moving_both_three.f3d',
 'patchcontinuity-b9b0be85a281/brep_curvature.f3d',
 'patchcontinuity-b9b0be85a281/brep_free.f3d',
 'patchcontinuity-b9b0be85a281/brep_tangent.f3d',
 'draftmodes-9b1a30f74aed/single.f3d',
 'draftmodes-9b1a30f74aed/two_angles.f3d',
 'draftmodes-9b1a30f74aed/symmetric.f3d',
 'surfacetools-856ca50cf4c7/patch_rectangle.f3d',
 'surfacetools-856ca50cf4c7/patch_circle.f3d',
 'assembly-acc48a9dc05d/assembly.f3d')
TOOL_SPECS=(
 ('parting_line_drafts','parting-line-draft-decoding.json',decode_parting_line_drafts,'Draft',
  'Unsupported observed fixed-plane Draft class/header',
  'Observed parting-line Draft controls and typed face/edge roles; direction variants, persistent topology and regeneration unresolved'),
 ('patch_continuity','patch-continuity-decoding.json',decode_patch_continuity,'SurfacePatch',
  'Unsupported basic sketch-profile patch layout',
  'Observed BRep Patch boundary continuity and owned source/result references; weights, flip semantics, persistent topology and regeneration unresolved'))
MESH_LEVEL='Observed component mesh ownership, native asset links and captured geometry buffers; general mesh formats, lifecycle and regeneration unresolved'


def normalized(value):return json.loads(json.dumps(value))


def restore_fields(current,prior,keys):
    for key in keys:
        if key in prior:current[key]=copy.deepcopy(prior[key])
        else:current.pop(key,None)


def goldens(report):
    rows=json.loads((ROOT/report).read_text())['samples']
    assert len({row['archive'] for row in rows})==len(rows),(report,'Duplicate report archive')
    return {row['archive']:row['expected_decoded'] for row in rows}


def check_output_manifest(outputs):
    assert len(outputs)==len(FILES)==15,'Focused cache must contain exactly fifteen outputs'
    for filename,output in zip(FILES,outputs):
        expected=Path(filename).parts
        assert Path(output['file']).parts[-len(expected):]==expected,(filename,'Cache output filename/order differs')
        members=[stream['member'] for stream in output['streams']]
        assert len(members)==len(set(members)),(filename,'Duplicate native stream member')
        for stream in output['streams']:
            identities=[feature['object_id'] for feature in stream['features']]
            assert len(identities)==len(set(identities)),(filename,'Duplicate feature identity')


def compare(before,current,filename,zstd):
    after=copy.deepcopy(current);members=read_members(ROOT/filename,zstd)
    totals=dict(parting_drafts=0,patch_continuities=0,recovered_tool_errors=0,
        meshes=0,mesh_base_features=0)
    assert len(before['streams'])==len(after['streams'])
    for original,stream in zip(before['streams'],after['streams']):
        member=stream['member'];assert member==original['member'],(filename,'Native stream order differs')
        data=members[member]
        records,_=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
        features={f['object_id']:f for f in stream['features']}
        old_features={f['object_id']:f for f in original['features']}
        recovered=[]
        for key,report,decoder,kind,old_error,level in TOOL_SPECS:
            summary=normalized(decoder(data,records,stream['features']))
            assert stream.pop(key,None)==(summary if summary['decoded'] or summary['unresolved'] else None)
            expected=goldens(report)
            if filename in expected:assert summary==expected[filename],(filename,key,'Focused report differs')
            elif summary['decoded']:raise AssertionError((filename,key,'Unexpected positive helper'))
            for row in summary['decoded']:
                identity=row['feature_object_id'];feature=features[identity]
                assert feature['kind']==kind and feature['tool_settings']==row['settings']
                assert feature['decode_level']==level
                restore_fields(feature,old_features[identity],('tool_settings','decode_level'))
                entry=dict(object_id=identity,kind=kind)
                assert entry not in original['tool_decoding']['decoded']
                assert stream['tool_decoding']['decoded'].count(entry)==1
                stream['tool_decoding']['decoded'].remove(entry)
                recovered.append((identity,kind,old_error))
                totals['parting_drafts' if kind=='Draft' else 'patch_continuities']+=1
        prior_errors=original['tool_decoding']['unresolved']
        removed=[e for e in prior_errors if (e['object_id'],e['kind'],e['reason']) in recovered]
        assert len(removed)==len(recovered)
        assert stream['tool_decoding']['unresolved']==[e for e in prior_errors if e not in removed]
        stream['tool_decoding']['unresolved']=copy.deepcopy(prior_errors)
        totals['recovered_tool_errors']+=len(removed)
        mesh=normalized(decode_mesh_contents(data,records,member,members))
        assert stream.pop('mesh_contents',None)==(mesh if mesh['decoded'] or mesh['unresolved'] else None)
        expected=goldens('mesh-decoding.json')
        if filename in expected:assert mesh==expected[filename],(filename,'Mesh focused report differs')
        elif mesh['decoded']:raise AssertionError((filename,'Unexpected positive mesh'))
        mesh_ids=set()
        if filename.startswith('meshcontrasts-10c2557c91a3/'):
            assert features[202]['kind']=='UnsupportedFeature', (filename,'BaseFeature202 must remain unsupported')
            assert features[202]==old_features[202], (filename,'BaseFeature202 metadata changed')
            assert len(mesh['decoded'])==1 and not mesh['unresolved'], (filename,'Expected one bounded mesh')
            expected_owner=None if filename.endswith('/triangle_data_centimeter.f3d') else 224
            assert mesh['decoded'][0]['feature_object_id']==expected_owner,(filename,'Actual mesh owner route changed')
        for row in mesh['decoded']:
            totals['meshes']+=1
            identity=row['feature_object_id']
            if identity is None:continue
            feature=features[identity]
            assert feature['kind']=='BaseMeshFeature' and feature['decode_level']==MESH_LEVEL
            assert feature.pop('mesh_contents')==row
            restore_fields(feature,old_features[identity],('kind','decode_level'))
            mesh_ids.add(identity);totals['mesh_base_features']+=1
        if mesh_ids:
            discovery=stream['feature_discovery'];prior=original['feature_discovery']
            assert discovery.pop('class_decoded_mesh_base_feature_count')==len(mesh_ids)
            assert discovery['unsupported_features']==[r for r in prior['unsupported_features'] if r['object_id'] not in mesh_ids]
            assert discovery['unsupported_feature_count']==len(discovery['unsupported_features'])
            restore_fields(discovery,prior,('unsupported_features','unsupported_feature_count'))
            def restore_entry(entry):
                if entry['object_id'] in mesh_ids:
                    assert entry['kind']=='BaseMeshFeature'
                    entry['kind']=old_features[entry['object_id']]['kind']
                for child in entry.get('children',[]):restore_entry(child)
            for sequence in stream['timeline_decoding']['sequences']:
                for entry in sequence['visible_entries']:restore_entry(entry)
    assert after==before,(filename,'Unexpected prior-output difference',differences(before,after))
    return dict(file=filename,**totals,all_other_prior_fields_exact=True,
        ASM_geometry_stored_placement_and_unrelated_warnings_exact=True,
        qualified_difference_paths=differences(before,current))


def validate(zstd,saved=None,baseline_cache=None,current_cache=None):
    if saved is not None:
        assert saved['baseline_commit']==BASELINE and saved['files']==list(FILES)
        before,current=saved['before'],saved['after']
    else:
        if baseline_cache is None:
            cache=Path('/private/tmp/fusion-draft-patch-mesh-baseline.json')
            baseline_cache=json.loads(cache.read_text()) if cache.exists() else None
        if baseline_cache is not None:
            assert baseline_cache['baseline_commit']==BASELINE and baseline_cache['files']==list(FILES)
            before=baseline_cache['before']
        else:before=baseline_outputs(list(FILES),zstd,revision=BASELINE)
        if current_cache is not None:
            assert current_cache['baseline_commit']==BASELINE and current_cache['files']==list(FILES)
            current=current_cache['after']
        else:current=[normalized(decode_basics(ROOT/name,zstd)) for name in FILES]
    check_output_manifest(before);check_output_manifest(current)
    rows=[compare(prior,actual,name,zstd) for name,prior,actual in zip(FILES,before,current)]
    totals={k:sum(row[k] for row in rows) for k,value in rows[0].items() if type(value) is int}
    assert totals['parting_drafts']==totals['patch_continuities']==totals['meshes']==3
    assert totals['recovered_tool_errors']==6 and totals['mesh_base_features']==2
    assert all(prior==actual for prior,actual in zip(before[9:],current[9:]))
    return dict(scope='Fifteen pinned saved designs against local cd4cad1; focused helper/report matches and exact prior-field restoration',
        baseline_commit=BASELINE,files=list(FILES),samples=rows,
        inputs=dict(current_cache_used=saved is not None or current_cache is not None,
            source_archive_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES},
            focused_report_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
                ('parting-line-draft-decoding.json','patch-continuity-decoding.json','mesh-decoding.json')},
            source_module_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
                ('decode_basics.py','decode_parting_line_drafts.py','decode_draft.py','decode_patch_continuity.py',
                 'decode_mesh_contents.py','validate_draft_patch_mesh_integration.py')}),
        summary=dict(saved_files=15,legacy_full_output_controls=6,**totals,
            unexpected_prior_output_changes=0,ASM_geometry_changes=0,live_API_calls=0),
        limits=['New native roles do not identify persistent selected ASM topology or regenerate drafted/patched surfaces.',
            'Mesh provenance does not make BaseFeature202 an owner; actual null API owner and unsupported BaseFeature remain explicit.',
            'Ten newly observed ASM EDGE attribute diagnostics are preserved; successful native control decoding does not remove them.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('saved','baseline','current'):parser.add_argument('--'+name+'-outputs',type=Path)
    parser.add_argument('--zstd-library');args=parser.parse_args()
    zstd=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    def read(path):return json.loads(path.read_text()) if path else None
    report=validate(zstd,read(args.saved_outputs),read(args.baseline_outputs),read(args.current_outputs))
    (ROOT/'draft-patch-mesh-integration.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['summary'],sort_keys=True))
