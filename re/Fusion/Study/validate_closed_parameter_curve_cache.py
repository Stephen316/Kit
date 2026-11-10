"""Focused closed Patch par_int_cur caches and namespace-qualified compact UVs.

Only saved archives are read. Source-circle and parent-surface deviations are
counterexamples to exactness, not source identity or a parameter remapping.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from asm_records import inspect_asm
from decode_asm_subtypes import decode_asm_subtypes
from decode_brep import decode_topology
from decode_bspline import evaluate_curve, evaluate_surface
from decode_closed_parameter_curve_cache import decode_closed_parameter_curve_cache
from decode_parameter_curve_cache import decode_parameter_curve_cache
from decode_pcurve import evaluate_pcurve
from decode_pcurve_variants import encode_pcurve_fields
from fusion_archive import read_members

ROOT=Path(__file__).resolve().parent
FILES=('patchcontinuity-b9b0be85a281/brep_tangent.f3d','patchcontinuity-b9b0be85a281/brep_curvature.f3d')
OLD_FILES=('lofts-03b4a6f1ce2f/centerline.f3d','sweeps-5f87eff25e24/line_twist.f3d','solidsweeps-5b5ecd5e01b9/solid_twist_sixty.f3d')
DEFAULT_ZSTD='/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production/c139e2731e42a0340acc3d34de2cbdb01237a27c/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'


def sha(value):return hashlib.sha256(value).hexdigest()


def canonical(value):return sha(json.dumps(value,sort_keys=True,separators=(',',':')).encode())


def basis_point(grid,parameter):
    # Independent Cox/de Boor basis recurrence, rather than production de Boor.
    knots=grid['knots'];points=grid['raw_control_points'];degree=grid['degree']
    if parameter==grid['parameter_domain'][1]:return list(points[-1])
    memo={}
    def basis(index,order):
        key=index,order
        if key in memo:return memo[key]
        if order==0:value=float(knots[index]<=parameter<knots[index+1])
        else:
            first=knots[index+order]-knots[index]
            second=knots[index+order+1]-knots[index+1]
            value=((parameter-knots[index])*basis(index,order-1)/first if first else 0.)
            value+=((knots[index+order+1]-parameter)*basis(index+1,order-1)/second if second else 0.)
        memo[key]=value;return value
    return [sum(point[axis]*basis(i,degree) for i,point in enumerate(points)) for axis in range(len(points[0]))]


def bezier_point(points,parameter):
    return [sum(math.comb(3,i)*parameter**i*(1-parameter)**(3-i)*point[axis]
                for i,point in enumerate(points)) for axis in range(3)]


def bezier_grid_bounds(grid):
    # XYZ interior multiplicity3 yields eight independently bounded cubic spans.
    assert grid['degree']==3 and all(multiple==3 for _,multiple in grid['stored_compact_knots'])
    values=[];errors=[];compact=grid['stored_compact_knots']
    for span in range(len(compact)-1):
        points=grid['raw_control_points'][3*span:3*span+4]
        assert len(points)==4
        candidates={0.,1.}
        for axis in range(3):
            p0,p1,p2,p3=[point[axis] for point in points]
            a=3*(-p0+3*p1-3*p2+p3);b=6*(p0-2*p1+p2);c=3*(p1-p0)
            roots=[]
            if abs(a)<1e-14:
                if abs(b)>=1e-14:roots=[-c/b]
            elif b*b-4*a*c>=0:
                disc=math.sqrt(b*b-4*a*c);roots=[(-b-disc)/(2*a),(-b+disc)/(2*a)]
            candidates.update(root for root in roots if 0<root<1)
        values.extend(bezier_point(points,q) for q in candidates)
        for fraction in (.2,.5,.8):
            parameter=compact[span][0]+(compact[span+1][0]-compact[span][0])*fraction
            errors.append(math.dist(bezier_point(points,fraction),evaluate_curve(grid,parameter)))
    assert max(errors)<1e-12
    return dict(min=[min(point[axis] for point in values) for axis in range(3)],
        max=[max(point[axis] for point in values) for axis in range(3)]),errors


def record_replay(blob,record):
    parts=record['name'].split('-');prefix=b''
    for index,part in enumerate(parts):
        raw=part.encode();assert 0<len(raw)<256
        prefix+=bytes([14 if index<len(parts)-1 else 13,len(raw)])+raw
    replay=prefix+encode_pcurve_fields(record['tokens'])+b'\x11'
    original=blob[record['offset']:record['end_offset']]
    assert replay==original
    return dict(offset=record['offset'],end_offset=record['end_offset'],byte_count=len(replay),
        original_sha256=sha(original),typed_replay_sha256=sha(replay),whole_record_replay_exact=True)


def validate(zstd,baseline_source):
    baseline_raw=Path(baseline_source).read_bytes();old={}
    exec(compile(baseline_raw,str(baseline_source),'exec'),old)
    old_reader=old['decode_parameter_curve_cache']
    truth_path=ROOT/'patchcontinuity-b9b0be85a281/ground_truth.json'
    truth=json.loads(truth_path.read_text())
    contexts={}
    def load(filename):
        if filename not in contexts:
            contexts[filename]=[(member,blob,inspect_asm(blob)) for member,blob in read_members(ROOT/filename,zstd).items() if member.endswith(('.smb','.smbh'))]
        return contexts[filename]
    report=dict(scope='Four strictly bounded closed polynomial par_int_cur XYZ/UV form2 caches in two saved Patch archives; four namespace-qualified dependent compact pcurves; no full main-reader scan or live API execution',
        interface='decode_closed_parameter_curve_cache(record); shared decode_parameter_curve_cache defaults remain strict form0, optional allowed_grid_forms=(0,2) used only by the new wrapper',
        source_sha256={name:sha((ROOT/name).read_bytes()) for name in ('decode_closed_parameter_curve_cache.py','decode_parameter_curve_cache.py','decode_bspline.py','decode_brep.py','decode_asm_subtypes.py','decode_pcurve_variants.py','validate_closed_parameter_curve_cache.py')},
        frozen_default_parser=dict(path=str(baseline_source),sha256=sha(baseline_raw)),
        native_framing=dict(token_count=169,xyz='Cubic NUBS form2, nine compact knots/25 XYZ controls',
            uv='Separate cubic NUBS form2, eight compact knots/10 UV controls',support='False spline wrapper, literal nonnegative inline ref, four false bounds, second null_surface',
            trailer='nullbs, false/false, four empty counted lists, true/false, subtype end, false/false outer intervals',
            periodicity='Both caches close at the clamped endpoints; form2 and interval flags remain literal, is_periodic=None'),
        capture_provenance=dict(ground_truth_file=str(truth_path.relative_to(ROOT)),sha256=sha(truth_path.read_bytes()),
            scope='Actual source Circle evaluator and result body bounds only; no direct result XYZ/UV cache getter captured'),
        samples=[],old_default_controls=[],malformed_guards=[],limitations=[
            'These are stored approximations. The original selected source Circle is not the exact resulting cache, and the five source-circle deviations are deliberately retained.',
            'Even the same stored XYZ/UV domains do not imply exact pointwise equality after support composition; nonzero interior deviations remain explicit.',
            'Inline support references are blob-local subtype allocation identities; typed coedge/loop/face linkage and the canonical namespace select the support, not coordinates or IDs guessed from numbers.',
            'Calculated XYZ-cache bounds and API result bounds are numerical corroboration only, with no BODY/source identity assignment by geometry.',
            'No universal periodicity, reversal, coedge parameterization, exact procedural reconstruction, geometry writer or regeneration is provided.'])
    originals=[];independent_errors=[];endpoint_errors=[];circle_errors=[];composition_errors=[]
    for filename in FILES:
        actual=next(sample for sample in truth['samples'] if sample['file']==Path(filename).name)
        assert actual['health_state']==0 and actual['close_owned_document_result'] is True
        source=actual['source_before_patch']['edge'];result,=actual['result_bodies']
        assert source['geometry_type']=='adsk::core::Circle3D'
        for member,blob,parsed in load(filename):
            catalog=decode_asm_subtypes(blob,parsed=parsed)
            topology=decode_topology(parsed,subtype_catalog=catalog);nodes={node['index']:node for node in topology['nodes']}
            curve_index,pcurve_index=(66,48) if member.endswith('.smbh') else (50,37)
            record=parsed['records'][curve_index];cache=decode_closed_parameter_curve_cache(record)
            originals.append((filename,member,record))
            assert nodes[curve_index]['bspline_curve']==cache
            pc=nodes[pcurve_index]['uv_curve']
            assert pc['stored_intcurve_record_pointer']==curve_index and pc['stored_form_code']==2
            assert pc['raw_control_points_uv']==cache['stored_embedded_uv_cache']['raw_control_points']
            coedge=nodes[pc['owning_coedge_index']];edge=nodes[coedge['edge_index']]
            loop=nodes[pc['parent_loop_index']];face=nodes[pc['parent_face_index']]
            assert coedge['pcurve_index']==pcurve_index and edge['curve_index']==curve_index
            assert coedge['loop_index']==loop['index'] and loop['face_index']==face['index']
            surface=nodes[pc['parent_surface_record_index']]['bspline_surface']
            endpoints=[]
            for which in ('start','end'):
                vertex=nodes[edge[which+'_vertex_index']];point=nodes[vertex['point_index']]
                evaluated=evaluate_curve(cache,edge[which+'_parameter'])
                error=math.dist(evaluated,point['raw_origin']);assert error<1e-12;endpoint_errors.append(error)
                endpoints.append(dict(role=which,vertex_index=vertex['index'],point_index=point['index'],native_parameter=edge[which+'_parameter'],stored_point=point['raw_origin'],evaluated_cache_point=evaluated,error_raw=error))
            assert endpoints[0]['vertex_index']==endpoints[1]['vertex_index']
            samples=[]
            for api in source['evaluator_samples']:
                assert api['returned'] is True
                parameter=api['parameter'];xyz=evaluate_curve(cache,parameter);uv=evaluate_pcurve(pc,parameter)
                independent=basis_point(cache['stored_embedded_uv_cache'],parameter)
                independent_error=math.dist(uv,independent);assert independent_error<1e-12;independent_errors.append(independent_error)
                composed=evaluate_surface(surface,*uv)
                circle_error=math.dist(xyz,api['point_cm']);composition_error=math.dist(xyz,composed)
                circle_errors.append(circle_error);composition_errors.append(composition_error)
                samples.append(dict(parameter=parameter,fraction=api['fraction'],xyz_cache=xyz,uv_cache=uv,
                    independent_UV_basis_error=independent_error,selected_support_composition=composed,
                    XYZ_support_composition_deviation_raw=composition_error,actual_source_circle_point_cm=api['point_cm'],
                    cache_source_circle_deviation_raw=circle_error,
                    comparison_scope='Same numeric stored parameter probe only; not an exact procedural/UV parameterization or source identity claim'))
            assert max(row['cache_source_circle_deviation_raw'] for row in samples)>1e-5
            assert max(row['XYZ_support_composition_deviation_raw'] for row in samples)>1e-5
            bounds,bezier_errors=bezier_grid_bounds(cache);independent_errors.extend(bezier_errors)
            bound_deltas={key:[a-b for a,b in zip(bounds[key],result['bounds_'+key+'_cm'])] for key in ('min','max')}
            report['samples'].append(dict(archive=filename,archive_sha256=sha((ROOT/filename).read_bytes()),member=member,asm_blob_sha256=sha(blob),
                curve_record_index=curve_index,expected_cache=cache,pcurve_record_index=pcurve_index,expected_pcurve=pc,
                curve_typed_byte_replay=record_replay(blob,record),pcurve_typed_byte_replay=record_replay(blob,parsed['records'][pcurve_index]),
                typed_parent_chain=dict(edge=edge,endpoint_vertices=endpoints,coedge=coedge,loop=loop,face=face,
                    selected_surface_record_index=pc['parent_surface_record_index'],selected_support_definition_index=pc['selected_support_definition_index']),
                independent_UV_and_approximation_samples=samples,independent_Bernstein_XYZ_errors_raw=bezier_errors,
                XYZ_cache_analytic_span_bounds_raw=bounds,actual_API_result_bounds_cm=dict(min=result['bounds_min_cm'],max=result['bounds_max_cm']),
                cache_minus_API_result_bound_deltas_raw=bound_deltas,
                bound_comparison_scope='Numeric cache/result-AABB corroboration; no source/BODY identity or exact cache equivalence inferred'))
    assert len(report['samples'])==4
    # Bounded old defaults: full dictionaries from frozen pre-stage parser, not
    # reconstructed expectations derived from the new implementation.
    seen=set()
    for filename in OLD_FILES:
        for member,blob,parsed in load(filename):
            for record in parsed['records']:
                tokens=record['tokens']
                if record['name']!='intcurve-curve' or len(tokens)<11 or tokens[5].get('value')!='par_int_cur':continue
                before=old_reader(record);after=decode_parameter_curve_cache(record)
                assert before==after
                shape=(before['stored_wrapper_flag'],before['is_rational'],before['stored_embedded_uv_cache']['degree'],before['stored_support_definition']['kind'],before['stored_support_definition'].get('procedural_subtype'))
                if shape in seen:continue
                seen.add(shape)
                report['old_default_controls'].append(dict(archive=filename,member=member,record_index=record['index'],
                    layout=list(shape),full_dictionary_exact=True,expected_cache_sha256=canonical(before),current_cache_sha256=canonical(after)))
    assert len(report['old_default_controls'])>=3
    for filename,member,record in originals:
        for reader in (old_reader,decode_parameter_curve_cache):
            try:reader(record)
            except ValueError as error:assert str(error)=='Unsupported procedural cache field 10'
            else:raise AssertionError('Strict default accepted the new form')
    base=originals[0][2]
    def reject(label,mutate):
        changed=copy.deepcopy(base);mutate(changed['tokens'])
        try:decode_closed_parameter_curve_cache(changed)
        except (ValueError,IndexError) as error:report['malformed_guards'].append(dict(case=label,rejected=True,reason=str(error)))
        else:raise AssertionError('Malformed closed parameter cache accepted: '+label)
    reject('XYZ form1 unobserved',lambda tokens:tokens[10].update(value=1))
    reject('Mismatched UV form',lambda tokens:tokens[119].update(value=0))
    reject('Rational XYZ unobserved',lambda tokens:tokens[8].update(value='nurbs'))
    reject('Unobserved XYZ compact shape',lambda tokens:tokens[11].update(value=8))
    reject('Open XYZ controls',lambda tokens:tokens[102].update(value=tokens[102]['value']+.1))
    reject('Open UV controls',lambda tokens:tokens[155].update(value=tokens[155]['value']+.1))
    reject('Nonfinite XYZ control',lambda tokens:tokens[30].update(value=float('nan')))
    reject('Negative inline support reference',lambda tokens:tokens[110].update(value=-1))
    reject('Wrong trailer flag',lambda tokens:tokens[164].update(value=False))
    def shifted_domain(tokens):
        for start,size in ((12,9),(121,8)):
            for index in range(size):tokens[start+2*index]['value']+=.1
    reject('Shifted unobserved domain',shifted_domain)
    report['summary']=dict(saved_archives=2,closed_XYZ_UV_cache_records=4,dependent_compact_pcurves=4,
        whole_record_typed_replays=8,typed_native_endpoint_checks=len(endpoint_errors),max_native_endpoint_error_raw=max(endpoint_errors),
        independent_cache_evaluations=len(independent_errors),max_independent_evaluation_error_raw=max(independent_errors),
        max_source_circle_deviation_raw=max(circle_errors),max_XYZ_support_composition_deviation_raw=max(composition_errors),
        previous_layout_controls=len(report['old_default_controls']),default_new_form_errors_exact=8,malformed_guards=len(report['malformed_guards']),
        native_periodicity_claims=0,full_main_runs=0,live_API_calls=0)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zstd-library',default=DEFAULT_ZSTD)
    parser.add_argument('--baseline-source',type=Path,default=Path('/private/tmp/fusion-parameter-curve-baseline-4587d9e.py'))
    parser.add_argument('--output',type=Path,default=ROOT/'closed-parameter-curve-decoding.json')
    args=parser.parse_args();report=validate(args.zstd_library,args.baseline_source)
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],sort_keys=True))
