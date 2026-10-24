"""Stored BoundaryFill modifying-result face naming, qualified by native registry.

Result selection identities remain historical native BODY identities. A feature
naming key comes from the reciprocal native registry, never from a guessed new
BODY name. Complete face groups are compared without selecting one term.
"""
from itertools import permutations
import struct

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags, _terms_key
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_selections import decode_body_selections
from decode_boundary_fill import BOUNDARY_FILL_GUID, decode_boundary_fill
from decode_boundary_fill_results import decode_boundary_fill_results
from decode_brep import decode_topology
from decode_native_naming_registry import decode_native_naming_registry
from decode_recipe_components import decode_counted_recipe

SCOPE = ('Observed BoundaryFill Join/Cut/Intersect result selection, typed native BODY/history-blob association '
         'and complete stored face-name groups qualified through reciprocal native feature naming-key ownership. '
         'Persistent face identity, Boolean regeneration and current/final body lifecycle remain unresolved.')


def _permutation(expected,stored):
    if len(expected)!=len(stored):
        return None
    matches=[list(p)for p in permutations(range(len(expected)))if tuple(expected[i]for i in p)==tuple(stored)]
    return matches[0]if len(matches)==1 else None


def decode_boundary_modifying_faces(data,records,member,members,body_identifier_summary):
    """Return decoded/unresolved/scope; no original source is changed."""
    out={'decoded':[],'unresolved':[],'scope':SCOPE}
    grouped={}
    for rec in records:
        if rec.is_primary:
            grouped.setdefault(rec.object_id,[]).append(rec)
    primary={i:rs[0]for i,rs in grouped.items()if len(rs)==1}
    features=[r for r in primary.values()if r.class_guid==BOUNDARY_FILL_GUID]
    if not features:
        return out
    if member not in members or members[member]!=data or not member.endswith('/FusionDesignSegmentType1/BulkStream.dat'):
        out['unresolved'].append({'reason':'Boundary modifying face same-asset Design bytes disagree'})
        return out
    registry=decode_native_naming_registry(data,records)
    mappings=decode_body_asm_identifiers(data,records,member,members,body_identifier_summary)
    native=decode_boundary_fill_results(data,records)
    selections=decode_body_selections(data,records)
    descriptors={d['object_id']:d for d in selections['body_descriptors']}
    cache={}

    def context(identity):
        choices=[(m,b)for m in mappings['decoded']for b in m['bindings']if b['native_body_object_id']==identity]
        if len(choices)!=1:
            raise ValueError('Boundary modifying BODY has no unique explicit same-asset mapping')
        mapping,binding=choices[0]
        supplied=[b for m in body_identifier_summary['decoded']if m['mapping_record_object_id']==mapping['mapping_record_object_id']
                  for b in m['bindings']if b['native_body_object_id']==identity]
        if len(supplied)!=1 or supplied[0]['asm_body_index']!=binding['asm_body_index']:
            raise ValueError('Boundary modifying supplied BODY index disagrees with actual stored handle')
        bm=mapping['history_blob_member']
        if bm not in cache:
            parsed=inspect_asm(members[bm])
            names=decode_asm_generic_tags(members[bm],parsed=parsed,allow_fpm_tracking=True)
            if names['unresolved']:
                raise ValueError('Boundary modifying names lack complete initial attribute coverage')
            top=decode_topology(parsed)
            cache[bm]=names,top
        names,top=cache[bm]
        graphs=[g for g in top['body_graphs']if g['body_index']==binding['asm_body_index']]
        if len(graphs)!=1:
            raise ValueError('Boundary modifying mapped BODY reciprocal graph unresolved')
        graph,=graphs
        body_names=[t for t in names['tags']if t['owner_kind']=='body'and t['owner_record_index']==graph['body_index']]
        face_names=[t for t in names['tags']if t['owner_kind']=='face'and t['owner_record_index']in graph['face_indices']]
        if (len(body_names)!=1 or len(face_names)!=len(graph['face_indices'])
                or {t['owner_record_index']for t in face_names}!=set(graph['face_indices'])):
            raise ValueError('Boundary modifying BODY/FACE naming groups incomplete or duplicated')
        return {'native_body_object_id':identity,'mapping_record_object_id':mapping['mapping_record_object_id'],
            'history_blob_member':bm,'stored_native_handle':binding['stored_handle'],'initial_ASM_BODY_record_index':graph['body_index'],
            'BODY_naming_tag':body_names[0],'FACE_naming_tags':face_names,'reciprocal_graph_counts':graph['counts'],
            'scope':'Explicit selected native BODY maps to this stored initial graph; no current/final lifecycle classification.'}

    def recipe(identity,kind):
        rec=primary.get(identity)
        if rec is None or rec.class_guid!='7ACC2A03-0261-4879-A14A-A93D661A5BDC':
            raise ValueError('Boundary modifying counted recipe missing or wrong typed class')
        r=decode_counted_recipe(data,rec)
        if (r['payload_kind']!=kind or r['payload_hex']!='00000000ffffffff'or len(r['name_table'])!=1
                or r['name_table'][0]['table_index']!=0 or len(r['name_table'][0]['terms'])!=1):
            raise ValueError('Unobserved modifying BoundaryFill single-term recipe layout')
        return r

    for feature in features:
        try:
            controls=decode_boundary_fill(data,records,data[feature.body:feature.end],{'object_id':feature.object_id,'class_guid':feature.class_guid})
            if controls['operation']=='NewBody':
                continue
            if (controls['operation']not in('Join','Cut','Intersect')or len(controls['selected_cells'])!=1
                    or controls['plane_tool_count'] or controls['body_tool_count']!=2):
                raise ValueError('Unobserved modifying BoundaryFill operation/cell/tool layout')
            explicit=[r for r in native['decoded']if r['feature_object_id']==feature.object_id]
            if len(explicit)!=1 or explicit[0]['owned_result_bodies']or not explicit[0]['result_selection_bodies']:
                raise ValueError('Boundary modifying result lacks its explicit descriptor/anchor selection')
            explicit,=explicit
            registries=[r for r in registry['decoded']if any(o['native_owner_object_id']==feature.object_id for o in r['owner_to_keys'])]
            if len(registries)!=1:
                raise ValueError('Boundary modifying feature has no unique reciprocal naming registry')
            reg,=registries
            owner,=[o for o in reg['owner_to_keys']if o['native_owner_object_id']==feature.object_id]
            if owner['native_owner_class_guid']!=BOUNDARY_FILL_GUID or len(owner['naming_keys'])!=1:
                raise ValueError('Unobserved BoundaryFill feature naming-key layout')
            feature_key,=owner['naming_keys']
            keys={r['naming_key']:r for r in reg['key_to_owner']}
            tools=[]
            for tool in explicit['historical_body_tools']:
                desc=descriptors[tool['descriptor_object_id']]
                ctx=context(tool['native_body_object_id']);body_recipe=recipe(desc['recipe_record_object_id'],'body_recipe_data')
                term,=body_recipe['name_table'][0]['terms']
                if (not term['name'].isascii()or not term['name'].isdecimal()or term['stored_index']!=7
                        or term['stored_reference_component_count']!=0 or str(int(term['name']))!=term['name']):
                    raise ValueError('Unobserved Boundary modifying source BODY namespace term')
                component=int(term['name'])
                if component not in keys or keys[component]['native_owner_object_id']!=desc['source_owner_object_id']:
                    raise ValueError('Source BODY naming key does not belong to its independently typed source owner')
                base=list(_terms_key([term]));extended=base+[(str(feature_key),1,())]
                actual=_terms_key(ctx['BODY_naming_tag']['terms'])
                form='ExactToolBodyRecipeGroup'if _permutation(base,actual)is not None else (
                    'ToolBodyRecipePlusRegistryFeatureKeyGroup'if _permutation(extended,actual)is not None else None)
                if form is None:
                    raise ValueError('Mapped source BODY entire naming group disagrees with source recipe/owned feature key')
                tools.append({'native_tool_selection':tool,'body_descriptor':desc,'body_recipe':body_recipe,
                    'source_naming_component':component,'source_registry_key_owner':keys[component],
                    'BODY_name_group_status':form,'body_context':ctx})
            if len({t['source_naming_component']for t in tools})!=len(tools):
                raise ValueError('Boundary modifying tool naming components ambiguous')
            cell,=controls['selected_cells'];recipes=[]
            for rr in cell['face_recipes']:
                r=recipe(rr['object_id'],'face_recipe_data');term,=r['name_table'][0]['terms']
                if term['stored_index']!=0 or term['stored_reference_component_count']!=1:
                    raise ValueError('Unobserved modifying BoundaryFill face namespace layout')
                component,=term['stored_reference_components_int32']
                source=[t for t in tools if t['source_naming_component']==component]
                if len(source)!=1:
                    raise ValueError('Boundary modifying face recipe lacks a selected typed source BODY namespace')
                base=list(_terms_key([term]));extension=[(term['name'],term['stored_index'],tuple(term['stored_reference_components_int32']+[feature_key]))]
                recipes.append({'recipe':r,'source_tool_native_body_object_id':source[0]['native_tool_selection']['native_body_object_id'],
                    'forms':{'ExactEntireRecipeGroup':base,'EntireRecipeWithRegistryFeatureKeyExtension':extension,
                             'EntireRecipePlusFeatureExtendedRecipeGroup':base+extension}})
            result_rows=[];matches=[]
            for selected in explicit['result_selection_bodies']:
                desc=descriptors[selected['descriptor_object_id']]
                tool=[t for t in tools if t['native_tool_selection']['native_body_object_id']==selected['native_body_object_id']]
                if len(tool)!=1 or selected['body_anchor_object_id']!=tool[0]['native_tool_selection']['body_anchor_object_id']:
                    raise ValueError('Modifying result descriptor does not return to the independently selected tool anchor')
                result_recipe=recipe(desc['recipe_record_object_id'],'body_recipe_data')
                if result_recipe['name_table']!=tool[0]['body_recipe']['name_table']:
                    raise ValueError('Modifying result and tool BODY recipe namespaces differ')
                ctx=tool[0]['body_context'];candidates=[]
                for tag in ctx['FACE_naming_tags']:
                    found=[];actual=_terms_key(tag['terms'])
                    for i,r in enumerate(recipes):
                        for form,expected in r['forms'].items():
                            order=_permutation(expected,actual)
                            if order is not None:
                                found.append({'recipe_ordinal':i,'naming_group_form':form,'stored_term_to_expected_term_permutation':order})
                    candidates.append({'result_FACE_naming_tag':tag,'candidates':found})
                    for found_match in found:
                        matches.append((selected['native_body_object_id'],tag['owner_record_index'],found_match['recipe_ordinal']))
                result_rows.append({'explicit_modifying_result_selection':selected,'result_body_descriptor':desc,'result_body_recipe':result_recipe,
                    'body_context':ctx,'FACE_candidate_groups':candidates})
            associations=[];used=set()
            for row in result_rows:
                for candidate in row['FACE_candidate_groups']:
                    if len(candidate['candidates'])!=1:
                        continue
                    match,=candidate['candidates'];i=match['recipe_ordinal']
                    if sum(j==i for _,_,j in matches)!=1:
                        continue
                    used.add(i)
                    associations.append({'face_recipe':recipes[i]['recipe'],'selected_cell_object_id':cell['object_id'],'stored_cell_key':cell['stored_cell_key'],
                        'result_selection':row['explicit_modifying_result_selection'],'result_FACE_naming_tag':candidate['result_FACE_naming_tag'],
                        'naming_group_form':match['naming_group_form'], 'stored_term_to_expected_term_permutation':match['stored_term_to_expected_term_permutation'],
                        'source_tool_native_body_object_id':recipes[i]['source_tool_native_body_object_id'],
                        'registry_object_id':reg['object_id'],'feature_naming_key':feature_key,
                        'exact_selected_source_identity':None,'persistent_FACE_identity':None,
                        'scope':'Unique complete naming-group correspondence in an explicitly selected mapped BODY cache; historical source and current lifecycle remain unqualified.'})
            associated={(a['result_selection']['native_body_object_id'],a['result_FACE_naming_tag']['owner_record_index'])for a in associations}
            for row in result_rows:
                row['unmatched_result_FACE_groups']=[r for r in row.pop('FACE_candidate_groups')
                    if(row['explicit_modifying_result_selection']['native_body_object_id'],r['result_FACE_naming_tag']['owner_record_index'])not in associated]
            out['decoded'].append({'feature_object_id':feature.object_id,'operation':controls['operation'],
                'native_feature_key_owner':owner,'registry_object_id':reg['object_id'],'registry_container_object_id':reg['registry_container_object_id'],
                'feature_naming_key':feature_key,'historical_body_tool_contexts':tools,'explicit_modifying_results':result_rows,
                'result_FACE_correspondences':associations,
                'unmatched_selected_face_recipes':[{'face_recipe':r['recipe'],'reason':'No unique complete group in the explicitly selected result BODY caches; no sign stripping or lifecycle interpretation'}for i,r in enumerate(recipes)if i not in used],
                'scope':SCOPE})
        except(ValueError,KeyError,IndexError,UnicodeError,struct.error)as error:
            out['unresolved'].append({'feature_object_id':feature.object_id,'reason':str(error)})
    return out
