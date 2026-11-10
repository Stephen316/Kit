"""Focused offline VBL component association and bounded-cache checks."""
import copy
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from asm_records import inspect_asm
from decode_asm_subtypes import decode_asm_subtypes
from decode_brep import decode_topology
from decode_bspline import evaluate_curve
from decode_vbl_components import decode_vbl_components, evaluate_vbl_component, prove_uv_refinement, SCOPE
from fusion_archive import read_members


def validate_fixtures(root, zstd_library=None):
    root=Path(root)
    filename='specialfillets-d50f7a4f04e0/rule_asymmetric.f3d'
    actual=next(s for s in json.loads((root/filename).parent.joinpath('ground_truth.json').read_text())['samples']
                if s['file']==Path(filename).name)
    report=dict(scope=SCOPE,interfaces={
        'decoder':'decode_vbl_components(blob,*,parsed=None,subtype_catalog=None,topology=None)->decoded/unresolved/scope',
        'evaluator':'evaluate_vbl_component(component,parameter)->rawXYZ for admitted component domain only',
        'UV_proof':'prove_uv_refinement(componentUV,boundaryUV)->full coefficient/knot-insertion evidence',
        'integration':'Call after topology construction, passing existing parsed/catalog/topology. Attach separate vbl_component_boundaries summary only; keep VBL partial-surface warnings and original bspline caches unchanged.'},
        recovered_semantics=[
            'Each of the eight saved VBL views has exactly six component descriptions and a six-coedge reciprocal owning-face ring.',
            'Each component joins one unique edge/parameter-curve boundary through complete plane-definition field equality or exact typed spline namespace identity, plus algebraic UV coefficient equality; partner coedge/adjacent-face support corroborates the same support.',
            'All24 quintic plane components are literal knot refinements of their corresponding boundary parameter-curve UV grids. Standard knot insertion reproduces every coefficient exactly in this fixture.',
            'All24 linear blend-support components retain the same UV polynomial after independent normalization of their stored parameter domains.12 components store domain[-1,0] instead of boundaryUV[0,1]; native edge parameters are separately retained.',
            'The six component slots agree with owning coedge order up to cyclic rotation of the linked ring, proven by explicit indices after association, not by positional sorting.',
            'All48 bounded support(UV(t)) compositions can be evaluated using framed plane definitions or namespace-resolved stored rational blend patches. These are boundary-cache evaluations, not a VBL interior evaluator.'],
        actual_API={'fillet_settings':actual['settings'],'rule_settings':actual['actual_rule'],
                    'direct_VBL_or_curve_surface_evaluator_captured':False,
                    'scope':'The saved API feature settings establish the Rule/asymmetric fixture; no exact procedural evaluator equivalence or approximation-error bound is claimed'},
        samples=[],old_controls=[],malformed_guards=[],limitations=[
            'No standalone VBL XYZ tensor grid or exact interior construction has been recovered. The eight partial-surface warnings remain valid.',
            'Serialized plane-definition equality is a bounded stored-definition correspondence, not a native persistent BRep identity; inline references use the typed blob-local allocation namespace.',
            'Knot-refinement/domain-normalization proof relates stored UV polynomials only. It does not establish native edge/VBL parameter maps or assign universal meaning to wrapper/terminal flags.',
            'Support composition and stored boundary XYZ approximations can disagree between endpoints; sampled deviations below are preserved and are not global error bounds.',
            'No sampled coordinate, endpoint match, source order or nearest-geometry search chooses a component boundary association.',
            'This helper only admits the observed one-loop/six-component plane-or-blend support configuration; general VBL definitions remain unsupported.'])
    totals=Counter(); saved=None
    for member,blob in read_members(root/filename,zstd_library).items():
        if not member.endswith(('.smb','.smbh')):continue
        parsed=inspect_asm(blob);catalog=decode_asm_subtypes(blob,parsed=parsed)
        topology=decode_topology(parsed,subtype_catalog=catalog)
        before_parsed=copy.deepcopy(parsed);before_topology=copy.deepcopy(topology)
        result=decode_vbl_components(blob,parsed=parsed,subtype_catalog=catalog,topology=topology)
        assert decode_vbl_components(blob)==result
        assert parsed==before_parsed and topology==before_topology
        assert not result['unresolved'],result['unresolved']
        row=dict(file=filename,member=member,blob_sha256=hashlib.sha256(blob).hexdigest(),expected_summary=result,
                 component_evaluation_checks=[],input_structures_unchanged=True,direct_and_passed_topology_outputs_equal=True)
        for vbl in result['decoded']:
            totals['VBL_views']+=1
            assert vbl['VBL_interior_geometry'] is None
            for component in vbl['components']:
                totals['component_boundary_associations']+=1
                uv=component['stored_uv_cache'];xyz=component['boundary_XYZ_cache'];other_uv=xyz['stored_embedded_uv_cache']
                totals['quintic_knot_refinements' if uv['degree']==5 else 'linear_UV_correspondences']+=1
                totals['negative_component_UV_domains']+=int(uv['parameter_domain']==[-1.,0.])
                a,b=uv['parameter_domain'];c,d=other_uv['parameter_domain'];e,f=xyz['parameter_domain']
                evaluations=[]
                for fraction in (0.,.25,.5,.75,1.):
                    t=a+(b-a)*fraction;other_t=c+(d-c)*fraction
                    decoded_uv=evaluate_curve(uv,t);other_decoded=evaluate_curve(other_uv,other_t)
                    UV_error=math.dist(decoded_uv,other_decoded)
                    assert UV_error<1e-11
                    composed=evaluate_vbl_component(component,t)
                    # Normalize the independent XYZ-cache domain for a sampled
                    # comparison only; this is not the native edge map.
                    cached=evaluate_curve(xyz,e+(f-e)*fraction)
                    evaluations.append(dict(fraction_of_each_stored_domain=fraction,component_parameter=t,
                        maximum_UV_equivalence_error=UV_error,composed_raw_XYZ=composed,boundary_cache_raw_XYZ=cached,
                        sampled_XYZ_cache_deviation=math.dist(composed,cached)))
                totals['bounded_composition_samples']+=len(evaluations)
                row['component_evaluation_checks'].append(dict(surface_record_index=vbl['surface_record_index'],slot=component['slot'],
                    coedge_index=component['coedge_index'],boundary_curve_index=component['boundary_curve_index'],
                    support_kind=component['evaluable_support']['kind'],degree=uv['degree'],samples=evaluations,
                    maximum_sampled_XYZ_cache_deviation=max(x['sampled_XYZ_cache_deviation'] for x in evaluations),
                    coefficient_proof_maximum_roundoff=component['UV_coefficient_correspondence']['maximum_coefficient_roundoff'],
                    scope='Coefficient proof precedes these checks; these sampled positions do not choose IDs or establish global approximation error'))
        report['samples'].append(row)
        if result['decoded']:saved=(blob,parsed,catalog,topology,result)
    assert totals['VBL_views']==8 and totals['component_boundary_associations']==48
    # Two old Fillet controls contain no admitted VBLs and acquire no unrelated
    # boundary associations. Neither their native caches nor topology is edited.
    for filename2 in ('edgemodes-87edbf67527b/fillet_asymmetric.f3d','edgemodes-87edbf67527b/fillet_chord.f3d'):
        for member,blob in read_members(root/filename2,zstd_library).items():
            if not member.endswith(('.smb','.smbh')):continue
            parsed=inspect_asm(blob);catalog=decode_asm_subtypes(blob,parsed=parsed)
            topology=decode_topology(parsed,subtype_catalog=catalog);before=copy.deepcopy(topology)
            result=decode_vbl_components(blob,parsed=parsed,subtype_catalog=catalog,topology=topology)
            assert not result['decoded'] and not result['unresolved'] and topology==before
            report['old_controls'].append(dict(file=filename2,member=member,no_unrelated_VBL_rows=True,topology_dictionary_unchanged=True))
    blob,parsed,catalog,topology,result=saved
    first=result['decoded'][0]['components'][0]
    def reject(label,action):
        try:action()
        except (ValueError,IndexError,KeyError) as error:
            report['malformed_guards'].append(dict(label=label,rejected=True,reason=str(error)))
        else:raise AssertionError(label+' accepted')
    changed=copy.deepcopy(first['stored_uv_cache']);changed['raw_control_points'][3][0]+=.001
    reject('Perturbed quintic UV coefficient is not knot refinement',lambda:prove_uv_refinement(changed,first['boundary_XYZ_cache']['stored_embedded_uv_cache']))
    changed2=copy.deepcopy(first['stored_uv_cache']);changed2['knots'][8]+=.001
    reject('Inconsistent refined knot vector',lambda:prove_uv_refinement(changed2,first['boundary_XYZ_cache']['stored_embedded_uv_cache']))
    changed3=copy.deepcopy(topology)
    next(n for n in changed3['nodes'] if n['index']==15)['loop_index']=13
    out=decode_vbl_components(blob,parsed=parsed,subtype_catalog=catalog,topology=changed3)
    assert any(r['surface_record_index']==10 for r in out['unresolved'])
    report['malformed_guards'].append(dict(label='Wrong coedge loop owner',rejected=True,reason=next(r['reason'] for r in out['unresolved'] if r['surface_record_index']==10)))
    changed4=copy.deepcopy(topology)
    next(n for n in changed4['nodes'] if n['index']==23)['partner_index']=21
    out=decode_vbl_components(blob,parsed=parsed,subtype_catalog=catalog,topology=changed4)
    assert any(r['surface_record_index']==10 for r in out['unresolved'])
    report['malformed_guards'].append(dict(label='Nonreciprocal partner edge owner',rejected=True,reason=next(r['reason'] for r in out['unresolved'] if r['surface_record_index']==10)))
    wrong=copy.deepcopy(catalog);wrong['source_blob_sha256']='0'*64
    reject('Cross-blob subtype catalog',lambda:decode_vbl_components(blob,parsed=parsed,subtype_catalog=wrong,topology=topology))
    stale=copy.deepcopy(parsed)
    next(r for r in stale['records'] if r['index']==187)['tokens'][3]['value'][0]+=.001
    out=decode_vbl_components(blob,parsed=stale,subtype_catalog=catalog,topology=topology)
    assert any(r['surface_record_index']==10 and 'Stale VBL plane host' in r['reason'] for r in out['unresolved'])
    report['malformed_guards'].append(dict(label='Bracket-free adjacent plane differs from original bytes',rejected=True,
        reason=next(r['reason'] for r in out['unresolved'] if r['surface_record_index']==10)))
    reject('Component parameter outside its stored domain',lambda:evaluate_vbl_component(first,2.))
    values=[c for r in report['samples'] for c in r['component_evaluation_checks']]
    report['validation']=dict(totals,old_control_blobs=len(report['old_controls']),malformed_guards_passed=len(report['malformed_guards']),
        maximum_coefficient_roundoff=max(c['coefficient_proof_maximum_roundoff'] for c in values),
        maximum_sampled_XYZ_cache_deviation=max(c['maximum_sampled_XYZ_cache_deviation'] for c in values),
        maximum_UV_equivalence_roundoff=max(s['maximum_UV_equivalence_error'] for c in values for s in c['samples']),
        no_input_mutation=True,direct_and_passed_topology_outputs_equal=True,
        new_live_API_calls=0,VBL_interior_evaluators=0,existing_VBL_partial_warnings_cleared=0)
    return report
