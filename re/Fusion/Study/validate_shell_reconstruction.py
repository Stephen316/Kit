"""Independent raw-native and analytic checks for bounded Shell reconstruction."""
import argparse
import copy
import hashlib
import itertools
import json
import math
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_shell_reconstruction import (decode_shell_reconstruction,
    decode_shell_face_operands, _collective_geometry, _group_selections)
from decode_brep import decode_topology
from decode_sketch import attributes, numbers, reference
from validate_mesh_remesh import load

ROOT=Path(__file__).resolve().parent
BASELINE=Path('/private/tmp/fusion-shell-reconstruction-baseline.json')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def near(a,b):
    assert len(a)==len(b) and all(math.isfinite(x) for x in list(a)+list(b))
    assert max((abs(x-y) for x,y in zip(a,b)),default=0.)<1e-8,(a,b)
def key(value):
    if isinstance(value,(float,int)):return round(value,9)
    return tuple(key(x) for x in value)
def cycle(points):
    variants=[]
    for row in (points,list(reversed(points))):variants.extend(row[i:]+row[:i] for i in range(len(row)))
    return min(variants,key=key)


def independent(data,records,members,owner,group):
    """Raw Sketch endpoint records then explicit view IDs; no model helper call."""
    native=next(g for g in owner['native_source_provenance']['source_groups']
        if g['native_body_object_id']==group['source_native_body_object_id'])
    primary={r.object_id:r for r in records if r.is_primary}
    literal=group['literal_source_prism'];identities=literal['identity_provenance']
    raw_points={};line_ids={}
    for row in native['native_profile_lines']:
        record=primary[row['object_id'] if 'object_id' in row else row['line_object_id']]
        payload=data[record.body:record.end];props,start=attributes(payload,2)
        endpoints=[reference(payload,start+107),reference(payload,start+96)]
        line_ids[record.object_id]=endpoints
        assert props['crv_primary_id']==next(c['native_entity_tag'] for c in native['profile_cache_correspondence']['source_curves']
            if c['native_entity_object_id']==record.object_id)
        for identity in endpoints:
            point=primary[identity];_,cursor=attributes(data[point.body:point.end],2)
            raw_points[identity]=numbers(data[point.body:point.end],cursor+19,3)
    assert len(line_ids)==len(raw_points)==4
    # All original endpoint IDs have degree two in one closed native profile.
    assert all(sum(point in ends for ends in line_ids.values())==2 for point in raw_points)
    # Independently rejoin initial tagged EDGE candidates to literal view IDs,
    # using only explicit alias/origin rows, then endpoint incidence.
    provenance=literal['provenance'];aliases=provenance['literal_pair_aliases'];origins=provenance['origin_map']
    raw=inspect_asm(members[group['history_blob_member']])['records']
    by_view={r['view_record_index']:r for r in origins}
    def view_endpoint(edge,field):
        origin=by_view[edge];record=raw[origin['inspection_record_index']]
        # The complete rewritten pointer evidence is explicit; no numeric
        # original/view ordinal coincidence is used as a fallback.
        original=record['tokens'][field]['value']
        replacements=[a['side0_inspection_record_index'] for a in aliases
            if a['kind']=='vertex' and a['side1_inspection_record_index']==original]
        target=replacements[0] if replacements else original
        rows=[o['view_record_index'] for o in origins if o['kind']=='vertex' and o['inspection_record_index']==target]
        assert len(rows)==1
        return rows[0]
    line_edges={}
    allowed={e['edge_index'] for e in identities['edge_vertex_pairs']}
    for curve in native['profile_cache_correspondence']['source_curves']:
        candidates=set()
        for edge in {r['edge_record_index'] for r in curve['cached_coedge_candidates']}:
            pairs=[a for a in aliases if a['kind']=='edge' and a['side1_inspection_record_index']==edge]
            assert len(pairs)<=1
            target=pairs[0]['side0_inspection_record_index'] if pairs else edge
            candidates.update(o['view_record_index'] for o in origins if o['kind']=='edge'
                and o['inspection_record_index']==target and o['view_record_index'] in allowed)
        assert len(candidates)==1
        line_edges[curve['native_entity_object_id']]=next(iter(candidates))
    bottom={};opposite={}
    for point in raw_points:
        incident=[line_edges[line] for line,ends in line_ids.items() if point in ends]
        vertices=[{view_endpoint(edge,field) for field in (3,5)} for edge in incident]
        common=vertices[0]&vertices[1];assert len(common)==1
        bottom[point]=next(iter(common))
    for point,vertex in bottom.items():
        connectors=[e for e in allowed-set(line_edges.values()) if vertex in {view_endpoint(e,f) for f in (3,5)}]
        assert len(connectors)==1
        opposite[point]=next(iter({view_endpoint(connectors[0],f) for f in (3,5)}-{vertex}))
    assert bottom==identities['bottom'] and opposite==identities['opposite']
    placement=native['source_sketch']['placement']['sketch_to_component_matrix']
    distance=native['extrude_controls']['extent']['side_one']['distance_cm']
    direction=native['extrude_direction_component']
    source_positions={}
    for identity,raw in raw_points.items():
        base=[sum(placement[4*i+j]*raw[j] for j in range(3))+placement[4*i+3] for i in range(3)]
        for layer,vertex in ((0,identities['bottom'][identity]),(1,identities['opposite'][identity])):
            point=[x+layer*distance*v for x,v in zip(base,direction)]
            source_positions[vertex]=point
            published=next(v for v in literal['native_derived_vertices'] if v['vertex_index']==vertex)
            near(point,published['derived_position_cm'])
            assert published['native_sketch_point_object_id']==identity and published['layer']==layer
    low=[min(p[i] for p in source_positions.values()) for i in range(3)]
    high=[max(p[i] for p in source_positions.values()) for i in range(3)]
    assert {key(p) for p in source_positions.values()}=={key(p) for p in itertools.product(*zip(low,high))}
    near(low,literal['derived_source_prism']['axis_aligned_bounds_cm']['minimum'])
    near(high,literal['derived_source_prism']['axis_aligned_bounds_cm']['maximum'])
    # Source FACE axis/side comes from fixed native endpoint IDs, not cache points.
    face_axes={}
    for face in identities['face_vertex_cycles']:
        points=[source_positions[i] for i in face['vertex_cycle']]
        fixed=[(a,s) for a in range(3) for s,bounds in ((0,low),(1,high))
            if all(abs(p[a]-bounds[a])<1e-8 for p in points)]
        assert len(fixed)==1
        face_axes[face['face_index']]=fixed[0]
    assert set(face_axes.values())==set(itertools.product(range(3),range(2)))
    openings=[]
    for operand in group['removed_face_operands']:
        recipe=operand['recipe'];words=struct.unpack('<119i',bytes.fromhex(recipe['payload_hex']))
        assert words[1:3]==(-1,4)
        named={r['name_table_index']:r['candidates'][0]['owner_record_index'] for r in operand['complete_name_correspondence']['name_entries']}
        assert all(r['candidate_count']==1 for r in operand['complete_name_correspondence']['name_entries'])
        selected=named[words[0]]
        assert selected==operand['selected_literal_FACE_index']
        axis,side=face_axes[selected]
        assert operand['source_axis_side']==dict(axis=axis,side=side)
        openings.append((axis,side))
    settings=owner['native_source_provenance']['settings']
    inside=settings['inside_thickness_cm'] or 0.;outside=settings['outside_thickness_cm'] or 0.
    outer_low=[x-outside for x in low];outer_high=[x+outside for x in high]
    inner_low=[x+inside for x in low];inner_high=[x-inside for x in high]
    for axis,side in openings:
        (outer_low if not side else outer_high)[axis]=(low if not side else high)[axis]
        (inner_low if not side else inner_high)[axis]=(low if not side else high)[axis]
    points={role:{bits:[(right if bit else left)[axis] for axis,bit in enumerate(bits)]
        for bits in itertools.product((0,1),repeat=3)}
        for role,left,right in (('outer',outer_low,outer_high),('inner',inner_low,inner_high))}
    expected_segments=[];expected_faces=[]
    for role in ('outer','inner'):
        for bits,point in points[role].items():
            for axis in range(3):
                if not bits[axis]:
                    other=list(bits);other[axis]=1
                    expected_segments.append(sorted((point,points[role][tuple(other)]),key=key))
    for axis in range(3):
        remaining=[a for a in range(3) if a!=axis]
        for side in range(2):
            def face_loop(role):
                result=[]
                for a,b in ((0,0),(1,0),(1,1),(0,1)):
                    bits=[0,0,0];bits[axis]=side;bits[remaining[0]]=a;bits[remaining[1]]=b
                    result.append(points[role][tuple(bits)])
                return cycle(result)
            if (axis,side) in openings:expected_faces.append(sorted((face_loop('outer'),face_loop('inner')),key=key))
            else:
                expected_faces.extend([[face_loop('outer')],[face_loop('inner')]])
    derived=group['derived_shell'];observed=group['collective_cache_geometry_corroboration']
    assert key(sorted([p for role in points.values() for p in role.values()],key=key))==key(sorted([v['position_cm'] for v in derived['vertices']],key=key))
    assert key(sorted(expected_segments,key=key))==key(sorted([sorted((s['start_position_cm'],s['end_position_cm']),key=key) for s in derived['segments']],key=key))
    assert key(sorted(expected_faces,key=key))==key(sorted([sorted([cycle(l['corner_positions_cm']) for l in f['loops']],key=key) for f in derived['planar_boundaries']],key=key))
    outer_volume=math.prod(b-a for a,b in zip(outer_low,outer_high))
    cavity_volume=math.prod(b-a for a,b in zip(inner_low,inner_high))
    near([outer_volume-cavity_volume],[derived['material_volume_cm3']])
    assert observed['semantic_role_to_native_entity_mapping'] is None
    blob=members[group['history_blob_member']];raw=inspect_asm(blob)['records']
    vertex_positions={}
    for row in observed['native_vertices']:
        identity=row['vertex_index'];point=raw[identity]['tokens'][5]['value'];assert raw[point]['name']=='point'
        position=raw[point]['tokens'][3]['value'];near(position,row['native_POINT']['raw_origin'])
        vertex_positions[identity]=position
    assert key(sorted(vertex_positions.values(),key=key))==key(sorted([p for role in points.values() for p in role.values()],key=key))
    endpoint_checks=[];reversal_counts={False:0,True:0}
    for row in observed['native_straight_segments']:
        edge=raw[row['edge_index']]['tokens'];curve=raw[edge[8]['value']]
        assert curve['name']=='straight-curve';origin,direction=curve['tokens'][3]['value'],curve['tokens'][4]['value']
        reversal_counts[edge[9]['value']]+=1
        sign=-1 if edge[9]['value'] else 1
        for field,parameter in ((3,edge[4]['value']),(5,edge[6]['value'])):
            point=vertex_positions[edge[field]['value']]
            evaluated=[o+sign*parameter*d for o,d in zip(origin,direction)]
            near(point,evaluated);endpoint_checks.append(dict(edge_index=row['edge_index'],vertex_index=edge[field]['value'],
                raw_parameter=parameter,raw_reversed=edge[9]['value'],observed_multiplier=sign,
                independent_evaluation=evaluated,typed_point=point))
    actual_faces=[]
    for row in observed['native_planar_boundaries']:
        face=raw[row['face_index']]['tokens'];plane=raw[face[7]['value']]
        assert plane['name']=='plane-surface'
        origin,normal=plane['tokens'][3]['value'],plane['tokens'][4]['value']
        near([sum(n*n for n in normal)],[1.])
        loops=[]
        for loop in row['loops']:
            c=raw[loop['loop_index']]['tokens'][4]['value'];seen=[];vertices=[]
            while c not in seen:
                coedge=raw[c]['tokens'];edge=raw[coedge[6]['value']]['tokens']
                assert raw[coedge[3]['value']]['tokens'][4]['value']==c
                vertices.append(edge[5 if coedge[7]['value'] else 3]['value']);seen.append(c);c=coedge[3]['value']
            assert c==seen[0] and len(seen)==4 and vertices==loop['vertex_cycle']
            corners=[vertex_positions[v] for v in vertices]
            for point in corners:near([sum(n*(x-o) for n,x,o in zip(normal,point,origin))],[0.])
            loops.append(cycle(corners))
        actual_faces.append(sorted(loops,key=key))
    assert key(sorted(actual_faces,key=key))==key(sorted(expected_faces,key=key))
    return dict(native_profile_point_count=4,source_vertex_count=8,target_vertex_count=16,
        segment_count=24,planar_FACE_count=len(actual_faces),loop_count=12,
        selected_openings=[dict(axis=a,side=s) for a,s in openings],
        independently_derived_bounds_cm=dict(source_minimum=low,source_maximum=high,
            outer_minimum=outer_low,outer_maximum=outer_high,cavity_minimum=inner_low,cavity_maximum=inner_high),
        independent_volume_cm3=outer_volume-cavity_volume,raw_endpoint_checks=endpoint_checks,
        raw_reversal_counts=[dict(flag=k,count=v) for k,v in reversal_counts.items()],
        API_geometry_comparison=None,
        scope='Raw native Sketch positions/extent and independent scalar box algebra, followed by whole unordered cache geometry corroboration; no coordinate ENTITY assignment')


