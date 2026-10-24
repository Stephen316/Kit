"""Qualified native BoundaryFill face recipes and stored result naming charts.

The saved recipe's entire term group must match a result FACE's entire term
group after a literal result-BODY naming extension. Native body/anchor/mapping
routes qualify the two naming contexts; no geometry or numeric ID guess does.
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
from decode_recipe_components import decode_counted_recipe

SCOPE = ('Observed complete BoundaryFill cell face-recipe term-group correspondence to an explicitly '
         'mapped feature-owned NewBody result FACE naming group, with literal result-BODY component '
         'extension and retained term permutation; no persistent face identity or lifecycle inference.')


def _key(terms):
    return _terms_key(terms)


def _body_component(tag):
    terms = tag['terms']
    if len(terms) != 1 or terms[0]['stored_reference_component_count'] != 0:
        raise ValueError('Boundary face BODY namespace is not one component-free naming term')
    name = terms[0]['name']
    if not name.isascii() or not name.isdecimal() or not 1 <= int(name) <= 0x7fffffff or str(int(name)) != name:
        raise ValueError('Boundary face BODY namespace name is not a canonical positive component literal')
    return int(name)


def decode_boundary_face_correspondences(data, records, member, members, body_identifier_summary):
    """Return decoded/unresolved/scope; native source/result identities stay scoped.

    Requires the shared complete generic-tag reader with counted component2 and
    initial BODY FPM admission. Unmatched recipes/faces and negative names remain
    explicit; names are never stripped, sign-normalized or matched by position.
    """
    out = {'decoded': [], 'unresolved': [], 'scope': SCOPE}
    grouped = {}
    for rec in records:
        if rec.is_primary:
            grouped.setdefault(rec.object_id, []).append(rec)
    primary = {i: rows[0] for i, rows in grouped.items() if len(rows) == 1}
    candidates = [r for r in primary.values() if r.class_guid == BOUNDARY_FILL_GUID]
    if not candidates:
        return out
    if member not in members or members[member] != data or not member.endswith('/FusionDesignSegmentType1/BulkStream.dat'):
        out['unresolved'].append({'reason': 'Boundary face Design member/bytes scope disagrees'})
        return out
    mappings = decode_body_asm_identifiers(data, records, member, members, body_identifier_summary)
    selections = decode_body_selections(data, records)
    native_results = decode_boundary_fill_results(data, records)
    by_feature = {r['feature_object_id']: r for r in native_results['decoded']}
    cache = {}

    def body_context(identity):
        choices = [(m, b) for m in mappings['decoded'] for b in m['bindings'] if b['native_body_object_id'] == identity]
        if len(choices) != 1:
            raise ValueError('Boundary face native BODY lacks one validated same-asset mapping')
        mapping, binding = choices[0]
        supplied = [b for m in body_identifier_summary['decoded'] if m['mapping_record_object_id'] == mapping['mapping_record_object_id']
                    for b in m['bindings'] if b['native_body_object_id'] == identity]
        if len(supplied) != 1 or supplied[0]['asm_body_index'] != binding['asm_body_index']:
            raise ValueError('Boundary face supplied ASM BODY identity disagrees with stored handle mapping')
        blob_member = mapping['history_blob_member']
        if blob_member not in cache:
            blob = members[blob_member]
            parsed = inspect_asm(blob)
            tags = decode_asm_generic_tags(blob, parsed=parsed, allow_fpm_tracking=True)
            if tags['unresolved']:
                raise ValueError('Boundary face requires complete initial generic naming coverage: '+str(tags['unresolved']))
            topology = decode_topology(parsed)
            cache[blob_member] = parsed, tags, topology
        parsed, tags, topology = cache[blob_member]
        graphs = [g for g in topology['body_graphs'] if g['body_index'] == binding['asm_body_index']]
        if len(graphs) != 1:
            raise ValueError('Boundary face explicitly mapped BODY lacks one complete reciprocal graph')
        graph = graphs[0]
        body_tags = [t for t in tags['tags'] if t['owner_kind'] == 'body' and t['owner_record_index'] == graph['body_index']]
        if len(body_tags) != 1:
            raise ValueError('Boundary face mapped BODY naming tag missing/ambiguous')
        face_tags = [t for t in tags['tags'] if t['owner_kind'] == 'face' and t['owner_record_index'] in graph['face_indices']]
        if (len(face_tags) != len(graph['face_indices'])
                or {t['owner_record_index'] for t in face_tags} != set(graph['face_indices'])):
            raise ValueError('Boundary face graph lacks exactly one validated naming group per FACE')
        return {'native_body_object_id': identity, 'mapping_record_object_id': mapping['mapping_record_object_id'],
            'mapping_collection_object_id': mapping['owner_object_id'], 'history_blob_member': blob_member,
            'stored_native_handle': binding['stored_handle'], 'initial_ASM_BODY_record_index': graph['body_index'],
            'BODY_naming_tag': body_tags[0], 'stored_BODY_naming_component': _body_component(body_tags[0]),
            'BODY_naming_component_scope': 'Decimal name literal of an explicitly mapped BODY naming namespace; not a native Design ID, ASM record index or stored handle',
            'FACE_naming_tags': face_tags, 'reciprocal_BODY_graph_counts': graph['counts'],
            'global_initial_generic_tag_count': len(tags['tags']), 'global_initial_generic_naming_complete': True}

    def recipe(identity, kind):
        rec = primary.get(identity)
        if rec is None or rec.class_guid != '7ACC2A03-0261-4879-A14A-A93D661A5BDC':
            raise ValueError('Boundary face typed counted recipe missing/ambiguous')
        value = decode_counted_recipe(data, rec)
        if (value['payload_kind'] != kind or value['payload_hex'] != '00000000ffffffff'
                or len(value['name_table']) != 1 or value['name_table'][0]['table_index'] != 0
                or len(value['name_table'][0]['terms']) not in (1, 2)):
            raise ValueError('Unobserved Boundary face/body recipe framing')
        return value

    for rec in candidates:
        try:
            feature = {'object_id': rec.object_id, 'class_guid': rec.class_guid}
            controls = decode_boundary_fill(data, records, data[rec.body:rec.end], feature)
            native_result = by_feature.get(rec.object_id)
            if native_result is None or controls['operation'] != 'NewBody' or len(native_result['owned_result_bodies']) != 1:
                raise ValueError('Boundary face correspondence requires one independently owned NewBody result anchor')
            owned_result = native_result['owned_result_bodies'][0]
            result = body_context(owned_result['native_body_object_id'])
            result_component = result['stored_BODY_naming_component']
            tools = []
            for tool in native_result['historical_body_tools']:
                descriptors = [d for d in selections['body_descriptors'] if d['object_id'] == tool['descriptor_object_id']]
                if len(descriptors) != 1 or descriptors[0]['owner_object_id'] != rec.object_id:
                    raise ValueError('Boundary face tool descriptor is not uniquely owned by feature')
                descriptor = descriptors[0]
                context = body_context(tool['native_body_object_id'])
                body_recipe = recipe(descriptor['recipe_record_object_id'], 'body_recipe_data')
                if _key(body_recipe['name_table'][0]['terms']) != _key(context['BODY_naming_tag']['terms']):
                    raise ValueError('Boundary face selected tool body recipe differs from explicitly mapped BODY name')
                tools.append({'explicit_native_tool': tool, 'body_context': context, 'body_recipe': body_recipe})
            if result_component in {t['body_context']['stored_BODY_naming_component'] for t in tools}:
                raise ValueError('Boundary face result naming namespace collides with a selected tool BODY namespace')
            if len({t['body_context']['stored_BODY_naming_component'] for t in tools}) != len(tools):
                raise ValueError('Boundary face selected tool naming components ambiguous')
            recipes = []
            for cell in controls['selected_cells']:
                for ref in cell['face_recipes']:
                    value = recipe(ref['object_id'], 'face_recipe_data')
                    terms = value['name_table'][0]['terms']
                    contexts = []
                    for term in terms:
                        if term['stored_reference_component_count'] != 1 or term['stored_index'] != 0:
                            raise ValueError('Unobserved Boundary face source recipe component/index layout')
                        component, = term['stored_reference_components_int32']
                        candidates_for_term = [t for t in tools if t['body_context']['stored_BODY_naming_component'] == component]
                        if len(candidates_for_term) != 1:
                            raise ValueError('Boundary face recipe namespace does not identify one independently selected tool BODY')
                        context = candidates_for_term[0]['body_context']
                        source_faces = [t for t in context['FACE_naming_tags'] if _key(t['terms']) == _key([term])]
                        contexts.append({'recipe_term_ordinal': len(contexts), 'native_source_tool_body_object_id': context['native_body_object_id'],
                            'source_BODY_naming_component': component, 'source_history_blob_member': context['history_blob_member'],
                            'source_ASM_BODY_record_index': context['initial_ASM_BODY_record_index'],
                            'exact_initial_source_FACE_candidates': source_faces,
                            'source_FACE_status': 'UniqueExactStoredSourceTermGroup' if len(source_faces) == 1 else
                                'NoExactStoredSourceTermGroup' if not source_faces else 'AmbiguousExactStoredSourceTermGroup',
                            'scope': 'Literal source naming only; negative names remain distinct and are not converted to positive source faces'})
                    extended = [(t['name'], t['stored_index'], tuple(t['stored_reference_components_int32']+[result_component])) for t in terms]
                    recipes.append({'selected_cell_object_id': cell['object_id'], 'stored_cell_key': cell['stored_cell_key'],
                        'face_recipe': value, 'source_term_contexts': contexts, 'expected_extended_term_keys': extended})
            candidate_rows = []
            for tag in result['FACE_naming_tags']:
                target = _key(tag['terms'])
                matches = []
                for i, r in enumerate(recipes):
                    expected = r['expected_extended_term_keys']
                    if len(expected) != len(target):
                        continue
                    orders = [list(p) for p in permutations(range(len(expected)))
                              if tuple(expected[j] for j in p) == target]
                    if len(orders) == 1:
                        matches.append({'recipe_ordinal': i, 'result_term_to_recipe_term_permutation': orders[0]})
                candidate_rows.append({'result_FACE_naming_tag': tag, 'complete_group_candidates': matches})
            associations, unmatched_faces, unresolved_recipes = [], [], []
            use_count = {i: sum(any(m['recipe_ordinal'] == i for m in row['complete_group_candidates']) for row in candidate_rows) for i in range(len(recipes))}
            used = set()
            for row in candidate_rows:
                matches = row['complete_group_candidates']
                if len(matches) != 1 or use_count[matches[0]['recipe_ordinal']] != 1:
                    unmatched_faces.append(dict(row, reason='No unique entire selected recipe group after qualified result-BODY extension'))
                    continue
                match, = matches
                i = match['recipe_ordinal']; used.add(i)
                associations.append({'selected_cell_object_id': recipes[i]['selected_cell_object_id'],
                    'stored_cell_key': recipes[i]['stored_cell_key'], 'face_recipe': recipes[i]['face_recipe'],
                    'source_term_contexts': recipes[i]['source_term_contexts'], 'result_FACE_naming_tag': row['result_FACE_naming_tag'],
                    'result_term_to_recipe_term_permutation': match['result_term_to_recipe_term_permutation'],
                    'stored_order_is_equal_after_extension': match['result_term_to_recipe_term_permutation'] == list(range(len(match['result_term_to_recipe_term_permutation']))),
                    'correspondence_status': 'UniqueCompleteTermGroupBijectionAfterExplicitResultBODYNamingExtension',
                    'exact_selected_source_identity': None, 'persistent_FACE_identity': None,
                    'scope': 'Stored selected-cell recipe and result-cache naming correspondence only; entire group retained, no single-term fallback'})
            for i, r in enumerate(recipes):
                if i not in used:
                    unresolved_recipes.append({'selected_cell_object_id': r['selected_cell_object_id'],
                        'recipe_object_id': r['face_recipe']['object_id'], 'face_recipe': r['face_recipe'],
                        'reason': 'No unique complete result FACE group for this stored selected-cell recipe; no interior/final/lifecycle interpretation'})
            out['decoded'].append({'feature_object_id': rec.object_id, 'owned_result_anchor': owned_result,
                'result_body_context': result, 'historical_body_tool_contexts': tools,
                'selected_cell_count': len(controls['selected_cells']), 'selected_face_recipe_count': len(recipes),
                'result_FACE_correspondences': associations, 'unmatched_selected_face_recipes': unresolved_recipes,
                'unmatched_result_FACE_naming_tags': unmatched_faces,
                'stored_plane_recipe_object_ids': [p['object_id'] for c in controls['selected_cells'] for p in c['plane_recipes']],
                'normalization_rule': 'Append the independently mapped result BODY naming component to every stored source term; compare the complete term group with explicit unique permutation.',
                'scope': SCOPE})
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            out['unresolved'].append({'feature_object_id': rec.object_id, 'reason': str(error)})
    return out
