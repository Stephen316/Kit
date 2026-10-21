"""Focused native BoundaryFill recipes, result naming and typed graph checks."""
import argparse
import copy
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_basics import decode_basics
from decode_boundary_face_correspondences import decode_boundary_face_correspondences
from decode_brep import decode_topology
from fusion_archive import read_members
from fusion_metadata import design_records

EXPECTED = {'component_middle.f3d':6, 'new_first.f3d':6, 'new_middle.f3d':6,
            'new_middle_remove.f3d':6, 'new_two.f3d':6, 'plane_first.f3d':5}


def validate(root, zstd):
    checks, samples, guards, saved = 0, [], [], None
    totals = {'result_FACE_correspondences':0, 'exact_initial_source_FACE_term_matches':0,
              'negative_source_names_without_exact_FACE_matches':0, 'explicit_reordered_two_term_groups':0,
              'unmatched_selected_face_recipes':0, 'unmatched_result_FACE_tags':0}
    files = sorted(root.joinpath('boundaryfills-a0953038318b').glob('*.f3d')) + [
        root/'edgemodes-87edbf67527b/chamfer_angle.f3d', root/'pipeedgecontrasts-5bd287323ae7/circle_full.f3d']

    def check(test, reason):
        nonlocal checks
        if not test:
            raise AssertionError(reason)
        checks += 1

    for filename in files:
        members = read_members(filename,zstd)
        stream = decode_basics(filename,zstd)['streams'][0]
        member = stream['member']; data = members[member]
        records,_ = design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
        mapping = stream['body_asm_identifiers']; before = copy.deepcopy(mapping)
        output = decode_boundary_face_correspondences(data,records,member,members,mapping)
        check(mapping == before, 'existing explicit body mappings unchanged')
        truth = json.loads(filename.parent.joinpath('ground_truth.json').read_text())
        actual = next(s for s in truth['samples']if s['file']==filename.name)
        row = {'file':str(filename.relative_to(root)), 'expected_summary':output}
        if filename.name in EXPECTED:
            check(output['unresolved']==[] and len(output['decoded'])==1, 'captured owned NewBody scope qualifies without failure')
            result, = output['decoded']; links = result['result_FACE_correspondences']
            check(len(links)==EXPECTED[filename.name], 'expected saved face correspondence count')
            context = result['result_body_context']
            check(context['global_initial_generic_naming_complete'], 'global initial naming complete before uniqueness claim')
            blob = members[context['history_blob_member']]
            parsed = inspect_asm(blob); top = decode_topology(parsed)
            graph, = [g for g in top['body_graphs']if g['body_index']==context['initial_ASM_BODY_record_index']]
            nodes = {n['index']:n for n in top['nodes']}
            points = [nodes[nodes[v]['point_index']]['raw_origin']for v in graph['vertex_indices']]
            bounds = {'min_cm':[min(p[k]for p in points)for k in range(3)],
                      'max_cm':[max(p[k]for p in points)for k in range(3)]}
            api, = actual['output_bodies']
            check(all(abs(a-b)<1e-10 for k in ('min_cm','max_cm')for a,b in zip(bounds[k],api['geometry'][k])),
                  'explicit mapped result graph bounds independently match actual saved API output bounds')
            row['API_result_bounds_corroboration'] = {'stored_graph_bounds':bounds, 'actual_API_output':api,
                'scope':'API result bounds corroborate mapped cache scope only; no API persistent face or UV evaluator was captured.'}
            for link in links:
                check(link['result_FACE_naming_tag']['owner_record_index']in graph['face_indices'],
                      'matched result FACE belongs to the explicit reciprocal mapped BODY graph')
                check(link['exact_selected_source_identity']is None and link['persistent_FACE_identity']is None,
                      'stored correspondence does not promote persistent/selected-source identity')
                source_terms = link['face_recipe']['name_table'][0]['terms']
                target_terms = link['result_FACE_naming_tag']['terms']
                order = link['result_term_to_recipe_term_permutation']
                check(sorted(order)==list(range(len(source_terms)))and len(order)==len(target_terms),
                      'entire stored group has a bijection, without omitted or duplicated terms')
                if order != list(range(len(order))):
                    totals['explicit_reordered_two_term_groups'] += 1
                    check(len(order)==2 and order==[1,0] and link['stored_order_is_equal_after_extension']is False,
                          'captured opposite term order is explicit and not relabeled ordered equality')
                for src in link['source_term_contexts']:
                    if src['source_FACE_status']=='UniqueExactStoredSourceTermGroup':
                        totals['exact_initial_source_FACE_term_matches'] += 1
                    elif src['source_FACE_status']=='NoExactStoredSourceTermGroup':
                        term = source_terms[src['recipe_term_ordinal']]
                        check(term['name'].startswith('-')and not src['exact_initial_source_FACE_candidates'],
                              'actual negative naming counterexample remains unmatched, without sign stripping')
                        totals['negative_source_names_without_exact_FACE_matches'] += 1
            totals['result_FACE_correspondences'] += len(links)
            totals['unmatched_selected_face_recipes'] += len(result['unmatched_selected_face_recipes'])
            totals['unmatched_result_FACE_tags'] += len(result['unmatched_result_FACE_naming_tags'])
            if filename.name=='new_two.f3d':
                check(result['selected_face_recipe_count']==12 and len(result['unmatched_selected_face_recipes'])==6,
                      'twelve selected-cell recipes are not forced onto six result faces')
            if filename.name=='plane_first.f3d':
                check(len(result['unmatched_result_FACE_naming_tags'])==1 and result['stored_plane_recipe_object_ids'],
                      'unmatched plane-boundary face and typed plane recipe remain explicit')
            if filename.name=='new_middle_remove.f3d':
                check([x['result_FACE_naming_tag']['attribute_record_index']for x in links]==[29,43,68,117,188,254],
                      'all six previously unsupported component2 FACE tags correspond to actual cell recipes')
                saved = data,records,member,members,mapping,output
        elif filename.parent.name.startswith('boundaryfills-'):
            check(output['decoded']==[]and len(output['unresolved'])==1,
                  'modifying operation without supported owned NewBody anchor stays unsupported')
        else:
            check(output=={'decoded':[],'unresolved':[],'scope':output['scope']},'unrelated features acquire no BoundaryFill correspondences')
        samples.append(row)
    data,records,member,members,mapping,output = saved
    decoded, = output['decoded']; context = decoded['result_body_context']; bm = context['history_blob_member']
    blob = members[bm]; parsed = inspect_asm(blob); primary={r.object_id:r for r in records if r.is_primary}

    def run(label, data2=None, members2=None, mapping2=None, expected_count=0, expect_failure=False):
        result = decode_boundary_face_correspondences(data if data2 is None else data2, records, member,
            members if members2 is None else members2, mapping if mapping2 is None else mapping2)
        count = sum(len(x['result_FACE_correspondences'])for x in result['decoded'])
        check(count==expected_count and (bool(result['unresolved'])if expect_failure else not result['unresolved']),label)
        guards.append({'guard':label,'remaining_qualified_result_FACE_correspondences':count,
            'unresolved':result['unresolved'], 'unmatched_recipe_ids':[r['recipe_object_id']for x in result['decoded']for r in x['unmatched_selected_face_recipes']]})

    recipe = primary[374]
    raw = data[recipe.body:recipe.end]
    pos = raw.index(b'6\0\0\0')
    changed = bytearray(data); changed[recipe.body+pos]=ord('9')
    run('Changed recipe label cannot match the old result FACE',bytes(changed),dict(members,**{member:bytes(changed)}),expected_count=5)
    # Serialized full tuples retain their valid framing, but wrong namespace
    # components or duplicate groups cannot gain a coordinate fallback.
    changed = bytearray(blob); token=parsed['records'][29]['tokens'][16]
    check(token['value']==306,'namespace guard edits actual result extension component')
    struct.pack_into('<q',changed,token['offset']+1,999)
    run('Wrong result namespace component loses that whole FACE group',members2=dict(members,**{bm:bytes(changed)}),expected_count=5)
    changed=bytearray(blob); token=parsed['records'][43]['tokens'][12]
    check(token['value']=='2','duplicate guard edits actual face naming string')
    changed[token['offset']+2]=ord('6')
    run('Duplicate entire result naming groups remain ambiguous',members2=dict(members,**{bm:bytes(changed)}),expected_count=4)
    changed=bytearray(blob); token=parsed['records'][29]['tokens'][6]
    struct.pack_into('<q',changed,token['offset']+1,2)
    run('Malformed global naming blocks every uniqueness claim',members2=dict(members,**{bm:bytes(changed)}),expect_failure=True)
    altered=copy.deepcopy(mapping)
    b=next(b for m in altered['decoded']for b in m['bindings']if b['native_body_object_id']==442)
    b['asm_body_index']=1
    run('Supplied ordinal cannot replace actual stored BODY-handle mapping',mapping2=altered,expect_failure=True)
    changed=bytearray(data); anchor=primary[446]
    struct.pack_into('<Q',changed,anchor.body+81,275)
    run('Result anchor retargeted onto source namespace is rejected',bytes(changed),dict(members,**{member:bytes(changed)}),expect_failure=True)
    return {'stage':'BoundaryFill selected face recipe and result-cache naming correspondence',
        'interface':'decode_boundary_face_correspondences(data, records, member, members, body_identifier_summary) -> decoded/unresolved/scope',
        'integration':'Separate late summary after body identifier recovery. Requires complete shared generic naming (counted payload framing plus reciprocal owner chains, allow_fpm_tracking=True BODY/EDGE admission). Do not clear generic or exact selected-source/lifecycle errors based on this cache correspondence.',
        'validation':{'checks':checks,'saved_files':len(files),'supported_BoundaryFill_cases':len(EXPECTED),**totals,
                      'malformed_guards':guards,'new_API_calls':0,'API_persistent_face_or_surface_evaluator_getters_captured':False},
        'findings':['All six previously unframed result FACE tags in the removal case map to stored selected-cell recipes only after independent result BODY namespace qualification.',
            'The stored face recipe does not contain the full result tag: every recipe component list is extended by the explicitly mapped result BODY naming component. Source tools are independently bound through body recipes, typed descriptors/anchors and native stored-handle mappings.',
            'Full two-term groups can occur in opposite order. Both orders and their explicit unique term permutation are preserved; matching one term never qualifies a face.',
            'Two negative recipe names have no exact initial source FACE match. Their result naming correspondences do not turn them into the positive source faces.',
            'Six selected recipes remain unmatched in the two-cell case, and one result face remains unmatched by body-face recipes in the plane case. Neither receives an inferred interior/plane/persistent identity.'],
        'limitations':['Stored naming correspondence is not persistent FACE identity, exact selected-source reconstruction, Boolean regeneration or a current/final lifecycle classifier.',
            'The result-BODY component extension is bounded to the observed single-owned-NewBody result, one/two-term face recipes and explicit selected body-tool namespaces. Modifying result cases remain unsupported.',
            'Plane-cell recipe evaluation and negative-name surface orientation semantics are unresolved.',
            'Saved API output bounds corroborate overall result geometry only; no API face identity or UV evaluator is used to choose matches.'],
        'samples':samples}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--zstd-library',type=Path,required=True)
    p.add_argument('--report',type=Path)
    args=p.parse_args(); result=validate(args.root,args.zstd_library)
    (args.report or args.root/'boundary-face-correspondence-decoding.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['validation'],indent=2))