def validate(root,zstd):
    baseline=json.loads(BASELINE.read_text());files=baseline['files']
    report=dict(scope='Independent focused native/analytic Shell verification; no main/live calls',
        baseline_commit=baseline['baseline_commit'],baseline_sha256=sha(BASELINE),
        acquisition_main_calls=0,live_API_calls=0,samples=[],guards=[],positive_controls=[],source_sha256={})
    saved=None;totals=dict(owners=0,groups=0,vertices=0,segments=0,planar_faces=0,loops=0,endpoint_evaluations=0)
    for archive,old in zip(files,baseline['before']):
        data,records,features,member,members=load(root,archive,zstd)
        bindings=old['streams'][0]['body_blob_bindings'];before=copy.deepcopy((features,bindings,members))
        summary=decode_shell_reconstruction(data,records,features,member,members,bindings)
        assert (features,bindings,members)==before
        assert not summary['unresolved'],(archive,summary['unresolved'])
        assert len(summary['decoded'])==(0 if archive.endswith(('Scale.f3d','offset_positive.f3d')) else 1)
        proofs=[]
        for owner in summary['decoded']:
            totals['owners']+=1
            for group in owner['source_groups']:
                proof=independent(data,records,members,owner,group);proofs.append(proof)
                totals['groups']+=1;totals['vertices']+=16;totals['segments']+=24
                totals['planar_faces']+=proof['planar_FACE_count'];totals['loops']+=12;totals['endpoint_evaluations']+=48
                assert all(group[k] is None for k in ('Shell_owned_result_anchor','qualified_historical_state','exact_API_handle_identity','current_or_final_geometry_identity'))
        report['samples'].append(dict(archive=archive,archive_sha256=sha(root/archive),expected_summary=summary,
            independent_native_analytic_checks=proofs,caller_inputs_unchanged=True,
            API_scope='Saved API controls/types/counts only; no saved numerical Shell vertices available'))
        if saved is None and summary['decoded']:saved=(data,records,features,member,members,bindings,summary)
    data,records,features,member,members,bindings,summary=saved
    group=summary['decoded'][0]['source_groups'][0];blob=members[group['history_blob_member']]
    topology=decode_topology(inspect_asm(blob));nodes={n['index']:n for n in topology['nodes']}
    graph=next(g for g in topology['body_graphs'] if g['body_index']==group['asm_body_index'])
    def reject(name,operation):
        try:operation()
        except (ValueError,AssertionError) as error:report['guards'].append(dict(name=name,reason=str(error)));return
        raise AssertionError('Guard accepted: '+name)
    recipe=copy.deepcopy(group['removed_face_operands'][0]['recipe'])
    # Parser guards operate on the actual complete recipe, and preserve framing
    # fields except the explicit malformed operation under test.
    def recipe_mutation(offset,value):
        changed=copy.deepcopy(recipe);raw=bytearray.fromhex(changed['payload_hex']);struct.pack_into('<i',raw,offset,value)
        changed['payload_hex']=raw.hex()
        return changed
    reject('Wrong EDGE endpoint FACE count',lambda:decode_shell_face_operands(recipe_mutation((3+8+1)*4,2)))
    reject('Nonliteral EDGE terminal',lambda:decode_shell_face_operands(recipe_mutation((3+28)*4,0)))
    def mutated_nodes(identity,key,value):
        changed=copy.deepcopy(nodes);changed[identity][key]=value
        return _collective_geometry(graph,changed,group['derived_shell'])
    edge=nodes[graph['edge_indices'][0]];uses=[nodes[c] for c in graph['coedge_indices'] if nodes[c]['edge_index']==edge['index']]
    reject('Self partner',lambda:mutated_nodes(uses[0]['index'],'partner_index',uses[0]['index']))
    reject('Nonincident EDGE head',lambda:mutated_nodes(edge['index'],'first_coedge_index',next(c for c in graph['coedge_indices'] if nodes[c]['edge_index']!=edge['index'])))
    vertex=nodes[graph['vertex_indices'][0]]
    reject('Nonincident VERTEX head',lambda:mutated_nodes(vertex['index'],'first_edge_index',next(e for e in graph['edge_indices'] if vertex['index'] not in (nodes[e]['start_vertex_index'],nodes[e]['end_vertex_index']))))
    point=nodes[vertex['point_index']]
    reject('Target POINT finite but displaced',lambda:mutated_nodes(point['index'],'raw_origin',[x+.01 for x in point['raw_origin']]))
    reject('Target POINT NaN',lambda:mutated_nodes(point['index'],'raw_origin',[float('nan'),0.,0.]))
    face=nodes[graph['face_indices'][0]];plane=nodes[face['surface_index']]
    reject('Plane moved off its boundary',lambda:mutated_nodes(plane['index'],'raw_origin',[x+.1*n for x,n in zip(plane['raw_origin'],plane['normal'])]))
    regrouped=copy.deepcopy(group['derived_shell']);annulus=next(f for f in regrouped['planar_boundaries'] if len(f['loops'])==2)
    annulus['loops'][0]['corner_positions_cm']=annulus['loops'][0]['corner_positions_cm'][:2]
    annulus['loops'][1]['corner_positions_cm']+=annulus['loops'][1]['corner_positions_cm'][:2]
    reject('Same flat scalar count but malformed loop grouping',lambda:_collective_geometry(graph,nodes,regrouped))
    crossed=copy.deepcopy(group['derived_shell']);loop=crossed['planar_boundaries'][0]['loops'][0]['corner_positions_cm']
    loop[1],loop[2]=loop[2],loop[1]
    reject('Same corner set but crossed cyclic boundary',lambda:_collective_geometry(graph,nodes,crossed))
    reject('Same BODY mixed whole and Face operands',lambda:_group_selections(
        dict(selected_inputs=[dict(kind='Body'),dict(kind='Face')]),dict(selected_input_indices=[0,1])))
    reject('Same BODY repeated whole operands',lambda:_group_selections(
        dict(selected_inputs=[dict(kind='Body'),dict(kind='Body')]),dict(selected_input_indices=[0,1])))
    # Valid head selection is literal, not an assumed fixed enumeration.
    changed=copy.deepcopy(nodes);changed[edge['index']]['first_coedge_index']=uses[1]['index']
    positive=_collective_geometry(graph,changed,group['derived_shell'])
    assert positive['collective_residuals_raw']==group['collective_cache_geometry_corroboration']['collective_residuals_raw']
    report['positive_controls'].append(dict(name='Other incident EDGE coedge head retained',passed=True))
    annotated=copy.deepcopy(bindings)
    for mapping in annotated['decoded']:
        for binding in mapping['bindings']:binding['previous_ordinal_candidate']=987654321
    assert decode_shell_reconstruction(data,records,features,member,members,annotated)==summary
    report['positive_controls'].append(dict(name='Caller ordinal annotations do not enter native mapping proof',passed=True))
    report['totals']=totals;report['check_count']=len(files)*3+totals['groups']*8
    report['guard_count']=len(report['guards'])
    for name in ('decode_shell_reconstruction.py','validate_shell_reconstruction.py','decode_shell_source_operands.py',
            'decode_shell_box_geometry.py','decode_scale_reconstruction.py','materialize_asm_literal_view.py'):
        report['source_sha256'][name]=sha(root/name)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library',required=True);args=parser.parse_args()
    result=validate(ROOT,args.zstd_library)
    (ROOT/'shell-reconstruction-decoding.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(totals=result['totals'],checks=result['check_count'],guards=result['guard_count'])))
