"""Focused six-state Untrim literal-view evidence and old-materializer controls."""
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
from decode_recipe_components import decode_counted_recipe
from fusion_archive import read_members
from fusion_metadata import design_records
from materialize_asm_literal_view import materialize_asm_literal_view
from materialize_untrim_six_state_cache import materialize_untrim_six_state_cache, SCOPE

ROOT = Path(__file__).resolve().parent
FILES = tuple('surfacebounds-ac801bb00fae/untrim_'+n+'.f3d' for n in ('external', 'all', 'manual', 'internal'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate(zstd):
    samples, controls, checks, guards = [], [], [], []
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
        minimal = dict(streams=[dict(member=n, complete_token_stream=True, declared_root_records=[])
            for n in members if n.endswith('.smbh')])
        native = decode_body_bindings(data, records, member, minimal)
        mappings = decode_body_asm_identifiers(data, records, member, members, native)
        check(filename+' fresh singleton typed native BODY mapping', not mappings['unresolved']
            and len(mappings['decoded']) == 1 and len(mappings['decoded'][0]['bindings']) == 1)
        mapping = mappings['decoded'][0]
        binding = mapping['bindings'][0]
        blob_member = mapping['history_blob_member']
        blob = members[blob_member]
        parsed = inspect_asm(blob)
        original = copy.deepcopy(parsed)
        history = decode_asm_history(blob, parsed=parsed)
        initial_tags = decode_asm_generic_tags(blob, parsed, allow_fpm_tracking=True)
        initial_topology = decode_topology(parsed)
        args = dict(initial_body_record_index=binding['asm_body_index'], stored_body_identifier=binding['stored_handle'])
        if filename.endswith(('/untrim_manual.f3d', '/untrim_internal.f3d')):
            try:
                materialize_untrim_six_state_cache(blob, **args)
            except ValueError as error:
                reason = str(error)
            else:
                raise AssertionError('Five-state family admitted to six-state Untrim wrapper')
            check(filename+' explicit five-state family rejection', reason == 'Untrim cache view is outside the observed six-state journal family')
            controls.append(dict(archive=filename, member=blob_member, new_six_state_rejection=reason))
            continue
        view = materialize_untrim_six_state_cache(blob, parsed=parsed, history=history, **args)
        literal = materialize_asm_literal_view(blob, parsed=parsed, history=history)
        check(filename+' exact neutral factory reused', all(view[k] == v for k, v in literal.items() if k != 'scope'))
        check(filename+' complete canonical six-state journal retained', view['canonical_history'] == history
            and history['neighbor_chain'] == [0, 2, 4, 5, 3, 1])
        topology = view['topology']
        nodes = {n['index']: n for n in topology['nodes']}
        graph = next(g for g in topology['body_graphs'] if g['body_index'] == view['qualified_body_view_record_index'])
        check(filename+' all three graphs complete with mapped same-ID BODY', not topology['unresolved']
            and len(topology['body_graphs']) == 3 and nodes[graph['body_index']]['stored_entity_id'] == binding['stored_handle'])
        check(filename+' exact captured quad/optional-circle shape', graph['counts'] == dict(lump=1, shell=1, face=1,
            loop=2 if filename.endswith('/untrim_external.f3d') else 1,
            coedge=5 if filename.endswith('/untrim_external.f3d') else 4,
            edge=5 if filename.endswith('/untrim_external.f3d') else 4,
            vertex=5 if filename.endswith('/untrim_external.f3d') else 4))
        chosen = view['selected_geometry_entity_ordinals']
        dense = {ordinal: index for index, ordinal in enumerate(chosen)}
        aliases = {r['side1_entity_ordinal']: r['side0_entity_ordinal'] for r in view['literal_pair_aliases']}
        table = history['geometry_entities']
        origins = {r['view_record_index']: r for r in view['origin_map']}
        replayed = []
        for row in view['view_parsed']['records']:
            o = origins[row['index']]
            expected = copy.deepcopy(parsed['records'][o['inspection_record_index']])
            expected['index'], expected['section'] = row['index'], 'geometry'
            for token in expected['tokens']:
                if token['tag'] == 12 and token['value'] != -1:
                    token['value'] = dense[aliases.get(token['value'], token['value'])]
            replayed.append(row == expected)
        check(filename+' every literal record/pointer rewrite exact', all(replayed)
            and all(blob[r['token_offset']] == 12 and struct.unpack_from('<q', blob, r['token_offset']+1)[0]
                == r['stored_target_geometry_entity_ordinal'] for r in view['rewritten_pointer_evidence']))
        check(filename+' explicit BODY pair namespace and stored ID agree',
            view['source_body_pair']['pointer_sides'][1]['inspection_record_index'] == binding['asm_body_index']
            and view['qualified_body_origin']['inspection_record_index'] != view['qualified_body_origin']['geometry_entity_ordinal']
            and view['qualified_dangling_pointer_count'] == 0)
        consistency = view['derived_stored_geometry_consistency']
        check(filename+' derived stored endpoint/plane/oriented-cycle consistency',
            consistency['finite_nondegenerate_line_domains'] and consistency['coplanar_with_qualified_plane']
            and consistency['typed_domain_endpoints_consistent'] and consistency['oriented_four_vertex_cycle_closed'])
        recipes = []
        for r in records:
            if r.is_primary and r.class_guid == '7ACC2A03-0261-4879-A14A-A93D661A5BDC':
                recipe = decode_counted_recipe(data, r)
                if recipe['payload_kind'] == 'face_recipe_data' and len(bytes.fromhex(recipe['payload_hex'])) == 8:
                    recipes.append(recipe)
        check(filename+' one complete face operand recipe', len(recipes) == 1)
        naming = match_recipe_tag_names(recipes[0], view['view_tag_summary'], parsed=view['view_parsed'])
        check(filename+' complete face name globally unique on paired BODY', len(naming['name_entries']) == 1
            and naming['name_entries'][0]['candidate_count'] == 1
            and naming['name_entries'][0]['candidates'][0]['owner_kind'] == 'face'
            and naming['name_entries'][0]['candidates'][0]['body_graph_membership'] == [graph['body_index']])
        check(filename+' canonical data unchanged', parsed == original and initial_topology == decode_topology(parsed)
            and initial_tags == decode_asm_generic_tags(blob, parsed, allow_fpm_tracking=True))
        truth_path = (ROOT/filename).parent/'ground_truth.json'
        actual = next(s for s in json.loads(truth_path.read_text())['samples'] if s['file'] == Path(filename).name)
        samples.append(dict(archive=filename, archive_sha256=sha(ROOT/filename), member=blob_member,
            blob_sha256=hashlib.sha256(blob).hexdigest(), native_source_mapping=mapping,
            expected_provenance={k: v for k, v in view.items() if k not in ('view_parsed', 'topology')},
            expected_topology=topology,
            expected_view_record_token_sha256=[dict(view_record_index=r['index'], token_sha256=digest(r['tokens']))
                for r in view['view_parsed']['records']],
            full_face_recipe=recipes[0], exact_face_name_correspondence=naming,
            saved_API_context=dict(source=str(truth_path.relative_to(ROOT)), source_sha256=sha(truth_path),
                settings=actual['settings'], scope='Actual controls only; no source/API handle assignment or historical-state evaluator')))
        if fixture is None:
            fixture = blob, parsed, binding, view

    # The old wrappers and their full public dictionaries remain independent.
    from materialize_untrim_cache import materialize_untrim_cache
    from materialize_extend_cache import materialize_extend_cache
    from materialize_asm_alternative import materialize_asm_alternative
    old_untrim = json.loads((ROOT/'untrim-cache-decoding.json').read_text())
    old_extend = json.loads((ROOT/'extend-cache-decoding.json').read_text())
    frozen_controls = []
    for report, function in ((old_untrim, materialize_untrim_cache), (old_extend, materialize_extend_cache)):
        for sample in report['samples']:
            if 'expected_provenance' not in sample:
                continue
            members = read_members(ROOT/sample['archive'], zstd)
            p = sample['expected_provenance']
            old = function(members[sample['member']], initial_body_record_index=p['initial_body_record_index'],
                stored_body_identifier=p['stored_body_identifier'])
            check(sample['archive']+' frozen old wrapper provenance/topology exact',
                {k: v for k, v in old.items() if k not in ('view_parsed', 'topology')} == p
                and old['topology'] == sample['expected_topology'])
            frozen_controls.append(dict(archive=sample['archive'], member=sample['member'], full_dictionary_exact=True))
    box = old_untrim['old_three_state_box_control']
    members = read_members(ROOT/box['archive'], zstd)
    check('Frozen three-state wrapper dictionary exact',
        materialize_asm_alternative(members[box['member']]) == box['expected_old_materializer_summary'])
    frozen_controls.append(dict(archive=box['archive'], member=box['member'], full_dictionary_exact=True))

    blob, parsed, binding, view = fixture
    def guard(label, mutate=None, **kwargs):
        raw = bytearray(blob)
        if mutate:
            mutate(raw)
        args = dict(initial_body_record_index=binding['asm_body_index'], stored_body_identifier=binding['stored_handle'])
        args.update(kwargs)
        try:
            materialize_untrim_six_state_cache(bytes(raw), **args)
        except (ValueError, KeyError, IndexError, TypeError, struct.error) as error:
            reason = str(error)
        else:
            raise AssertionError(label)
        guards.append(dict(guard=label, rejected=True, reason=reason))

    guard('Reject supplied BODY identifier mismatch', stored_body_identifier=99)
    target = view['source_body_pair']['pointer_sides'][0]['inspection_record_index']
    guard('Reject paired BODY identifier mismatch',
        lambda raw: struct.pack_into('<q', raw, parsed['records'][target]['tokens'][1]['offset']+1, 99))
    graph = next(g for g in view['topology']['body_graphs'] if g['body_index'] == view['qualified_body_view_record_index'])
    nodes = {n['index']: n for n in view['topology']['nodes']}
    origins = {o['view_record_index']: o for o in view['origin_map']}
    quad = next(c for c in view['derived_stored_geometry_consistency']['loops'] if c['stored_curve_family'] == 'FourLines')
    circle = next(c for c in view['derived_stored_geometry_consistency']['loops'] if c['stored_curve_family'] == 'FullCircle')
    c = nodes[quad['lines'][0]['coedge_view_record_index']]
    raw_coedge = parsed['records'][origins[c['index']]['inspection_record_index']]
    guard('Reject changed coedge reversal that breaks oriented endpoint cycle',
        lambda raw: raw.__setitem__(raw_coedge['tokens'][7]['offset'], 11 if c['is_reversed'] else 10))
    point_id = nodes[nodes[c['edge_index']]['start_vertex_index']]['point_index']
    raw_point = parsed['records'][origins[point_id]['inspection_record_index']]
    guard('Reject corrupted typed line endpoint coordinate',
        lambda raw: struct.pack_into('<d', raw, raw_point['tokens'][3]['offset']+1, .125))
    raw_circle = parsed['records'][origins[circle['curve_view_record_index']]['inspection_record_index']]
    guard('Reject corrupted optional circle center',
        lambda raw: struct.pack_into('<d', raw, raw_circle['tokens'][3]['offset']+1, .125))
    raw_edge = parsed['records'][origins[circle['edge_view_record_index']]['inspection_record_index']]
    guard('Reject partial circle domain', lambda raw: struct.pack_into('<d', raw, raw_edge['tokens'][6]['offset']+1, 0.))
    stale = copy.deepcopy(parsed)
    stale['records'][target]['tokens'][1]['value'] = 99
    guard('Reject stale supplied canonical parse', parsed=stale)

    # Equivalent serialization start points do not supply semantic traversal.
    loop = nodes[quad['loop_view_record_index']]
    raw_loop = parsed['records'][origins[loop['index']]['inspection_record_index']]
    next_coedge = nodes[loop['first_coedge_index']]['next_coedge_index']
    rotated_blob = bytearray(blob)
    struct.pack_into('<q', rotated_blob, raw_loop['tokens'][4]['offset']+1, origins[next_coedge]['geometry_entity_ordinal'])
    rotated = materialize_untrim_six_state_cache(bytes(rotated_blob),
        initial_body_record_index=binding['asm_body_index'], stored_body_identifier=binding['stored_handle'])
    rotated_quad = next(c for c in rotated['derived_stored_geometry_consistency']['loops'] if c['stored_curve_family'] == 'FourLines')
    check('Equivalent quad loop-head rotation remains accepted', rotated_quad['oriented_vertex_cycle_view_record_indices']
        == quad['oriented_vertex_cycle_view_record_indices'][1:]+quad['oriented_vertex_cycle_view_record_indices'][:1])
    # A singleton closed edge has the same endpoint regardless of coedge Boolean.
    raw_circle_coedge = parsed['records'][origins[circle['coedge_view_record_index']]['inspection_record_index']]
    flipped_blob = bytearray(blob)
    flipped_blob[raw_circle_coedge['tokens'][7]['offset']] = 10
    flipped = materialize_untrim_six_state_cache(bytes(flipped_blob),
        initial_body_record_index=binding['asm_body_index'], stored_body_identifier=binding['stored_handle'])
    flipped_circle = next(c for c in flipped['derived_stored_geometry_consistency']['loops'] if c['stored_curve_family'] == 'FullCircle')
    check('Singleton circular coedge Boolean retained independently', flipped_circle['stored_coedge_reversal'] is True)
    return dict(scope=SCOPE, samples=samples, five_state_negative_controls=controls,
        frozen_old_materializer_controls=frozen_controls,
        validation=dict(saved_Untrim_archives=4, qualified_six_state_views=2, complete_BODY_graphs=6,
            exact_complete_face_names=2, frozen_old_materializer_dictionaries_exact=len(frozen_controls),
            accepted_equivalent_serialization_controls=2, focused_checks=len(checks),
            malformed_guards=len(guards), main_calls=0, live_API_calls=0),
        checks=checks, malformed_guards=guards,
        equivalent_serialization_controls=dict(quad_loop_head_rotation_accepted=True,
            optional_closed_circle_coedge_boolean_accepted=True,
            scope='Synthetic local framing controls only; no API/native traversal or semantic loop-role correspondence'),
        integration=dict(callable='materialize_untrim_six_state_cache(blob, *, initial_body_record_index, stored_body_identifier, parsed=None, history=None)',
            expected_provenance='Every return field except view_parsed/topology; separate from canonical ASM output',
            expected_topology='Full pointer-closed alternate geometry, with complete original-record origins',
            loop_roles='Circle/quad geometry families only; no inside/outside or chronological state assignment'),
        source_sha256={f: sha(ROOT/f) for f in ('materialize_untrim_six_state_cache.py', 'validate_untrim_six_state_cache.py',
            'materialize_asm_literal_view.py', 'materialize_untrim_cache.py', 'materialize_extend_cache.py',
            'materialize_asm_alternative.py', 'decode_asm_history.py', 'decode_asm_recipe_tags.py', 'decode_brep.py')},
        historical_reports_sha256={f: sha(ROOT/f) for f in ('untrim-cache-decoding.json', 'extend-cache-decoding.json')},
        limitations=['Literal slot0/side0 pair selection is not chronology, current state or geometry before Untrim',
            'Same stored BODY identifier qualifies explicit pair consistency, not native historical identity',
            'Geometry follows namespace/typed BODY qualification and never selects identity by coordinates',
            'Coedge reversal is used for reciprocal endpoint-cycle checks only; UV/API traversal remains unresolved',
            'The optional circle is not labeled inner/outer and no semantic loop-role or native handle identity is inferred',
            'All original ASM data and prior three/five-state and Extend wrapper dictionaries remain unchanged'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--zstd-library')
    parser.add_argument('--output', default='untrim-six-state-cache-decoding.json')
    args = parser.parse_args()
    zstd = args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report = validate(zstd)
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['validation'], sort_keys=True))


if __name__ == '__main__':
    main()
