"""Scoped negative SplitBody Profile attempts; no runtime decoding coverage added."""
import argparse
import hashlib
import json
from pathlib import Path

from validate_mesh_repair import context

ROOT=Path(__file__).resolve().parent
DIRECTORY='splitbodyprofiles-be9787c7a7d8'
SPLIT='65CA3206-E33A-471E-8E40-2C72B57C6181'
EXTRUDE='DD405BC2-D673-44F0-8833-5CB2A1C186C7'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def getter_errors(value,path=''):
    result=[]
    if isinstance(value,dict):
        if value.get('getter_errors'):result.append(dict(path=path,errors=value['getter_errors']))
        for key,item in value.items():
            if key!='getter_errors':result.extend(getter_errors(item,path+'/'+key))
    elif isinstance(value,list):
        for index,item in enumerate(value):result.extend(getter_errors(item,path+'/'+str(index)))
    return result


def validate(zstd):
    folder=ROOT/DIRECTORY;truth=json.loads((folder/'ground_truth.json').read_text())
    assert truth['terminal_status']=='CompleteWithErrors' and len(truth['samples'])==len(truth['errors'])==3
    assert (folder/'complete.txt').is_file()
    progress=json.loads((folder/'progress.json').read_text())
    assert progress['phase']=='batch_terminal' and progress['exported_sample_count']==3 and progress['error_count']==3
    assert digest(folder/'executed-generator-source.txt')==truth['executed_generator_sha256']
    assert digest(folder/'executed-sdk-surface.txt')==truth['executed_sdk_surface_sha256']
    sdk=(folder/'executed-sdk-surface.txt').read_text()
    assert 'construction plane, profile, or a face.' in sdk
    report=dict(scope='Three actual owned SplitBody Profile-input attempts in Fusion2705.1.30; createInput accepted, add rejected, unchanged input body counts and absence of native SplitBody records. Negative evidence only, not universal Profile support/absence.',
        runtime_coverage_added=False,
        capture_provenance=dict(ground_truth=DIRECTORY+'/ground_truth.json',ground_truth_sha256=digest(folder/'ground_truth.json'),
            executed_generator_sha256=truth['executed_generator_sha256'],executed_sdk_surface_sha256=truth['executed_sdk_surface_sha256'],
            sdk_runtime_sha256=truth['sdk_runtime_sha256'],fusion_version=truth['fusion_version']),
        documented_API=dict(source_snapshot='executed-sdk-surface.txt',method='SplitBodyFeatures.createInput',
            allowed_tool_excerpt='construction plane, profile, or a face.',
            scope='Installed Python SDK documentation explicitly lists Profile, while actual add rejects these three valid-looking Profile inputs.'),
        samples=[],
        findings=['All three input Profile objects are valid and on the sketch plane, with one outer four-line loop and no captured Profile subtree getter errors.',
            'createInput returns a valid SplitBodyFeatureInput retaining the actual Profile tool and requested extension flag; acceptance is not feature creation.',
            'All three add calls raise RuntimeError3 Invalid splitting tool. SplitBody API collection remains empty and full primary native metadata contains no SplitBody definition records.',
            'The successful exports contain the owned setup geometry only. Actual source body counts remain1/1/2, and every owned document close returns true.',
            'Profile.plane and ProfileCurve.geometry are in local sketch coordinates at z0; sketch worldGeometry and origin are at z1cm. No failure cause is assigned from that normal coordinate distinction.'],
        decision='No decoder or native Profile-tool coverage can be claimed from these failed creations. Retain exact captured failures; use separately captured valid sheet tools for the multi-target study.',
        limitations=['These outcomes are scoped to the three saved inputs, SDK/build, and captured document setup. They do not prove Profile is universally unsupported or contradict all documented uses.',
            'No confirmed corrective input change is evidenced. The exact engine restriction/failure cause is unresolved; no repeated capture or undocumented workaround is proposed.',
            'Optional body.tempId/baseOrFormFeature getters fail in nested input body truth; these recorded failures are retained separately from Profile/input top-level validity and do not create topology identity.',
            'API collections and native absence are independently checked. Geometry, names, array order and opaque entity tokens are not used to invent a missing feature or source/result identity.'])
    for actual in truth['samples']:
        filename=DIRECTORY+'/'+actual['file'];data,records,features,member,members=context(filename,zstd)
        assert actual['close_owned_document_returned'] is True and not actual['getter_errors']
        assert actual['export']['returned_success'] is True and actual['export']['sha256']==digest(ROOT/filename)
        assert actual['export']['size_bytes']==(ROOT/filename).stat().st_size
        assert actual['timeline_count']==actual['timeline_marker_position']
        assert actual['split_status']=='AttemptError' and actual['feature_at_timeline_end'] is None
        errors=[error for error in truth['errors'] if error['case']==actual['case']]
        assert len(errors)==1 and errors[0]['phase']=='split_attempt' and 'RuntimeError: 3 : Invalid splitting tool' in errors[0]['error']
        assert actual['split_error']==errors[0]
        profile=actual['profile_tool_before_split'];inp=actual['input_before_add']
        assert profile['objectType']=='adsk::fusion::Profile' and profile['isValid'] is True and profile['isOnSketchPlane'] is True
        assert not getter_errors(profile)
        assert profile['parentSketch']['isValid'] is True and profile['parentSketch']['origin_cm']==[0.,0.,1.]
        loops=profile['profileLoops'];assert len(loops)==1 and loops[0]['isOuter'] is True and len(loops[0]['profileCurves'])==4
        for curve in loops[0]['profileCurves']:
            assert curve['isValid'] is True and curve['sketchEntity']['isValid'] is True
            assert curve['geometry']['objectType']=='adsk::core::Line3D'
            assert curve['geometry']['startPoint'][2]==curve['geometry']['endPoint'][2]==0.
            assert curve['sketchEntity']['worldGeometry']['startPoint'][2]==curve['sketchEntity']['worldGeometry']['endPoint'][2]==1.
        assert profile['API_profile_plane']['origin'][2]==0. and profile['API_profile_plane']['normal']==[0.,0.,1.]
        assert inp['objectType']=='adsk::fusion::SplitBodyFeatureInput' and inp['isValid'] is True and not inp['getter_errors']
        assert inp['splittingTool']['actual_type_branch']=='Profile' and inp['splittingTool']['value']['isOnSketchPlane'] is True
        assert inp['isSplittingToolExtended']==actual['requested']['isSplittingToolExtended']
        assert actual['exact_createInput_arguments']['splitting_tool_argument_type']=='adsk::fusion::Profile'
        expected=actual['requested']['split_body_count']
        assert actual['component_bodies_before_split']['count']==actual['component_bodies_after_split']['count']==expected
        assert actual['split_collection_count_before']==actual['split_collection_count_after']==0
        native=[r for r in records if r.is_primary and r.class_guid==SPLIT]
        assert not native
        setup=[r.object_id for r in records if r.is_primary and r.class_guid==EXTRUDE]
        assert len(setup)==expected
        report['samples'].append(dict(archive=filename,archive_sha256=digest(ROOT/filename),case=actual['case'],
            actual_requested=actual['requested'],actual_createInput_arguments=actual['exact_createInput_arguments'],
            actual_input_valid=True,actual_input_tool_type='Profile',actual_profile_valid=True,actual_profile_isOnSketchPlane=True,
            actual_profile_outer_loop_count=1,actual_profile_line_count=4,actual_profile_getter_errors=[],
            actual_profile_local_plane=profile['API_profile_plane'],actual_parent_sketch_world_origin_cm=profile['parentSketch']['origin_cm'],
            actual_add_error=errors[0],actual_split_status=actual['split_status'],actual_SplitBody_collection_count_before=0,actual_SplitBody_collection_count_after=0,
            actual_BRep_count_before=expected,actual_BRep_count_after=expected,primary_native_SplitBody_record_ids=[],native_setup_Extrude_record_ids=setup,
            nested_input_getter_errors=getter_errors(inp),export_completed=True,owned_document_closed_true=True))
    report['validation']=dict(attempts=3,valid_Profile_inputs=3,createInput_accepted=3,add_failures=3,actual_exports=3,owned_closes_true=3,
        native_SplitBody_records=0,unchanged_body_counts=[1,1,2],no_runtime_changes=True,no_main_calls=True)
    report['validator_sha256']=digest(ROOT/'validate_split_body_profile_attempts.py')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',default='split-body-profile-attempts.json');args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd);Path(args.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['validation'],sort_keys=True))
