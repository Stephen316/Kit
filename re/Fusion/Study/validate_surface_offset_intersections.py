"""Ten saved Offset fixtures; independent raw-pointer intersection proofs."""
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags, match_recipe_tag_names
from decode_asm_subtypes import decode_asm_subtypes
from decode_brep import decode_topology
from decode_surface_offset_intersections import (
    decode_surface_offset_intersection_operands, resolve_surface_offset_intersections)
from decode_surface_offset_sources import decode_surface_offset_sources as strict_sources
from decode_surface_offset_source_variants import decode_surface_offset_sources
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
FILES = tuple('rulefilletsurfaces-7b26b40f98f7/'+name+'.f3d' for name in (
    'offsets_one_two_witnesses','offsets_one_three_witnesses','offsets_one_two','offsets_one_three')) + tuple(
    'surfacetools-856ca50cf4c7/offset_'+name+'.f3d' for name in ('positive','negative','rounded')) + (
    'specialfillets-d50f7a4f04e0/rule_asymmetric.f3d',
    'surfacebounds-ac801bb00fae/untrim_all.f3d', 'surfacebounds-ac801bb00fae/extend_natural.f3d')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def raw_incidence(blob, parsed, topology, row):
    """Follow raw ASM tokens independently of resolver-produced incidence."""
    records = parsed['records']
    graph = next(g for g in topology['body_graphs'] if g['body_index'] == row['explicit_asm_body_index'])
    def pointer(identity, field, expected):
        record = records[identity]
        token = record['tokens'][field]
        target = token['value']
        assert token['tag'] == 12 and struct.unpack_from('<q', blob, token['offset']+1)[0] == target
        assert target >= 0 and records[target]['section'] == 'geometry'
        assert records[target]['name'] == expected
        return target
    def coedge_face(identity):
        return pointer(pointer(identity,8,'loop'),5,'face')
    edge_faces = {}
    vertex_faces = {}
    for coedge in graph['coedge_indices']:
        edge = pointer(coedge,6,'edge')
        face = coedge_face(coedge)
        assert face in graph['face_indices']
        next_id, previous_id = pointer(coedge,3,'coedge'), pointer(coedge,4,'coedge')
        assert pointer(next_id,4,'coedge') == pointer(previous_id,3,'coedge') == coedge
        partner = pointer(coedge,5,'coedge')
        assert pointer(partner,5,'coedge') == coedge and pointer(partner,6,'edge') == edge
        edge_faces.setdefault(edge,set()).add(face)
        for endpoint in (pointer(edge,3,'vertex'),pointer(edge,5,'vertex')):
            vertex_faces.setdefault(endpoint,set()).add(face)
    recipe = row['recipe']
    words = struct.unpack('<369i', bytes.fromhex(recipe['payload_hex']))
    matches = match_recipe_tag_names(recipe,
        decode_asm_generic_tags(blob,parsed,allow_fpm_tracking=True),parsed=parsed)
    faces = {}
    for entry in matches['name_entries']:
        assert entry['candidate_count'] == 1
        candidate = entry['candidates'][0]
        assert candidate['owner_kind'] == 'face'
        assert candidate['body_graph_membership'] == [graph['body_index']]
        faces[entry['name_table_index']] = candidate['owner_record_index']
    face_id = faces[words[0]]
    assert face_id == row['cached_face']['face_record_index']
    loop = pointer(face_id,4,'loop')
    assert records[loop]['tokens'][3]['value'] == -1
    cycle = []
    current = pointer(loop,4,'coedge')
    while current not in cycle:
        assert len(cycle) < 7 and pointer(current,8,'loop') == loop
        cycle.append(current)
        current = pointer(current,3,'coedge')
    assert current == cycle[0] and len(cycle) == 6
    boundary_edges = {pointer(c,6,'edge') for c in cycle}
    edge_order, endpoint_order, tails = [], [], []
    for ordinal in range(6):
        block = words[3+61*ordinal:3+61*(ordinal+1)]
        pair = [faces[block[3]],faces[block[5]]]
        chosen = [edge for edge, incident in edge_faces.items() if incident == set(pair)]
        assert len(chosen) == 1
        edge = chosen[0]
        published = row['boundary_incidence'][ordinal]
        assert published['edge_record_index'] == edge and published['face_operand_record_indices'] == pair
        assert pointer(published['coedge_record_index'],6,'edge') == edge
        assert coedge_face(published['coedge_record_index']) == face_id
        assert published['coedge_record_index'] in cycle and published['loop_record_index'] == loop
        assert published['stored_edge_reversal'] is records[edge]['tokens'][9]['value']
        assert published['stored_coedge_reversal'] is records[published['coedge_record_index']]['tokens'][7]['value']
        endpoints = []
        for endpoint in range(2):
            vertex_words = block[8+26*endpoint:8+26*(endpoint+1)]
            triple = [faces[vertex_words[i]] for i in (2,4,6)]
            candidates = [v for v, incident in vertex_faces.items() if incident == set(triple)]
            assert len(candidates) == 1
            vertex = candidates[0]
            evidence = published['endpoint_incidence'][endpoint]
            point = pointer(vertex,5,'point')
            assert evidence['vertex_record_index'] == vertex and evidence['point_record_index'] == point
            assert evidence['face_operand_record_indices'] == triple
            assert evidence['raw_point'] == records[point]['tokens'][3]['value']
            assert evidence['opaque_tail_int32'] == list(vertex_words[9:])
            assert evidence['opaque_tail_semantics'] is None
            assert evidence['stored_edge_endpoint_role'] == ('Start' if vertex == pointer(edge,3,'vertex') else 'End')
            endpoints.append(vertex)
            tails.append(tuple(vertex_words[9:]))
        assert set(endpoints) == {pointer(edge,3,'vertex'),pointer(edge,5,'vertex')}
        assert endpoints == published['operand_endpoint_vertex_indices']
        assert published['stored_edge_endpoint_vertex_indices'] == [pointer(edge,3,'vertex'),pointer(edge,5,'vertex')]
        edge_order.append(edge)
        endpoint_order.append(endpoints)
    assert set(edge_order) == boundary_edges and len(set(edge_order)) == 6
    assert row['cached_face']['surface']['index'] == pointer(face_id,7,'spline-surface')
    assert 'partial_surface_definition' in row['cached_face']['surface']
    for boundary in row['cached_face']['boundary_edges']:
        edge = boundary['edge']
        assert edge['index'] in boundary_edges
        assert boundary['curve']['index'] == pointer(edge['index'],8,'intcurve-curve')
        for vertex in boundary['vertices']:
            assert vertex['index'] in (pointer(edge['index'],3,'vertex'),pointer(edge['index'],5,'vertex'))
            assert vertex['point_index'] == pointer(vertex['index'],5,'point')
    support = row['support_source_provenance']
    source_ids = [source['source_feature_object_id'] for source in support['support_sources']]
    assert source_ids in ([344,385],[243,344,385])
    assert support['historical_anchor_owner_object_id'] == row['historical_source_owner_object_id'] == 243
    assert support['component_object_id'] == 3 and support['exact_support_payload_replay']
    assert all(b['body_properties']['component_object_id'] == 3 for b in support['body_ownership'])
    assert row['native_body_object_id'] == 275 and row['explicit_asm_body_index'] == 1
    assert all(row[k] is None for k in ('exact_selected_source_identity','API_handle_identity',
        'current_source_identity','persistent_source_identity','qualified_historical_state','traversal'))
    origins = {r['record_index']:r for r in row['source_record_origins']}
    required = {face_id,loop,pointer(face_id,7,'spline-surface')} | set(cycle) | set(edge_order)
    required |= set(faces.values()) | {v for pair in endpoint_order for v in pair}
    assert required <= set(origins)
    for identity, origin in origins.items():
        record = records[identity]
        assert origin == dict(record_index=identity,kind=record['name'],section=record['section'],
            record_offset=record['offset'],record_end_offset=record['end_offset'])
        assert origin['section'] == 'geometry'
    return dict(owner_object_id=row['owner_object_id'],face_record_index=face_id,
        surface_record_index=pointer(face_id,7,'spline-surface'),
        complete_named_FACE_record_indices=[faces[i] for i in range(7)],
        raw_topological_coedge_cycle=cycle, edge_indices_literal_operand_order=edge_order,
        endpoint_vertex_indices_literal_operand_order=endpoint_order,
        immediate_support_source_object_ids=source_ids,historical_anchor_owner_object_id=243,
        opaque_endpoint_tails_int32=[list(tail) for tail in tails],
        identity_basis='Complete full names plus raw reciprocal FACE/COEDGE/EDGE/VERTEX pointers; coordinates copied only after identities',
        API_or_current_or_historical_identity=None)


