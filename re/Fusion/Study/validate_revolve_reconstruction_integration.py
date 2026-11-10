"""Fixed native Revolve construction integration with identity-first corroboration."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASELINE = '676607d'
FILES = (
    'models-97a5e41e2ba7/revolve_partial.f3d',
    'models-97a5e41e2ba7/revolve_full.f3d',
    'revolvemodes-8eb734486235/positive.f3d',
    'revolvemodes-8eb734486235/negative.f3d',
    'revolvemodes-8eb734486235/symmetric.f3d',
    'revolvemodes-8eb734486235/two_sided.f3d',
    'revolvemodes-8eb734486235/axis_x.f3d',
    'revolveaxes-36bd04ac77e1/custom_two_points.f3d',
    'revolveaxes-a83b542c4a07/sketch_line.f3d',
    'revolveaxes-a83b542c4a07/sketch_line_reversed.f3d',
    'revolveaxes-a83b542c4a07/brep_edge.f3d',
    'revolveaxes-14700158dba9/brep_edge_offset_x.f3d',
    'analytic-86a12b291d0a/analytic.f3d',
    'revolvemodes-8eb734486235/join.f3d',
    'revolvemodes-8eb734486235/cut.f3d',
    'revolvemodes-8eb734486235/intersect.f3d',
    'revolvemodes-8eb734486235/surface.f3d',
    'revolvemodes-b9796d532f94/project_axis.f3d',
    'revolveto-b1d196f65c46/positive_plane.f3d',
    'revolveto-b1d196f65c46/negative_plane.f3d',
    'revolveto-b1d196f65c46/two_planes.f3d',
    'extents-f0f33a9a605f/distance_positive.f3d',
    'placement-c6ad25e75d60/placement.f3d',
)
SUMMARY = ATTACHMENT = 'revolve_reconstruction'


from validate_trimmed_extrusion_reconstruction_integration import _near


def _dot(a, b): return sum(x*y for x, y in zip(a, b))
def _cross(a, b): return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def rectangle_source_reference(before, feature_id):
    """Source-only effective axis, angle domain and ring-sector integrals/extrema."""
    import math
    stream, = before['streams']; feature, = [f for f in stream['features'] if f['object_id'] == feature_id]
    assert feature['kind'] == 'Revolve' and feature['operation']['kind'] == 'NewBody'
    assert feature['is_solid'] is True and feature['is_project_axis'] is False
    settings = feature['revolve']; assert settings['extent_kind'] == 'Angle'
    selected, = feature['profile_selection']; loop, = selected['loops']; assert loop['is_outer'] is True
    refs = loop['curve_references']; assert len(refs) == 4 and all(r['entity_kind'] == 'Line' for r in refs)
    sketch, = [f for f in stream['features'] if f['kind'] == 'Sketch' and f['sketch_object_id'] == selected['sketch_object_id']]
    assert sketch['component_object_id'] == feature['component_object_id']
    native = {g['object_id']: g for g in sketch['geometry']}; matrix = sketch['placement']['sketch_to_component_matrix']
    points = {}; line_ids = []
    for ref in refs:
        line = native[ref['entity_id']]; assert line['kind'] == 'Line' and line['entity_tag'] == ref['entity_tag']
        line_ids.append(line['object_id'])
        for endpoint, value in zip((line['start_point_id'], line['end_point_id']), (line['start_cm'], line['end_cm'])):
            assert native[endpoint]['kind'] == 'Point'; _near(native[endpoint]['position_cm'], value)
            point = [sum(matrix[4*i+j]*value[j] for j in range(3))+matrix[4*i+3] for i in range(3)]
            if endpoint in points: _near(points[endpoint], point)
            points[endpoint] = point
    assert len(points) in (4, 8)  # Independently added Lines retain distinct coincident native POINT IDs.
    entity = settings['axis']['entity']; origin = entity['origin_cm']; raw_axis = entity['direction']
    _near(math.hypot(*raw_axis), 1.)
    normal = [matrix[2], matrix[6], matrix[10]]; _near(math.hypot(*normal), 1.)
    center = [sum(p[i] for p in points.values())/4 for i in range(3)]
    delta = [c-o for c, o in zip(center, origin)]; axial = _dot(delta, raw_axis)
    radial = [d-axial*a for d, a in zip(delta, raw_axis)]
    orientation = _dot(_cross(raw_axis, radial), normal); assert abs(orientation) > 1e-10
    effective = [(-1 if orientation < 0 else 1)*a for a in raw_axis]
    radius = math.hypot(*radial); u = [r/radius for r in radial]; v = _cross(effective, u)
    _near(_dot(v, normal), 1.)
    heights = []; radii = []
    for point in points.values():
        delta = [p-o for p, o in zip(point, origin)]; height = _dot(delta, effective)
        perpendicular = [d-height*a for d, a in zip(delta, effective)]; r = _dot(perpendicular, u)
        _near(perpendicular, [r*x for x in u]); assert r > 0
        heights.append(height); radii.append(r)
    h0, h1, r0, r1 = min(heights), max(heights), min(radii), max(radii)
    assert h1 > h0 and r1 > r0 > 0
    along = settings['angle_radians']; assert along != 0
    if settings['mode'] == 'OneSided': angle_interval = sorted((0., along))
    else:
        assert settings['mode'] in ('Symmetric', 'TwoSided')
        against = settings['against_angle_radians']; assert against > 0 and along > 0
        if settings['mode'] == 'Symmetric': _near(against, along)
        angle_interval = [-against, along]
    low, high = angle_interval; assert 0 < high-low <= 2*math.pi+1e-10
    candidates = [low, high]
    for i in range(3):
        phase = math.atan2(v[i], u[i])
        candidates.extend(t for k in range(-4, 5) if low <= (t := phase+k*math.pi) <= high)
    positions = [[origin[i]+h*effective[i]+r*(math.cos(t)*u[i]+math.sin(t)*v[i]) for i in range(3)]
        for h in (h0, h1) for r in (r0, r1) for t in candidates]
    return dict(feature_object_id=feature_id, native_sketch_object_id=selected['sketch_object_id'],
        native_profile_descriptor_object_id=selected['descriptor_object_id'], native_profile_loop_definition_object_id=selected['loop_definition_object_id'],
        native_profile_Line_ids=line_ids, native_profile_POINT_ids=list(points), native_component_points_cm=list(points.values()),
        native_axis_selection_record_object_id=settings['axis_selection_record_object_id'], native_axis_kind=entity['kind'],
        native_axis_origin_cm=origin, native_raw_axis_direction=raw_axis, native_sketch_normal=normal,
        source_only_orientation_triple_product=orientation, effective_axis_direction=effective, radial_reference=u,
        independently_derived_angular_interval_radians=angle_interval, axial_interval_cm=[h0, h1], radial_interval_cm=[r0, r1],
        independently_derived_volume_cm3=(high-low)*(r1*r1-r0*r0)*(h1-h0)/2,
        independently_derived_bounds_cm=[[min(p[i] for p in positions) for i in range(3)], [max(p[i] for p in positions) for i in range(3)]],
        native_ENTITY_assignment_by_coordinates=None,
        scope='Native profile/Sketch/axis joins precede source-only right-handed orientation, ring-sector integral and bounded angular extrema; no cached axis/vertices fit the sign')


EVIDENCE = 'revolve-reconstruction-decoding.json'
SOURCE_EVIDENCE = 'revolve-source-operand-decoding.json'
MATH_EVIDENCE = 'revolve-geometry-decoding.json'
FROZEN_PRODUCTION = {'decode_revolve_source_operands.py': '84d464ae5827a853b9bb79c4a9ab3c3f46e3a38fc608e5542b4875b6ce7a959d', 'decode_revolve_geometry.py': 'c611ae23feacfa587d19a87a6f4011f2e87395a08c540b281d7b1b03c544cc44', 'decode_revolve_reconstruction.py': 'b2e91e2bc0ea1fb67d3fe7d7ad6f339e9dc28cf5c3fd45a24d4e9564156f89d0'}
FROZEN_EVIDENCE = {'revolve-reconstruction-decoding.json': 'd6b5ffd627144c476317dff6df89a01bb5ccea32fa4c8ebe6b2d0d152a93b319', 'revolve-source-operand-decoding.json': '56ebc090f471bea72b12f46b3f217b191f7df32ca0a409feded3e7cc00e7d324', 'revolve-geometry-decoding.json': 'c7cd9903c682d9d39694cd8f56798b43e174d5b5fd9fffa9022f7adb6f60025a'}
FROZEN_MAIN_SHA256 = '1ce45522c7c7350216fb8944cf6ce9cfd5547e5d41cb65c02f378247c338eec0'


def read_cache(path, side):
    import json
    from validate_rectangular_cache_evidence_integration import sha
    cache = json.loads(Path(path).read_text())
    assert cache['baseline_commit'] == BASELINE and cache['files'] == list(FILES)
    assert cache['acquisition_main_calls'] == 23 and cache['acquisition_passes'] == 1 and len(cache[side]) == 23
    if side == 'before':
        assert cache['archive_sha256'] == {f: sha(ROOT/f) for f in FILES}
        assert cache['baseline_snapshot_provenance']['archived_Python_source_sha256']
    else:
        assert cache['production_source_sha256'] == FROZEN_PRODUCTION
        assert cache['main_source_sha256'] == FROZEN_MAIN_SHA256 == sha(ROOT/'decode_basics.py')
    return cache


def focused_evidence():
    import json
    from validate_rectangular_cache_evidence_integration import sha
    assert FROZEN_PRODUCTION and FROZEN_EVIDENCE and FROZEN_MAIN_SHA256
    for filename, expected in {**FROZEN_PRODUCTION, **FROZEN_EVIDENCE, 'decode_basics.py': FROZEN_MAIN_SHA256}.items():
        assert sha(ROOT/filename) == expected, (filename, 'Frozen source/evidence changed')
    reports = [json.loads((ROOT/f).read_text()) for f in (EVIDENCE, SOURCE_EVIDENCE, MATH_EVIDENCE)]
    for report in reports:
        for filename, expected in report['source_sha256'].items():
            assert sha(ROOT/filename) == expected, (filename, 'Stale focused source provenance')
    summaries = {s['archive']: s['expected_summary'] for s in reports[0]['samples'] if s['archive'] in FILES}
    sources = {s['archive']: s['expected_sources'] for s in reports[1]['samples'] if s['archive'] in FILES}
    assert set(summaries) == set(sources) == set(FILES)
    for archive in FILES:
        summary = summaries[archive]; assert set(summary) == {'decoded', 'unresolved', 'scope'}
        source_by_id = {s['feature_object_id']: s for s in sources[archive]}
        assert len(source_by_id) == len(sources[archive])
        for row in summary['decoded']:
            assert row['native_source_provenance'] == source_by_id[row['feature_object_id']]
        if archive in FILES[-2:]:
            assert not summary['decoded'] and not summary['unresolved'] and not sources[archive]
    return summaries, sources


def compare(before, current, archive, expected, sources, zstd):
    import copy
    from validate_rectangular_cache_evidence_integration import sha, digest, differences
    restored = copy.deepcopy(current); old, = before['streams']; stream, = restored['streams']
    assert old['member'] == stream['member'] and SUMMARY not in old
    proofs = []
    if expected['decoded'] or expected['unresolved']:
        assert stream.pop(SUMMARY) == expected
    else:
        assert SUMMARY not in stream
    source_by_id = {r['feature_object_id']: r for r in sources}
    for row in expected['decoded']:
        identity = row['feature_object_id']
        feature, = [f for f in stream['features'] if f['object_id'] == identity]
        prior, = [f for f in old['features'] if f['object_id'] == identity]
        assert prior['kind'] == feature['kind'] == 'Revolve' and ATTACHMENT not in prior
        assert feature.pop(ATTACHMENT) == row
        proofs.append(qualify(row, before, source_by_id[identity], archive, zstd))
    assert all(ATTACHMENT not in f for f in stream.get('features', []))
    assert restored == before, (archive, 'Unexpected prior-output change', differences(before, restored))
    return dict(archive=archive, archive_sha256=sha(ROOT/archive), decoded_Revolves=len(expected['decoded']),
        explicit_unresolved_Revolves=len(expected['unresolved']), receiving_feature_annotations=len(proofs),
        independent_geometry_proofs=proofs, whole_output_unchanged=current == before,
        whole_output_exact_after_removing_only_new_summary_and_successful_owner_annotations=True,
        all_previous_profile_settings_warnings_kinds_timeline_ASM_geometry_topology_and_placement_exact=True,
        baseline_output_sha256=digest(before), current_output_sha256=digest(current),
        qualified_difference_paths=differences(before, current))


def analytic_source_reference(before, feature_id):
    """Independent full-turn Sphere/Torus/Cone equations from typed native profiles."""
    import math
    stream, = before['streams']; feature, = [f for f in stream['features'] if f['object_id'] == feature_id]
    assert feature['kind'] == 'Revolve' and feature['operation']['kind'] == 'NewBody'
    controls = feature['revolve']; _near(controls['angle_radians'], 2*math.pi)
    assert controls['mode'] == 'OneSided' and controls['extent_kind'] == 'Angle'
    selected, = feature['profile_selection']; loop, = selected['loops']; assert loop['is_outer']
    sketch, = [f for f in stream['features'] if f['kind'] == 'Sketch' and f['sketch_object_id'] == selected['sketch_object_id']]
    assert sketch['component_object_id'] == feature['component_object_id']
    native = {g['object_id']: g for g in sketch['geometry']}; matrix = sketch['placement']['sketch_to_component_matrix']
    refs = loop['curve_references']; primitives = [native[r['entity_id']] for r in refs]
    for ref, p in zip(refs, primitives): assert p['kind'] == ref['entity_kind'] and p['entity_tag'] == ref['entity_tag']
    def transform(point): return [sum(matrix[4*i+j]*point[j] for j in range(3))+matrix[4*i+3] for i in range(3)]
    axis = controls['axis']['entity']['direction']; origin = controls['axis']['entity']['origin_cm']; _near(math.hypot(*axis), 1.)
    if sorted(p['kind'] for p in primitives) == ['Arc', 'Line']:
        arc, = [p for p in primitives if p['kind'] == 'Arc']; line, = [p for p in primitives if p['kind'] == 'Line']
        center = transform(arc['center_cm']); radius = arc['radius_cm']
        _near(arc['end_angle_radians']-arc['start_angle_radians'], math.pi)
        for endpoint in (line['start_cm'], line['end_cm']):
            point = transform(endpoint); d = [p-c for p, c in zip(point, center)]
            _near(math.hypot(*d), radius); _near(d, [_dot(d, axis)*a for a in axis])
        d = [c-o for c, o in zip(center, origin)]; _near(d, [_dot(d, axis)*a for a in axis])
        kind = 'Sphere'; coefficients = dict(center_cm=center, radius_cm=radius)
        bounds = [[c-radius for c in center], [c+radius for c in center]]; volume = 4*math.pi*radius**3/3
    elif len(primitives) == 1 and primitives[0]['kind'] == 'Circle':
        circle = primitives[0]; center = transform(circle['center_cm']); radius = circle['radius_cm']
        delta = [c-o for c, o in zip(center, origin)]; height = _dot(delta, axis)
        axis_point = [o+height*a for o, a in zip(origin, axis)]; major = math.dist(center, axis_point)
        assert major > radius > 0
        kind = 'Torus'; coefficients = dict(center_cm=axis_point, unit_axis=axis, major_radius_cm=major, minor_radius_cm=radius)
        extents = [major*math.sqrt(max(0., 1-a*a))+radius for a in axis]
        bounds = [[c-e for c, e in zip(axis_point, extents)], [c+e for c, e in zip(axis_point, extents)]]
        volume = 2*math.pi**2*major*radius**2
    else:
        assert len(primitives) == 3 and all(p['kind'] == 'Line' for p in primitives)
        points = {p[k]: transform(p[v]) for p in primitives for k, v in (('start_point_id', 'start_cm'), ('end_point_id', 'end_cm'))}
        assert len(points) == 3
        classified = []
        for identity, point in points.items():
            delta = [p-o for p, o in zip(point, origin)]; h = _dot(delta, axis)
            classified.append((identity, point, h, math.hypot(*[d-h*a for d, a in zip(delta, axis)])))
        on_axis = [p for p in classified if p[3] < 1e-9]; radial, = [p for p in classified if p[3] >= 1e-9]
        assert len(on_axis) == 2
        base_axis, = [p for p in on_axis if abs(p[2]-radial[2]) < 1e-9]
        apex, = [p for p in on_axis if p is not base_axis]
        radius, height = radial[3], abs(apex[2]-base_axis[2]); assert radius > 0 and height > 0
        base = base_axis[1]; tip = apex[1]; toward_apex = [(p-b)/height for b, p in zip(base, tip)]
        kind = 'Cone'; coefficients = dict(base_center_cm=base, apex_cm=tip, unit_axis_toward_apex=toward_apex,
            base_radius_cm=radius, axial_height_cm=height, half_angle_radians=math.atan(radius/height))
        extents = [radius*math.sqrt(max(0., 1-a*a)) for a in axis]
        bounds = [[min(p, b-e) for p, b, e in zip(tip, base, extents)], [max(p, b+e) for p, b, e in zip(tip, base, extents)]]
        volume = math.pi*radius**2*height/3
    return dict(feature_object_id=feature_id, native_sketch_object_id=selected['sketch_object_id'],
        native_profile_descriptor_object_id=selected['descriptor_object_id'], native_profile_loop_definition_object_id=selected['loop_definition_object_id'],
        native_profile_primitive_ids=[p['object_id'] for p in primitives], native_profile_kind=kind,
        native_axis_selection_record_object_id=controls['axis_selection_record_object_id'],
        independently_derived_coefficients=coefficients, independently_derived_volume_cm3=volume,
        independently_derived_bounds_cm=bounds, native_ENTITY_assignment_by_coordinates=None,
        scope='Typed native selected profile and axis establish full-turn analytic equations before cache or API comparison; source mathematical roles assign no result ENTITY')


def saved_API_controls(archive, before, feature_id, reference):
    import json
    truth_file = str(Path(archive).parent/'ground_truth.json'); truth = json.loads((ROOT/truth_file).read_text())
    feature, = [f for f in before['streams'][0]['features'] if f['object_id'] == feature_id]
    sample, = [s for s in truth['samples'] if s['file'] == Path(archive).name]
    settings = sample.get('settings', {}); native = feature['revolve']; checks = 0
    if 'angle' in settings: _near(settings['angle'], native['angle_radians']); checks += 1
    if 'angle_radians' in settings: _near(settings['angle_radians'], native['angle_radians']); checks += 1
    if 'angleOne' in settings:
        _near(settings['angleOne'], native['angle_radians']); _near(settings['angleTwo'], native['against_angle_radians']); checks += 2
    actual_axis = sample.get('actual_axis'); entity = native['axis']['entity']
    if actual_axis:
        if 'start_cm' in actual_axis:
            _near(actual_axis['start_cm'], entity['start_cm']); _near(actual_axis['end_cm'], entity['end_cm']); checks += 2
        else:
            _near(actual_axis['origin_cm'], entity['origin_cm']); _near(actual_axis['direction'], entity['direction']); checks += 2
    for p in sample.get('parameters', []):
        if p['role'] not in ('AlongAngle', 'AgainstAngle'): continue
        expected = native['angle_radians'] if p['role'] == 'AlongAngle' else native['against_angle_radians']
        _near(p['value'], expected); checks += 1
    assert checks
    return dict(truth_file=truth_file, actual_numerical_control_checks=checks,
        actual_axis=actual_axis, actual_settings=settings,
        saved_API_result_bounds=None, saved_API_result_volume=None, saved_API_result_vertex_set=None,
        API_ENTITY_assignment=None,
        scope='Saved API source-axis/angle controls corroborate after native source joins; these twelve captures contain no saved numerical result bounds, volume or vertex set')


def saved_API_analytic(archive, before, row, reference, graph, nodes):
    """Unique stored BODY name + typed mapping precede complete API bundle comparison."""
    import json, math
    stream, = before['streams']; body_id = row['source_native_body_object_id']
    body, = [b for b in stream['body_properties']['bodies'] if b['object_id'] == body_id]
    assert body['name_status'] == 'Stored custom name recovered'
    truth_file = str(Path(archive).parent/'ground_truth.json'); truth = json.loads((ROOT/truth_file).read_text())
    actual, = [b for b in truth['bodies'] if b['name'] == body['name']]
    assert actual['face_count'] == graph['counts']['face'] and actual['edge_count'] == graph['counts']['edge']
    assert actual['vertex_count'] == graph['counts']['vertex']
    kind = reference['native_profile_kind']; coefficients = reference['independently_derived_coefficients']
    if kind == 'Sphere':
        surface, = actual['surfaces']; assert surface['kind'] == kind
        _near(surface['origin'], coefficients['center_cm']); _near(surface['radius'], coefficients['radius_cm'])
    elif kind == 'Torus':
        surface, = actual['surfaces']; assert surface['kind'] == kind
        _near(surface['origin'], coefficients['center_cm']); _near(surface['majorRadius'], coefficients['major_radius_cm'])
        _near(surface['minorRadius'], coefficients['minor_radius_cm'])
        sign = 1 if _dot(surface['axis'], coefficients['unit_axis']) > 0 else -1
        _near(surface['axis'], [sign*a for a in coefficients['unit_axis']])
    else:
        cone, = [s for s in actual['surfaces'] if s['kind'] == 'Cone']; plane, = [s for s in actual['surfaces'] if s['kind'] == 'Plane']
        base = coefficients['base_center_cm']; tip = coefficients['apex_cm']; axis = coefficients['unit_axis_toward_apex']
        delta = [p-b for p, b in zip(cone['origin'], base)]; height = _dot(delta, axis)
        _near(delta, [height*a for a in axis])
        _near(cone['radius'], coefficients['base_radius_cm']*(1-height/coefficients['axial_height_cm']))
        _near(abs(cone['halfAngle']), coefficients['half_angle_radians'])
        sign = 1 if _dot(cone['axis'], axis) > 0 else -1; _near(cone['axis'], [sign*a for a in axis])
        _near(_dot(plane['normal'], [p-b for p, b in zip(plane['origin'], base)]), 0.)
        sign = 1 if _dot(plane['normal'], axis) > 0 else -1; _near(plane['normal'], [sign*a for a in axis])
    positions = [nodes[nodes[v]['point_index']]['raw_origin'] for v in graph['vertex_indices']]
    # This is a complete unordered bundle comparison, with no assignment of API vertices to native IDs.
    assert len(positions) == len(actual['vertex_positions_cm'])
    from itertools import permutations
    if positions:
        assert any(all(math.dist(p, q) < 2e-8 for p, q in zip(positions, ordered)) for ordered in permutations(actual['vertex_positions_cm']))
    else:
        assert actual['vertex_positions_cm'] == []
    return dict(truth_file=truth_file, native_body_object_id=body_id, explicit_stored_BODY_name=body['name'],
        actual_API_body_geometry=actual, complete_unordered_native_vertex_positions_cm=positions,
        API_ENTITY_assignment=None, geometry_selects_native_or_API_identity=False,
        saved_API_result_bounds=None, saved_API_result_volume=None,
        scope='Native owned anchor/BODY/name/same-asset stored-ID mapping precedes uniquely named complete API analytic coefficients/counts and unordered vertex-bundle corroboration; no ordinal or coordinate ENTITY mapping')


def qualify(row, before, source, archive, zstd):
    import math
    from fusion_archive import read_members
    from fusion_metadata import design_records
    from asm_records import inspect_asm
    from decode_brep import decode_topology
    from validate_rectangular_cache_evidence_integration import digest
    assert row['native_source_provenance'] == source and row['feature_object_id'] == source['feature_object_id']
    feature_id = row['feature_object_id']; stream, = before['streams']
    feature, = [f for f in stream['features'] if f['object_id'] == feature_id]
    group, = source['source_groups']; assert source['source_group_count'] == 1
    assert group['source_feature_object_id'] == feature_id
    selection, = feature['profile_selection']; selected = group['native_profile_selection']
    assert selected['native_sketch_object_id'] == selection['sketch_object_id']
    assert selected['profile_descriptor_object_id'] == selection['descriptor_object_id']
    assert selected['profile_loop_definition_object_id'] == selection['loop_definition_object_id']
    assert selected['profile_loops'] == selection['loops']
    assert source['source_axis']['selection_object_id'] == feature['revolve']['axis_selection_record_object_id']
    for key in ('origin_cm', 'direction'):
        _near(source['source_axis']['entity'][key], feature['revolve']['axis']['entity'][key])
    anchor, = [a for a in stream['body_selections']['body_anchors'] if a['object_id'] == group['body_anchor_object_id']]
    assert anchor['source_owner_object_id'] == feature_id and anchor['native_body_object_id'] == group['native_body_object_id']
    mapping, = [m for m in stream['body_blob_bindings']['decoded'] if m['mapping_record_object_id'] == group['mapping_record_object_id']]
    binding, = [b for b in mapping['bindings'] if b['native_body_object_id'] == group['native_body_object_id']]
    native_binding_keys = ('native_body_object_id', 'stored_handle', 'asm_body_index', 'asm_stored_entity_id', 'asm_body_record_offset', 'asm_identifier_token_offset')
    assert {k: binding[k] for k in native_binding_keys} == {k: group['binding'][k] for k in native_binding_keys}
    assert row['source_native_body_object_id'] == group['native_body_object_id'] and row['binding'] == group['binding']
    assert row['asm_body_index'] == group['asm_body_index'] and row['history_blob_member'] == mapping['history_blob_member'] == group['history_blob_member']
    members = read_members(ROOT/archive, zstd); member = stream['member']; data = members[member]
    records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')]); primary = {}
    for r in records:
        if r.is_primary: primary.setdefault(r.object_id, []).append(r)
    checked = set()
    def raw(value):
        if isinstance(value, dict):
            fields = {'object_id', 'class_guid', 'record_offset', 'body_offset', 'end_offset', 'payload_hex'}
            if fields <= value.keys():
                r, = primary[value['object_id']]
                assert (r.class_guid, r.start, r.body, r.end) == (value['class_guid'], value['record_offset'], value['body_offset'], value['end_offset'])
                assert data[r.body:r.end].hex() == value['payload_hex']; checked.add(r.object_id)
            for child in value.values(): raw(child)
        elif isinstance(value, list):
            for child in value: raw(child)
    raw(source); assert feature_id in checked
    topology = decode_topology(inspect_asm(members[row['history_blob_member']]))
    nodes = {n['index']: n for n in topology['nodes']}; graph, = [g for g in topology['body_graphs'] if g['body_index'] == row['asm_body_index']]
    assert nodes[graph['body_index']]['stored_entity_id'] == group['binding']['stored_handle'] and graph['body_transform_is_identity'] is True
    model = row['derived_geometry']; cache = row['native_cache_geometry_corroboration']
    assert model['source_to_cache_entity_mapping'] is None and cache['mathematical_role_to_native_ENTITY_mapping'] is None
    if archive == FILES[12]:
        reference = analytic_source_reference(before, feature_id)
        if reference['native_profile_kind'] == 'Cone':
            assert model['kind'] == 'PolygonRevolve' and len(model['meridian_profile']['vertices']) == 3
        else:
            assert model['kind'] == reference['native_profile_kind']
        API = saved_API_analytic(archive, before, row, reference, graph, nodes)
    else:
        reference = rectangle_source_reference(before, feature_id)
        _near(model['effective_axis']['direction'], reference['effective_axis_direction'])
        _near(model['angular_interval_radians'], reference['independently_derived_angular_interval_radians'])
        API = saved_API_controls(archive, before, feature_id, reference)
    _near(model['volume_cm3'], reference['independently_derived_volume_cm3'])
    _near([model['component_axis_aligned_bounds_cm']['minimum'], model['component_axis_aligned_bounds_cm']['maximum']], reference['independently_derived_bounds_cm'])
    native_checks = qualify_native_cache(cache, graph, nodes)
    for key in ('exact_API_handle_identity', 'current_or_final_geometry_identity', 'qualified_historical_state'): assert row[key] is None
    return dict(feature_object_id=feature_id, source_reference=reference, raw_native_provenance_records=len(checked),
        native_source_provenance_sha256=digest(source), independent_native_cache_geometry=native_checks,
        saved_API_corroboration=API,
        scope='Native selected profile/axis/component/owned anchor/BODY/same-asset IDs and literal frames precede independent equations; no target-axis fitting or coordinate ENTITY assignment')


def qualify_native_cache(cache, graph, nodes):
    import math
    assert cache['counts'] == graph['counts']
    assert len(cache['native_analytic_faces']) == graph['counts']['face']
    assert len(cache['native_bounded_edges']) == graph['counts']['edge']
    assert len(cache['native_vertices']) == graph['counts']['vertex']
    for row in cache['native_vertices']:
        v = row['native_VERTEX']; assert v == nodes[v['index']] and row['native_POINT'] == nodes[v['point_index']]
    edge_evals = singular = planar_incidence = 0; flags = {}; max_residual = 0.
    for row in cache['native_bounded_edges']:
        edge = row['native_EDGE']; assert edge == nodes[edge['index']] and edge['index'] in graph['edge_indices']
        flags[str(edge['is_reversed'])] = flags.get(str(edge['is_reversed']), 0)+1
        ends = [nodes[nodes[edge[k]]['point_index']]['raw_origin'] for k in ('start_vertex_index', 'end_vertex_index')]
        if edge['curve_index'] is None:
            assert edge['start_vertex_index'] == edge['end_vertex_index']; singular += 1; continue
        curve = nodes[edge['curve_index']]; assert row['native_curve'] == curve
        calculated = []
        for parameter in (edge['start_parameter'], edge['end_parameter']):
            if curve['kind'] == 'straight-curve':
                value = [o+parameter*d for o, d in zip(curve['raw_origin'], curve['direction'])]
            else:
                assert curve['kind'] == 'ellipse-curve'; u, n = curve['stored_reference_axis'], curve['normal']; ratio = curve['stored_axis_ratio']
                v = [ratio*(n[1]*u[2]-n[2]*u[1]), ratio*(n[2]*u[0]-n[0]*u[2]), ratio*(n[0]*u[1]-n[1]*u[0])]
                value = [o+math.cos(parameter)*x+math.sin(parameter)*y for o, x, y in zip(curve['raw_origin'], u, v)]
            calculated.append(value)
        _near(calculated, row['native_endpoint_evaluations_cm'])
        # Native endpoint order may use a distinct orientation convention; compare the complete two-position bundle.
        errors = [max(math.dist(p, q) for p, q in zip(calculated, candidate)) for candidate in (ends, list(reversed(ends)))]
        assert min(errors) < 2e-8; max_residual = max(max_residual, min(errors)); edge_evals += 2
    seen_loops, seen_coedges = set(), set()
    for row in cache['native_analytic_faces']:
        face = row['native_FACE']; surface = row['native_surface']
        assert face == nodes[face['index']] and face['index'] in graph['face_indices'] and surface == nodes[face['surface_index']]
        for loop in row['native_boundary_loops']:
            lid = loop['loop_index']; assert lid not in seen_loops and nodes[lid]['face_index'] == face['index']; seen_loops.add(lid)
            cycle = loop['coedge_cycle']
            for j, cid in enumerate(cycle):
                c = nodes[cid]; assert cid not in seen_coedges and c['loop_index'] == lid; seen_coedges.add(cid)
                assert c['next_coedge_index'] == cycle[(j+1)%len(cycle)] and c['previous_coedge_index'] == cycle[(j-1)%len(cycle)]
                if c['partner_index'] is not None:
                    partner = nodes[c['partner_index']]; assert partner['partner_index'] == cid and partner['edge_index'] == c['edge_index']
                edge = nodes[c['edge_index']]
                if surface['kind'] == 'plane-surface':
                    for end in ('start_vertex_index', 'end_vertex_index'):
                        point = nodes[nodes[edge[end]]['point_index']]['raw_origin']
                        _near(_dot(surface['normal'], [p-o for p, o in zip(point, surface['raw_origin'])]), 0.); planar_incidence += 1
    assert seen_loops == set(graph['loop_indices']) and seen_coedges == set(graph['coedge_indices'])
    return dict(native_cache_counts=graph['counts'], independently_evaluated_finite_native_endpoints=edge_evals,
        null_curve_singular_EDGE_count=singular, incident_planar_FACE_endpoint_checks=planar_incidence,
        literal_EDGE_reversal_flags=flags, maximum_native_endpoint_residual_raw=max_residual,
        mathematical_role_to_native_ENTITY_mapping=None,
        scope='Fresh typed mapped BODY topology and full literal node copies; reciprocal FACE/LOOP/COEDGE ownership plus independently evaluated raw finite Line/Circle domains, preserving singular edges and zero-edge smooth surfaces')


def validate(zstd, baseline_cache, current_cache):
    from validate_rectangular_cache_evidence_integration import sha
    baseline, acquisition = read_cache(baseline_cache, 'before'), read_cache(current_cache, 'after')
    before, current = baseline['before'], acquisition['after']; expected, sources = focused_evidence()
    assert [r['file'] for r in before] == [str(ROOT/f) for f in FILES] == [r['file'] for r in current]
    rows = [compare(a, b, f, expected[f], sources[f], zstd) for a, b, f in zip(before, current, FILES)]
    proofs = [p for row in rows for p in row['independent_geometry_proofs']]
    counts = {k: sum(p['independent_native_cache_geometry']['native_cache_counts'][k] for p in proofs)
        for k in ('lump', 'shell', 'face', 'loop', 'coedge', 'edge', 'vertex')}
    summary = dict(saved_files=23, decoded_Revolves=len(proofs), source_qualified_Revolves=sum(len(sources[f]) for f in FILES),
        explicit_unresolved_Revolves=sum(r['explicit_unresolved_Revolves'] for r in rows),
        new_summaries=sum(bool(expected[f]['decoded'] or expected[f]['unresolved']) for f in FILES),
        receiving_feature_annotations=sum(r['receiving_feature_annotations'] for r in rows),
        independent_rectangle_sector_constructions=sum('source_only_orientation_triple_product' in p['source_reference'] for p in proofs),
        independent_full_turn_analytic_constructions=sum('independently_derived_coefficients' in p['source_reference'] for p in proofs),
        raw_native_provenance_records=sum(p['raw_native_provenance_records'] for p in proofs), native_cache_counts=counts,
        finite_native_endpoint_evaluations=sum(p['independent_native_cache_geometry']['independently_evaluated_finite_native_endpoints'] for p in proofs),
        null_curve_singular_EDGE_count=sum(p['independent_native_cache_geometry']['null_curve_singular_EDGE_count'] for p in proofs),
        saved_API_source_axis_angle_numerical_checks=sum(p['saved_API_corroboration'].get('actual_numerical_control_checks', 0) for p in proofs),
        saved_API_analytic_body_bundles=sum('actual_API_body_geometry' in p['saved_API_corroboration'] for p in proofs),
        saved_API_analytic_vertex_positions=sum(len(p['saved_API_corroboration'].get('actual_API_body_geometry', {}).get('vertex_positions_cm', [])) for p in proofs),
        saved_API_result_bounds_controls=0, saved_API_result_volume_controls=0,
        whole_output_unchanged_controls=sum(r['whole_output_unchanged'] for r in rows), unexpected_changes=0,
        comparator_baseline_main_calls=0, comparator_current_main_calls=0, live_API_calls=0)
    assert summary['decoded_Revolves'] == summary['receiving_feature_annotations'] == 15
    assert summary['source_qualified_Revolves'] == 18 and summary['explicit_unresolved_Revolves'] == 11
    assert summary['independent_rectangle_sector_constructions'] == 12 and summary['independent_full_turn_analytic_constructions'] == 3
    assert summary['new_summaries'] == 21 and summary['whole_output_unchanged_controls'] == 2
    assert counts == dict(lump=15, shell=15, face=74, loop=77, coedge=275, edge=138, vertex=94)
    assert summary['finite_native_endpoint_evaluations'] == 274 and summary['null_curve_singular_EDGE_count'] == 1
    assert summary['saved_API_source_axis_angle_numerical_checks'] == 35
    assert summary['saved_API_analytic_body_bundles'] == 3 and summary['saved_API_analytic_vertex_positions'] == 2
    truth_files = {str(Path(f).parent/'ground_truth.json') for f in FILES[:13]}
    return dict(scope='Native source-profile/axis/angular Revolve reconstruction; source-only orientation and analytic integral/extrema checks, bounded same-asset native topology/geometry and saved API controls; all prior whole outputs preserved',
        baseline_commit=BASELINE, files=list(FILES), summary=summary, samples=rows,
        fixed_manifest_acquisition=dict(baseline_main_calls=23, current_main_calls=23, baseline_passes=1, current_passes=1,
            interpreter='/usr/bin/python3', entrypoint='decode_basics.decode_basics(ROOT / filename, zstd_library)', fixed_order=list(FILES),
            scope='Original fixed acquisition; separate from this cached comparator with zero main-reader calls'),
        baseline_snapshot_provenance=baseline['baseline_snapshot_provenance'],
        cache_provenance={side: dict(path=str(Path(p).resolve()), sha256=sha(p)) for side, p in (('baseline', baseline_cache), ('current', current_cache))},
        frozen_production_sha256=FROZEN_PRODUCTION, frozen_main_sha256=FROZEN_MAIN_SHA256, evidence_sha256=FROZEN_EVIDENCE,
        saved_API_truth_sha256={f: sha(ROOT/f) for f in sorted(truth_files)},
        source_sha256={f: sha(ROOT/f) for f in ('validate_revolve_reconstruction_integration.py',
            'validate_trimmed_extrusion_reconstruction_integration.py', 'validate_rectangular_cache_evidence_integration.py', 'decode_basics.py', *FROZEN_PRODUCTION)},
        limitations=[
            'Native selected profile/Sketch/axis/owned anchor/BODY/same-asset stored-ID identities precede all mathematical and numerical corroboration.',
            'Effective angular orientation is derived solely from source axis, occupied radial half-plane and Sketch normal. No target-cache rotation or best-fit sign chooses the axis.',
            'Symmetric 65-degree controls represent a 130-degree total span; along60/against25 represent [-25,+60] about the source-derived effective axis.',
            'Distinct coincident native POINT IDs remain distinct. Source endpoint joins establish mathematical polygon roles only, without native welding or result ENTITY identity.',
            'Twelve rectangle captures have saved source-axis/angle controls but no saved numerical API result bounds, volume or vertex sets. Derived bounds/volumes are not advertised as API-verified.',
            'Three analytic bodies have actual saved coefficients/counts and a two-position Cone vertex bundle; explicit unique stored BODY names are used only after typed native ownership/mapping, never API collection ordinal or geometry-selected identities.',
            'Three Boolean seed NewBody sources qualify but their modified complete caches fail reconstruction; eight receiving unsupported operations/modes remain explicit unresolved. No general Boolean regeneration is claimed.',
            'Full Sphere and Torus preserve actual zero-EDGE topology; the Cone retains its null-curve singular EDGE without an invented seam evaluator.',
            'All previous controls, settings, warnings, selection recipes, ASM geometry/topology and placement remain exact. Native/API UV, traversal, persistent and chronological/current/final identities remain unresolved.'])


def main():
    import argparse, json
    p = argparse.ArgumentParser(); p.add_argument('--baseline-cache', required=True); p.add_argument('--current-cache', required=True)
    p.add_argument('--zstd-library'); p.add_argument('--output', default='revolve-reconstruction-integration.json'); args = p.parse_args()
    zstd = args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report = validate(zstd, args.baseline_cache, args.current_cache)
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n'); print(json.dumps(report['summary'], sort_keys=True))


if __name__ == '__main__': main()
