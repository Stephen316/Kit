"""Owned Hole placement providers joined to named sketch points by native leaves.

The Hole association list need not follow position order. Sketch ID and point
tag in independent typed leaves establish the join; coordinates corroborate it.
"""
import math
import struct
import uuid

from decode_holes import decode_hole
from decode_parameters import read_string
from decode_sketch import numbers, reference, same

HOLE = '1C037A07-4A15-43F6-ABFC-BBF61B9038D4'
PROVIDER = '69EE2FA7-BCC7-449E-9CA9-976CEFDFED44'
DESCRIPTOR = '5A1BF548-241F-46FD-9FB5-E4B05126EB9D'
NAMING = 'CB4F4CC2-9D6F-48BA-9B1F-20C1992C9C9C'
LEAF = 'D95DBAC0-238B-4429-A0AD-4AE5BEE79ADF'
SCOPE = 'Observed single/multiple Hole sketch-point sources through owned providers, typed sketch-ID/tag leaves and reciprocal supports; supporting faces, context transforms and persistent BRep topology unresolved'


def decode_hole_point_sources(data, records, features):
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: items[0] for identity, items in grouped.items() if len(items) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Hole point-source typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    def leaf(identity):
        _, payload = typed(identity, LEAF)
        if len(payload) != 18 or payload[:2] != bytes(2):
            raise ValueError('Unsupported Hole sketch point leaf')
        return struct.unpack_from('<QQ', payload, 2)

    def support(payload, start, source, owner, repeated):
        if (payload[start+18:start+22] != b'\1\1\0\0'
                or payload[start+30:start+34] != b'\1\1\0\0'
                or payload[start+45:start+48] != b'\1\0\0' or payload[start+59] != 0):
            raise ValueError('Unsupported Hole point-source support trailer')
        helper_id, support_id = reference(payload, start+34), reference(payload, start+48)
        _, helper = typed(helper_id, '5FBE538E-139B-46D4-BCAF-CC796D1E1F78')
        _, links = typed(support_id, '6CCF41D5-40BE-48ED-A834-18F3EAED6C57')
        count = 2 if repeated else 1
        if (helper != bytes.fromhex('0001000000000000000000000000')
                or len(links) != 39+19*count
                or links[:12] != bytes(6)+b'\1\1'+struct.pack('<I', count)
                or reference(links, 12) != source or reference(links, 31) != owner
                or (repeated and reference(links, 50) != owner) or links[-8:] != bytes(8)):
            raise ValueError('Hole point-source support references are not reciprocal')
        return {'helper_object_id': helper_id, 'support_object_id': support_id}

    decoded, unresolved = [], []
    for feature in features:
        if (feature['kind'] != 'Hole' or feature.get('tool_settings', {}).get('position_definition')
                not in ('SketchPoint', 'SketchPoints')):
            continue
        owner = feature['object_id']
        try:
            _, body = typed(owner, HOLE)
            settings = decode_hole(data, records, body, feature)
            if settings['position_definition'] not in ('SketchPoint', 'SketchPoints'):
                raise ValueError('Hole source mode disagrees with decoded settings')
            naming = {}
            for index, association in enumerate(settings['point_association_records']):
                naming_id = association['record_object_id']
                _, payload = typed(naming_id, NAMING)
                if len(payload) != 18 or payload[:6] != bytes.fromhex('000100000000') or payload[-1] != 0:
                    raise ValueError('Unsupported Hole point association naming framing')
                leaf_id = reference(payload, 6)
                key = leaf(leaf_id)
                if key in naming:
                    raise ValueError('Ambiguous repeated Hole naming point identity')
                naming[key] = {'association_ordinal': index, 'naming_record_object_id': naming_id,
                               'naming_leaf_object_id': leaf_id,
                               'stored_association_tag': association['stored_point_tag'],
                               'stored_association_tag_scope': 'Opaque separate field; never equated with a sketch entity tag'}
            sources, used = [], set()
            for index, provider_id in enumerate(settings['input_record_object_ids']['positions']):
                _, provider = typed(provider_id, PROVIDER)
                if (len(provider) != 178 or provider[:23] != bytes(23)
                        or struct.unpack_from('<I', provider, 47)[0] != 10
                        or struct.unpack_from('<I', provider, 75)[0] != 1
                        or reference(provider, 167) != owner):
                    raise ValueError('Unsupported owned Hole sketch-point provider')
                descriptor_id = reference(provider, 79)
                _, descriptor = typed(descriptor_id, DESCRIPTOR)
                if (len(descriptor) != 263 or descriptor[:2] != bytes(2)
                        or struct.unpack_from('<I', descriptor, 13)[0] != 1
                        or reference(descriptor, 252) != owner):
                    raise ValueError('Unsupported owned Hole point descriptor')
                namespace, cursor = read_string(descriptor, 17)
                entity_uuid, cursor = read_string(descriptor, cursor)
                for text in (namespace, entity_uuid):
                    if len(text) != 36:
                        raise ValueError('Unsupported Hole point-source UUID length')
                    uuid.UUID(text)
                if cursor != 169 or descriptor[169:181] != struct.pack('<QI', 2, 1):
                    raise ValueError('Unsupported Hole point-source context framing')
                context_id = reference(descriptor, 181)
                _, context = typed(context_id, '994C518A-A831-400A-B7C7-16DAC55F4F1C')
                if len(context) != 166 or context[:2] != bytes(2):
                    raise ValueError('Unobserved Hole point-source context layout')
                terminal_id = reference(descriptor, 2)
                key = leaf(terminal_id)
                if key not in naming or key in used:
                    raise ValueError('Hole provider/naming sketch point identity missing or ambiguous')
                used.add(key)
                sketch_id, tag = key
                typed(sketch_id, '44A64366-4BD3-4B24-881A-F94C206E8F2D')
                sketches = [s for s in features if s['kind'] == 'Sketch' and s['sketch_object_id'] == sketch_id]
                if len(sketches) != 1:
                    raise ValueError('Hole point source sketch unresolved or ambiguous')
                sketch = sketches[0]
                points = [p for p in sketch.get('geometry', []) if p['kind'] == 'Point' and p['entity_tag'] == tag]
                if len(points) != 1:
                    raise ValueError('Hole point source tag unresolved or ambiguous')
                point = points[0]
                _, native_point = typed(point['object_id'], 'C2CEDAE7-1716-47C1-B7B1-07B70081D0FB')
                if reference(native_point, len(native_point)-11) != sketch_id:
                    raise ValueError('Hole source point/sketch ownership disagrees')
                component_position = point.get('component_position_cm')
                cached = numbers(provider, 23, 3)
                if (component_position is None or not all(math.isfinite(v) for v in cached)
                        or not same(cached, component_position) or not same(cached, settings['positions_cm'][index])
                        or not same(cached, numbers(context, 2, 3))):
                    raise ValueError('Hole selected sketch point and independently framed caches disagree')
                provider_support = support(provider, 107, descriptor_id, provider_id, False)
                descriptor_support = support(descriptor, 192, sketch['object_id'], descriptor_id, True)
                sources.append({'position_ordinal': index, 'provider_object_id': provider_id,
                                'descriptor_object_id': descriptor_id, 'terminal_object_id': terminal_id,
                                'sketch_object_id': sketch_id, 'sketch_feature_object_id': sketch['object_id'],
                                'sketch_name': sketch.get('name'), 'point_object_id': point['object_id'],
                                'point_entity_tag': tag, 'position_cm': point['position_cm'],
                                'component_position_cm': component_position, 'cached_position_cm': cached,
                                'namespace_text': namespace, 'entity_guid_text': entity_uuid,
                                'context_object_id': context_id, 'context_payload_hex': context.hex(),
                                'context_status': 'Typed point cache retained; additional matrix/support semantics unresolved',
                                'provider_support': provider_support, 'descriptor_support': descriptor_support,
                                **naming[key]})
            if used != set(naming) or len(sources) != settings['position_count']:
                raise ValueError('Hole provider/naming point associations are not bijective')
            decoded.append({'feature_object_id': owner, 'position_definition': settings['position_definition'],
                            'point_sources': sources,
                            'association': 'Owned provider and separate naming leaves agree on sketch ID/tag; native position order retained without pairing association ordinals',
                            'coordinate_scope': 'Stored parent-component sketch placement; occurrence contexts and joint solving unverified'})
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            unresolved.append({'feature_object_id': owner, 'reason': str(error)})
    return {'decoded': decoded, 'unresolved': unresolved, 'scope': SCOPE}


