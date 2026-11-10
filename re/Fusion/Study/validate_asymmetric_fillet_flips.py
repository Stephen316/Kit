"""Actual returned asymmetric flip, normalization contrasts and bounded guards."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_basics import decode_basics
from decode_edge_tools import decode_edge_tool
from decode_asymmetric_fillet_flips import decode_asymmetric_fillet_flips,decode_asymmetric_fillet
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT=Path(__file__).resolve().parent
DIRECTORY='asymmetricfilletflips-b09b81df3c08'


def validate(zstd):
    directory=ROOT/DIRECTORY;truth=json.loads((directory/'ground_truth.json').read_text())
    assert truth['status']=='complete' and not truth['errors'] and len(truth['samples'])==3
    assert hashlib.sha256((directory/'executed-generator-source.txt').read_bytes()).hexdigest()==truth['executed_generator_sha256']
    report={'scope':'Three actual owned-document straight-edge asymmetric fillets, unequal offsets false/true and swapped-offset false control; focused saved-file checks only',
        'interface':'decode_asymmetric_fillet_flips(data,records,features)->decoded/unresolved/scope; decode_asymmetric_fillet(data,records,body,feature) reuses shared decoder through asymmetric_radius_decoder callback',
        'integration':'Attach summary and same-feature tool_settings only on successful rows, retaining existing exact topology warnings; shared default behavior remains unchanged',
        'capture_provenance':{'file':DIRECTORY+'/ground_truth.json','sha256':hashlib.sha256((directory/'ground_truth.json').read_bytes()).hexdigest(),
            'executed_generator_sha256':truth['executed_generator_sha256'],'exact_executed_source_snapshot':DIRECTORY+'/executed-generator-source.txt'},
        'schema':{'definition_body_length':88,'mode_prefix_offsets2_through4_hex':'010000','flip_bool_offset':5,
            'common_flags':'byte6 continuity and byte7 tangent-chain remain shared; selection/offset/weight references and trailer remain existing parser structure',
            'offset_parameter_roles':['EdgeOffset1','EdgeOffset2'],'meaning':'Actual API isFlipped reverses application of two offsets; world-side/native-edge traversal mapping unknown'},
        'samples':[],'malformed_guards':[],'legacy_controls':[],
        'limitations':['Actual source getter geometry before consumption and under rollback corroborates the controlled source; it does not establish a serialized ASM edge identity.',
            'Flip meaning is the documented API offset reversal; no absolute world direction, selected face ordering, topology generation or radius interpolation law is claimed.',
            'Existing numeric parameter bindings/common fillet owner checks are reused. No setter request is promoted over actual feature getters.']}
    contexts={};checks=0
    for sample in truth['samples']:
        assert sample['status']=='exported' and not sample['getter_errors'] and sample['close_owned_document_result'] is True
        members=read_members(directory/sample['file'],zstd);stream=decode_basics(directory/sample['file'],zstd)['streams'][0]
        data=members[stream['member']];records,_=design_records(data,members[stream['member'].replace('BulkStream.dat','MetaStream.dat')])
        feature,=[f for f in stream['features'] if f['kind']=='Fillet'];before=copy.deepcopy(stream['features']);summary=decode_asymmetric_fillet_flips(data,records,stream['features'])
        assert not summary['unresolved'] and stream['features']==before;row,=summary['decoded'];settings=row['tool_settings'];edge,=settings['edge_sets'];api,=sample['settings']['edge_sets']
        assert edge['isFlipped']==api['is_flipped']==sample['actual_input']['is_flipped']==sample['requested']['is_flipped']
        assert settings['rolling_ball_corner']==sample['settings']['rolling_ball_corner'] is False
        assert edge['continuity']==api['continuity']==2 and sample['actual_input']['continuity']==1
        assert edge['tangent_chain']==api['is_tangent_chain'] is False
        for key,actual in (('offsetOne','offset_one'),('offsetTwo','offset_two'),('tangencyWeight','tangency_weight')):
            n,a=edge[key],api[actual];assert n['role']==a['role'] and n['name']==a['name'] and math.isclose(n['value'],a['raw_value'],rel_tol=0,abs_tol=1e-14)
            assert a['created_by']==feature['name'];checks+=1
        source=sample['selected_source_edge_before_fillet'];actual_source,=api['actual_source_edges']
        for key in ('geometry_type','start_vertex_cm','end_vertex_cm','trimmed_parameter_extents','trimmed_evaluator_samples','is_param_reversed'):
            assert source[key]==actual_source[key]
        assert sample['health_state']==0 and not sample['warning']
        definition,=[r for r in records if r.is_primary and r.object_id==edge['definition_record_object_id']]
        chunk=data[definition.body:definition.end];ref=lambda identity:b'\1'+struct.pack('<Q',identity)+bytes(2)
        replay=bytes(2)+b'\1\0\0'+bytes([int(edge['isFlipped']),int(edge['continuity']==2),int(edge['tangent_chain'])])+bytes(2)
        replay+=ref(edge['selection_record_object_id'])+bytes(1)+ref(edge['offsetOne']['binding_object_id'])+ref(edge['offsetTwo']['binding_object_id'])+bytes(25)+struct.pack('<I',0)+ref(edge['tangencyWeight']['binding_object_id'])+bytes(4)
        assert replay==chunk
        report['samples'].append({'file':DIRECTORY+'/'+sample['file'],'expected_summary':summary,'expected_settings':settings,'definition_body_hex':chunk.hex(),
            'exact_payload_replay':True,'source_before_rollback_getters_agree':True,'actual_API_isFlipped':api['is_flipped'],
            'normalization':{'requested_rolling_ball_corner':sample['requested']['rolling_ball_corner'],'actual_rolling_ball_corner':False,
                'input_continuity':sample['actual_input']['continuity'],'actual_continuity':api['continuity']},
            'actual_health_state':sample['health_state'],'owned_document_close_result':True})
        contexts[sample['case']]=(data,records,stream['features'],feature,definition,chunk)
    a=contexts['unequal_default_false'][-1];b=contexts['unequal_flipped_true'][-1];c=contexts['swapped_offsets_false'][-1]
    assert [i for i,(x,y) in enumerate(zip(a,b)) if x!=y]==[5] and a==c
    report['contrasts']={'same_offsets_false_vs_true_differing_native_byte_offsets':[5],
        'swapped_offsets_control_has_identical_definition_reference_bytes':True,
        'swapped_offsets_are_numeric_binding_values_not_flip_encoding':True,
        'actual_API_flip_sequence':[False,True,False],
        'actual_normalization':'All three input continuity1→actual2 and rollingBall requestTrue→actualFalse; decoded native values agree actual feature getters'}
    data,records,features,feature,definition,chunk=contexts['unequal_default_false'];offset=definition.body
    def reject(label,bad=None,modified=None):
        result=decode_asymmetric_fillet_flips(bytes(bad) if bad is not None else data,records,modified if modified is not None else features)
        assert not result['decoded'] and len(result['unresolved'])==1
        report['malformed_guards'].append({'case':label,'reason':result['unresolved'][0]['reason']})
    bad=bytearray(data);bad[offset+5]=2;reject('Flip byte is not boolean',bad)
    bad=bytearray(data);bad[offset+4]=1;reject('Unknown asymmetric mode prefix',bad)
    bad=bytearray(data);bad[offset+69]=1;reject('Edge set index disagrees with feature order',bad)
    bad=bytearray(data);bad[definition.end-1]=1;reject('Nonzero definition trailer',bad)
    selection=next(s for s in records if s.is_primary and s.object_id==int.from_bytes(chunk[11:19],'little'))
    bad=bytearray(data);struct.pack_into('<Q',bad,selection.body+95,feature['object_id']+1);reject('Selection proxy owner differs from feature',bad)
    altered=copy.deepcopy(features);target=next(f for f in altered if f['kind']=='Fillet');next(p for p in target['parameters'] if p['role']=='EdgeOffset1')['role']='EdgeOffset2';reject('Offset binding has wrong role',modified=altered)
    for filename in ('fillet_constant.f3d','fillet_variable.f3d','fillet_chord.f3d'):
        relative='edgemodes-87edbf67527b/'+filename;members=read_members(ROOT/relative,zstd);stream=decode_basics(ROOT/relative,zstd)['streams'][0];data=members[stream['member']]
        records,_=design_records(data,members[stream['member'].replace('BulkStream.dat','MetaStream.dat')]);feature,=[f for f in stream['features'] if f['kind']=='Fillet'];record,=[r for r in records if r.is_primary and r.object_id==feature['object_id']]
        assert decode_asymmetric_fillet(data,records,data[record.body:record.end],feature)==decode_edge_tool(data,records,data[record.body:record.end],feature)
        assert not decode_asymmetric_fillet_flips(data,records,stream['features'])['decoded']
        report['legacy_controls'].append({'file':relative,'default_dictionary_exact':True,'no_new_summary':True})
    report['summary']={'actual_exports':3,'decoded_flip_false':2,'decoded_flip_true':1,'actual_parameter_role_name_value_matches':checks,
        'exact_definition_replays':3,'source_getter_controls':3,'actual_normalization_controls':3,'malformed_guards':len(report['malformed_guards']),
        'legacy_default_controls':3,'all_owned_documents_closed_true':True}
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd');parser.add_argument('--output',default=str(ROOT/'asymmetric-fillet-flip-decoding.json'));args=parser.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd);Path(args.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],indent=2))


if __name__=='__main__':main()
