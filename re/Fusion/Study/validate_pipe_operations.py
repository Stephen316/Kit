"""Actual Pipe Boolean settings, owned target routes and focused guards."""
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
from decode_pipe import decode_pipe
from decode_pipe_operations import decode_pipe_operations
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT=Path(__file__).resolve().parent
DIRECTORY='pipeoperations-6afc81788dbf'


def validate(zstd):
    directory=ROOT/DIRECTORY;truth=json.loads((directory/'ground_truth.json').read_text())
    assert truth['status']=='complete' and not truth['errors'] and len(truth['samples'])==3
    assert hashlib.sha256((directory/'executed-generator-source.txt').read_bytes()).hexdigest()==truth['executed_generator_sha256']
    report={'scope':'Three actual owned single-root-target straight SketchLine full-distance circular-solid Pipe Join/Cut/Intersect exports; common controls parsed by shared decode_pipe',
        'interface':'decode_pipe_operations(data,records,features)->decoded/unresolved/scope; rows feature_object_id/tool_settings/target_body/layout and participant applicability. No assembly input required.',
        'integration':'Run immediately after decode_tools before old unresolved Pipe provenance fallback; apply only successful settings/explicit target attachments and clear only same-feature old unsupported-prefix error. Other paths/settings remain unchanged.',
        'capture_provenance':{'ground_truth_file':DIRECTORY+'/ground_truth.json','ground_truth_sha256':hashlib.sha256((directory/'ground_truth.json').read_bytes()).hexdigest(),
            'executed_generator_sha256':truth['executed_generator_sha256'],'executed_source_snapshot':DIRECTORY+'/executed-generator-source.txt'},
        'schema':{'prefix':'Observed00 00 empty attribute header; hollow@2, operationuint32@3; canonical common offsets shift bycursor2-minus-oldcursor6=-4 without changing source bytes',
            'operation_codes':{'1':'Join(API0)','2':'Cut(API1)','3':'Intersect(API2)'},
            'target_list':'After common section: zero16, countu32=1, owned proxyref; counted proxy list selects owned Body descriptor→typed anchor→explicit native BODY',
            'common_parser':'Shared decode_pipe.layout_resolver supplies delta/operation; bindings/path/section/fractions remain existing code'},
        'samples':[],'malformed_guards':[],'legacy_controls':[],
        'limitations':['Native target-body identity is historical provenance and does not establish general current/final visibility or persistent topology.',
            'Join has an explicit native body-selection route but API participantBodies is documented only for Cut/Intersect; Join participant setter/getter were deliberately not called.',
            'Only observed solid circular full-distance single-Line root-context family supported; composite/BRep/occurrence/hollow/partial Boolean variants remain unsupported.',
            'API volumes and keyed stored topology counts corroborate these fixtures after explicit identity qualification; neither geometry nor names choose candidate identity.',
            'No Boolean regeneration or native writing implemented. Existing NewBody and extended-path default outputs remain unchanged.']}
    contexts={};api_params=body_checks=0
    for sample in truth['samples']:
        assert sample['status']=='exported' and not sample['getter_errors'] and sample['close_owned_document_result'] is True
        filename=DIRECTORY+'/'+sample['file'];members=read_members(ROOT/filename,zstd);stream=decode_basics(ROOT/filename,zstd)['streams'][0];member=stream['member'];data=members[member]
        records,_=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')]);features=stream['features'];before=copy.deepcopy(features)
        summary=decode_pipe_operations(data,records,features);assert not summary['unresolved'] and before==features;row,=summary['decoded'];settings=row['tool_settings']
        feature,=[f for f in features if f['object_id']==row['feature_object_id']];api=sample['settings'];target=row['target_body']
        assert settings['operation'].lower()==sample['case'] and row['stored_operation_code']==api['operation']+1
        assert settings['stored_section_type_code']==api['section_type']==0 and settings['is_hollow']==api['is_hollow'] is False
        for field,key in (('section_size_cm','section_size'),('stored_section_thickness_cm','section_thickness'),('distance_one_fraction','distance_one')):
            actual=api[key];assert math.isclose(settings[field],actual['raw_value'],abs_tol=1e-14)
            native,=[p for p in feature['parameters'] if p['binding_object_id']==settings['parameter_bindings'][actual['role']]]
            assert native['parameter_name']==actual['name'] and native['role']==actual['role'] and actual['created_by']==feature['name'];api_params+=1
        assert api['distance_two']=={'getter_returned_null':True} and settings['distance_two_fraction'] is None
        path=settings['path'];assert path['kind']=='Line' and not path['is_closed'] and api['path']['count']==1 and api['path']['is_closed'] is False
        sketch,=[f for f in features if f['kind']=='Sketch' and f['sketch_object_id']==path['sketch_object_id']]
        curve,=[g for g in sketch['geometry'] if g['object_id']==path['curve_object_id']]
        getter=api['path']['members'][0]['entity'];assert getter['sketch_name']==sketch['name'] and curve['entity_tag']==path['curve_entity_tag']
        assert curve['start_cm']==getter['start_world_cm']==[-1.,0.,0.] and curve['end_cm']==getter['end_world_cm']==[4.,0.,0.]
        assert target['stored_name']==sample['source_before_pipe']['target_body']['name']=='PipeOperationTarget'
        if sample['case'] in ('cut','intersect'):
            participant,=api['participant_bodies'];assert participant['name']==target['stored_name'] and participant['volume_cm3']==12.
            assert row['API_participant_applicability'] is True
        else:assert row['API_participant_applicability'] is False and api['participant_bodies']['applicable'] is False
        actual_body,=sample['result_bodies'];assert len(sample['root_bodies_after'])==1 and sample['health_state']==0 and not sample['warning']
        area=math.pi*(settings['section_size_cm']/2)**2
        expected_volume={'join':12+2*area,'cut':12-3*area,'intersect':3*area}[sample['case']]
        assert math.isclose(actual_body['volume_cm3'],expected_volume,rel_tol=0,abs_tol=1e-9)
        pairs=[(m,b) for m in stream['body_asm_identifiers']['decoded'] for b in m['bindings'] if b['native_body_object_id']==target['native_body_object_id']]
        mapping,binding=pairs[0];assert len(pairs)==1
        graph,=[g for g in decode_topology(inspect_asm(members[mapping['history_blob_member']]))['body_graphs'] if g['body_index']==binding['asm_body_index']]
        for kind in ('face','edge','vertex'):assert graph['counts'][kind]==actual_body[kind+'_count']
        body_checks+=1
        record,=[r for r in records if r.is_primary and r.object_id==feature['object_id']];body=data[record.body:record.end]
        layout=row['layout'];assert bytes.fromhex(layout['target_list_hex'])==body[layout['target_list_start_offset']:layout['target_list_start_offset']+31]
        try:decode_pipe(data,records,body,feature,features)
        except ValueError as error:assert str(error)=='Unsupported observed Pipe prefix/operation'
        else:raise AssertionError('Old default unexpectedly accepted new operation prefix')
        report['samples'].append({'file':filename,'expected_summary':summary,'expected_settings':settings,'actual_API_operation':api['operation'],
            'actual_API_participant_bodies':api['participant_bodies'],'actual_result_body':actual_body,
            'analytic_volume_corroboration_cm3':expected_volume,'typed_keyed_cache_topology_control':{'native_body_object_id':target['native_body_object_id'],
                'stored_handle':binding['stored_handle'],'history_blob_member':mapping['history_blob_member'],'asm_body_index':binding['asm_body_index'],
                'stored_counts':graph['counts'],'counts_match_actual_getters_after_keyed_join':True,'scope':'Stored body cache at explicit native identity; no general lifecycle claim'},
            'exact_target_list_byte_replay':True,'original_default_prefix_rejection_retained':True,'owned_document_close_result':True})
        contexts[sample['case']]=(data,records,features,feature,record,row)
    data,records,features,feature,record,row=contexts['cut'];offset=record.body
    def reject(label,bad,modified=None):
        result=decode_pipe_operations(bytes(bad),records,modified if modified is not None else features)
        assert not result['decoded'] and len(result['unresolved'])==1
        report['malformed_guards'].append({'case':label,'reason':result['unresolved'][0]['reason']})
    bad=bytearray(data);struct.pack_into('<I',bad,offset+3,99);reject('Unknown operation code',bad)
    bad=bytearray(data);bad[offset+2]=2;reject('Hollow field not boolean',bad)
    bad=bytearray(data);struct.pack_into('<I',bad,offset+96,2);reject('Target count outside captured one-body list',bad)
    proxy,=[r for r in records if r.is_primary and r.object_id==row['target_body']['proxy_object_id']]
    bad=bytearray(data);struct.pack_into('<Q',bad,proxy.body+95,feature['object_id']+1);reject('Target proxy owner differs from feature',bad)
    descriptor,=[r for r in records if r.is_primary and r.object_id==row['target_body']['descriptor_object_id']]
    bad=bytearray(data);struct.pack_into('<Q',bad,descriptor.end-10,feature['object_id']+1);reject('Target descriptor owner differs from feature',bad)
    modified=copy.deepcopy(features);pipe=next(f for f in modified if f['kind']=='Pipe');next(p for p in pipe['parameters'] if p['role']=='SectionSize')['role']='AlongDistance';reject('Section binding has wrong role',data,modified)
    for relative in ('pipepaths-3d11bd427946/composite_circular.f3d','pipepaths-3d11bd427946/spline_circular.f3d','pipeedgecontrasts-5bd287323ae7/line_full.f3d'):
        members=read_members(ROOT/relative,zstd);stream=decode_basics(ROOT/relative,zstd)['streams'][0];data=members[stream['member']]
        records,_=design_records(data,members[stream['member'].replace('BulkStream.dat','MetaStream.dat')]);before=copy.deepcopy(stream['features']);summary=decode_pipe_operations(data,records,stream['features'])
        assert not summary['decoded'] and not summary['unresolved'] and stream['features']==before
        report['legacy_controls'].append({'file':relative,'no_new_summary_or_feature_mutation':True})
    report['summary']={'actual_exports':3,'Boolean_operations_decoded':3,'actual_API_parameter_role_name_value_matches':api_params,
        'explicit_native_target_body_routes':3,'explicit_API_participant_controls':2,'Join_inference_distinguished':1,
        'keyed_stored_topology_count_controls':body_checks,'analytic_actual_volume_controls':3,'target_list_byte_replays':3,
        'malformed_guards':len(report['malformed_guards']),'legacy_controls':3,'all_owned_documents_closed_true':True}
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',default=str(ROOT/'pipe-operation-decoding.json'));args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(zstd);Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))