def validate_fixtures(root, zstd_library):
    import copy
    import json
    from pathlib import Path
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records

    root = Path(root)
    report = {'scope': SCOPE, 'samples': [], 'older_controls': [], 'guards': [],
              'evidence_limits': [
                  'Single-point feature.position is an actual saved API getter.',
                  'Multiple input_positions_cm are original generator inputs, not post-creation source-point getters.',
                  'Source identity follows explicit sketch IDs/tags and reciprocal native links before comparing positions.',
                  'Stored association tags 304..306 belong to a separate opaque field, not source sketch tags 118..120.',
                  'Point-context matrix/tail semantics, supporting faces and assembly occurrences remain unresolved.']}

    def load(case):
        path = root/'holeplacements-04adf73afe93'/(case+'.f3d')
        members = read_members(path, zstd_library)
        model = decode_basics(path, zstd_library)
        stream = model['streams'][0]
        data = members[stream['member']]
        records, _ = design_records(data, members[stream['member'].replace('BulkStream.dat', 'MetaStream.dat')])
        return data, records, stream['features']

    truth = json.loads((root/'holeplacements-04adf73afe93/ground_truth.json').read_text())
    contexts = {}
    for case in ('sketch_point', 'sketch_points'):
        data, records, features = load(case)
        parsed = decode_hole_point_sources(data, records, features)
        assert not parsed['unresolved'] and len(parsed['decoded']) == 1
        item = parsed['decoded'][0]
        actual = next(s for s in truth['samples'] if s['file'] == case+'.f3d')
        positions = [p['component_position_cm'] for p in item['point_sources']]
        assert all(same(a, b) for a, b in zip(positions, actual['input_positions_cm']))
        assert len(positions) == len(actual['input_positions_cm'])
        if actual['position_cm'] is not None:
            assert same(positions[0], actual['position_cm'])
        report['samples'].append({'file': 'holeplacements-04adf73afe93/'+case+'.f3d',
                                  'expected_summary': parsed,
                                  'generator_input_positions_match': True,
                                  'actual_API_position_getter_match': True if actual['position_cm'] is not None else None})
        contexts[case] = data, records, features, parsed
    for case in ('reversed_distance', 'reversed_all', 'center_edge'):
        data, records, features = load(case)
        parsed = decode_hole_point_sources(data, records, features)
        assert not parsed['decoded'] and not parsed['unresolved']
        report['older_controls'].append({'file': 'holeplacements-04adf73afe93/'+case+'.f3d', 'no_unrelated_point_source_inference': True})

    data, records, features, expected = contexts['sketch_points']
    primary = {r.object_id: r for r in records if r.is_primary}
    hole = primary[347]
    changed = bytearray(data)
    a, b = data[hole.body+43:hole.body+62], data[hole.body+62:hole.body+81]
    changed[hole.body+43:hole.body+81] = b+a
    reordered = decode_hole_point_sources(bytes(changed), records, features)
    assert not reordered['unresolved']
    assert [p['point_object_id'] for p in reordered['decoded'][0]['point_sources']] == [341, 343, 345]
    assert [p['association_ordinal'] for p in expected['decoded'][0]['point_sources']] == [1, 0, 2]
    report['association_order_control'] = {'original_association_ordinals_in_position_order': [1, 0, 2],
                                           'swapping_native_association_pairs_preserves_position_to_point_IDs': True}

    def rejected(label, changed_data=data, changed_features=features):
        result = decode_hole_point_sources(changed_data, records, changed_features)
        assert not result['decoded'] and len(result['unresolved']) == 1, (label, result)
        report['guards'].append({'label': label, 'reason': result['unresolved'][0]['reason'], 'rejected': True})

    for label, identity, offset, replacement in [
        ('Missing provider point tag never falls back to coordinates', 358, 10, struct.pack('<Q', 999)),
        ('Naming point disagrees with provider identity', 379, 10, struct.pack('<Q', 999)),
        ('Provider owner must be the Hole', 359, 168, struct.pack('<Q', 286)),
        ('Provider support must refer to its own descriptor', 360, 13, struct.pack('<Q', 371)),
        ('Selected source position and provider cache must agree', 359, 23, struct.pack('<d', 99.0))]:
        record = primary[identity]
        changed = bytearray(data)
        changed[record.body+offset:record.body+offset+len(replacement)] = replacement
        rejected(label, bytes(changed))
    ambiguous = copy.deepcopy(features)
    sketch = next(f for f in ambiguous if f['kind'] == 'Sketch' and f['sketch_object_id'] == 282)
    sketch['geometry'].append(copy.deepcopy(next(p for p in sketch['geometry'] if p['object_id'] == 341)))
    rejected('Duplicate same-coordinate source tags are ambiguous', changed_features=ambiguous)
    report['validation'] = {'saved_files': 5, 'new_point_sources': 4,
                            'actual_API_feature_position_getter_comparisons': 1,
                            'generator_input_position_comparisons': 4,
                            'nonmatching_association_order_controls': 2, 'malformed_guards': len(report['guards']),
                            'new_API_calls': 0}
    return report


if __name__ == '__main__':
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zstd-library')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    zstd = args.zstd_library or next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report = validate_fixtures(root, zstd)
    (root/'hole-point-source-decoding.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['validation']))
