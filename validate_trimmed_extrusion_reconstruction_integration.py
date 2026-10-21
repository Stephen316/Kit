"""Fixed trimmed-profile straight Extrude reconstruction integration."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASELINE = 'd5f29a9'
FILES = (
    'trimselectorholdouts-ac245ecd1e2f/shifted_unequal_lens.f3d',
    'trimselectorholdouts-ac245ecd1e2f/reverse_creation_lens.f3d',
    'trimselectorholdouts-ac245ecd1e2f/repeated_circle.f3d',
    'trimselectorholdouts-ac245ecd1e2f/repeated_circle_reverse_creation.f3d',
    'trimmedprofiles-a804f8da1496/circle_lens.f3d',
    'trimmedprofiles-a804f8da1496/circle_right_complement.f3d',
    'linetrimholdouts-456e1d19906d/reverse_rectangle_creation.f3d',
    'linetrimholdouts-456e1d19906d/translated_unequal_rectangles.f3d',
    'trimmedprofiles-a804f8da1496/rectangle_overlap.f3d',
    'mixedprofiletrims-a125a4c1749e/circle_line_segment.f3d',
    'mixedprofiletrims-a125a4c1749e/line_circle_reverse_creation.f3d',
    'mixedprofiletrims-a125a4c1749e/shifted_circle_line_segment.f3d',
    'placedprofiletrims-037ed41056a4/offset_xy_circle_lens.f3d',
    'placedprofiletrims-037ed41056a4/origin_xz_mixed_segment.f3d',
    'placedprofiletrims-037ed41056a4/angled_rectangle_overlap.f3d',
    'extents-f0f33a9a605f/distance_positive.f3d',
    'thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d',
    'extents-f0f33a9a605f/to_plane.f3d',
    'placement-c6ad25e75d60/placement.f3d',
)
SUMMARY = ATTACHMENT = 'trimmed_extrusion_reconstruction'


def _near(a, b, tolerance=2e-8):
    import math
    if isinstance(a, dict):
        assert set(a) == set(b)
        for key in a: _near(a[key], b[key], tolerance)
    elif isinstance(a, (list, tuple)):
        assert len(a) == len(b)
        for x, y in zip(a, b): _near(x, y, tolerance)
    else:
        assert math.isfinite(a) and math.isfinite(b) and abs(a-b) <= tolerance * max(1., abs(a), abs(b)), (a, b)


def source_reference(before):
    """Independent source integrals/extrema, with no cached geometry as an input."""
    import itertools, math
    stream, = before['streams']
    key = next(k for k in ('placed_profile_portions', 'profile_mixed_portions',
        'profile_line_portions', 'profile_circle_portions') if stream.get(k, {}).get('decoded'))
    portion, = stream[key]['decoded']
    feature, = [f for f in stream['features'] if f['object_id'] == portion['source_feature_object_id']]
    assert feature['kind'] == 'Extrude' and feature['operation']['kind'] == 'NewBody'
    assert feature['start']['kind'] == 'ProfilePlane' and feature['extent']['mode'] == 'OneSided'
    side = feature['extent']['side_one']
    assert side['condition'] == 'Distance' and side['taper_angle_radians'] == 0 and side['distance_cm'] > 0
    sketch, = [f for f in stream['features'] if f['kind'] == 'Sketch' and f['sketch_object_id'] == portion['native_sketch_object_id']]
    assert sketch['component_object_id'] == feature['component_object_id']
    primitives = {g['object_id']: g for g in sketch['geometry']}
    matrix = sketch['placement']['sketch_to_component_matrix']
    axis = [matrix[2], matrix[6], matrix[10]]
    _near(axis, feature['extent']['stored_direction_vector'])
    assert len(portion['profile_loops']) == 1 and portion['profile_loops'][0]['is_outer'] is True
    references = portion['profile_loops'][0]['curve_references']
    def tuple_key(ref): return ref['entity_id'], tuple(ref['stored_tuple_fields'])
    reference_keys = {tuple_key(ref) for ref in references}
    assert len(reference_keys) == len(references)
    ends, integrals, extrema, identity_rows = [], [], [], []
    for p in portion['derived_source_portions']:
        ref = p['stored_profile_reference']; identity = ref['entity_id']; primitive = primitives[identity]
        assert tuple_key(ref) in reference_keys and primitive['entity_tag'] == ref['entity_tag']
        assert primitive['kind'] == ref['entity_kind']
        local = p['derived_sketch_local_points_cm']
        ends.append([local['start'], local['end']])
        if primitive['kind'] == 'Circle':
            a, b = p['derived_reference_axis_angle_interval_radians']; center = primitive['center_cm']; radius = primitive['radius_cm']
            _near(primitive['normal'], [0., 0., 1.]); _near(primitive['reference_axis'], [1., 0., 0.])
            def at(t): return [center[0]+radius*math.cos(t), center[1]+radius*math.sin(t), 0.]
            _near([at(a), at(b)], ends[-1])
            # Antiderivative of (x dy - y dx)/2 over the bounded source arc.
            integrals.append((radius*center[0]*(math.sin(b)-math.sin(a)) +
                radius*center[1]*(math.cos(a)-math.cos(b)) + radius**2*(b-a))/2)
            parameters = [a, b]
            for i in range(3):
                phase = math.atan2(matrix[4*i+1], matrix[4*i])
                for turn in range(-2, 5):
                    t = phase + turn*math.pi
                    if a <= t <= b: parameters.append(t)
            local_extrema = [at(t) for t in parameters]
            interval = [a, b]
        else:
            assert primitive['kind'] == 'Line'
            a, b = p['derived_native_start_end_fraction_interval']
            start, end = primitive['start_cm'], primitive['end_cm']
            calculated = [[x+t*(y-x) for x, y in zip(start, end)] for t in (a, b)]
            _near(calculated, ends[-1]); x, y = calculated
            integrals.append((x[0]*y[1]-x[1]*y[0])/2)
            local_extrema = calculated; interval = [a, b]
        for point in local_extrema:
            for height in (0., side['distance_cm']):
                extrema.append([sum(matrix[4*i+j]*point[j] for j in range(3)) + matrix[4*i+3]+height*axis[i] for i in range(3)])
        identity_rows.append(dict(native_primitive_object_id=identity, native_primitive_kind=primitive['kind'],
            full_selected_tuple=ref['stored_tuple_fields'], derived_source_interval=interval))
    assert len(ends) == len(reference_keys) and len(ends) in (2, 4)
    # Enumerate mathematical source cycles. Endpoint joins never assign native VERTEX IDs.
    areas = []
    for order in itertools.permutations(range(1, len(ends))):
        indices = (0,)+order
        for tail_signs in itertools.product((1, -1), repeat=len(ends)-1):
            signs = (1,)+tail_signs
            pairs = [ends[i] if sign == 1 else list(reversed(ends[i])) for i, sign in zip(indices, signs)]
            if all(math.dist(pairs[j][1], pairs[(j+1)%len(pairs)][0]) < 1e-8 for j in range(len(pairs))):
                areas.append(abs(sum(integrals[i]*sign for i, sign in zip(indices, signs))))
    assert areas and all(abs(x-areas[0]) < 1e-8 for x in areas)
    assert areas[0] > 0
    anchor, = [a for a in stream['body_selections']['body_anchors'] if a['object_id'] == portion['body_anchor_object_id']]
    assert anchor['source_owner_object_id'] == feature['object_id'] and anchor['native_body_object_id'] == portion['native_body_object_id']
    mapping, = [m for m in stream['body_blob_bindings']['decoded'] if m['mapping_record_object_id'] == portion['mapping_record_object_id']]
    binding, = [b for b in mapping['bindings'] if b['native_body_object_id'] == portion['native_body_object_id']]
    assert binding['asm_body_index'] == portion['asm_body_index'] and binding['stored_handle'] == portion['asm_stored_body_entity_id']
    assert mapping['history_blob_member'] == portion['history_blob_member']
    return dict(feature_object_id=feature['object_id'], native_sketch_object_id=portion['native_sketch_object_id'],
        profile_descriptor_object_id=portion['profile_descriptor_object_id'], profile_loop_definition_object_id=portion['profile_loop_definition_object_id'],
        body_anchor_object_id=anchor['object_id'], native_body_object_id=portion['native_body_object_id'],
        mapping_record_object_id=mapping['mapping_record_object_id'], history_blob_member=portion['history_blob_member'],
        asm_body_index=portion['asm_body_index'], binding=binding,
        typed_source_portions=identity_rows, source_frame_matrix=matrix, source_axis_component=axis,
        independent_profile_area_cm2=areas[0], independent_volume_cm3=areas[0]*side['distance_cm'],
        independent_bounds_cm=[[min(p[i] for p in extrema) for i in range(3)], [max(p[i] for p in extrema) for i in range(3)]],
        mathematical_cycle_count=len(areas), native_VERTEX_assignment=None, API_ENTITY_assignment=None,
        scope='Baseline typed tuple/primitive/Sketch/anchor/mapping identities precede independent source Green integrals and bounded transformed extrema; mathematical endpoint cycles assign no native ENTITY')


def saved_API_result(archive, reference):
    import json
    truth_file = str(Path(archive).parent/'ground_truth.json')
    truth = json.loads((ROOT/truth_file).read_text())
    sample, = [s for s in truth['samples'] if s['file'] == Path(archive).name]
    actual, = sample['result_bodies']
    _near(actual['bounds_cm'], reference['independent_bounds_cm'])
    _near(actual['volume_cm3'], reference['independent_volume_cm3'])
    return dict(truth_file=truth_file, actual_API_result_bounds_cm=actual['bounds_cm'],
        actual_API_result_volume_cm3=actual['volume_cm3'], independent_bounds_cm=reference['independent_bounds_cm'],
        independent_volume_cm3=reference['independent_volume_cm3'], API_ENTITY_assignment=None,
        scope='Complete single-result API bounds and volume corroborate after native joins; no API ENTITY or current/historical identity assigned by coordinates')


EVIDENCE = 'trimmed-extrusion-reconstruction-decoding.json'
SOURCE_EVIDENCE = 'trimmed-extrusion-source-decoding.json'
MATH_EVIDENCE = 'trimmed-extrusion-geometry-decoding.json'
FROZEN_PRODUCTION = {'decode_trimmed_extrusion_reconstruction.py': 'd4287d0058f68969170b4c69ecccd6dba0ab2406e99684d5cb0b2263e94b4603', 'decode_trimmed_extrusion_sources.py': 'c213185146f985522ce7ebf40003bfb930b30423d07e125f1e89be282e688cdb', 'decode_extrusion_source_operands.py': 'b3a58131c722402fcddf5a8e9dafb35ab78323e51c99adb08dea2378d16576ff', 'decode_trimmed_extrusion_geometry.py': '4aefa41536c987b49ac0639312aecec0211898e94a8a64e0614f2391a5f485ad'}
FROZEN_MAIN_SHA256 = 'e2442a2d2a034b9f3eadb1c7ca7537a8224763378c54934e6cd2b846fdc0a1ba'
FROZEN_EVIDENCE = {'trimmed-extrusion-reconstruction-decoding.json': 'fe9aa7bfa9fad06022750996e5cc091005431b08f1770116a785fd636887f00a', 'trimmed-extrusion-source-decoding.json': '263869caf06625be476682847081789e692681f8e6ab997b4c83fb654e335af3', 'trimmed-extrusion-geometry-decoding.json': '6a4961943ef4343c74c99ba84ba5b0792fc7bf3f4fe4b2fc8e3b04b0b4f68809'}


def read_cache(path, side):
    import json
    from validate_rectangular_cache_evidence_integration import sha
    cache = json.loads(Path(path).read_text())
    assert cache['baseline_commit'] == BASELINE and cache['files'] == list(FILES)
    assert cache['acquisition_main_calls'] == 19 and cache['acquisition_passes'] == 1
    assert len(cache[side]) == 19
    if side == 'before':
        assert cache['archive_sha256'] == {f: sha(ROOT/f) for f in FILES}
    else:
        assert cache['production_source_sha256'] == FROZEN_PRODUCTION
        assert cache['main_source_sha256'] == FROZEN_MAIN_SHA256 == sha(ROOT/'decode_basics.py')
    return cache[side]


def focused_evidence():
    import json
    from validate_rectangular_cache_evidence_integration import sha
    assert FROZEN_PRODUCTION and FROZEN_EVIDENCE, 'Production freeze has not been recorded'
    for filename, expected in {**FROZEN_PRODUCTION, **FROZEN_EVIDENCE}.items():
        assert sha(ROOT/filename) == expected, (filename, 'Frozen source/evidence changed')
    reports = [json.loads((ROOT/name).read_text()) for name in (EVIDENCE, SOURCE_EVIDENCE, MATH_EVIDENCE)]
    for report in reports:
        for filename, expected in report['source_sha256'].items():
            assert sha(ROOT/filename) == expected, (filename, 'Stale focused source provenance')
    summaries = {s['archive']: s['expected_summary'] for s in reports[0]['samples'] if s['archive'] in FILES}
    sources = {s['archive']: s['expected_sources'] for s in reports[1]['samples'] if s['archive'] in FILES}
    assert set(summaries) == set(sources) == set(FILES)
    for archive in FILES:
        summary = summaries[archive]
        assert set(summary) == {'decoded', 'unresolved', 'scope'}
        if archive in FILES[:15]:
            row, = summary['decoded']; source, = sources[archive]
            assert not summary['unresolved'] and row['native_source_provenance'] == source
        else:
            assert not summary['decoded'] and not summary['unresolved'] and not sources[archive]
    return summaries, sources


def compare(before, current, archive, expected, sources, zstd):
    import copy
    from validate_rectangular_cache_evidence_integration import sha, digest, differences
    after = copy.deepcopy(current); old, = before['streams']; stream, = after['streams']
    assert old['member'] == stream['member'] and SUMMARY not in old
    proofs = []
    if archive in FILES[:15]:
        assert stream.pop(SUMMARY) == expected
        row, = expected['decoded']; source, = sources
        feature, = [f for f in stream['features'] if f['object_id'] == row['feature_object_id']]
        prior, = [f for f in old['features'] if f['object_id'] == row['feature_object_id']]
        assert prior['kind'] == feature['kind'] == 'Extrude' and ATTACHMENT not in prior
        assert feature.pop(ATTACHMENT) == row
        proofs.append(qualify(row, before, source, archive, zstd))
    else:
        assert SUMMARY not in stream and not expected['decoded'] and not expected['unresolved']
    assert all(ATTACHMENT not in f for f in stream.get('features', []))
    assert after == before, (archive, 'Unexpected prior-output change', differences(before, after))
    return dict(archive=archive, archive_sha256=sha(ROOT/archive), decoded_trimmed_Extrudes=len(proofs),
        receiving_feature_annotations=len(proofs), independent_geometry_proofs=proofs,
        whole_output_unchanged=current == before,
        whole_output_exact_after_removing_only_new_summary_and_successful_owner_annotation=True,
        all_previous_profile_portions_settings_warnings_kinds_timeline_ASM_geometry_topology_and_placement_exact=True,
        baseline_output_sha256=digest(before), current_output_sha256=digest(current),
        qualified_difference_paths=differences(before, current))


def qualify(row, before, source, archive, zstd):
    """Recheck native identity joins and literal records before geometry/API comparison."""
    from fusion_archive import read_members
    from fusion_metadata import design_records
    from validate_rectangular_cache_evidence_integration import digest
    assert row['native_source_provenance'] == source
    reference = source_reference(before)
    assert row['feature_object_id'] == source['feature_object_id'] == reference['feature_object_id']
    group, = source['source_groups']; assert source['source_group_count'] == 1
    for key in ('source_feature_object_id', 'native_body_object_id', 'body_anchor_object_id',
            'mapping_record_object_id', 'history_blob_member', 'asm_body_index'):
        expected = reference['feature_object_id'] if key == 'source_feature_object_id' else reference[key]
        assert group[key] == expected
    native_binding_keys = ('native_body_object_id', 'stored_handle', 'asm_body_index', 'asm_stored_entity_id',
        'asm_body_record_offset', 'asm_identifier_token_offset', 'association_status', 'identifier_scope', 'lifecycle_status')
    assert {k: group['binding'][k] for k in native_binding_keys} == {k: reference['binding'][k] for k in native_binding_keys}
    assert group['binding']['previous_ordinal_candidate'] is None  # Fresh native source proof excludes caller ordinal metadata.
    selection = group['native_profile_selection']
    assert selection['native_sketch_object_id'] == reference['native_sketch_object_id']
    assert selection['profile_descriptor_object_id'] == reference['profile_descriptor_object_id']
    assert selection['profile_loop_definition_object_id'] == reference['profile_loop_definition_object_id']
    _near(group['source_sketch']['placement']['sketch_to_component_matrix'], reference['source_frame_matrix'])
    _near(group['stored_direction_vector'], reference['source_axis_component'])
    known = {(p['native_primitive_object_id'], tuple(p['full_selected_tuple'])): p for p in reference['typed_source_portions']}
    assert len(known) == len(group['derived_source_portions']) == len(group['mathematical_inputs'])
    native_parts = {}
    for p in group['derived_source_portions']:
        r = p['stored_profile_reference']; key = (r['entity_id'], tuple(r['stored_tuple_fields']))
        assert key in known and key not in native_parts
        interval = p.get('derived_reference_axis_angle_interval_radians', p.get('derived_native_start_end_fraction_interval'))
        _near(interval, known[key]['derived_source_interval']); native_parts[key] = p
    primitive_by_id = {p['object_id']: p for p in group['source_sketch']['geometry']}
    for p in group['mathematical_inputs']:
        native = primitive_by_id[p['source_primitive_id']]
        expected_geometry = {k: native[k] for k in (('center_cm', 'radius_cm', 'normal', 'reference_axis') if native['kind'] == 'Circle' else ('start_cm', 'end_cm'))}
        assert p['source_geometry'] == expected_geometry
        assert p['kind'] == ('CircleArc' if native['kind'] == 'Circle' else 'LineSegment')
        native_part, = [v for v in native_parts.values() if v['role_key'] == p['role_key']]
        _near(p['parameter_interval'], native_part.get('derived_reference_axis_angle_interval_radians', native_part.get('derived_native_start_end_fraction_interval')))
    members = read_members(ROOT/archive, zstd); stream, = before['streams']; member = stream['member']; data = members[member]
    records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
    primaries = {}
    for r in records:
        if r.is_primary: primaries.setdefault(r.object_id, []).append(r)
    checked = set()
    def raw(value):
        if isinstance(value, dict):
            fields = {'object_id', 'class_guid', 'record_offset', 'body_offset', 'end_offset', 'payload_hex'}
            if fields <= value.keys():
                r, = primaries[value['object_id']]
                assert (r.class_guid, r.start, r.body, r.end) == (value['class_guid'], value['record_offset'], value['body_offset'], value['end_offset'])
                assert data[r.body:r.end].hex() == value['payload_hex']; checked.add(r.object_id)
            for child in value.values(): raw(child)
        elif isinstance(value, list):
            for child in value: raw(child)
    raw(source)
    assert reference['feature_object_id'] in checked
    model = row['derived_geometry']
    _near(model['profile']['area_cm2'], reference['independent_profile_area_cm2'])
    _near(model['volume_cm3'], reference['independent_volume_cm3'])
    _near([model['component_axis_aligned_bounds_cm']['minimum'], model['component_axis_aligned_bounds_cm']['maximum']], reference['independent_bounds_cm'])
    assert len(model['boundary_curves']) == len(known)
    assert all(c['native_ENTITY_identity'] is None and c['native_UV'] is None for c in model['boundary_curves'])
    assert model['source_to_cache_entity_mapping'] is None
    return dict(source_reference=reference, raw_native_provenance_records=len(checked),
        native_source_provenance_sha256=digest(source), saved_API_result=saved_API_result(archive, reference),
        cache_geometry_proof=qualify_cache_geometry(row, members),
        identity_scope='All native tuple/source/Sketch/anchor/BODY/mapping identities fixed before equations; no native vertex or API entity chosen by coordinates')


def qualify_cache_geometry(row, members):
    """Fresh topology, native parameter equations and incidence (not the new core)."""
    import math
    from asm_records import inspect_asm
    from decode_brep import decode_topology
    topology = decode_topology(inspect_asm(members[row['history_blob_member']]))
    nodes = {n['index']: n for n in topology['nodes']}
    graph, = [g for g in topology['body_graphs'] if g['body_index'] == row['asm_body_index']]
    group, = row['native_source_provenance']['source_groups']
    n = len(group['derived_source_portions']); cache = row['native_cache_geometry_corroboration']
    assert graph['body_transform_is_identity'] is True
    assert graph['counts'] == cache['counts'] == dict(lump=1, shell=1, face=n+2, loop=n+2, coedge=6*n, edge=3*n, vertex=2*n)
    assert nodes[graph['body_index']]['stored_entity_id'] == group['binding']['stored_handle']
    identity = cache['identity_provenance']
    assert identity['endpoint_role_to_native_VERTEX'] is None and cache['endpoint_role_to_native_VERTEX'] is None
    assert cache['source_to_cache_entity_mapping'] is None
    portions = group['profile_portion_cache_corroboration']['qualified_profile_cache']
    roles = identity['portion_incidence']; assert len(roles) == n
    named_edges, named_coedges, side_faces, top_edges, connectors = set(), set(), set(), set(), set()
    for role in roles:
        ref = role['stored_full_tuple']; primitive = role['source_primitive_id']
        expected = [c for s in portions['source_curves'] if s['native_entity_object_id'] == primitive
            for c in s['cached_coedge_candidates'] if c['stored_decimal_text_fields'] == ref['stored_coedge_text_fields']]
        assert role['full_tuple_COEDGE_matches'] == expected and len(expected) == 2
        assert {c['edge_record_index'] for c in expected} == {role['base_edge_index']}
        for candidate in expected:
            coedge = nodes[candidate['coedge_record_index']]
            assert coedge['attribute_index'] == candidate['attribute_record_index']
            assert coedge['edge_index'] == candidate['edge_record_index']
            assert coedge['loop_index'] == candidate['loop_record_index']
            assert nodes[coedge['loop_index']]['face_index'] == candidate['face_record_index']
            named_coedges.add(coedge['index'])
        incident = {nodes[nodes[c['coedge_record_index']]['loop_index']]['face_index'] for c in expected}
        assert incident == {identity['base_cap_face_index'], role['side_face_index']}
        named_edges.add(role['base_edge_index']); side_faces.add(role['side_face_index']); top_edges.add(role['top_edge_index'])
        top = nodes[role['top_edge_index']]
        for c in role['connector_incidence']:
            edge = nodes[c['edge_index']]
            assert {edge['start_vertex_index'], edge['end_vertex_index']} == {c['base_vertex_index'], c['top_vertex_index']}
            base = nodes[role['base_edge_index']]
            assert c['base_vertex_index'] in (base['start_vertex_index'], base['end_vertex_index'])
            assert c['top_vertex_index'] in (top['start_vertex_index'], top['end_vertex_index'])
            connectors.add(c['edge_index'])
    assert len(named_edges) == len(top_edges) == len(side_faces) == len(connectors) == n
    assert named_edges | top_edges | connectors == set(graph['edge_indices'])
    assert {identity['base_cap_face_index'], identity['top_cap_face_index']} | side_faces == set(graph['face_indices'])
    all_coedges, point_plane_checks = set(), 0
    for loop in identity['loops']:
        fid, lid = loop['face_index'], loop['loop_index']
        assert nodes[fid]['first_loop_index'] == lid and nodes[lid]['face_index'] == fid
        cycle = loop['coedge_cycle']; assert set(cycle).isdisjoint(all_coedges)
        assert loop['native_LOOP'] == nodes[lid] and loop['native_COEDGEs'] == [nodes[c] for c in cycle]
        assert nodes[lid]['first_coedge_index'] == cycle[0]
        surface = nodes[nodes[fid]['surface_index']]
        for j, cid in enumerate(cycle):
            c = nodes[cid]
            assert c['loop_index'] == lid and c['next_coedge_index'] == cycle[(j+1)%len(cycle)]
            assert c['previous_coedge_index'] == cycle[(j-1)%len(cycle)]
            partner = nodes[c['partner_index']]
            assert partner['index'] != cid and partner['partner_index'] == cid and partner['edge_index'] == c['edge_index']
            if surface['kind'] == 'plane-surface':
                for end in ('start_vertex_index', 'end_vertex_index'):
                    point = nodes[nodes[nodes[c['edge_index']][end]]['point_index']]['raw_origin']
                    _near(sum(v*(p-o) for v, p, o in zip(surface['normal'], point, surface['raw_origin'])), 0.)
                    point_plane_checks += 1
        all_coedges.update(cycle)
    assert all_coedges == set(graph['coedge_indices'])
    evaluations, kinds, maximum_residual = 0, {}, 0.
    for eid in graph['edge_indices']:
        edge = nodes[eid]; curve = nodes[edge['curve_index']]
        assert edge['is_reversed'] is False  # Literal observation of these 126 bounded native EDGEs.
        kinds[curve['kind']] = kinds.get(curve['kind'], 0)+1
        uses = [c for c in graph['coedge_indices'] if nodes[c]['edge_index'] == eid]
        assert len(uses) == 2 and edge['first_coedge_index'] in uses
        for end in ('start', 'end'):
            p = edge[end+'_parameter']; actual = nodes[nodes[edge[end+'_vertex_index']]['point_index']]['raw_origin']
            if curve['kind'] == 'straight-curve':
                calculated = [o+p*d for o, d in zip(curve['raw_origin'], curve['direction'])]
            else:
                assert curve['kind'] == 'ellipse-curve'; u, normal = curve['stored_reference_axis'], curve['normal']
                ratio = curve['stored_axis_ratio']
                v = [ratio*(normal[1]*u[2]-normal[2]*u[1]), ratio*(normal[2]*u[0]-normal[0]*u[2]), ratio*(normal[0]*u[1]-normal[1]*u[0])]
                calculated = [o+math.cos(p)*x+math.sin(p)*y for o, x, y in zip(curve['raw_origin'], u, v)]
            _near(calculated, actual); maximum_residual = max(maximum_residual, math.dist(calculated, actual)); evaluations += 1
    return dict(native_cache_counts=graph['counts'], complete_tuple_named_base_edges=len(named_edges),
        complete_tuple_COEDGE_matches=len(named_coedges), independently_checked_native_endpoint_evaluations=evaluations,
        native_EDGE_curve_kinds=kinds, native_EDGE_reversed_flags={'False': len(graph['edge_indices'])},
        maximum_native_endpoint_residual_raw=maximum_residual, incident_planar_FACE_endpoint_checks=point_plane_checks,
        native_ENTITY_assignment_by_coordinates=None,
        scope='Complete tuple naming fixes base EDGE uses; reciprocal FACE/LOOP/COEDGE/EDGE/VERTEX incidence fixes other roles before independent raw native parameter equations and plane incidence')


def baseline_snapshot_provenance():
    """Reproduce the archived source bytes, without executing the decoder again."""
    import ast, hashlib, io, subprocess, tarfile
    payload = subprocess.check_output(['git', 'archive', BASELINE, '--', '*.py'], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(payload)) as archive:
        hashes = {m.name: hashlib.sha256(archive.extractfile(m).read()).hexdigest() for m in archive if m.isfile()}
    tree = ast.parse((ROOT/'validate_history_cache_integration.py').read_text())
    function, = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'baseline_outputs']
    return dict(baseline_commit=BASELINE, archived_Python_source_count=len(hashes),
        reproducible_git_archive_sha256=hashlib.sha256(payload).hexdigest(), archived_Python_source_sha256=hashes,
        trusted_acquisition_helper_AST_sha256=hashlib.sha256(ast.dump(function, include_attributes=False).encode()).hexdigest(),
        acquisition_method='Trusted baseline_outputs function extracted by AST; complete git archive d5f29a9 -- *.py extracted into a temporary directory; /usr/bin/python3 subprocess imports decode_basics and its dependencies with that directory as cwd',
        ephemeral_snapshot_path=None,
        scope='Actual acquisition used isolated committed dependencies. Temporary source directory was deleted by context manager. Source archive/module hashes were reproduced retrospectively without rerunning any decoder; they are not a retained live import trace.')


def validate(zstd, baseline_cache, current_cache):
    import json
    from validate_rectangular_cache_evidence_integration import sha
    before, current = read_cache(baseline_cache, 'before'), read_cache(current_cache, 'after')
    expected, sources = focused_evidence()
    assert [r['file'] for r in before] == [str(ROOT/f) for f in FILES] == [r['file'] for r in current]
    rows = [compare(a, b, f, expected[f], sources[f], zstd) for a, b, f in zip(before, current, FILES)]
    proofs = [p for r in rows for p in r['independent_geometry_proofs']]
    counts = {k: sum(p['cache_geometry_proof']['native_cache_counts'][k] for p in proofs)
        for k in ('lump', 'shell', 'face', 'loop', 'coedge', 'edge', 'vertex')}
    summary = dict(saved_files=19, decoded_trimmed_Extrudes=len(proofs), new_summaries=len(proofs),
        receiving_feature_annotations=sum(r['receiving_feature_annotations'] for r in rows),
        complete_selected_source_portions=sum(len(p['source_reference']['typed_source_portions']) for p in proofs),
        raw_native_provenance_records=sum(p['raw_native_provenance_records'] for p in proofs), native_cache_counts=counts,
        native_endpoint_evaluations=sum(p['cache_geometry_proof']['independently_checked_native_endpoint_evaluations'] for p in proofs),
        independently_checked_saved_API_bounds=len(proofs), independently_checked_saved_API_volumes=len(proofs),
        whole_output_unchanged_controls=sum(r['whole_output_unchanged'] for r in rows), unexpected_changes=0,
        comparator_baseline_main_calls=0, comparator_current_main_calls=0, live_API_calls=0)
    assert summary['decoded_trimmed_Extrudes'] == summary['receiving_feature_annotations'] == 15
    assert summary['complete_selected_source_portions'] == 42 and summary['native_endpoint_evaluations'] == 252
    assert counts == dict(lump=15, shell=15, face=72, loop=72, coedge=252, edge=126, vertex=84)
    assert summary['whole_output_unchanged_controls'] == 4
    truth_files = {str(Path(f).parent/'ground_truth.json') for f in FILES[:15]}
    return dict(scope='Fifteen selected native trimmed-profile straight Extrude reconstructions; independent source area/bounds/volume and reciprocal bounded native cache equations; all prior outputs preserved exactly',
        baseline_commit=BASELINE, files=list(FILES), summary=summary, samples=rows,
        fixed_manifest_acquisition=dict(baseline_main_calls=19, current_main_calls=19, baseline_passes=1, current_passes=1,
            interpreter='/usr/bin/python3', entrypoint='decode_basics.decode_basics(ROOT / filename, zstd_library)', fixed_order=list(FILES),
            scope='Original fixed acquisition; separate from this cached comparator with zero main-reader calls'),
        baseline_snapshot_provenance=baseline_snapshot_provenance(),
        cache_provenance={side: dict(path=str(Path(p).resolve()), sha256=sha(p)) for side, p in (('baseline', baseline_cache), ('current', current_cache))},
        frozen_production_sha256=FROZEN_PRODUCTION, frozen_main_sha256=FROZEN_MAIN_SHA256, evidence_sha256=FROZEN_EVIDENCE,
        saved_API_truth_sha256={f: sha(ROOT/f) for f in sorted(truth_files)},
        source_sha256={f: sha(ROOT/f) for f in ('validate_trimmed_extrusion_reconstruction_integration.py',
            'validate_rectangular_cache_evidence_integration.py', 'validate_history_cache_integration.py', 'decode_basics.py', *FROZEN_PRODUCTION)},
        limitations=[
            'Complete native tuple/primitive/Sketch/frame/anchor/BODY/asset identities precede all numerical comparison.',
            'Mathematical cycle orientation and endpoint joining establish abstract source boundary roles; they assign no native VERTEX, EDGE or API ENTITY identity.',
            'Bounded source Arc intervals are derived analytic reference-axis parameters, separate from serialized fields, API evaluator parameters and native traversal.',
            'All fifteen saved API complete result bounds and volumes corroborate after native joins; coordinates never choose an API or native entity.',
            'The current/final/historical and persistent identities of the selected source/cache remain unresolved; this is bounded reconstruction, not a general CAD solver.',
            'Four whole-Circle/rectangle/selected-plane/no-Extrude controls remain whole-output exact; every earlier profile portion, setting, warning and ASM output is unchanged.'])


def main():
    import argparse, json
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline-cache', required=True)
    parser.add_argument('--current-cache', required=True)
    parser.add_argument('--zstd-library')
    parser.add_argument('--output', default='trimmed-extrusion-reconstruction-integration.json')
    args = parser.parse_args()
    zstd = args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report = validate(zstd, args.baseline_cache, args.current_cache)
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))


if __name__ == '__main__': main()
