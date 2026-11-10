"""Focused qualified profile/cache naming provenance and namespace counterexamples."""
import argparse
import copy
import json
import math
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_basics import decode_basics
from decode_brep import decode_topology
from decode_profile_cache_correspondence import decode_profile_cache_correspondence
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT=Path(__file__).resolve().parent
FILES=('loftbrepends-e07e3859ed20/edge_both_tangent.f3d',
       'loftbrepends-e07e3859ed20/edge_start_free.f3d',
       'pipeedgecontrasts-5bd287323ae7/circle_full.f3d',
       'scaleshellinputs-97ef1cfd19e4/scale_vertex.f3d')


def validate(zstd):
    report={'scope':'Four saved NewBody Extrude/profile fixtures; explicit native profile/Sketch/entity and mapped BODY routes qualify multiple COEDGE text correspondences. No global numeric identity conversion.',
        'interface':'decode_profile_cache_correspondence(data,records,features,member,members,body_identifier_summary)',
        'integration':'Separate profile_cache_correspondence decoded/unresolved summary after native profiles and body identifiers; attach rows by source_feature_object_id/feature_object_id. Preserve old settings and warnings.',
        'samples':[],'API_context_checks':[],'counterexamples':[],'guards':[],'unqualified_controls':[],
        'limitations':['Only observed single-source-BODY NewBody Extrude, owned Line/Circle profile curve sets and COEDGE literal suffix0 0 0 1 1 are qualified.',
            'First decimal field comparison is only within the independently qualified source profile/BODY route; it is not a native object ID or ASM record index.',
            'All six fields remain original strings, and all matching COEDGE candidates survive; no unique selected/coedge direction/trim interpretation is introduced.',
            'Correspondence is naming provenance. Scale modifies the cache geometry while source profile tags survive; equality of original sketch and current cached geometry is not claimed.',
            'Unbound parallel .smb data has other EDGE/VERTEX namespaces; no order/name/coordinate-based association to mapped .smbh roots is made.',
            'API radii and selected-edge checks follow the independently established identity route, and do not choose the profile or cached candidate.',
            'No live Fusion, solver, world placement, lifecycle classification or native writer is performed.']}
    contexts=[];curves=coedges=circles=length_mismatches=0
    for relative in FILES:
        ms=read_members(ROOT/relative,zstd);model=decode_basics(ROOT/relative,zstd);s=model['streams'][0];m=s['member'];d=ms[m]
        rs,_=design_records(d,ms[m.replace('BulkStream.dat','MetaStream.dat')]);before=copy.deepcopy(s['features'])
        result=decode_profile_cache_correspondence(d,rs,s['features'],m,ms,s['body_asm_identifiers'])
        assert not result['unresolved'] and result['decoded'] and s['features']==before
        primary={r.object_id:r for r in rs if r.is_primary}
        props={b['object_id']:b for b in s['body_properties']['bodies']}
        native={g['object_id']:g for f in s['features'] if f['kind']=='Sketch' for g in f['geometry']}
        truth=json.loads((ROOT/Path(relative).parent/'ground_truth.json').read_text());api=next(x for x in truth['samples'] if x['file']==Path(relative).name)
        if relative.startswith('loftbrepends'):
            api_sources=[segment['entity'] for path in api['source_entities_before_loft'] if path['entity_type']=='adsk::fusion::Path' for segment in path['segments']]
        elif 'source_before_pipe' in api: api_sources=[api['source_before_pipe']]
        else: api_sources=[]
        for row in result['decoded']:
            parsed=inspect_asm(ms[row['history_blob_member']]);top=decode_topology(parsed);nodes={n['index']:n for n in top['nodes']}
            for source in row['source_curves']:
                curves+=1;coedges+=len(source['cached_coedge_candidates']);assert len(source['cached_coedge_candidates'])==2
                geometry=native[source['native_entity_object_id']]
                assert source['native_entity_tag'] != source['native_entity_object_id']
                for candidate in source['cached_coedge_candidates']:
                    assert candidate['stored_decimal_text_fields'][0]==str(source['native_entity_tag'])
                    assert candidate['attribute_record_index'] != source['native_entity_tag']
                    if source['native_entity_kind']=='Circle':
                        curve=nodes[candidate['curve_record_index']]
                        assert curve['kind']=='ellipse-curve' and math.isclose(curve['stored_axis_ratio'],1.)
                        assert math.isclose(curve['raw_major_radius'],geometry['radius_cm'],abs_tol=1e-10)
                if source['native_entity_kind']=='Circle':
                    name=props[row['native_body_object_id']]['name']
                    matching=[a for a in api_sources if a.get('body',{}).get('name',a.get('body_name'))==name]
                    assert len(matching)==1
                    actual=matching[0];radius=actual.get('radius_cm',actual.get('natural_geometry',{}).get('radius_cm'))
                    assert math.isclose(radius,geometry['radius_cm'],abs_tol=1e-10);circles+=1
                    report['API_context_checks'].append({'file':relative,'source_feature_object_id':row['source_feature_object_id'],
                        'native_body_object_id':row['native_body_object_id'],'actual_API_body_name':name,
                        'native_curve_object_id':source['native_entity_object_id'],'native_curve_tag':source['native_entity_tag'],
                        'actual_API_circle_radius_cm':radius,'both_qualified_cache_circle_radii_agree':True,
                        'scope':'Body/source route established before circle-radius context comparison; no candidate selected by geometry'})
                elif relative.startswith('scaleshellinputs'):
                    original_length=math.dist(geometry['start_cm'],geometry['end_cm'])
                    for candidate in source['cached_coedge_candidates']:
                        edge=nodes[candidate['edge_record_index']]
                        points=[nodes[nodes[v]['point_index']]['raw_origin'] for v in candidate['endpoint_vertex_record_indices']]
                        cached_length=math.dist(*points)
                        if not math.isclose(original_length,cached_length,abs_tol=1e-10):
                            length_mismatches+=1
                            report['counterexamples'].append({'file':relative,'kind':'Modified cache is not original sketch geometry',
                                'native_entity_object_id':source['native_entity_object_id'],'native_curve_tag':source['native_entity_tag'],
                                'coedge_record_index':candidate['coedge_record_index'],'native_sketch_line_length_cm':original_length,
                                'cached_edge_length_raw':cached_length,'same_first_text_tag_survives':True})
            if relative.startswith('pipeedgecontrasts'):
                incidence,=s['pipe_recipe_incidence']['decoded'];selected=incidence['source_edge_record_index']
                source,=row['source_curves']
                assert selected not in {c['edge_record_index'] for c in source['cached_coedge_candidates']}
                curve=nodes[nodes[selected]['curve_index']];actual=api['source_before_pipe']['natural_geometry']
                assert math.dist(curve['raw_origin'],actual['center_cm'])<1e-10 and math.isclose(curve['raw_major_radius'],actual['radius_cm'],abs_tol=1e-10)
                report['API_context_checks'].append({'file':relative,'kind':'Independent named/API Pipe edge is outside source profile-boundary tags',
                    'native_source_body_object_id':incidence['native_source_body_object_id'],'selected_edge_record_index':selected,
                    'edge_is_in_qualified_profile_COEDGE_group':False,'API_center_and_radius_agree_for_independently_named_Pipe_edge':True,
                    'no_profile_correspondence_added_for_untagged_generated_edge':True})
        report['samples'].append({'file':relative,'expected_summary':result,'feature_dictionaries_unchanged':True})
        contexts.append((d,rs,s,m,ms,result))
    assert circles==4 and length_mismatches==8
    # Explicit unbound .smb VERTEX/EDGE text values are not native sketch tags.
    d,rs,s,m,ms,result=contexts[0]
    native_tags={g['entity_tag'] for f in s['features'] if f['kind']=='Sketch' for g in f['geometry']}
    for member,raw in ms.items():
        if not member.endswith('.smb'):continue
        parsed=inspect_asm(raw)
        for rec in parsed['records']:
            t=rec['tokens']
            if rec['section']!='geometry' or rec['name']!='ATTRIB_CUSTOM-attrib' or len(t)!=10 or t[5]['value']!='sketch_attrib_def':continue
            owner=parsed['records'][t[4]['value']]
            if owner['name'] in ('vertex','edge') and int(t[9]['value'].split()[0]) not in native_tags:
                report['counterexamples'].append({'file':FILES[0],'kind':'Unbound parallel asset first field outside native sketch-tag set',
                    'member':member,'owner_kind':owner['name'],'owner_record_index':owner['index'],
                    'uninterpreted_text':t[9]['value'],'all_decoded_native_sketch_entity_tags':sorted(native_tags)})
    primary={r.object_id:r for r in rs if r.is_primary};target=result['decoded'][0];feature_id=target['source_feature_object_id']
    def reject(label, data=None, members=None):
        actual=decode_profile_cache_correspondence(data if data is not None else d,rs,s['features'],m,members if members is not None else ms,s['body_asm_identifiers'])
        assert not any(x['source_feature_object_id']==feature_id for x in actual['decoded'])
        reasons=[x['reason'] for x in actual['unresolved'] if x['source_feature_object_id']==feature_id];assert reasons
        report['guards'].append({'case':label,'rejected':True,'reason':reasons[0]})
    native_curve=primary[target['source_curves'][0]['native_entity_object_id']]
    native=d[native_curve.body:native_curve.end]
    # Typed attribute data is modified, leaving prior decoded geometry unchanged.
    # Locate the exact length-prefixed ASCII attribute value through a bounded table walk.
    from decode_sketch import ascii_string
    p=6
    for _ in range(struct.unpack_from('<I',native,2)[0]):
        name,p=ascii_string(native,p);kind,p=ascii_string(native,p)
        if name=='crv_primary_id':tag_offset=p;break
        p+=8
    bad=bytearray(d);struct.pack_into('<Q',bad,native_curve.body+tag_offset,999);reject('Native primary curve tag differs from serialized profile loop',data=bytes(bad))
    bad=bytearray(d);struct.pack_into('<Q',bad,native_curve.end-10,289);reject('Native curve owner changed to other actual Sketch',data=bytes(bad))
    anchor=primary[target['body_anchor_object_id']]
    other=result['decoded'][1]['native_body_object_id']
    bad=bytearray(d);struct.pack_into('<Q',bad,anchor.body+81,other);reject('Typed BODY anchor changed to other profile BODY',data=bytes(bad))
    blob_member=target['history_blob_member'];blob=ms[blob_member];parsed=inspect_asm(blob)
    attribute=parsed['records'][target['source_curves'][0]['cached_coedge_candidates'][0]['attribute_record_index']]
    token=attribute['tokens'][9]
    for label,replacement in [('COEDGE first field outside its complete owned profile tag set','105 0 0 0 1 1'),
                              ('Unobserved literal suffix rejected without flag interpretation','102 0 0 0 1 2')]:
        bad=bytearray(blob);raw=replacement.encode('ascii');assert len(raw)==len(token['value'])
        bad[token['offset']+2:token['offset']+2+len(raw)]=raw
        badmembers=dict(ms);badmembers[blob_member]=bytes(bad);reject(label,members=badmembers)
    descriptor=primary[target['profile_descriptor_object_id']]
    bad=bytearray(d);struct.pack_into('<Q',bad,descriptor.end-10,feature_id+1);reject('Profile descriptor no longer owned by source Extrude',data=bytes(bad))
    for relative in ['advanced-627f7fe095f4/advanced.f3d','analytic-86a12b291d0a/analytic.f3d']:
        members=read_members(ROOT/relative,zstd);stream=decode_basics(ROOT/relative,zstd)['streams'][0];member=stream['member'];data=members[member]
        records,_=design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
        actual=decode_profile_cache_correspondence(data,records,stream['features'],member,members,stream['body_asm_identifiers'])
        assert not actual['decoded']
        report['unqualified_controls'].append({'file':relative,'no_unbound_number_based_conversion':True,'expected_summary':actual})
    report['summary']={'saved_positive_files':len(FILES),'qualified_Extrude_BODY_groups':sum(len(r['expected_summary']['decoded']) for r in report['samples']),
        'native_profile_curves':curves,'retained_COEDGE_candidates':coedges,'distinct_cached_EDGE_groups':sum(len({c['edge_record_index'] for c in source['cached_coedge_candidates']}) for row in report['samples'] for item in row['expected_summary']['decoded'] for source in item['source_curves']),'circle_API_context_checks':circles,
        'independent_selected_Pipe_edge_API_negative_control':1,'modified_geometry_counterexamples':length_mismatches,
        'unbound_namespace_counterexamples':sum(x['kind'].startswith('Unbound') for x in report['counterexamples']),
        'malformed_guards':len(report['guards']),'unqualified_controls':len(report['unqualified_controls']),'new_live_API_calls':0}
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library');parser.add_argument('--output',default='profile-cache-correspondence-decoding.json');args=parser.parse_args()
    zstd=args.zstd_library or next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    result=validate(zstd);Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))
