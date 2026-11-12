"""Focused checks of directed Revolve source axes against actual API captures."""

import argparse
import copy
import json
import math
from pathlib import Path

from decode_basics import decode_basics
from decode_revolve_axes import decode_revolve_axes
from decode_sketch import same
from fusion_archive import read_members
from fusion_metadata import design_records


def validate(root, zstd_library):
    samples = []
    for folder in ('revolveaxes-a83b542c4a07', 'revolveaxes-14700158dba9'):
        directory = root/folder
        truth = json.loads((directory/'ground_truth.json').read_text())
        assert (directory/'complete.txt').exists() and not truth['errors']
        for sample in truth['samples']:
            archive = directory/sample['file']
            stream = decode_basics(archive,zstd_library)['streams'][0]
            feature = next(f for f in stream['features'] if f['kind']=='Revolve')
            assert not stream['revolve_axes']['unresolved']
            axis, actual = feature['revolve']['axis'], sample['actual_axis']
            entity, controls = axis['entity'], sample['settings']
            start,end = actual['start_cm'],actual['end_cm']
            delta = [b-a for a,b in zip(start,end)]
            length = math.sqrt(sum(x*x for x in delta))
            checks = {'source_type': actual['entity_type'].endswith('::'+entity['kind']),
                      'source_start':same(entity['start_cm'],start), 'source_end':same(entity['end_cm'],end),
                      'origin':same(entity['origin_cm'],start),
                      'derived_unit_direction':same(entity['direction'],[x/length for x in delta]),
                      'operation':feature['operation']['kind']=='NewBody' and controls['operation']==3,
                      'solid':feature['is_solid']==controls['is_solid'],
                      'project_axis':feature['is_project_axis']==controls['is_project_axis'],
                      'angle':feature['revolve']['angle_radians']==controls['angle_radians']}
            if entity['kind']=='SketchLine':
                checks['source_sketch_name']=entity['sketch_name']==actual['sketch_name']
                sketch_baseline = archive,stream,feature,axis
            else:
                properties = {b['object_id']:b for b in stream['body_properties']['bodies']}
                checks['historical_body_name']=properties[entity['native_body_object_id']]['name']==actual['body_name']
                checks['api_line_geometry_type']=actual['geometry_type']=='adsk::core::Line3D'
                edge_baseline = archive,stream,feature,axis
            assert all(checks.values()),(archive,checks)
            samples.append({'file':str(archive.relative_to(root)),'checks':checks,'decoded_axis':axis,'actual_api_capture':sample})
    negative = []
    for label,baseline,target,relative,replacement in (
        ('Foreign sketch-axis proxy owner',sketch_baseline,'selection_object_id',-10,(0).to_bytes(8,'little')),
        ('Missing selected source tag',sketch_baseline,'terminal_object_id',18,(999999).to_bytes(8,'little')),
        ('Degenerate cached edge-axis direction',edge_baseline,'context_record_object_id',26,bytes(24)),
    ):
        archive,stream,feature,axis = baseline
        members=read_members(archive,zstd_library);data=members[stream['member']]
        records,_=design_records(data,members[stream['member'].replace('BulkStream.dat','MetaStream.dat')])
        record=next(r for r in records if r.is_primary and r.object_id==axis[target])
        offset=record.body+relative if relative>=0 else record.end+relative
        changed=bytearray(data);changed[offset:offset+len(replacement)]=replacement
        features=copy.deepcopy(stream['features'])
        next(f for f in features if f['object_id']==feature['object_id'])['revolve']['axis_selection']='Undecoded'
        summary=decode_revolve_axes(bytes(changed),records,features)
        assert not summary['decoded'] and summary['unresolved'],label
        negative.append({'check':label,'passed':True,'reason':summary['unresolved'][0]['reason']})
    return {'samples':samples,'negative_checks':negative,
            'summary':{'new_archives':len(samples),'api_comparisons':sum(len(s['checks']) for s in samples),'negative_checks':len(negative),'all_passed':True},
            'limitations':['Source line geometry is decoded; effective angular orientation and solid regeneration are not tested.',
                           'BRep source axis comes from explicitly referenced typed cache; persistent recipe-to-ASM edge identity remains unresolved.',
                           'Captured BRep axes are root-component X/Y examples. Other frames and projected selected-axis transforms are unverified.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zstd-library',required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parent
    report=validate(root,args.zstd_library)
    (root/'revolve-selected-axis-decoding.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['summary']))
