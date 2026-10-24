"""Observed endpoint-normal construction planes on one explicit spline path.

PathDistance is admitted only at the captured unitless endpoints 0 and 1.
Interior arc-length mapping, distance-mode bytes and general paths stay unknown.
"""
import copy
import math
import struct
import uuid

from decode_loft_composite_guides import _source_geometry
from decode_parameters import read_string
from decode_plane_definitions import decode_plane_definitions
from decode_sketch import reference, same

PATH_METHOD = {13: ('AlongPath', 6, 8, ('path',), 'PathDistance', 171)}
SCOPE = 'Captured unitless endpoint PathDistance planes on an explicitly selected open fitted spline; cached plane origin/normal corroborated by native source evaluation, without general path-distance mapping or regeneration'


def decode_path_planes(data, records, features):
    candidates = {f['object_id'] for f in features if f['kind'] == 'ConstructionPlane'
                  and any(p.get('role') == 'PathDistance' for p in f.get('parameters', []))}
    if not candidates:
        return {'definitions': [], 'unresolved': [], 'scope': SCOPE}
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: items[0] for identity, items in grouped.items() if len(items) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Path-plane typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    def source(identity, role, owner):
        if role != 'path':
            return None
        _, descriptor = typed(identity, '5A1BF548-241F-46FD-9FB5-E4B05126EB9D')
        if (len(descriptor) != 263 or descriptor[:2] != bytes(2)
                or struct.unpack_from('<I', descriptor, 13)[0] != 1 or reference(descriptor, 252) != owner):
            raise ValueError('Unsupported path-plane owned source descriptor')
        namespace, cursor = read_string(descriptor, 17)
        entity_uuid, cursor = read_string(descriptor, cursor)
        for text in (namespace, entity_uuid):
            if len(text) != 36:
                raise ValueError('Unsupported path-plane source UUID length')
            uuid.UUID(text)
        if cursor != 169 or descriptor[169:181] != struct.pack('<QI', 2, 1):
            raise ValueError('Unsupported path-plane source context framing')
        context_id = reference(descriptor, 181)
        _, context = typed(context_id, '2319971D-8E07-441A-8F16-11C8F6F862D4')
        if len(context) != 1289:
            raise ValueError('Unobserved path-plane spline context layout')
        leaf_id = reference(descriptor, 2)
        _, leaf = typed(leaf_id, 'E2CEFD18-D755-4E09-8E7F-953A2F6D43F8')
        if len(leaf) != 26 or leaf[:10] != bytes(10):
            raise ValueError('Unsupported path-plane source sketch curve leaf')
        sketch_id, tag = struct.unpack_from('<QQ', leaf, 10)
        typed(sketch_id, '44A64366-4BD3-4B24-881A-F94C206E8F2D')
        matches = [(s, g) for s in features if s['kind'] == 'Sketch' and s['sketch_object_id'] == sketch_id
                   for g in s.get('geometry', []) if g.get('entity_tag') == tag]
        if len(matches) != 1 or matches[0][1]['kind'] != 'FittedSpline':
            raise ValueError('Path-plane explicit fitted spline source unresolved or ambiguous')
        sketch, curve = matches[0]
        typed(curve['object_id'], 'D82E012F-6DDD-4AED-BDE1-C0F7F9100B9B')
        if curve['sketch_object_id'] != sketch_id:
            raise ValueError('Path-plane decoded source curve/sketch ownership disagrees')
        if (descriptor[210:214] != b'\1\1\0\0' or descriptor[222:226] != b'\1\1\0\0'
                or descriptor[237:240] != b'\1\0\0' or descriptor[251] != 0):
            raise ValueError('Unsupported path-plane descriptor trailer')
        helper_id, support_id = reference(descriptor, 226), reference(descriptor, 240)
        _, helper = typed(helper_id, '5FBE538E-139B-46D4-BCAF-CC796D1E1F78')
        _, support = typed(support_id, '6CCF41D5-40BE-48ED-A834-18F3EAED6C57')
        if (helper != bytes.fromhex('0001000000000000000000000000')
                or len(support) != 77 or support[:12] != bytes(6)+b'\1\1'+struct.pack('<I', 2)
                or reference(support, 12) != sketch['object_id']
                or reference(support, 31) != identity or reference(support, 50) != identity
                or support[-8:] != bytes(8)):
            raise ValueError('Path-plane source support is not reciprocal')
        geometry = _source_geometry(sketch, curve)
        return {'role': role, 'input_record_object_id': identity, 'proxy_object_id': None,
                'entity': {'kind': 'SketchSplinePath', 'descriptor_object_id': identity,
                           'terminal_object_id': leaf_id, 'sketch_object_id': sketch_id,
                           'sketch_feature_object_id': sketch['object_id'], 'sketch_name': sketch.get('name'),
                           'curve_object_id': curve['object_id'], 'curve_entity_tag': tag,
                           'namespace_text': namespace, 'entity_guid_text': entity_uuid,
                           'context_object_id': context_id, 'context_payload_hex': context.hex(),
                           'context_status': 'Typed source context retained; no context matrix or traversal flags inferred',
                           'helper_object_id': helper_id, 'support_object_id': support_id,
                           'natural_source_geometry': geometry,
                           'association': 'Owned descriptor/native sketch-ID/curve-tag leaf with reciprocal support; coordinates never select source IDs'}}

    # Reuse strict common feature/backend/scalar/cache framing, without mutating
    # the original feature list or promoting unrelated plane variants.
    cloned = copy.deepcopy(features)
    parsed = decode_plane_definitions(data, records, cloned, method_schemas=PATH_METHOD, support_resolver=source)
    decoded, unresolved = [], [u for u in parsed['unresolved'] if u['feature_object_id'] in candidates]
    for item in parsed['definitions']:
        if item['stored_backend_method_code'] != 13:
            continue
        try:
            scalar, = item['scalar_parameters']
            fraction = scalar['value']
            if (scalar['units'] != 'unitless' or fraction not in (0.0, 1.0)
                    or item['stored_extra_offset_cm'] != 0.0):
                raise ValueError('Only captured endpoint PathDistance and zero ExtraOffset supported')
            geometry = item['support_inputs'][0]['entity']['natural_source_geometry']
            sample = geometry['analytic_samples'][0 if fraction == 0.0 else -1]
            derivative = sample['parameter_derivative_component']
            length = math.sqrt(sum(v*v for v in derivative))
            if not math.isfinite(length) or length <= 1e-12:
                raise ValueError('Degenerate path-plane endpoint tangent')
            normal = [v/length for v in derivative]
            cache = item['cached_geometry']
            if (not same(cache['origin_cm'], sample['point_component_cm'])
                    or not same(cache['normal'], normal)):
                raise ValueError('Path-plane cached origin/normal disagrees with explicitly selected spline endpoint')
            item.update(path_distance={'stored_value': fraction, 'units': 'unitless',
                                       'observed_position': 'StartEndpoint' if fraction == 0.0 else 'EndEndpoint',
                                       'mapping_scope': 'Endpoint correspondence only; interior proportional-distance/arc-length mapping and native distance-mode flags unverified'},
                        source_geometry_consistency={'endpoint_matches_plane_origin': True,
                                                     'normalized_derivative_matches_plane_normal': True},
                        definition_scope=SCOPE)
            decoded.append(item)
        except (ValueError, KeyError, IndexError) as error:
            unresolved.append({'feature_object_id': item['feature_object_id'], 'reason': str(error)})
    return {'definitions': decoded, 'unresolved': unresolved, 'scope': SCOPE}


