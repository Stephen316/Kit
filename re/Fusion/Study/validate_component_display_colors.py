"""Controlled componentColor capture, bounded prefix replay and quantization limit."""
import argparse
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct

from decode_component_display_colors import decode_component_display_colors, COMPONENT_GUID
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT=Path(__file__).resolve().parent
SAME_DOC=tuple('parameteridentity-8fc83529b236/'+name+'.f3d' for name in
               ('01_literal','02_alpha_reference','03_bravo_reference','04_literal_return'))
COLOR_FILE='componentcolorcontrast-775cb30dfc1e/known_component_color.f3d'
CONTROL='assembly-acc48a9dc05d/assembly.f3d'


def validate(zstd):
    truth=json.loads((ROOT/'componentcolorcontrast-775cb30dfc1e/ground_truth.json').read_text())
    assert truth['status']=='exported' and not truth['errors'] and truth['close_owned_document_result'] is True
    assert hashlib.sha256((ROOT/truth['source_archive']).read_bytes()).hexdigest()==truth['source_sha256']
    assert hashlib.sha256((ROOT/COLOR_FILE).read_bytes()).hexdigest()==truth['sha256']
    report={'scope':'Four same-document parameter-expression exports preserve inherited COMPONENT color prefix; one actual owned-import color setter/getter contrast qualifies raw RGB float32 channels, with root/child structural controls',
        'interface':'decode_component_display_colors(data,records)->decoded/unresolved/scope; rows keyed component_object_id',
        'integration':'Add a separate component_display_colors stream summary or attach rows to matching assembly component object IDs. No existing parameter/modeling/geometry field changes required.',
        'grammar':{'class':'Metadata-validated inherited COMPONENT42054630-20A0-40E1-B969-CFE9E742F5C9 continuation with same-ID primaryFusion E03784ED-5E19-4E14-B9F2-3B07017018CD',
            'prefix':'Leading4 literalzero bytes;2 typed reciprocal references;4 float64=-1;7 typed reciprocal references;zero byte;4 typed reciprocal references;zero byte;uint32 literal;3 finite unit-interval float32 channels;8 observed literal opaque adjacent bytes.',
            'offset_scope':'Computed cursor after bounded prefix, not a global181-byte seek or pattern scan. All13 target classes and reciprocal owner references are checked.',
            'end_scope':'Only the observed prefix through color-adjacent framing is replayed; remaining component payload is opaque.'},
        'samples':[],'same_document_control':{},'actual_API_contrast':{},'quantization_counterexample':{},'guards':[],
        'limitations':['Only observed inherited COMPONENT prefix variant is admitted; different classes, sentinel quartets, reference grammar or adjacent framing remain unresolved.',
            'Production output contains rawfloat32 RGB channels and bytes only. It does not derive8-bit getter values or assert general rounding/truncation behavior.',
            'The8 adjacent bytes remain opaque; the invariant fourthfloat-looking1 is not promoted to alpha/opacity without a contrasting capture.',
            'Channel order is corroborated by one three-channel controlled setter and before/after getters, not a general color-space characterization.',
            'Component-color assignment is separate from material appearance and from whether Display Component Colors is enabled; neither material nor toggle state is decoded.',
            'Root/child controls establish matching typed prefix framing and literal storage, not independent actual color getter comparisons for every component.',
            'No live Fusion call, native writer, geometry regeneration or external display-setting change is performed by this validator.']}
    contexts={};channel_sets=[];component_count=references=0
    for filename in SAME_DOC+(COLOR_FILE,CONTROL):
        members=read_members(ROOT/filename,zstd)
        member=next(n for n in members if n.endswith('/FusionDesignSegmentType1/BulkStream.dat'))
        data=members[member];records,_=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
        before=copy.deepcopy(records);actual=decode_component_display_colors(data,records)
        assert records==before and not actual['unresolved'] and actual['decoded']
        for row in actual['decoded']:
            assert bytes.fromhex(row['framed_prefix_hex'])==data[row['framed_prefix_offset']:row['framed_prefix_end_offset']]
            assert bytes.fromhex(row['stored_rgb_float32_bytes_hex'])==data[row['color_offset']:row['color_offset']+12]
            assert len(row['prefix_references'])==13
            component_count+=1;references+=13
            assert not any(k in row for k in ('rgb8','opacity','alpha','color_space'))
        if filename in SAME_DOC:
            row,=actual['decoded'];assert row['component_object_id']==3
            channel_sets.append(row['stored_rgb_float32_bytes_hex'])
        report['samples'].append({'file':filename,'member':member,'expected_summary':actual,
            'all_prefixes_and_color_channels_replay_exactly':True,'input_records_unchanged':True,
            'proof_scope':'Actual root getter/setter contrast' if filename==COLOR_FILE else 'Saved same-document invariance' if filename in SAME_DOC else 'Root plus three child typed-prefix structural controls'})
        contexts[filename]=(data,records,actual)
    assert len(set(channel_sets))==1
    source=contexts[SAME_DOC[0]][2]['decoded'][0];changed=contexts[COLOR_FILE][2]['decoded'][0]
    assert len({contexts[f][2]['decoded'][0]['framed_prefix_hex'] for f in SAME_DOC})==1
    old_prefix=bytes.fromhex(source['framed_prefix_hex']);new_prefix=bytes.fromhex(changed['framed_prefix_hex'])
    differences=[i for i,(a,b) in enumerate(zip(old_prefix,new_prefix)) if a!=b]
    color_start=source['color_offset']-source['framed_prefix_offset']
    assert differences and all(color_start<=i<color_start+12 for i in differences)
    requested=truth['requested_color'];after=truth['actual_color_after'];before=truth['actual_color_before']
    expected=[struct.unpack('<f',struct.pack('<f',after[name]/255.))[0] for name in ('red','green','blue')]
    actual=[changed['stored_component_color_rgb_float32'][name] for name in ('red','green','blue')]
    assert actual==expected and all(requested[name]==after[name] for name in ('red','green','blue'))
    assert all(source['stored_component_color_rgb_float32'][name]!=changed['stored_component_color_rgb_float32'][name] for name in ('red','green','blue'))
    assert before['opacity']==after['opacity']==255
    report['same_document_control']={'files':list(SAME_DOC),'stored_RGB_bytes_identical':True,'entire_bounded_prefix_bytes_identical':True,
        'stored_rgb_float32_bytes_hex':channel_sets[0],
        'scope':'Raw invariance across actual same-document equal-value literal/alpha/bravo expression changes; color getters were not repeated for these4 exports'}
    report['actual_API_contrast']={'source_archive':truth['source_archive'],'controlled_export':COLOR_FILE,
        'actual_color_before':before,'actual_color_after':after,'requested_color':requested,
        'stored_before_float32':source['stored_component_color_rgb_float32'],'stored_after_float32':changed['stored_component_color_rgb_float32'],
        'changed_prefix_byte_offsets_from_raw_component_payload':differences,
        'all_prefix_changes_within_qualified_RGB_fields':True,'all_three_after_channels_equal_f32_actual_getter_divided_by255':True,
        'opaque_adjacent_bytes_unchanged':source['stored_color_adjacent_bytes_hex']==changed['stored_color_adjacent_bytes_hex'],
        'scope':'One controlled case-specific correspondence; not a general quantization/color-space/alpha rule'}
    scaled={name:source['stored_component_color_rgb_float32'][name]*255 for name in ('red','green','blue')}
    rounded={name:round(value) for name,value in scaled.items()}
    assert rounded['red']==181 and before['red']==180
    report['quantization_counterexample']={'source_archive':SAME_DOC[0],'stored_float32_times255':scaled,
        'naive_nearest_integer_RGB':rounded,'actual_API_before_RGB':{name:before[name] for name in ('red','green','blue')},
        'red_rounding_prediction_differs':True,'conclusion':'No general RGB8 rounding conversion is implemented; raw float32 channels preserved'}
    data,records,original=contexts[SAME_DOC[0]];row=original['decoded'][0]
    component=next(r for r in records if r.class_guid==COMPONENT_GUID and r.object_id==3)
    primary={r.object_id:r for r in records if r.is_primary}
    def reject(label,mutate=None,changed_records=None):
        bad=bytearray(data)
        if mutate:mutate(bad)
        result=decode_component_display_colors(bytes(bad),changed_records if changed_records is not None else records)
        assert not result['decoded'] and len(result['unresolved'])==1
        report['guards'].append({'case':label,'rejected':True,'reason':result['unresolved'][0]['reason']})
    reject('Inherited leading prefix changed',lambda b:b.__setitem__(component.payload_start,1))
    reject('Prefix reference points to valid wrong-class primary object',lambda b:struct.pack_into('<Q',b,component.body+1,3))
    referenced=primary[row['prefix_references'][0]['object_id']]
    reject('Referenced record no longer reciprocates component owner',lambda b:struct.pack_into('<Q',b,referenced.end-10,999))
    scalar_offset=component.body+2*11
    reject('Unobserved scalar quartet',lambda b:struct.pack_into('<d',b,scalar_offset,0.))
    separator=component.body+2*11+32+7*11
    reject('Reference-run separator changed while stored color bytes stay intact',lambda b:b.__setitem__(separator,1))
    reject('Nonfinite channel',lambda b:struct.pack_into('<f',b,row['color_offset'],float('nan')))
    reject('Adjacent invariant bytes cannot be silently treated as alpha',lambda b:b.__setitem__(row['color_offset']+12,1))
    altered=[replace(r,class_guid='00000000-0000-0000-0000-000000000000') if r.is_primary and r.object_id==3 else r for r in records]
    reject('Same-ID primary class does not qualify COMPONENT inheritance',changed_records=altered)
    report['summary']={'saved_archives':6,'qualified_component_prefixes':component_count,'typed_reciprocal_references':references,
        'same_document_exports_with_identical_RGB':4,'actual_controlled_setter_exports':1,'changed_channels_corroborated':3,
        'child_component_structural_controls':3,'RGB8_rounding_counterexamples':1,'malformed_guards':len(report['guards']),
        'derived_RGB8_or_alpha_values_exposed':False,'new_live_API_calls':0}
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library');parser.add_argument('--output',default='component-display-color-decoding.json');args=parser.parse_args()
    zstd=args.zstd_library or next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report=validate(zstd);Path(args.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],indent=2))
