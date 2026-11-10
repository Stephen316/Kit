"""Three stored interpolation-width caches, independent basis sums and API rows."""
import argparse
import copy
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import subprocess
import types

from asm_records import inspect_asm
from decode_asm_subtypes import decode_asm_subtypes,expand_asm_subtype_record
from decode_brep import decode_topology
from decode_bspline import evaluate_curve,evaluate_surface
from decode_interp_blend_cache import decode_interp_blend_cache,SCOPE
from decode_pcurve import evaluate_pcurve
from decode_pcurve_variants import encode_pcurve_fields
from decode_rule_blend_cache import decode_rule_blend_cache
from decode_variable_blend_cache import decode_variable_blend_cache
from fusion_archive import read_members

CAPTURE='variablefillets-a5080b076434'
FILES=('one_quarter.f3d','one_three_quarters.f3d','two_intermediates.f3d')
BASELINE='4587d9efec3e64e6f1a239caedef02a46ce74334'


def normalized(value):return json.loads(json.dumps(value))


def independent_curve(cache,parameter):
    knots=cache['knots'];degree=cache['degree'];points=cache['raw_control_points']
    if parameter==cache['parameter_domain'][1]:return list(points[-1])
    @lru_cache(None)
    def basis(i,d):
        if d==0:return float(knots[i]<=parameter<knots[i+1])
        left=knots[i+d]-knots[i];right=knots[i+d+1]-knots[i+1]
        return ((parameter-knots[i])/left*basis(i,d-1) if left else 0.)+((knots[i+d+1]-parameter)/right*basis(i+1,d-1) if right else 0.)
    weights=cache.get('weights') or [1.]*len(points);co=[basis(i,degree)*w for i,w in enumerate(weights)]
    return [sum(w*p[axis] for w,p in zip(co,points))/sum(co) for axis in range(len(points[0]))]


def independent_surface(cache,u,v):
    # Direct tensor basis sum, separate from the production tensor de Boor path.
    def bases(knots,degree,parameter,count):
        if parameter==knots[-degree-1]:return [0.]*(count-1)+[1.]
        @lru_cache(None)
        def b(i,d):
            if not d:return float(knots[i]<=parameter<knots[i+1])
            left=knots[i+d]-knots[i];right=knots[i+d+1]-knots[i+1]
            return ((parameter-knots[i])/left*b(i,d-1) if left else 0.)+((knots[i+d+1]-parameter)/right*b(i+1,d-1) if right else 0.)
        return [b(i,degree) for i in range(count)]
    nu,nv=cache['control_count_u'],cache['control_count_v'];bu=bases(cache['knots_u'],cache['degree_u'],u,nu);bv=bases(cache['knots_v'],cache['degree_v'],v,nv)
    factors=[bu[i]*bv[j]*cache['weights'][i*nv+j] for i in range(nu) for j in range(nv)]
    return [sum(f*p[axis] for f,p in zip(factors,cache['raw_control_points']))/sum(factors) for axis in range(3)]


