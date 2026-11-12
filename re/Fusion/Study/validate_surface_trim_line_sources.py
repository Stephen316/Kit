"""Focused native SketchLine Trim source proof, separately from kept-cell recipes."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from decode_basics import decode_sketches
from decode_placement import decode_placement
from decode_sketch import attributes,reference,same
from decode_surface_trim_line_sources import resolve_surface_trim_line_source,SCOPE,TRIM
from decode_surface_trim_lines import decode_surface_trim_lines
from decode_surface_trim_sources import resolve_surface_trim_source
from validate_mesh_remesh import load

CAPTURES = [('surfacetrimtools-ca26d21e7ad9','sketch_line.f3d'),
            ('surfacetrimtools-650ca09579b1','sketch_line_offset_positive.f3d'),
            ('surfacetrimtools-650ca09579b1','sketch_line_reversed_negative.f3d')]


def validate(root,zstd):
    checks=[];samples=[];guards=[];contexts=[];legacy=[]
    def check(label,value):
        if not value:raise AssertionError(label)
        checks.append(label)
    def context(archive):
        data,records,features,member,members=load(root,archive,zstd)
        decode_sketches(data,records,features);decode_placement(data,records,features)
        return data,records,features
    for capture,filename in CAPTURES:
        folder=root/capture;truth=json.loads((folder/'ground_truth.json').read_text())
        actual=next(s for s in truth['samples'] if s['file']==filename);archive=capture+'/'+filename
        check(archive+' actual completed batch/errors empty',truth['terminal_status']=='Complete' and not truth['errors'] and (folder/'complete.txt').is_file())
        check(archive+' executed source snapshot matches hash',hashlib.sha256((folder/'executed-generator-source.txt').read_bytes()).hexdigest()==truth['executed_generator_sha256'])
        entry=truth.get('entrypoint_provenance')
        if entry:check(archive+' executed entrypoint hash',hashlib.sha256((folder/entry['executed_snapshot']).read_bytes()).hexdigest()==entry['sha256'])
        check(archive+' owned export and close succeed/hash exact',actual['export']['returned_success'] is True and actual['close_owned_document_returned'] is True and hashlib.sha256((root/archive).read_bytes()).hexdigest()==actual['export']['sha256'])
        check(archive+' before-node wrapper release and latercompute recorded',actual['trim_wrappers_released_before_move_to_end'] is True and actual['post_wrapper_release_compute_all_returned'] is True)
        data,records,features=context(archive);before=copy.deepcopy(features)
        wrapper=decode_surface_trim_lines(data,records,features)
        check(archive+' one source-qualified common Trim',len(wrapper['decoded'])==1 and not wrapper['unresolved'])
        decoded=wrapper['decoded'][0];settings=decoded['settings'];tool=settings['tool'];evidence=tool['native_source_evidence'];fid=decoded['feature_object_id']
        source_row=dict(feature_object_id=fid,native_source_evidence=evidence,scope=SCOPE)
        check(archive+' owned common/source IDs agree',tool['selection_record_object_id']==settings['tool_selection']['selection_record_object_id']==evidence['tool_selection_record_object_id'] and evidence['feature_object_id']==fid)
        source_stages=[]
        for label,value in [('input_argument',actual['exact_createInput_tool_argument']),('input_actual',actual['input_actual_trimTool']),('rolled_feature',actual['feature_before_node']['trimTool'])]:
            check(archive+' '+label+' actual SketchLine',value['actual_type_branch']=='SketchLine')
            value=value['value'];local=value['geometry_local'];world=value['geometry_world']
            check(archive+' '+label+' canonical local endpoint order agrees',same(local['startPoint'],evidence['source_start_sketch_local_cm']) and same(local['endPoint'],evidence['source_end_sketch_local_cm']))
            samples_by_fraction=evidence['natural_derived_samples']
            check(archive+' '+label+' component endpoint order independently agrees',same(world['startPoint'],samples_by_fraction[0]['point_component_cm']) and same(world['endPoint'],samples_by_fraction[-1]['point_component_cm']) and same(value['start_world_cm'],samples_by_fraction[0]['point_component_cm']) and same(value['end_world_cm'],samples_by_fraction[-1]['point_component_cm']))
            check(archive+' '+label+' canonical matrix corroborates APIbasis',same(value['sketch_transform'],evidence['canonical_placement']['sketch_to_component_matrix']))
            source_stages.append(dict(stage=label,actual_API_local_endpoints_cm=[local['startPoint'],local['endPoint']],actual_API_component_endpoints_cm=[world['startPoint'],world['endPoint']]))
        check(archive+' native source/endpoints fixed by tags before geometry',len(evidence['source_endpoints'])==2 and len({x['point_object_id'] for x in evidence['source_endpoints']})==2 and evidence['selection']['kind']=='Line')
        check(archive+' cellside/APIidentity remain unknown',evidence['native_API_source_assignment'] is None and evidence['native_trim_cell_assignment'] is None and evidence['selected_asm_face_id'] is None and 'undecoded' in settings['trim_cell_status'])
        check(archive+' callback no feature mutation',features==before)
        samples.append(dict(archive=archive,feature_object_id=fid,expected_source_row=source_row,
            expected_source_summary=dict(decoded=[source_row],unresolved=[],scope=SCOPE),actual_source_geometry_stages=source_stages,
            actual_requested=actual['requested'],actual_selected_input_cell_indices=actual['selected_input_cell_indices'],native_trim_cell_assignment=None,
            actual_API_interior_evaluator_samples=None,derived_interior_sample_status='Derived linear interpolation only; API truth records ordered local/component endpoints, not curve evaluator parameters or interior samples',
            executed_generator_sha256=truth['executed_generator_sha256'],entrypoint_provenance=entry,capture_status=truth['terminal_status']))
        contexts.append((data,records,features,decoded,evidence))
    # Historical Face/Body output dictionaries are checked without rewriting old reports.
    old=json.loads((root/'surface-trim-source-decoding.json').read_text())
    for sample in old['samples']:
        data,records,features=context(sample['archive']);expected=sample['expected_tool'];row=sample['expected_source_row']
        current=resolve_surface_trim_source(data,records,expected['selection_record_object_id'],row['feature_object_id'],features)
        check(sample['archive']+' old FaceBody fulltool exact',current==expected)
        check(sample['archive']+' Line wrapper no falsematch',decode_surface_trim_lines(data,records,features)['decoded']==[])
        legacy.append(dict(archive=sample['archive'],old_face_body_full_tool_exact=True,line_family_no_false_match=True))
    data,records,features,decoded,evidence=contexts[0]
    def guard(label,mutation=None,alter_features=None,tool_override=None):
        changed=bytearray(data);new_features=copy.deepcopy(features)
        if mutation:mutation(changed)
        if alter_features:alter_features(new_features)
        try:resolve_surface_trim_line_source(bytes(changed),records,evidence['tool_selection_record_object_id'] if tool_override is None else tool_override,decoded['feature_object_id'],new_features)
        except (ValueError,KeyError,TypeError,IndexError,UnicodeError,struct.error) as error:reason=str(error)
        else:raise AssertionError(label)
        check(label,True);guards.append(dict(guard=label,reason=reason))
    def primary(i):return next(r for r in records if r.is_primary and r.object_id==i)
    feature=primary(decoded['feature_object_id']);body=data[feature.body:feature.end]
    guard('Reject target proxy substituted as Line source',tool_override=reference(body,44))
    proxy=primary(evidence['tool_selection_record_object_id'])
    guard('Reject source proxy owner mismatch',lambda b:struct.pack_into('<Q',b,proxy.end-10,decoded['feature_object_id']+1))
    leaf=primary(evidence['selection']['terminal_object_id'])
    guard('Reject native source tag mismatch',lambda b:struct.pack_into('<Q',b,leaf.body+18,evidence['selection']['curve_entity_tag']+1))
    line=primary(evidence['selection']['curve_object_id']);raw=data[line.body:line.end];_,cursor=attributes(raw,2)
    guard('Reject native endpoint source aliased to opposite point',lambda b:struct.pack_into('<Q',b,line.body+cursor+108,evidence['source_endpoints'][1]['point_object_id']))
    point=primary(evidence['source_endpoints'][0]['point_object_id'])
    guard('Reject endpoint other-Sketch ownership',lambda b:struct.pack_into('<Q',b,point.end-10,evidence['selection']['sketch_object_id']+1))
    def placement_alias(fs):
        s=next(f for f in fs if f.get('sketch_object_id')==evidence['selection']['sketch_object_id']);s['placement']['sketch_to_component_matrix'][3]=1.
    guard('Reject canonical frame differing from stored transform',alter_features=placement_alias)
    transform=primary(evidence['native_transform_object_id'])
    guard('Reject transform component reference alias',lambda b:struct.pack_into('<Q',b,transform.end-10,evidence['selection']['sketch_object_id']))
    files=('decode_surface_trim_line_sources.py','validate_surface_trim_line_sources.py','decode_surface_trim_lines.py','decode_surface_tools.py','decode_selection.py','decode_sketch.py','decode_placement.py','decode_assembly.py')
    return dict(sample_count=len(samples),check_count=len(checks),malformed_guard_count=len(guards),samples=samples,legacy_controls=legacy,checks=checks,malformed_guards=guards,
        source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in files},
        limitations=['Production output identifies the selected native source line and component frame only; no selected-cell/side or persistent face identity',
            'API endpoint geometry numerically corroborates source after explicit native tag/ownership joins; entityToken/temporaryIDs never choose native identity',
            'Interior samples are derived segment fractions, not serialized Trim intervals or independently measured API evaluator samples',
            'No resultBODY/ASM changes, live Fusion calls, UI, solver or regeneration'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--zstd-library');p.add_argument('--output',default='surface-trim-line-source-decoding.json');args=p.parse_args();root=Path(__file__).resolve().parent
    z=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(root,z);Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('sample_count','check_count','malformed_guard_count')}))
if __name__=='__main__':main()
