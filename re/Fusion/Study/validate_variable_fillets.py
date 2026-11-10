"""Focused saved API validation for counted variable-fillet midpoint lists."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_basics import decode_basics
from decode_edge_tools import decode_edge_tool
from decode_sketch import reference
from decode_variable_fillets import decode_variable_fillet, decode_variable_fillets
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT=Path(__file__).resolve().parent
DIRECTORY='variablefillets-a5080b076434'
SET_GUID='4A557CE2-375C-4F69-AA76-2403109F1493'


def validate(zstd):
    directory=ROOT/DIRECTORY;truth=json.loads((directory/'ground_truth.json').read_text())
    assert truth['status']=='complete' and not truth['errors'] and len(truth['samples'])==4
    source=directory/'executed-generator-source.txt'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==truth['executed_generator_sha256']
    report={'scope':'Four actual owned-document straight-edge fillets: endpoint-only control, quarter/three-quarter single midpoint contrast, two intermediate points. No whole-corpus sweep.',
        'interface':'decode_variable_fillets(data,records,features)->decoded/unresolved/scope (intermediate-only); decode_variable_fillet(data,records,body,feature) reuses shared controls; decode_variable_radius_payload(chunk,value) is shared-reader callback',
        'integration':'Add intermediate-only summary and replace same-feature tool_settings on successful rows; keep existing input topology warning. Default shared decoder and endpoint-only output are unchanged.',
        'capture_provenance':{'file':DIRECTORY+'/ground_truth.json','sha256':hashlib.sha256((directory/'ground_truth.json').read_bytes()).hexdigest(),
            'executed_generator_sha256':truth['executed_generator_sha256'],'exact_executed_source_snapshot':DIRECTORY+'/executed-generator-source.txt'},
        'schema':{'mid_position_count_offset':28,'mid_position_refs_offset':32,'list_rule':'u32 position count, counted11byte MidParams refs, zero4, u32radius count=count+2, StartRadius/EndRadius/MidRadius refs in native/API order, zero9, setIndexu32, TangencyWeightref, zero4',
            'extent_rule':'Edge-set body length90+22*midpointcount; positive bounded count; exact references and all separators/trailer checked',
            'position_units':'Actual API unitless MidParams fraction; no automatic reversal or coordinate inference',
            'parameter_units':'Start/End/MidRadius raw internal cm; actual display unit mm retained in API evidence'},
        'samples':[],'malformed_guards':[],'legacy_controls':[],
        'limitations':['New branch observed only continuity1, straight single-edge input and rolling ball; numeric values are decoded bindings, not fixture constants.',
            'Stored list order is actual API getter order. The two-point setter order is reversed by Fusion; no ascending sort/request-order assumption.',
            'Existing owned selection proxy remains validated by shared reader; exact selected ASM edge identity and traversal orientation remain unresolved.',
            'No fillet regeneration, midpointXYZ inference, nonlinear arc-length mapping or radius interpolation law is claimed.']}
    contexts={};parameter_checks=0;source_checks=0;replays=0
    for sample in truth['samples']:
        assert sample['status']=='exported' and not sample['getter_errors'] and sample['close_owned_document_result'] is True
        path=directory/sample['file'];members=read_members(path,zstd);model=decode_basics(path,zstd);stream=model['streams'][0]
        name=stream['member'];data=members[name];records,_=design_records(data,members[name.replace('BulkStream.dat','MetaStream.dat')])
        feature,=[f for f in stream['features'] if f['kind']=='Fillet'];record,=[r for r in records if r.is_primary and r.object_id==feature['object_id']]
        body=data[record.body:record.end];before=copy.deepcopy(feature);settings=decode_variable_fillet(data,records,body,feature)
        summary=decode_variable_fillets(data,records,stream['features']);assert not summary['unresolved'] and feature==before
        actual=sample['settings'];edge,=settings['edge_sets'];api,=actual['edge_sets']
        assert settings['rolling_ball_corner']==actual['rolling_ball_corner'] and edge['tangent_chain']==api['is_tangent_chain'] and edge['continuity']==api['continuity']
        assert sample['health_state']==0 and not sample['warning']
        pairs=[(edge['startRadius'],api['start_radius']),(edge['endRadius'],api['end_radius']),(edge['tangencyWeight'],api['tangency_weight'])]
        if api['mid_radius_count']:
            assert len(summary['decoded'])==1 and summary['decoded'][0]['tool_settings']==settings
            assert len(edge['midRadii'])==api['mid_radius_count']==len(edge['midPositions'])==api['mid_position_count']
            pairs+=list(zip(edge['midRadii'],api['mid_radii']))+list(zip(edge['midPositions'],api['mid_positions']))
        else:
            assert not summary['decoded'] and settings==decode_edge_tool(data,records,body,feature)
        for native,getter in pairs:
            assert native['role']==getter['role'] and native['name']==getter['name'] and math.isclose(native['value'],getter['raw_value'],rel_tol=0,abs_tol=1e-14)
            assert getter['created_by']==feature['name'];parameter_checks+=1
        source_before=sample['selected_source_edge_before_fillet'];source_after,=api['actual_source_edges']
        for key in ('geometry_type','start_vertex_cm','end_vertex_cm','trimmed_parameter_extents','trimmed_evaluator_samples','is_param_reversed'):
            assert source_before[key]==source_after[key]
        assert source_before['geometry_type']=='adsk::core::Line3D';source_checks+=1
        definition,=[r for r in records if r.is_primary and r.object_id==edge['definition_record_object_id'] and r.class_guid==SET_GUID]
        chunk=data[definition.body:definition.end];count=api['mid_radius_count'];selection=edge['selection_record_object_id']
        ref=lambda identity:b'\x01'+struct.pack('<Q',identity)+bytes(2)
        replay=bytes(7)+bytes([int(edge['tangent_chain'])])+bytes(2)+ref(selection)+bytes(7)+struct.pack('<I',count)
        replay+=b''.join(ref(p['binding_object_id']) for p in edge.get('midPositions',[]))+bytes(4)+struct.pack('<I',count+2)
        replay+=b''.join(ref(p['binding_object_id']) for p in [edge['startRadius'],edge['endRadius']]+edge.get('midRadii',[]))+bytes(9)+struct.pack('<I',0)+ref(edge['tangencyWeight']['binding_object_id'])+bytes(4)
        assert replay==chunk;replays+=1
        row={'file':DIRECTORY+'/'+sample['file'],'expected_summary':summary,'expected_settings':settings,'edge_set_definition_object_id':definition.object_id,
            'native_body_hex':chunk.hex(),'exact_payload_replay':True,'actual_mid_radius_values':[p['raw_value'] for p in api['mid_radii']],
            'actual_mid_position_values':[p['raw_value'] for p in api['mid_positions']],
            'source_getters_before_consumption_equal_rolled_getters':True,'native_to_ASM_source_orientation':'unresolved',
            'actual_API_health_state':sample['health_state'],'close_owned_document_result':sample['close_owned_document_result']}
        report['samples'].append(row);contexts[sample['case']]=(data,records,stream['features'],feature,definition)
    two=next(s for s in truth['samples'] if s['case']=='two_intermediates')
    assert two['requested']['positions']==[.25,.75]
    assert [p['raw_value'] for p in two['settings']['edge_sets'][0]['mid_positions']]==[.75,.25]
    report['setter_order_counterexample']={'case':'two_intermediates','requested_positions':[.25,.75],'actual_getter_positions':[.75,.25],
        'requested_radii_cm':[.18,.24],'actual_getter_radii_cm':[.24,.18000000000000002],'native_lists_match_actual_getter_order':True}
    data,records,features,feature,definition=contexts['one_quarter'];offset=definition.body
    def reject(label,bad_data=None,bad_features=None):
        result=decode_variable_fillets(bytes(bad_data) if bad_data is not None else data,records,bad_features if bad_features is not None else features)
        assert not result['decoded'] and len(result['unresolved'])==1
        report['malformed_guards'].append({'case':label,'reason':result['unresolved'][0]['reason']})
    bad=bytearray(data);struct.pack_into('<I',bad,offset+28,2);reject('Position count exceeds exact payload extent',bad)
    bad=bytearray(data);struct.pack_into('<I',bad,offset+47,2);reject('Radius count disagrees with midpoint count',bad)
    bad=bytearray(data);bad[offset+43]=1;reject('Nonzero counted-list separator',bad)
    bad=bytearray(data);bad[offset+32:offset+43]=bad[offset+73:offset+84];reject('Position reference repeats radius binding',bad)
    bad=bytearray(data);bad[offset+93]=1;reject('Set index disagrees with feature order',bad)
    proxy_id=reference(data[offset:definition.end],10);proxy,=[r for r in records if r.is_primary and r.object_id==proxy_id]
    bad=bytearray(data);struct.pack_into('<Q',bad,proxy.body+95,feature['object_id']+1);reject('Selection proxy owner disagrees with feature',bad)
    modified=copy.deepcopy(features);target=next(f for f in modified if f['kind']=='Fillet');next(p for p in target['parameters'] if p['role']=='MidParams')['raw_float64']=0.;reject('Midpoint fraction at endpoint rejected',bad_features=modified)
    modified=copy.deepcopy(features);target=next(f for f in modified if f['kind']=='Fillet');next(p for p in target['parameters'] if p['role']=='MidRadius')['role']='StartRadius';reject('Correct typed binding with wrong parameter role',bad_features=modified)
    for filename in ('fillet_constant.f3d','fillet_variable.f3d','fillet_chord.f3d'):
        path=ROOT/'edgemodes-87edbf67527b'/filename;members=read_members(path,zstd);stream=decode_basics(path,zstd)['streams'][0];data=members[stream['member']]
        records,_=design_records(data,members[stream['member'].replace('BulkStream.dat','MetaStream.dat')]);feature,=[f for f in stream['features'] if f['kind']=='Fillet'];record,=[r for r in records if r.is_primary and r.object_id==feature['object_id']]
        assert decode_variable_fillet(data,records,data[record.body:record.end],feature)==decode_edge_tool(data,records,data[record.body:record.end],feature)
        assert not decode_variable_fillets(data,records,stream['features'])['decoded']
        report['legacy_controls'].append({'file':'edgemodes-87edbf67527b/'+filename,'shared_default_dictionary_exact':True,'no_new_summary':True})
    report['summary']={'actual_exports':4,'intermediate_features':3,'endpoint_control':1,'actual_parameter_getter_matches':parameter_checks,
        'actual_midpoint_pairs':4,'exact_edge_set_payload_replays':replays,'before_after_source_getter_controls':source_checks,
        'malformed_guards':len(report['malformed_guards']),'legacy_default_controls':3,'all_owned_documents_closed_true':True}
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',default=str(ROOT/'variable-fillet-decoding.json'));args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd);Path(args.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],indent=2))


if __name__=='__main__':main()