def validate(root,zstd):
    checks=[];samples=[];guards=[];legacy=[];contexts=[];loaded={}
    def check(label,value):
        if not value:raise AssertionError(label)
        checks.append(label)
    def members(archive):
        if archive not in loaded:loaded[archive]=read_members(root/archive,zstd)
        return loaded[archive]
    truth=json.loads((root/CAPTURE/'ground_truth.json').read_text())
    check('Actual variable fillet batch complete and errors empty',truth['status']=='complete' and not truth['errors'] and (root/CAPTURE/'complete.txt').is_file())
    for filename in FILES:
        archive=CAPTURE+'/'+filename;actual=next(s for s in truth['samples'] if s['file']==filename)
        member,blob=next((n,b) for n,b in members(archive).items() if n.endswith('.smbh'))
        parsed=inspect_asm(blob);record=parsed['records'][10];before=copy.deepcopy(record)
        check(archive+' complete typed token stream',parsed['complete_token_stream'])
        cache=decode_interp_blend_cache(record)
        check(archive+' source record unchanged',record==before)
        replay=b'\x0e\x06spline\x0d\x07surface'+bytes.fromhex(cache['stored_complete_payload_hex'])+b'\x11'
        check(archive+' complete typed source record replay',replay==blob[record['offset']:record['end_offset']])
        check(archive+' healthy actual owned close',actual['health_state']==0 and actual['close_owned_document_result'] is True)
        width=cache['stored_interp_width_cache'];a,b=width['parameter_domain'];width_evaluations=[]
        for fraction in (0.,.19,.43,.71,1.):
            t=a+(b-a)*fraction;x=evaluate_curve(width,t);y=independent_curve(width,t)
            check(archive+' independent width basis'+str(fraction),math.dist(x,y)<1e-12)
            width_evaluations.append(dict(parameter=t,value=x,independent_basis_value=y))
        settings=actual['settings']['edge_sets'];check(archive+' singleton actualAPI edge set',len(settings)==1)
        edge_set=settings[0];api=edge_set['actual_source_edges'][0];lo,hi=api['trimmed_parameter_extents']
        check(archive+' explicit native width domain and API source extent agree',width['parameter_domain']==[lo,hi])
        origin=cache['stored_spine']['raw_origin'];direction=cache['stored_spine']['raw_direction']
        source_evaluator=[]
        for point in api['trimmed_evaluator_samples']:
            expected=[o+point['parameter']*d for o,d in zip(origin,direction)]
            check(archive+' native spine corroborates actual source evaluator'+str(point['parameter']),point['returned'] is True and math.dist(expected,point['point_cm'])<1e-12)
            source_evaluator.append(dict(parameter=point['parameter'],native_straight_point=expected,actual_API_source_point=point['point_cm']))
        pairs=[(lo,edge_set['start_radius']['raw_value']),(hi,edge_set['end_radius']['raw_value'])]
        for pos,radius in zip(edge_set['mid_positions'],edge_set['mid_radii']):pairs.append((lo+pos['raw_value']*(hi-lo),radius['raw_value']))
        pairs.sort();rows=cache['stored_interp_rows']
        check(archive+' complete stored rows and API radius/position pairs agree',len(rows)==len(pairs) and all(math.isclose(r['parameter'],p,abs_tol=1e-12) and math.isclose(r['width_scalar'],v,abs_tol=1e-12) for r,(p,v) in zip(rows,pairs)))
        row_evaluations=[]
        for row in rows:
            value=evaluate_curve(width,row['parameter']);check(archive+' width cache meets captured row'+str(row['parameter']),abs(value[0]-row['width_scalar'])<1e-12 and value[1]==0.)
            row_evaluations.append(dict(stored_parameter=row['parameter'],stored_width_scalar=row['width_scalar'],derived_width_coordinates=value))
        surface_evaluations=[];au,bu=cache['parameter_domain_u'];av,bv=cache['parameter_domain_v']
        for fu,fv in ((.13,.21),(.37,.59),(.73,.83)):
            u,v=au+(bu-au)*fu,av+(bv-av)*fv;x=evaluate_surface(cache,u,v);y=independent_surface(cache,u,v)
            check(archive+' independent tensor basis'+str((fu,fv)),math.dist(x,y)<1e-11)
            surface_evaluations.append(dict(u=u,v=v,derived_point=x,independent_tensor_basis_point=y))
        catalog=decode_asm_subtypes(blob,parsed=parsed);topology=decode_topology(parsed,subtype_catalog=catalog);nodes={n['index']:n for n in topology['nodes']}
        boundary=[]
        for coedge in nodes.values():
            if coedge['kind']!='coedge' or coedge['loop_index'] is None:continue
            loop=nodes[coedge['loop_index']];face=nodes[loop['face_index']]
            if face['surface_index']!=10:continue
            edge=nodes[coedge['edge_index']];following=nodes[coedge['next_coedge_index']];previous=nodes[coedge['previous_coedge_index']]
            check(archive+' reciprocal owning boundary'+str(coedge['index']),following['previous_coedge_index']==coedge['index'] and previous['next_coedge_index']==coedge['index'] and loop['face_index']==face['index'])
            uv=nodes[coedge['pcurve_index']]['uv_curve'];endpoints=[]
            for role in ('start','end'):
                vertex=nodes[edge[role+'_vertex_index']];point=nodes[vertex['point_index']]
                check(archive+' typed vertex-point boundary'+str((coedge['index'],role)),vertex['kind']=='vertex' and point['kind']=='point')
                endpoints.append(dict(vertex_index=vertex['index'],point_index=point['index'],raw_position=point['raw_origin']))
            surface_points=[evaluate_surface(cache,*evaluate_pcurve(uv,t)) for t in uv['parameter_domain']]
            stored=[p['raw_position'] for p in endpoints]
            error=max(max(min(math.dist(x,y) for y in stored) for x in surface_points),max(min(math.dist(x,y) for y in surface_points) for x in stored))
            check(archive+' surfaceUV endpoint set agrees after typed incidence'+str(coedge['index']),error<1e-9)
            edge_parameters=[edge['start_parameter'],edge['end_parameter']]
            boundary.append(dict(face_index=face['index'],loop_index=loop['index'],coedge_index=coedge['index'],edge_index=edge['index'],pcurve_index=coedge['pcurve_index'],curve_index=edge['curve_index'],
                typed_vertex_points=endpoints,derived_UV_surface_endpoints=surface_points,unordered_endpoint_set_error_raw=error,
                native_edge_parameters=edge_parameters,stored_UV_cache_domain=uv['parameter_domain'],edge_UV_parameter_map=None))
        check(archive+' exactly four explicit face boundary chains',len(boundary)==4)
        samples.append(dict(archive=archive,file=archive,member=member,record_index=10,record_offset=record['offset'],expected_cache=cache,
            source_record_replay=dict(matches=True,byte_count=len(replay),sha256=hashlib.sha256(replay).hexdigest()),
            actual_API_source_edge=api,actual_API_mid_parameters=edge_set['mid_positions'],actual_API_mid_radii=edge_set['mid_radii'],
            native_API_persistent_source_identity=None,source_spine_evaluator_corroboration=source_evaluator,stored_row_API_radius_position_pairs=pairs,
            derived_width_evaluations=width_evaluations,derived_width_row_evaluations=row_evaluations,independent_tensor_evaluations=surface_evaluations,
            explicit_parent_boundary_checks=boundary,actual_API_result_body_summary=actual['result_bodies'],
            actual_API_result_surface_grid_or_evaluator=None,source_result_scope='API source edge/radius data corroborate stored definition fields only; result caches are independently fixed by native record and parent topology, with no source/result/API face identity assignment or exact procedural evaluator claim'))
        contexts.append(record)
    # Exact default-success/error comparison against the pinned pre-extension rule module.
    old_source=subprocess.check_output(['git','show',BASELINE+':decode_rule_blend_cache.py'],cwd=root)
    old=types.ModuleType('_pinned_rule_blend');exec(compile(old_source,'<pinned Rule blend reader>','exec'),old.__dict__)
    for record in contexts:
        reasons=[]
        for decoder in (old.decode_rule_blend_cache,decode_rule_blend_cache):
            try:decoder(record)
            except (ValueError,IndexError) as error:reasons.append(str(error))
            else:raise AssertionError('Default Rule reader unexpectedly accepts interp branch')
        check('Default interp rejection reason preserved',reasons==['Rule blend fallback requires captured unbounded spine']*2)
    report=json.loads((root/'rule-blend-cache-decoding.json').read_text());old_rule_count=0
    for sample in report['samples']:
        blob=members(sample['file'])[sample['member']];parsed=inspect_asm(blob);catalog=decode_asm_subtypes(blob,parsed=parsed)
        for item in sample['XYZ_caches']:
            record=parsed['records'][item['record_index']]
            if record['tokens'][5]['value']=='ref':record=expand_asm_subtype_record(record,catalog,parsed['records'])['record']
            current=decode_rule_blend_cache(record);prior=old.decode_rule_blend_cache(record)
            check(sample['file']+' old Rule full dictionary'+str(item['record_index']),current==prior and normalized(current)==item['expected_decoded']);old_rule_count+=1
    legacy.append(dict(report='rule-blend-cache-decoding.json',pinned_default_full_dictionary_count=old_rule_count,pinned_revision=BASELINE,pinned_rule_source_sha256=hashlib.sha256(old_source).hexdigest()))
    report=json.loads((root/'variable-blend-cache-decoding.json').read_text())
    for sample in report['samples']:
        parsed=inspect_asm(members(sample['file'])[sample['member']]);current=decode_variable_blend_cache(parsed['records'][sample['record_index']])
        check(sample['file']+' old Variable full dictionary exact',normalized(current)==sample['cache'])
        legacy.append(dict(archive=sample['file'],old_variable_full_dictionary_exact=True))
    first=contexts[0];cache=samples[0]['expected_cache']
    def guard(label,mutate):
        changed=copy.deepcopy(first);mutate(changed['tokens'])
        try:decode_interp_blend_cache(changed)
        except (ValueError,IndexError,TypeError) as error:reason=str(error)
        else:raise AssertionError(label)
        check(label,True);guards.append(dict(guard=label,reason=reason))
    start=cache['stored_grid_start_token'];width_row=cache['stored_interp_rows'][0]['stored_token_start'];row_count_offset=width_row-1
    def set_value(index,value):return lambda ts:ts[index].update(value=value)
    guard('Reject unsupported interpolation row count',set_value(row_count_offset,5))
    guard('Reject nonmonotonic interpolation parameters',set_value(cache['stored_interp_rows'][1]['stored_token_start'],0.))
    guard('Reject changed literal auxiliary row scalar',set_value(width_row+2,0.))
    guard('Reject nonfinite native spine origin',set_value(40,[float('nan'),4.,2.]))
    guard('Reject unobserved rational grid axis tuple',set_value(start+7,2))
    # Locate first weight using the complete counted knots, not a marker search.
    from decode_bspline import knot_vector
    _,_,_,cursor=knot_vector(first['tokens'],start+10,first['tokens'][start+8]['value'],3)
    _,_,_,cursor=knot_vector(first['tokens'],cursor,first['tokens'][start+9]['value'],3)
    guard('Reject nonpositive rational weight',set_value(cursor+3,0.))
    guard('Reject outer trim exceeding stored knot domain',set_value(len(first['tokens'])-1,cache['parameter_domain_v'][1]+1.))
    guard('Reject unobserved interpolation degree',set_value(55,4))
    guard('Reject unconsumed trailing token',lambda ts:ts.append(copy.deepcopy(ts[-1])))
    files=('decode_interp_blend_cache.py','validate_interp_blend_cache.py','decode_rule_blend_cache.py','decode_bspline.py','decode_pcurve_variants.py')
    return dict(scope=SCOPE,sample_count=3,recovered_XYZ_surface_count=3,stored_interp_row_count=sum(len(s['expected_cache']['stored_interp_rows']) for s in samples),
        check_count=len(checks),malformed_guard_count=len(guards),typed_parent_boundary_count=sum(len(s['explicit_parent_boundary_checks']) for s in samples),
        samples=samples,legacy_controls=legacy,checks=checks,malformed_guards=guards,
        source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in files},
        limitations=['Stored XYZ tensor grids are approximations, not exact procedural fillet reconstruction; no result API surface grid/evaluator truth was captured',
            'Sentinel1e37 scalars and native axis/trailer/bound flags are preserved without tolerance, derivative, periodicity or reversal interpretation',
            'Width/radius and source parameter correspondence is corroborated at the actual captured interpolation rows only; no universal interpolation-law exactness claim',
            'Typed topology fixes all native boundary identities before numerical endpoint comparisons; no source/result, per-face API handle or lifecycle assignment',
            'Negative native edge32 limits remain distinct from positive UV-cache limits; no sign correction inferred',
            'Historical reports unchanged; no live API/UI, full main-reader/corpus rerun, writer or regeneration'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--zstd-library');p.add_argument('--output',default='interp-blend-cache-decoding.json');args=p.parse_args();root=Path(__file__).resolve().parent
    z=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(root,z);Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('sample_count','recovered_XYZ_surface_count','check_count','malformed_guard_count','typed_parent_boundary_count')}))
if __name__=='__main__':main()