def validate_fixtures(root, zstd_library):
    import json
    from pathlib import Path
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records

    root = Path(root)
    report = {'scope': SCOPE, 'samples': [], 'comparisons': [], 'older_controls': [], 'guards': [],
              'limitations': [
                  'Two planes in one saved single-spline archive, at requested path fractions 0 and 1 only.',
                  'Actual section-circle world center/normal getters corroborate the supporting cached planes; direct plane-definition getters were not saved.',
                  'Only unitless PathDistance and zero ExtraOffset are admitted. No native distance-mode flag or interior arc-length mapping is inferred.',
                  'Closed/composite/BRep paths, occurrences, general offsets and parametric regeneration remain unsupported.']}

    def load(relative):
        path = root/relative
        stream = decode_basics(path, zstd_library)['streams'][0]
        members = read_members(path, zstd_library)
        data = members[stream['member']]
        records, _ = design_records(data, members[stream['member'].replace('BulkStream.dat', 'MetaStream.dat')])
        return data, records, stream['features']

    def check(label, actual, expected):
        assert same(actual, expected), (label, actual, expected)
        report['comparisons'].append({'label': label, 'actual': actual, 'expected': expected, 'passed': True})

    relative = 'loftcompositeguides-8ea2ef593872/spline_centerline.f3d'
    data, records, features = load(relative)
    parsed = decode_path_planes(data, records, features)
    assert len(parsed['definitions']) == 2 and not parsed['unresolved']
    truth = next(s for s in json.loads((root/Path(relative).parent/'ground_truth.json').read_text())['samples']
                 if s['file'] == Path(relative).name)
    api_geometry = truth['source_curves_before_loft'][0]['natural_world_geometry']
    for index, item in enumerate(parsed['definitions']):
        actual_section = truth['settings']['sections'][index]
        geometry = item['cached_geometry']
        check(f'Plane{index} origin matches actual section-circle world center', geometry['origin_cm'], actual_section['circle_center_world_cm'])
        check(f'Plane{index} normal matches actual section-circle world normal', geometry['normal'], actual_section['circle_normal_world'])
        api_parameter = next(p for p in truth['parameters'] if p['created_by'] == 'Plane'+str(index+1) and p['role'] == 'PathDistance')
        check(f'Plane{index} scalar matches actual parameter getter', [item['path_distance']['stored_value']], [api_parameter['value']])
        source_geometry = item['support_inputs'][0]['entity']['natural_source_geometry']
        for observed, actual in zip(source_geometry['analytic_samples'], api_geometry['samples']):
            check(f'Plane{index} explicit source position at {actual["parameter_fraction"]}', observed['point_component_cm'], actual['point_cm'])
            check(f'Plane{index} explicit source derivative at {actual["parameter_fraction"]}', observed['parameter_derivative_component'], actual['tangent'])
    report['samples'].append({'file': relative, 'expected_summary': parsed,
                              'actual_section_getters': truth['settings']['sections'], 'actual_parameters': truth['parameters']})
    for relative_control in ('planedefinitions-6cd0820a832e/offset.f3d', 'planedefinitions-6cd0820a832e/tangent_at_point.f3d'):
        raw, rs, fs = load(relative_control)
        baseline = decode_plane_definitions(raw, rs, copy.deepcopy(fs))
        extra = decode_path_planes(raw, rs, fs)
        assert not extra['definitions'] and not extra['unresolved']
        assert decode_plane_definitions(raw, rs, copy.deepcopy(fs)) == baseline
        report['older_controls'].append({'file': relative_control, 'default_reader_unchanged': True, 'no_unrelated_path_inference': True})

    primary = {r.object_id: r for r in records if r.is_primary}
    for label, identity, offset, replacement in [
        ('Missing source curve tag', 280, 18, struct.pack('<Q', 999)),
        ('Source descriptor owner mismatch', 277, 253, struct.pack('<Q', 303)),
        ('Nonreciprocal source support', 278, 32, struct.pack('<Q', 310))]:
        record = primary[identity]
        changed = bytearray(data)
        changed[record.body+offset:record.body+offset+len(replacement)] = replacement
        result = decode_path_planes(bytes(changed), records, features)
        assert not any(d['feature_object_id'] == 270 for d in result['definitions'])
        error = next(e for e in result['unresolved'] if e['feature_object_id'] == 270)
        report['guards'].append({'label': label, 'reason': error['reason'], 'rejected': True})
    for label, role, value in [('Interior path-distance remains unsupported', 'PathDistance', 0.5),
                                ('Nonzero ExtraOffset remains unsupported', 'ExtraOffset', 1.0)]:
        changed = copy.deepcopy(features)
        feature = next(f for f in changed if f['object_id'] == 270)
        next(p for p in feature['parameters'] if p['role'] == role)['raw_float64'] = value
        result = decode_path_planes(data, records, changed)
        error = next(e for e in result['unresolved'] if e['feature_object_id'] == 270)
        report['guards'].append({'label': label, 'reason': error['reason'], 'rejected': True})
    report['validation'] = {'saved_files': 3, 'new_plane_definitions': 2,
                            'actual_API_comparisons': len(report['comparisons']), 'guards': len(report['guards']),
                            'direct_plane_definition_API_getters_captured': 0, 'new_API_calls': 0}
    return report


if __name__ == '__main__':
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parent
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report = validate_fixtures(root, zstd)
    (root/'path-plane-decoding.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['validation']))
