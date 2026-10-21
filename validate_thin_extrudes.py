"""Actual Thin Extrude getters, common-parser compatibility and malformed guards."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_basics import decode_basics
from decode_brep import decode_topology
from decode_extrude import decode_extrude
from decode_thin_extrudes import decode_thin_extrudes, inspect_thin_extrude, EXTRUDE
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT=Path(__file__).resolve().parent
DIRECTORIES=('thinextrudes-c1632bcb5efe','thinextrudes-f758eff14202')


def validate(zstd):
    truths={directory:json.loads((ROOT/directory/'ground_truth.json').read_text()) for directory in DIRECTORIES}
    assert all(t['status']=='complete' for t in truths.values())
    assert len(truths[DIRECTORIES[0]]['errors'])==1 and truths[DIRECTORIES[0]]['errors'][0]['case']=='open_line_side1'
    assert not truths[DIRECTORIES[1]]['errors']
    report={'scope':'Six actual thin Extrude exports plus one ordinary-solid control; initial failed open-profile capture retained and one targeted retry succeeds',
        'interface':'decode_thin_extrudes(data,records,features)->decoded/unresolved/scope; no mutation; onlyTrue thin rows published',
        'inspection_interface':'inspect_thin_extrude(data,records,body,feature,*,features=()) additionally exposes the ordinaryFalse block for focused controls',
        'integration':'Attach thin_metadata and explicit source/profile/body evidence to corresponding Extrude feature IDs in a separate thin_extrudes summary. Existing common operation/start/extent settings remain exactly those of shared decode_extrude. Helper itself does not mutate warnings; integration may clear only the same-feature profile-source failure after the independently owned single-Line route is resolved.',
        'schema':{'shared_common_controls':'decode_extrude.layout_observer supplies common_controls_end_offset and extent_mode_code; no common extrusion schema copied into new reader',
            'thin_block':'Reserveduint32zero; one nativeboolthin flag; uint32wallLocationOne+optional typed11-byte binding; uint32wallLocationTwo+optional binding. Variable optional references determine following profile/result list offsets.',
            'wall_locations':'Native0/1/2 match actual API ThinExtrudeWallLocation.Side1/Center/Side2; names are preserved, no universal inward/outward claim.',
            'binding':'Existing attached feature bindings reused. Each wall has typed numeric ModelParameter, decoded again by decode_parameters.decode_stream, correct Side1/2WallThickness role, positive finite internal cm value and reciprocal85-byte binding owner/parameter/value copies.',
            'unverified':'Other operations, symmetric extents, taper/start offsets, non-distance extents, negative/zero thickness and general thin geometry regeneration remain unsupported.'},
        'capture_provenance':{'actual_truth_files':[{'file':directory+'/ground_truth.json','sha256':hashlib.sha256((ROOT/directory/'ground_truth.json').read_bytes()).hexdigest()} for directory in DIRECTORIES],
            'current_reproduction_source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('GenerateThinExtrudeContrasts.py','GenerateThinOpenProfileRetry.py')},
            'source_hash_scope':'Current reproduction source hashes only. Initial generator was corrected after the first six exports; no exact executed-source hash was captured, reconstructed or claimed.',
            'initial_open_failure':{'case':'open_line_side1','error':truths[DIRECTORIES[0]]['errors'][0]['error'],
                'getter_errors':next(s for s in truths[DIRECTORIES[0]]['samples'] if s['case']=='open_line_side1')['getter_errors']},
            'targeted_retry':'Generic Profile.parentSketch can be null; unsupported optional generic-profile token getter not retried. Original selected SketchLine endpoints/token retained separately.',
            'all_owned_documents_closed_true':all(s['close_owned_document_result'] is True for t in truths.values() for s in t['samples'])},
        'samples':[],'ordinary_control':{},'malformed_guards':[],'legacy_controls':[],
        'limitations':['Thin wall sides denote extrusion extent sides, not independently asymmetric offsets around a single profile.',
            'Inactive one-sided wall-two code is retained without interpreting it as an active getter value; no inactive getter was called.',
            'Open source generic Profile has no parentSketch, and feature.profile actually returns Path. No actual Path member getters were captured; original selected Line getters and native owned single-Line references remain explicit. Profile loops/open single-line selection and feature-owned native BODY anchors are explicit provenance; persistent topology/current-final lifecycle and wall geometry generation are not established.',
            'Positive finite numeric values are not restricted to fixture constants; actual numeric bindings and parameter roles establish their meaning.',
            'Stored body bounds/counts below corroborate actual results after keyed identity mapping; no candidate chosen by coordinates.',
            'Ordinary/surface existing features get no new thin sidecar or diagnostic. Current generator hashes are not historical capture-source hashes.']}
    contexts={};bindings=thin_count=closed=open_count=0;compatibility=0;getter_checks=0;body_checks=0
    for directory,truth in truths.items():
        for sample in truth['samples']:
            if sample['status']!='exported':continue
            assert not sample['getter_errors'] and sample['close_owned_document_result'] is True
            relative=directory+'/'+sample['file'];members=read_members(ROOT/relative,zstd);model=decode_basics(ROOT/relative,zstd);stream=model['streams'][0]
            member=stream['member'];data=members[member];records,_=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
            features=stream['features'];before=copy.deepcopy(features);feature,=[f for f in features if f['kind']=='Extrude'];record,=[r for r in records if r.is_primary and r.object_id==feature['object_id']]
            body=data[record.body:record.end];observed=[]
            common=decode_extrude(body,feature);callback_common=decode_extrude(body,feature,layout_observer=observed.append)
            assert common==callback_common and len(observed)==1;compatibility+=1
            summary=decode_thin_extrudes(data,records,features);assert not summary['unresolved'] and features==before
            api=sample['settings'];assert api['operation']==3 and api['is_solid'] is True
            if not api['is_thin_extrude']:
                assert not summary['decoded'];inspection=inspect_thin_extrude(data,records,body,feature,features=features)
                assert inspection['is_thin_extrude'] is False
                report['ordinary_control']={'file':relative,'actual_API_isThinExtrude':False,'expected_inspection':inspection,
                    'no_runtime_thin_sidecar_or_diagnostic':True,'common_default_and_callback_outputs_exact':True}
                contexts[sample['case']]=(data,records,features,member,members,stream,None)
                continue
            row,=summary['decoded'];metadata=row['thin_metadata'];thin_count+=1
            assert row['common_extrusion_controls']==common[0] and metadata['is_thin_extrude'] is True
            assert bytes.fromhex(metadata['block_hex'])==body[metadata['block_start_offset']:metadata['block_end_offset']]
            for side in (1,2):
                key='side_one' if side==1 else 'side_two';actual_key='wall_one' if side==1 else 'wall_two'
                wall=metadata[key]
                if side==2 and not wall['applicable']:
                    assert api['has_two_extents'] is False and api['wall_two']['applicable'] is False
                    continue
                actual=api[actual_key];assert wall['stored_wall_location_code']==actual['location']
                assert wall['parameter_role']==actual['thickness']['role'] and wall['parameter_name']==actual['thickness']['name']
                assert math.isclose(wall['thickness_cm'],actual['thickness']['raw_value'],abs_tol=1e-12)
                assert actual['thickness']['created_by']==feature['name'];bindings+=1;getter_checks+=1
            extent=common[0]['extent'];assert (extent['mode']=='TwoSided')==api['has_two_extents']
            assert math.isclose(extent['side_one']['distance_cm'],api['extent_one']['distance']['raw_value'],abs_tol=1e-12)
            if api['has_two_extents']:assert math.isclose(extent['side_two']['distance_cm'],api['extent_two']['distance']['raw_value'],abs_tol=1e-12)
            if row['profile'].get('profile_kind')=='SketchOpenProfile':
                open_count+=1;assert sample['source_profile_before_feature']['parent_sketch_is_null'] is True
                assert api['profile']['entity_type']=='adsk::fusion::Path'
                native=next(g for f in features if f['kind']=='Sketch' for g in f['geometry'] if g['object_id']==row['profile']['curve_object_id'])
                assert math.dist(native['start_cm'],sample['open_profile_input']['start_world_cm'])<1e-12 and math.dist(native['end_cm'],sample['open_profile_input']['end_world_cm'])<1e-12
            else:
                closed+=1;assert row['profile']['sketch_name']==api['profile']['sketch_name']
                assert len(row['profile']['loops'])==len(api['profile']['loops'])==1
                assert len(row['profile']['loops'][0]['curve_references'])==len(api['profile']['loops'][0]['curves'])==4
            # Source/body identity is explicit before result geometry is examined.
            pairs=[(m,b) for m in stream['body_asm_identifiers']['decoded'] for b in m['bindings'] if b['native_body_object_id']==row['native_body_object_id']]
            mapping,binding=pairs[0];assert len(pairs)==1
            parsed=inspect_asm(members[mapping['history_blob_member']]);topology=decode_topology(parsed)
            graph,=[g for g in topology['body_graphs'] if g['body_index']==binding['asm_body_index']]
            actual_body,=sample['result_bodies'];assert graph['body_transform_is_identity'] is True
            for kind in ('face','edge','vertex'):assert graph['counts'][kind]==actual_body[kind+'_count']
            low=[min(p[a] for p in graph['raw_vertex_positions']) for a in range(3)];high=[max(p[a] for p in graph['raw_vertex_positions']) for a in range(3)]
            assert math.dist(low,actual_body['bounds_min_cm'])<1e-9 and math.dist(high,actual_body['bounds_max_cm'])<1e-9;body_checks+=1
            report['samples'].append({'file':relative,'expected_summary':summary,'common_default_and_callback_outputs_exact':True,
                'actual_API_isThinExtrude':True,'actual_API_hasTwoExtents':api['has_two_extents'],'actual_API_profile_returned_type':api['profile']['entity_type'],
                'actual_API_wall_one':api['wall_one'],'actual_API_wall_two':api['wall_two'],
                'actual_API_health_state':sample['health_state'],'actual_API_warning':sample['warning'],
                'typed_result_geometry_control':{'native_body_object_id':row['native_body_object_id'],'history_blob_member':mapping['history_blob_member'],
                    'asm_body_index':graph['body_index'],'stored_identifier':binding['stored_handle'],
                    'counts_match_actual_getters':True,'bounds_match_actual_getters_after_keyed_join':True},'feature_dictionaries_unchanged':True})
            contexts[sample['case']]=(data,records,features,member,members,stream,row)
    assert thin_count==6 and bindings==8 and closed==5 and open_count==1
    data,records,features,member,members,stream,row=contexts['closed_side1'];feature,=[f for f in features if f['kind']=='Extrude'];primary={r.object_id:r for r in records if r.is_primary};record=primary[feature['object_id']]
    metadata=row['thin_metadata'];one=metadata['side_one']
    def reject(label,altered_data,source_context=None,altered_features=None):
        d,rs,fs,_,_,_,expected=source_context if source_context is not None else contexts['closed_side1']
        result=decode_thin_extrudes(altered_data,rs,altered_features if altered_features is not None else fs)
        assert not result['decoded'] and len(result['unresolved'])==1
        report['malformed_guards'].append({'case':label,'rejected':True,'reason':result['unresolved'][0]['reason']})
    bad=bytearray(data);bad[record.body+metadata['stored_flag_offset']]=2;reject('Native thin flag is not boolean',bytes(bad))
    bad=bytearray(data);struct.pack_into('<I',bad,record.body+one['location_code_offset'],99);reject('Unknown wall location enum',bytes(bad))
    along=next(p for p in feature['parameters'] if p['role']=='AlongDistance')
    bad=bytearray(data);struct.pack_into('<Q',bad,record.body+one['binding_reference_offset']+1,along['binding_object_id']);reject('Thickness field points to valid binding with wrong role',bytes(bad))
    binding=primary[one['binding_object_id']]
    bad=bytearray(data);struct.pack_into('<Q',bad,binding.end-10,feature['object_id']+1);reject('Wall binding footer owner is not feature',bytes(bad))
    bad=bytearray(data);struct.pack_into('<d',bad,binding.body+21,.19);reject('Wall binding cached value differs from numeric parameter',bytes(bad))
    parameter=next(p for p in feature['parameters'] if p['binding_object_id']==one['binding_object_id'])
    bad=bytearray(data);struct.pack_into('<d',bad,parameter['value_offset'],0.);struct.pack_into('<d',bad,binding.body+21,0.)
    modified=copy.deepcopy(features)
    for f in modified:
        if f['object_id']==feature['object_id']:
            next(p for p in f['parameters'] if p['binding_object_id']==one['binding_object_id'])['raw_float64']=0.
    reject('Zero thickness rejected with matching parameter/binding copies',bytes(bad),altered_features=modified)
    two_context=contexts['closed_two_sides_mixed'];d,rs,fs,_,_,_,two_row=two_context
    rec=next(r for r in rs if r.is_primary and r.object_id==two_row['feature_object_id']);bad=bytearray(d)
    bad[rec.body+two_row['thin_metadata']['side_two']['binding_reference_offset']]=0
    reject('Active second side missing thickness binding',bytes(bad),source_context=two_context)
    proxy=primary[row['profile_proxy_object_id']];bad=bytearray(data);struct.pack_into('<Q',bad,proxy.end-10,feature['object_id']+1);reject('Profile proxy owner no longer feature',bytes(bad))
    for relative in ('scaleshellinputs-97ef1cfd19e4/scale_vertex.f3d','moretools-88a2cd6cad0b/Thicken.f3d'):
        ms=read_members(ROOT/relative,zstd);s=decode_basics(ROOT/relative,zstd)['streams'][0];m=s['member'];d=ms[m];rs,_=design_records(d,ms[m.replace('BulkStream.dat','MetaStream.dat')]);before=copy.deepcopy(s['features'])
        result=decode_thin_extrudes(d,rs,s['features']);assert result['decoded']==result['unresolved']==[] and s['features']==before
        report['legacy_controls'].append({'file':relative,'no_new_sidecars_or_diagnostics':True,'feature_dictionaries_unchanged':True})
    report['summary']={'actual_successful_exports':7,'decoded_thin_features':thin_count,'closed_profiles':closed,'open_line_profiles':open_count,
        'actual_owned_wall_parameter_matches':getter_checks,'keyed_result_BODY_geometry_controls':body_checks,
        'ordinary_actualFalse_controls':1,'common_callback_default_output_exact_controls':compatibility,
        'malformed_guards':len(report['malformed_guards']),'legacy_ordinary_surface_controls':len(report['legacy_controls']),
        'initial_open_capture_failure_retained':True,'new_live_API_calls':0}
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library');parser.add_argument('--output',default='thin-extrude-decoding.json');args=parser.parse_args()
    zstd=args.zstd_library or next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    result=validate(zstd);Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))
