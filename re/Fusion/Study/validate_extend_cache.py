"""Focused saved-file evidence for the literal Extend quad cache view."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_asm_history import decode_asm_history
from decode_asm_recipe_tags import decode_asm_generic_tags, match_recipe_tag_names
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_bindings import decode_body_bindings
from decode_brep import decode_topology
from decode_extend_edge_sources import EXTEND, decode_extend_edge_operands
from decode_recipe_components import decode_counted_recipe
from decode_selection_context_recipes import TOPOLOGY
from decode_sketch import reference
from fusion_archive import read_members
from fusion_metadata import design_records
from materialize_asm_literal_view import materialize_asm_literal_view
from materialize_extend_cache import materialize_extend_cache, SCOPE, COUNTS

ROOT = Path(__file__).resolve().parent
FILES = tuple('surfacebounds-ac801bb00fae/extend_'+name+'.f3d' for name in
    ('natural', 'tangent', 'perpendicular', 'perpendicular_negative', 'aligned', 'two_edges')) + (
    'surfacebounds-8804bbf80755/extend_no_chain.f3d',)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate(zstd):
    checks, guards, samples = [], [], []
    recipe_count = 0
    fixture = None

    def check(label, value):
        if not value:
            raise AssertionError(label)
        checks.append(label)

    for filename in FILES:
        members = read_members(ROOT/filename, zstd)
        member = next(n for n in members if n.endswith('/FusionDesignSegmentType1/BulkStream.dat'))
        data = members[member]
        records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
        primary = {r.object_id: r for r in records if r.is_primary}
        minimal = dict(streams=[dict(member=n, complete_token_stream=True, declared_root_records=[])
            for n in members if n.endswith('.smbh')])
        native = decode_body_bindings(data, records, member, minimal)
        mapped = decode_body_asm_identifiers(data, records, member, members, native)
        check(filename+' fresh explicit native mapping', not mapped['unresolved'] and len(mapped['decoded']) == 1)
        mapping = mapped['decoded'][0]
        check(filename+' singleton mapped source BODY', mapping['body_count'] == 1 and len(mapping['bindings']) == 1)
        binding = mapping['bindings'][0]
        blob_member = mapping['history_blob_member']
        blob = members[blob_member]
        parsed = inspect_asm(blob)
        frozen = copy.deepcopy(parsed)
        history = decode_asm_history(blob, parsed=parsed)
        initial_topology = decode_topology(parsed)
        initial_tags = decode_asm_generic_tags(blob, parsed, allow_fpm_tracking=True)
        view = materialize_extend_cache(blob, initial_body_record_index=binding['asm_body_index'],
            stored_body_identifier=binding['stored_handle'], parsed=parsed, history=history)
        literal = materialize_asm_literal_view(blob, parsed=parsed, history=history)
        check(filename+' exact neutral factory output reused', all(view[k] == v for k, v in literal.items() if k != 'scope'))
        check(filename+' all literal journal states retained', view['canonical_history'] == history
            and history['neighbor_chain'] == [0, 2, 4, 5, 3, 1])
        check(filename+' exact independently mapped stored BODY identifier',
            view['initial_body_record_index'] == binding['asm_body_index']
            and view['stored_body_identifier'] == binding['stored_handle']
            and view['qualified_dangling_pointer_count'] == 0)
        table = history['geometry_entities']
        entities = [parsed['records'][row['inspection_record_index']] for row in table]
        origins = {r['view_record_index']: r for r in view['origin_map']}
        aliases = {r['side1_entity_ordinal']: r['side0_entity_ordinal'] for r in view['literal_pair_aliases']}
        chosen = view['selected_geometry_entity_ordinals']
        dense = {v: i for i, v in enumerate(chosen)}
        replayed = []
        for row in view['view_parsed']['records']:
            original = entities[origins[row['index']]['geometry_entity_ordinal']]
            expected = copy.deepcopy(original)
            expected['index'] = row['index']
            expected['section'] = 'geometry'
            for token in expected['tokens']:
                if token['tag'] == 12 and token['value'] != -1:
                    token['value'] = dense[aliases.get(token['value'], token['value'])]
            replayed.append(row == expected)
        check(filename+' every view record differs only in explicit dense indices and pointers', all(replayed))
        check(filename+' every raw pointer byte replay exact', all(blob[r['token_offset']] == 12
            and struct.unpack_from('<q', blob, r['token_offset']+1)[0] == r['stored_target_geometry_entity_ordinal']
            for r in view['rewritten_pointer_evidence']))
        check(filename+' initial ordinal/global index/trailing index remain distinct',
            origins[view['qualified_body_view_record_index']] == view['qualified_body_origin']
            and aliases[view['initial_body_geometry_ordinal']] == view['qualified_body_origin']['geometry_entity_ordinal']
            and view['qualified_body_origin']['inspection_record_index'] != view['qualified_body_origin']['geometry_entity_ordinal'])
        topology = view['topology']
        nodes = {n['index']: n for n in topology['nodes']}
        graph = next(g for g in topology['body_graphs'] if g['body_index'] == view['qualified_body_view_record_index'])
        check(filename+' all three BODY graphs complete and selected quad topology qualified',
            not topology['unresolved'] and len(topology['body_graphs']) == 3
            and graph['counts'] == COUNTS and graph['surface_record_types'] == {'plane-surface': 1})
        consistency = view['derived_stored_geometry_consistency']
        check(filename+' after-identity line endpoints/plane/cycle consistent',
            consistency['finite_nondegenerate_line_domains'] and consistency['coplanar_with_qualified_plane']
            and consistency['typed_domain_endpoints_consistent'] and consistency['closed_four_vertex_cycle'])
        named_operands = []
        descriptors = [r for r in records if r.is_primary and r.class_guid == TOPOLOGY and r.end-r.body == 276
            and primary.get(reference(data[r.body:r.end], 265)) is not None
            and primary[reference(data[r.body:r.end], 265)].class_guid == EXTEND]
        check(filename+' one or two owned Extend descriptors', len(descriptors) == (2 if filename.endswith('/extend_two_edges.f3d') else 1))
        for descriptor in descriptors:
            body = data[descriptor.body:descriptor.end]
            recipe = decode_counted_recipe(data, primary[reference(body, 4)])
            operands = decode_extend_edge_operands(recipe)
            naming = match_recipe_tag_names(recipe, view['view_tag_summary'], parsed=view['view_parsed'])
            check(filename+' descriptor '+str(descriptor.object_id)+' complete names unique',
                [n['candidate_count'] for n in naming['name_entries']] == [1, 1, 1, 1])
            candidates = [n['candidates'][0] for n in naming['name_entries']]
            check(filename+' descriptor '+str(descriptor.object_id)+' four typed names on mapped BODY',
                [c['owner_kind'] for c in candidates] == ['edge', 'face', 'edge', 'edge']
                and all(c['body_graph_membership'] == [graph['body_index']] for c in candidates))
            selected = nodes[candidates[0]['owner_record_index']]
            face_id = candidates[1]['owner_record_index']
            operand_proofs = []
            for operand, vertex_key in zip(operands['endpoint_operands'], ('start_vertex_index', 'end_vertex_index')):
                edge_ids = [candidates[n['name_table_index']]['owner_record_index'] for n in operand['nested_edges']]
                shared = set.intersection(*(set((nodes[e]['start_vertex_index'], nodes[e]['end_vertex_index'])) for e in edge_ids))
                check(filename+' descriptor '+str(descriptor.object_id)+' exact endpoint intersection '+vertex_key,
                    shared == {selected[vertex_key]})
                edge_coedges = [[nodes[c] for c in graph['coedge_indices'] if nodes[c]['edge_index'] == e] for e in edge_ids]
                check(filename+' descriptor '+str(descriptor.object_id)+' named endpoint edges share selected face loop '+vertex_key,
                    all(len(rows) == 1 and nodes[rows[0]['loop_index']]['face_index'] == face_id for rows in edge_coedges))
                operand_proofs.append(dict(operand=operand, edge_view_record_indices=edge_ids,
                    exact_common_vertex_view_record_index=selected[vertex_key],
                    native_inline_order_preserved=True, selected_stored_endpoint_field=vertex_key))
            named_operands.append(dict(descriptor_object_id=descriptor.object_id,
                receiving_feature_object_id=reference(body, 265), recipe_object_id=recipe['object_id'],
                full_operation=operands, complete_name_correspondence=naming,
                selected_edge_origin=origins[selected['index']], selected_face_origin=origins[face_id],
                endpoint_intersections=operand_proofs,
                scope='Complete native recipe names and reciprocal typed cache incidence; API handles, chronology and geometry before Extend are not assigned'))
            recipe_count += 1
        check(filename+' canonical parse/topology/naming remain unchanged', parsed == frozen
            and initial_topology == decode_topology(parsed)
            and initial_tags == decode_asm_generic_tags(blob, parsed, allow_fpm_tracking=True))
        truth_path = (ROOT/filename).parent/'ground_truth.json'
        truth = json.loads(truth_path.read_text())
        actual = next(s for s in truth['samples'] if s['file'] == Path(filename).name)
        samples.append(dict(archive=filename, archive_sha256=sha(ROOT/filename), member=blob_member,
            blob_sha256=hashlib.sha256(blob).hexdigest(), native_source_mapping=mapping,
            expected_provenance={k: v for k, v in view.items() if k not in ('view_parsed', 'topology')},
            expected_topology=topology,
            expected_view_record_token_sha256=[dict(view_record_index=r['index'], token_sha256=digest(r['tokens']))
                for r in view['view_parsed']['records']],
            complete_named_recipe_proofs=named_operands,
            saved_API_context=dict(source=str(truth_path.relative_to(ROOT)), source_sha256=sha(truth_path),
                settings=actual['settings'],
                scope='Saved modeling controls only; no historical-state evaluator, source-handle identity or correspondence to a pre-Extend state is inferred')))
        if fixture is None:
            fixture = blob, parsed, history, binding, view

    # Previous materializer dictionaries are frozen by their independent reports.
    from materialize_untrim_cache import materialize_untrim_cache
    from materialize_asm_alternative import materialize_asm_alternative
    prior = json.loads((ROOT/'untrim-cache-decoding.json').read_text())
    old_controls = []
    for sample in prior['samples']:
        if 'expected_provenance' not in sample:
            continue
        members = read_members(ROOT/sample['archive'], zstd)
        p = sample['expected_provenance']
        old = materialize_untrim_cache(members[sample['member']],
            initial_body_record_index=p['initial_body_record_index'], stored_body_identifier=p['stored_body_identifier'])
        check(sample['archive']+' old five-state full provenance/topology exact',
            {k: v for k, v in old.items() if k not in ('view_parsed', 'topology')} == p
            and old['topology'] == sample['expected_topology'])
        old_controls.append(dict(archive=sample['archive'], member=sample['member'], full_prior_dictionary_exact=True))
    box = prior['old_three_state_box_control']
    members = read_members(ROOT/box['archive'], zstd)
    check('Old three-state full box dictionary exact',
        materialize_asm_alternative(members[box['member']]) == box['expected_old_materializer_summary'])
    old_controls.append(dict(archive=box['archive'], member=box['member'], full_prior_dictionary_exact=True))

    blob, parsed, history, binding, view = fixture
    def guard(label, mutate=None, factory=False, **kwargs):
        raw = bytearray(blob)
        if mutate is not None:
            mutate(raw)
        args = {} if factory else dict(initial_body_record_index=binding['asm_body_index'], stored_body_identifier=binding['stored_handle'])
        args.update(kwargs)
        try:
            (materialize_asm_literal_view if factory else materialize_extend_cache)(bytes(raw), **args)
        except (ValueError, KeyError, IndexError, TypeError, struct.error) as error:
            reason = str(error)
        else:
            raise AssertionError(label)
        guards.append(dict(guard=label, rejected=True, reason=reason))

    guard('Reject supplied stored identifier differing from mapped BODY', stored_body_identifier=99)
    guard('Reject auxiliary initial BODY as mapped source', initial_body_record_index=1)
    target = view['source_body_pair']['pointer_sides'][0]['inspection_record_index']
    guard('Reject changed paired BODY identifier', lambda raw: struct.pack_into('<q', raw, parsed['records'][target]['tokens'][1]['offset']+1, 99))
    other_origin = next(o for o in view['origin_map'] if o['kind'] == 'plane-surface' and o['section'] == 'trailing_states')
    guard('Reject kind-changing literal BODY/surface pair in shared factory',
        lambda raw: struct.pack_into('<q', raw, view['source_body_pair']['pointer_sides'][0]['token_offset']+1,
            other_origin['geometry_entity_ordinal']), factory=True)
    def duplicate(raw):
        state = parsed['records'][history['journal_states'][0]['inspection_record_index']]
        at = 12+3*view['source_body_pair']['entry_ordinal']
        begin, end = state['tokens'][at]['offset'], state['tokens'][at+3]['offset']
        insert = state['tokens'][-3]['offset']
        raw[insert:insert] = blob[begin:end]
    guard('Reject duplicated complete nonnull pair in shared factory', duplicate, factory=True)
    graph = next(g for g in view['topology']['body_graphs'] if g['body_index'] == view['qualified_body_view_record_index'])
    nodes = {n['index']: n for n in view['topology']['nodes']}
    origin_by_view = {o['view_record_index']: o for o in view['origin_map']}
    edge = nodes[graph['edge_indices'][0]]
    edge_raw = parsed['records'][origin_by_view[edge['index']]['inspection_record_index']]
    guard('Reject geometry pointer outside entity namespace',
        lambda raw: struct.pack_into('<q', raw, edge_raw['tokens'][8]['offset']+1, len(history['geometry_entities'])+10), factory=True)
    # A removed-only right-side target has no alias and cannot be silently retained.
    removed_only = next(e['pointer_sides'][1]['stored_geometry_entity_ordinal'] for e in history['journal_states'][0]['entries']
        if e['pointer_sides'][0]['stored_geometry_entity_ordinal'] == -1)
    guard('Reject dangling pointer to an unpaired removed literal',
        lambda raw: struct.pack_into('<q', raw, edge_raw['tokens'][8]['offset']+1, removed_only), factory=True)
    point_id = nodes[edge['start_vertex_index']]['point_index']
    point_raw = parsed['records'][origin_by_view[point_id]['inspection_record_index']]
    guard('Reject endpoint coordinate corruption after identity qualification',
        lambda raw: struct.pack_into('<d', raw, point_raw['tokens'][3]['offset']+1, .125))
    coedge_id = graph['coedge_indices'][0]
    coedge_raw = parsed['records'][origin_by_view[coedge_id]['inspection_record_index']]
    guard('Reject nonreciprocal quad coedge',
        lambda raw: struct.pack_into('<q', raw, coedge_raw['tokens'][4]['offset']+1,
            origin_by_view[coedge_id]['geometry_entity_ordinal']))
    stale = copy.deepcopy(parsed)
    stale['records'][target]['tokens'][1]['value'] = 99
    guard('Reject stale supplied canonical parse', factory=True, parsed=stale)

    return dict(scope=SCOPE, samples=samples, old_controls=old_controls,
        validation=dict(saved_Extend_archives=len(FILES), qualified_literal_views=len(samples),
            complete_named_recipes=recipe_count, complete_BODY_graphs=3*len(samples),
            frozen_old_materializer_dictionaries_exact=len(old_controls),
            focused_checks=len(checks), malformed_guards=len(guards), main_calls=0, live_API_calls=0),
        checks=checks, malformed_guards=guards,
        integration=dict(callable='materialize_extend_cache(blob, *, initial_body_record_index, stored_body_identifier, parsed=None, history=None)',
            shared_factory='materialize_asm_literal_view(blob, *, state_slot=0, pointer_side=0, parsed=None, history=None)',
            expected_provenance='Every public wrapper field except view_parsed/topology; independently qualified native source may embed it exactly',
            expected_topology='Full alternate topology, separate from every original main ASM field',
            raw_view_distinction='Serialized geometry entity ordinals, global inspection record indices and dense view row identifiers are separate namespaces. Original record offsets/bytes are retained; rewritten pointer values are not serialized ASM.'),
        source_sha256={f: sha(ROOT/f) for f in ('materialize_asm_literal_view.py', 'materialize_extend_cache.py',
            'validate_extend_cache.py', 'decode_asm_history.py', 'decode_asm_recipe_tags.py', 'decode_brep.py',
            'decode_body_asm_identifiers.py', 'decode_extend_edge_sources.py', 'materialize_untrim_cache.py', 'materialize_asm_alternative.py')},
        old_materializer_evidence_sha256=sha(ROOT/'untrim-cache-decoding.json'),
        limitations=['The literal slot/side view is not chronological replay or geometry before Extend',
            'Equal BODY stored identifiers corroborate one explicit pair, not a general historical native identity bridge',
            'The neutral factory qualifies reference framing only; the wrapper alone qualifies the observed six-state three-graph planar quad family',
            'Named operands are uniquely incident in this nonserialized cache; API handle assignment, persistent identity and native traversal remain unresolved',
            'Canonical ASM bytes, tags and topology remain unchanged, as do the prior three/five-state materializers'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--zstd-library')
    parser.add_argument('--output', default='extend-cache-decoding.json')
    args = parser.parse_args()
    zstd = args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report = validate(zstd)
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['validation'], sort_keys=True))


if __name__ == '__main__':
    main()