def validate(zstd, baseline_path):
    baseline = json.loads(baseline_path.read_text())
    assert baseline['baseline_commit'] == 'cf0ffb9' and baseline['files'] == list(FILES)
    before = {Path(row['file']).relative_to(ROOT).as_posix():row for row in baseline['before']}
    checks, samples, guards, positive_controls = [], [], [], []
    totals = Counter()
    opaque_tails = set()
    contexts = {}
    saved = None
    def check(label, condition):
        if not condition:
            raise AssertionError(label)
        checks.append(label)
    for archive in FILES:
        data,records,features,member,members = load(ROOT,archive,zstd)
        stream = before[archive]['streams'][0]
        ids,selections = stream['body_asm_identifiers'],stream['body_selections']
        original = copy.deepcopy((features,records,ids,selections))
        summary = decode_surface_offset_sources(data,records,features,member,members,ids,selections)
        default = strict_sources(data,records,features,member,members,ids,selections)
        check(archive+' caller inputs unchanged', (features,records,ids,selections) == original)
        prior = stream.get('surface_offset_sources')
        check(archive+' strict default complete prior summary preserved',
            default == prior if prior is not None else not default['associations'] and not default['unresolved'])
        proofs = []
        if archive in FILES[:2]:
            check(archive+' eight qualified associations replace only old support rejections',
                len(summary['associations']) == 8 and not summary['unresolved']
                and not default['associations'] and len(default['unresolved']) == 8
                and {r['owner_object_id'] for r in summary['associations']} == {r['owner_object_id'] for r in default['unresolved']}
                and all(r['reason'] == 'Offset descriptor/source support reciprocity differs' for r in default['unresolved']))
            source_blob = None
            for row in summary['associations']:
                blob = members[row['history_blob_member']]
                if source_blob is None:
                    parsed = inspect_asm(blob)
                    tags = decode_asm_generic_tags(blob,parsed,allow_fpm_tracking=True)
                    topology = decode_topology(parsed,subtype_catalog=decode_asm_subtypes(blob,parsed=parsed))
                    source_blob = blob
                check(archive+' all existing same-blob XYZ/UV diagnostics retained',
                    row['source_geometry_diagnostics'] == topology['unresolved']
                    and Counter(r['kind'] for r in topology['unresolved']) == {'spline-surface':16,'pcurve':48})
                check(archive+' exact operation pure codec and whole native recipe replay',
                    row['operation_operands'] == decode_surface_offset_intersection_operands(row['recipe'])
                    and row['exact_full_counted_recipe_replay'] is True
                    and bytes.fromhex(row['full_counted_recipe_payload_hex']) ==
                        data[next(r for r in records if r.is_primary and r.object_id == row['recipe_object_id']).body:
                             next(r for r in records if r.is_primary and r.object_id == row['recipe_object_id']).end])
                proof = raw_incidence(blob,parsed,topology,row)
                proofs.append(proof)
                totals.update(owners=1,boundary_edges=6,endpoint_operands=12,complete_FACE_name_groups=7)
                totals['support_count_'+str(len(proof['immediate_support_source_object_ids']))] += 1
                opaque_tails.update(tuple(t) for t in proof['opaque_endpoint_tails_int32'])
                if saved is None:
                    saved = (blob,parsed,tags,topology,row)
            contexts[archive] = dict(blob_sha256=hashlib.sha256(source_blob).hexdigest(),
                exact_native_geometry_diagnostics=topology['unresolved'])
        else:
            check(archive+' complete old control summary exact', summary == default)
            totals['whole_source_summary_controls_exact'] += 1
        samples.append(dict(archive=archive,archive_sha256=sha(ROOT/archive),expected_summary=summary,
            expected_default_summary=default,independent_raw_pointer_incidence=proofs,
            inputs_unchanged=True,native_API_handle_assignment=None))
    check('Sixteen owners/96EDGEs/192endpoints/112FACE names observed',
        [totals[k] for k in ('owners','boundary_edges','endpoint_operands','complete_FACE_name_groups')] == [16,96,192,112])
    check('Both two/three immediate-source support families observed',totals['support_count_2'] == totals['support_count_3'] == 8)
    check('All19 opaque17-int tail variants retained without evaluation',len(opaque_tails) == 19)
    blob,parsed,tags,topology,row = saved
    recipe = row['recipe']
    def changed_words(replacement):
        result = copy.deepcopy(recipe)
        words = list(struct.unpack('<369i',bytes.fromhex(result['payload_hex'])))
        replacement(words)
        result['payload_hex'] = struct.pack('<369i',*words).hex()
        return result
    def reject(label, altered, resolution=False, changed_topology=None, body_id=1):
        try:
            if resolution:
                resolve_surface_offset_intersections(blob,parsed,tags,
                    topology if changed_topology is None else changed_topology,body_id,altered)
            else:
                decode_surface_offset_intersection_operands(altered)
        except (ValueError,KeyError,IndexError,TypeError,struct.error) as error:
            guards.append(dict(guard=label,rejected=True,reason=str(error)))
        else:
            raise AssertionError(label+' unexpectedly accepted')
    reject('Incorrect counted six-boundary frame',changed_words(lambda w:w.__setitem__(2,5)))
    reject('Endpoint count differs from three-FACE branch',changed_words(lambda w:w.__setitem__(12,2)))
    reject('Named FACE index leaves complete table',changed_words(lambda w:w.__setitem__(13,7)))
    repeated = copy.deepcopy(recipe)
    repeated['name_table'][1]['terms'] = copy.deepcopy(repeated['name_table'][0]['terms'])
    reject('Repeated complete table name group',repeated)
    reject('Well-framed wrong endpoint triple lacks unique incidence',
        changed_words(lambda w:w.__setitem__(15,4)),resolution=True)
    permutation = [3,0,6,2,1,5,4]
    permuted = copy.deepcopy(recipe)
    new_table = [None]*7
    for old,new in enumerate(permutation):
        new_table[new] = dict(copy.deepcopy(recipe['name_table'][old]),table_index=new)
    permuted['name_table'] = new_table
    reject('Table permutation without corresponding explicit operand references',permuted,resolution=True)
    stale = copy.deepcopy(topology)
    next(n for n in stale['nodes'] if n['index'] == row['boundary_incidence'][0]['coedge_record_index'])['partner_index'] = 0
    reject('Stale topology copy cannot redirect reciprocal partner',recipe,resolution=True,changed_topology=stale)
    reject('Wrong explicit BODY cannot reuse source FACE names',recipe,resolution=True,body_id=2)
    # Reorder complete table and ONLY the syntactically typed name references.
    # Opaque tail integers remain exactly untouched, even if numerically0..6.
    words = list(struct.unpack('<369i',bytes.fromhex(recipe['payload_hex'])))
    positions = [0]
    for ordinal in range(6):
        start = 3+61*ordinal
        positions += [start+3,start+5]
        for endpoint in range(2):
            positions += [start+8+26*endpoint+offset for offset in (2,4,6)]
    for position in positions:
        words[position] = permutation[words[position]]
    permuted['payload_hex'] = struct.pack('<369i',*words).hex()
    actual = resolve_surface_offset_intersections(blob,parsed,tags,topology,1,permuted)
    original_resolution = resolve_surface_offset_intersections(blob,parsed,tags,topology,1,recipe)
    def identity_projection(result):
        return result['cached_face'], [(r['edge_record_index'],
            [v['vertex_record_index'] for v in r['endpoint_incidence']]) for r in result['boundary_incidence']]
    check('Complete table permutation with only typed name-index remapping preserves all geometry identities',
          identity_projection(actual) == identity_projection(original_resolution))
    check('Table permutation leaves every opaque numeric tail literal unchanged',
        [[v['opaque_tail_int32'] for v in e['endpoint_operands']]
            for e in decode_surface_offset_intersection_operands(permuted)['boundary_edges']] ==
        [[v['opaque_tail_int32'] for v in e['endpoint_operands']]
            for e in decode_surface_offset_intersection_operands(recipe)['boundary_edges']])
    positive_controls.append(dict(control='Complete table permutation with typed-reference remap',
        old_to_new_table_indices=permutation,geometry_identities_unchanged=True,opaque_tail_literals_remapped=False))
    opaque_changed = changed_words(lambda w:w.__setitem__(20,777))
    actual = resolve_surface_offset_intersections(blob,parsed,tags,topology,1,opaque_changed)
    check('Changed opaque procedure-tail literal preserves naming/incidence proof only',
        identity_projection(actual) == identity_projection(original_resolution)
        and actual['boundary_incidence'][0]['endpoint_incidence'][0]['opaque_tail_int32'][0] == 777
        and actual['full_selection_procedure_evaluated'] is False)
    positive_controls.append(dict(control='Opaque endpoint-tail first integer2 replaced by777',
        accepted_as_literal=True,geometry_identities_unchanged=True,full_selection_procedure_evaluated=False,
        API_handle_identity=None))
    return dict(interface='decode_surface_offset_intersection_operands(recipe); resolve_surface_offset_intersections(blob,parsed,tags,topology,body_id,recipe,operands=None,naming=None)',
        integration=dict(stream='surface_offset_sources',owner_feature_list='surface_offset_sources',
            owner_field='owner_object_id',facade='decode_surface_offset_source_variants.decode_surface_offset_sources',
            only_two_existing_summaries_refined=True,old_tool_or_XYZ_or_UV_warning_changes=0),
        baseline=dict(commit='cf0ffb9',path=str(baseline_path),sha256=sha(baseline_path)),
        samples=samples,source_blobs=contexts,guards=guards,positive_controls=positive_controls,checks=checks,
        validation=dict(totals,opaque_tail_variants=len(opaque_tails),guards=len(guards),
            positive_controls=len(positive_controls),check_count=len(checks),main_runs=0,live_calls=0,
            full_selection_procedure_evaluations=0,native_API_identity_claims=0),
        source_sha256={name:sha(ROOT/name) for name in ('decode_surface_offset_intersections.py',
            'validate_surface_offset_intersections.py','decode_surface_offset_sources.py',
            'decode_surface_offset_source_variants.py','decode_owned_surface_selection.py',
            'decode_asm_recipe_tags.py','decode_brep.py','decode_untrim_sources.py',
            'decode_asm_subtypes.py','asm_records.py','decode_body_asm_identifiers.py')},
        limitations=['Seven complete names select FACEs; unnamed EDGE and VERTEX incidence is qualified only after explicit native BODY/blob ownership.',
            'All17 endpoint-tail integers are raw literals. Their small values are not remapped as name indices and no degree/count/procedure meaning is inferred.',
            'The complete1476-byte frame is replayed, but proprietary selection-procedure evaluation remains unknown. Accepted opaque-tail mutations are not a claim of API acceptance.',
            'Actual ordered endpoints and loop order remain native observations; no API traversal, UV parameter or persistent topology meaning is assigned.',
            'Initial-cache VBL partial definitions and all existing XYZ/UV diagnostics are retained. Naming/topology proof is independent of unknown procedural interiors.',
            'No saved ground truth enters the production resolver. Captured API equality and cross-export correspondence require separate immutable-fixture evidence.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--zstd')
    parser.add_argument('--baseline-cache',type=Path,default=Path('/private/tmp/fusion-surface-offset-intersection-baseline.json'))
    parser.add_argument('--output',default='surface-offset-intersection-decoding.json')
    args = parser.parse_args()
    zstd = args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report = validate(zstd,args.baseline_cache)
    Path(args.output).write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report['validation'],sort_keys=True))
