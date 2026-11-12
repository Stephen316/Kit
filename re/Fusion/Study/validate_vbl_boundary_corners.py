"""Eight saved VBL faces: typed corner cycles and strict ownership guards."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_asm_subtypes import decode_asm_subtypes
from decode_brep import decode_topology
from decode_vbl_components import decode_vbl_components
from decode_vbl_boundary_corners import decode_vbl_boundary_corners
from fusion_archive import read_members

ROOT=Path(__file__).resolve().parent
FILE='specialfillets-d50f7a4f04e0/rule_asymmetric.f3d'
CONTROLS=('specialfillets-d50f7a4f04e0/rule_all_both.f3d',
          'edgemodes-87edbf67527b/fillet_chord.f3d',
          'patchcontinuity-b9b0be85a281/brep_tangent.f3d')


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(zstd):
    checks=[];guards=[];samples=[];old_controls=[];saved=None
    def check(label,value,**evidence):
        if not value:raise AssertionError(label)
        checks.append(dict(check=label,**evidence))
    historical={s['member']:s['expected_summary'] for s in json.loads((ROOT/'vbl-component-decoding.json').read_text())['samples']}
    actual=next(s for s in json.loads((ROOT/FILE).parent.joinpath('ground_truth.json').read_text())['samples'] if s['file']==Path(FILE).name)
    total_faces=total_edges=total_corners=0
    for member,blob in read_members(ROOT/FILE,zstd).items():
        if not member.endswith(('.smb','.smbh')):continue
        parsed=inspect_asm(blob);catalog=decode_asm_subtypes(blob,parsed=parsed);topology=decode_topology(parsed,subtype_catalog=catalog)
        boundaries=decode_vbl_components(blob,parsed=parsed,subtype_catalog=catalog,topology=topology)
        before_parsed,before_catalog,before_topology,before_boundaries=map(copy.deepcopy,(parsed,catalog,topology,boundaries))
        decoded=decode_vbl_boundary_corners(blob,parsed=parsed,subtype_catalog=catalog,topology=topology,component_boundaries=boundaries)
        check(member+' direct and supplied views agree',decoded==decode_vbl_boundary_corners(blob))
        check(member+' complete old component dictionary exact',json.loads(json.dumps(boundaries))==historical[member])
        check(member+' no input structures mutated',(parsed,catalog,topology,boundaries)==(before_parsed,before_catalog,before_topology,before_boundaries))
        check(member+' only old VBL interior warnings retained',len(topology['unresolved'])==len(boundaries['decoded']) and all(r['reason']=='VBL component definitions decoded; standalone XYZ surface evaluator remains unsupported' for r in topology['unresolved']))
        check(member+' all admitted faces have corner proofs',len(decoded['decoded'])==len(boundaries['decoded']) and not decoded['unresolved'])
        nodes={n['index']:n for n in topology['nodes']};records={r['index']:r for r in parsed['records']};native_proofs=[]
        for row in decoded['decoded']:
            total_faces+=1;total_edges+=len(row['boundary_edges']);total_corners+=len(row['corners'])
            source=next(s for s in boundaries['decoded'] if s['surface_record_index']==row['surface_record_index'])
            check(member+' surface'+str(row['surface_record_index'])+' six native corner cycle',len(row['corners'])==len(row['boundary_edges'])==6 and len(row['ordered_vertex_cycle'])==7 and row['ordered_vertex_cycle'][0]==row['ordered_vertex_cycle'][-1] and len(set(row['ordered_vertex_cycle'][:-1]))==6)
            body=nodes[row['body_index']];face=nodes[row['face_index']];shell=nodes[face['shell_index']];lump=nodes[shell['lump_index']]
            check(member+' surface'+str(row['surface_record_index'])+' exact typed BODY ancestry',body['kind']=='body' and lump['body_index']==body['index'] and shell['lump_index']==lump['index'] and face['shell_index']==shell['index'] and nodes[row['loop_index']]['face_index']==face['index'] and face['surface_index']==row['surface_record_index'])
            for edge,corner,component in zip(row['boundary_edges'],row['corners'],source['components']):
                coedge=nodes[edge['coedge_index']];native_edge=nodes[edge['edge_index']]
                pair=[native_edge['start_vertex_index'],native_edge['end_vertex_index']]
                if coedge['is_reversed']:pair.reverse()
                check(member+' surface'+str(row['surface_record_index'])+' slot'+str(edge['component_slot'])+' literal traversal ID order',pair==[edge['entry']['vertex_index'],edge['exit']['vertex_index']] and coedge['is_reversed'] is edge['stored_coedge_reversal'] and edge['coedge_index']==component['coedge_index'] and edge['edge_index']==component['edge_index'])
                vertex=nodes[corner['vertex_index']];point=nodes[vertex['point_index']];point_record=records[point['index']];vertex_record=records[vertex['index']]
                check(member+' corner'+str(vertex['index'])+' explicit vertex/point field and source bytes',corner['vertex_index']==edge['entry']['vertex_index'] and corner['point_index']==vertex['point_index']==point['index'] and corner['raw_point']==point['raw_origin']==point_record['tokens'][3]['value'] and vertex_record['tokens'][5]['value']==point_record['index'])
                previous=row['boundary_edges'][corner['incoming_component_slot']]
                check(member+' corner'+str(vertex['index'])+' incoming/outgoing slots share exact vertex',previous['exit']==edge['entry'] and nodes[previous['coedge_index']]['next_coedge_index']==edge['coedge_index'] and nodes[edge['coedge_index']]['previous_coedge_index']==previous['coedge_index'])
                native_proofs.append(dict(surface_record_index=row['surface_record_index'],component_slot=edge['component_slot'],coedge_index=edge['coedge_index'],edge_index=edge['edge_index'],vertex_index=vertex['index'],vertex_record_offset=vertex_record['offset'],vertex_record_end_offset=vertex_record['end_offset'],vertex_payload_hex=blob[vertex_record['offset']:vertex_record['end_offset']].hex(),point_index=point['index'],point_record_offset=point_record['offset'],point_record_end_offset=point_record['end_offset'],point_payload_hex=blob[point_record['offset']:point_record['end_offset']].hex()))
            check(member+' surface'+str(row['surface_record_index'])+' no UV parameter/interior claim',row['component_parameter_orientation'] is None and row['native_edge_parameter_mapping'] is None and row['VBL_interior_geometry'] is None)
        samples.append(dict(file=FILE,archive=FILE,archive_sha256=digest(ROOT/FILE),member=member,blob_sha256=hashlib.sha256(blob).hexdigest(),expected_summary=decoded,existing_component_summary_exact=True,existing_interior_diagnostics=topology['unresolved'],typed_vertex_point_byte_proofs=native_proofs))
        if decoded['decoded']:saved=(blob,parsed,catalog,topology,boundaries,decoded)
    check('Exactly eight faces and48 oriented corner/edge associations',total_faces==8 and total_edges==total_corners==48)
    for archive in CONTROLS:
        for member,blob in read_members(ROOT/archive,zstd).items():
            if not member.endswith(('.smb','.smbh')):continue
            parsed=inspect_asm(blob);catalog=decode_asm_subtypes(blob,parsed=parsed);topology=decode_topology(parsed,subtype_catalog=catalog);before=copy.deepcopy(topology)
            answer=decode_vbl_boundary_corners(blob,parsed=parsed,subtype_catalog=catalog,topology=topology)
            check(archive+' '+member+' unrelated old control no corner claims',not answer['decoded'] and not answer['unresolved'] and topology==before)
            old_controls.append(dict(archive=archive,file=archive,member=member,expected_summary=answer,topology_unchanged=True))
    blob,parsed,catalog,topology,boundaries,decoded=saved
    first=decoded['decoded'][0];target=first['surface_record_index'];edge=first['boundary_edges'][0];by={n['index']:n for n in topology['nodes']}
    def guard(label,action):
        p,c,t,b=map(copy.deepcopy,(parsed,catalog,topology,boundaries));raw=bytearray(blob)
        action(raw,p,c,t,b)
        try:answer=decode_vbl_boundary_corners(bytes(raw),parsed=p,subtype_catalog=c,topology=t,component_boundaries=b)
        except (ValueError,KeyError,IndexError,TypeError) as error:reason=str(error)
        else:
            assert target not in {r['surface_record_index'] for r in answer['decoded']},label
            rejected=next(r for r in answer['unresolved'] if r['surface_record_index']==target);reason=rejected['reason']
        check(label,True);guards.append(dict(guard=label,rejected=True,reason=reason))
    def n(t,identity):return next(v for v in t['nodes'] if v['index']==identity)
    guard('Reject coedge reversal copy differing from raw Boolean',lambda raw,p,c,t,b:n(t,edge['coedge_index']).__setitem__('is_reversed',not edge['stored_coedge_reversal']))
    guard('Reject vertex point pointer copy alias',lambda raw,p,c,t,b:n(t,edge['entry']['vertex_index']).__setitem__('point_index',edge['exit']['point_index']))
    def stale_point(raw,p,c,t,b):
        r=next(r for r in p['records'] if r['index']==edge['entry']['point_index']);r['tokens'][3]['value'][0]+=.001
        n(t,edge['entry']['point_index'])['raw_origin'][0]+=.001
    guard('Reject stale parsed point even when topology copy agrees',stale_point)
    guard('Reject ambiguous owning BODY graph',lambda raw,p,c,t,b:t['body_graphs'].append(copy.deepcopy(next(g for g in t['body_graphs'] if first['face_index'] in g['face_indices']))))
    def break_cycle(raw,p,c,t,b):
        node=n(t,edge['edge_index']);r=next(r for r in p['records'] if r['index']==edge['edge_index'])
        # Change a real bounded pointer consistently in serialized bytes,
        # parsed tokens and node. Only the topological cycle can reject it.
        replacement=first['boundary_edges'][2]['entry']['vertex_index']
        node['end_vertex_index']=replacement;r['tokens'][5]['value']=replacement
        struct.pack_into('<q',raw,r['tokens'][5]['offset']+1,replacement)
        old_end=by[edge['edge_index']]['end_vertex_index']
        vertex=n(t,old_end);vertex_record=next(r for r in p['records'] if r['index']==old_end)
        next_edge=first['boundary_edges'][1]['edge_index']
        vertex['first_edge_index']=next_edge;vertex_record['tokens'][3]['value']=next_edge
        struct.pack_into('<q',raw,vertex_record['tokens'][3]['offset']+1,next_edge)
        c['source_blob_sha256']=hashlib.sha256(raw).hexdigest()
        fresh=decode_vbl_components(bytes(raw),parsed=p,subtype_catalog=c,topology=t)
        b.clear();b.update(fresh)
    guard('Reject consistently encoded endpoint breaking six-vertex cycle',break_cycle)
    guard('Reject stale supplied component association',lambda raw,p,c,t,b:b['decoded'][0]['components'][0].__setitem__('edge_index',edge['edge_index']+1))
    guard('Reject subtype catalog from another blob',lambda raw,p,c,t,b:c.__setitem__('source_blob_sha256','0'*64))
    return dict(interface='decode_vbl_boundary_corners(blob,*,parsed=None,subtype_catalog=None,topology=None,component_boundaries=None)->decoded/unresolved/scope',integration=dict(summary_field='topology.vbl_boundary_corners',location='After existing vbl_component_boundaries and before optional topology node removal',preserve_existing_components_and_eight_interior_warnings=True),samples=samples,old_controls=old_controls,malformed_guards=guards,checks=checks,actual_API_context=dict(settings=actual['settings'],actual_rule=actual['actual_rule'],corner_vertex_or_VBL_evaluator_getters_captured=False),validation=dict(VBL_faces=total_faces,oriented_boundary_edges=total_edges,typed_corners=total_corners,closed_six_vertex_cycles=total_faces,old_control_blobs=len(old_controls),malformed_guards=len(guards),check_count=len(checks),old_component_dictionaries_exact=True,retained_VBL_interior_warnings=8,new_VBL_interior_evaluators=0,no_live_calls=True,no_main_calls=True),source_sha256={p:digest(ROOT/p) for p in ('decode_vbl_boundary_corners.py','validate_vbl_boundary_corners.py','decode_vbl_components.py','decode_brep.py','decode_asm_subtypes.py','decode_pcurve_variants.py','asm_records.py')},limitations=['Native coedge reversal orders only the topological entry/exit vertices. It does not assign the direction of a component UV cache, stored XYZ approximation or native edge parameter.','Corners are linked by exact typed source IDs and reciprocal BODY ownership; no coordinate/name/nearest-geometry matching chooses them. Raw point coordinates remain in ASM asset scope.','Existing API settings establish the Rule/asymmetric fixture only; no direct API corner identity, VBL evaluator or approximation bound is captured.','Only observed six distinct vertices and six component edges are admitted; general singular/repeated-vertex VBL loops remain unsupported.','All eight VBL interior warnings and previous48 component dictionaries remain unchanged. No surface interior, persistent topology, final visible body identity or regeneration claim.'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--zstd');p.add_argument('--output',default='vbl-boundary-corner-decoding.json');a=p.parse_args()
    z=a.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(z);Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['validation'],sort_keys=True))
