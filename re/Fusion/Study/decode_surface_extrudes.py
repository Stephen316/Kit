"""Observed sheet extrusions from closed circles and single open sketch lines.

The solid flag is corroborated by actual source-body getters in the open-line
captures and explicit generator settings in the circle captures. This reader
does not infer solid/surface state for other extrusion modes or regenerate it.
"""

import math
import struct
import uuid

from decode_body_selections import decode_body_selections
from decode_body_properties import BODY
from decode_extrude import decode_extrude, optional_reference
from decode_parameters import read_string
from decode_profile_selections import resolve_sketch_profiles
from decode_selection import native_proxy_references, resolve_single_sketch_curve
from decode_sketch import reference


EXTRUDE = 'DD405BC2-D673-44F0-8833-5CB2A1C186C7'
PROXY = '2CA5A1CD-C99B-4C9B-91AF-57989148E841'
SCOPE = 'Observed positive one-sided NewBody sheet extrusions from one closed sketch Circle or one open sketch Line; no surface generation, general extents or persistent result topology'


def decode_surface_extrudes(data, records, features):
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: items[0] for identity, items in grouped.items() if len(items) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Surface extrusion typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    candidates = []
    for feature in features:
        if feature['kind'] != 'Extrude' or feature['class_guid'] != EXTRUDE:
            continue
        record = primary.get(feature['object_id'])
        if record is None:
            continue
        payload = data[record.body:record.end]
        try:
            _, cursor = optional_reference(payload, 6)
            # Ordinary solid extrusions remain entirely with the original reader.
            if payload[cursor+15] == 0:
                candidates.append((feature, payload))
        except (ValueError, IndexError, struct.error):
            continue
    decoded, unresolved = [], []
    bodies = decode_body_selections(data, records) if candidates else None
    for feature, payload in candidates:
        owner = feature['object_id']
        try:
            if (len(payload) < 378 or payload[:24] != bytes.fromhex('000100000000000000040000000100000002000000000000')
                    or struct.unpack_from('<I', payload, 128)[0] != 1
                    or payload[143:147] != bytes(4) or struct.unpack_from('<I', payload, 147)[0] != 1
                    or payload[162:170] != bytes(8) or payload[246:249] != bytes(3)):
                raise ValueError('Unobserved surface extrusion header/input/output layout')
            namespace, cursor = read_string(payload, 170)
            if namespace != str(uuid.UUID(int=0)) or cursor != 246:
                raise ValueError('Surface extrusion metadata namespace framing changed')
            fields, reasons = decode_extrude(payload, feature, allow_surface=True)
            extent = fields['extent']
            if (reasons or fields['is_solid'] is not False or fields['start'] != {'stored_code': 0, 'kind': 'ProfilePlane'}
                    or fields['operation'] != {'stored_code': 4, 'kind': 'NewBody'} or extent['mode'] != 'OneSided'
                    or extent['side_one_condition'] != 'Distance' or len(feature['parameters']) != 2
                    or not math.isfinite(extent['side_one']['distance_cm']) or extent['side_one']['distance_cm'] <= 0
                    or extent['side_one'].get('taper_angle_radians') != 0):
                raise ValueError('Only captured positive NewBody one-sided untapered surface extrusion supported')
            proxy_id = reference(payload, 132)
            proxy_record, proxy = typed(proxy_id, PROXY)
            descriptor_ids, props = native_proxy_references(data, proxy_record)
            if (len(proxy) != 105 or props or len(descriptor_ids) != 1
                    or reference(proxy, len(proxy)-11) != owner):
                raise ValueError('Surface extrusion profile proxy count/owner changed')
            descriptor_id = descriptor_ids[0]
            if struct.unpack_from('<I', payload, 249)[0] != 5:
                raise ValueError('Surface extrusion dependency count changed')
            refs = [reference(payload, 253+11*i) for i in range(5)]
            bindings = fields['extrusion_reference_fields']
            expected = [proxy_id, descriptor_id, bindings['along'], bindings['taper'], bindings['opaque']]
            if refs != expected:
                raise ValueError('Surface extrusion repeated profile/parameter reference table disagrees')
            _, extent_cache = typed(bindings['opaque'], '0897AF07-EF1B-42E5-BDD9-1C746A085CBC')
            if len(extent_cache) != 81 or reference(extent_cache, 2) != owner or reference(extent_cache, 70) != owner:
                raise ValueError('Surface extrusion auxiliary cache reciprocal owner changed')
            label, cursor = read_string(payload, 312)
            if label != 'Extrude' or struct.unpack_from('<Q', payload, cursor)[0] != feature['stored_index']:
                raise ValueError('Surface extrusion native kind/index disagrees')
            name, cursor = read_string(payload, cursor+8)
            if (name or None) != feature.get('name'):
                raise ValueError('Surface extrusion stored name disagrees')
            descriptor = primary.get(descriptor_id)
            if descriptor is None:
                raise ValueError('Surface extrusion profile descriptor unresolved')
            if descriptor.class_guid == '4BD53E5A-0B3E-45E5-AE8B-02044306485A':
                profiles = resolve_sketch_profiles(data, records, proxy_id, owner, features)
                if (len(profiles) != 1 or len(profiles[0]['loops']) != 1 or not profiles[0]['loops'][0]['is_outer']
                        or len(profiles[0]['loops'][0]['curve_references']) != 1
                        or profiles[0]['loops'][0]['curve_references'][0]['entity_kind'] != 'Circle'):
                    raise ValueError('Only captured single closed Circle surface profile supported')
                profile = {'kind': 'SketchProfile', **profiles[0]}
            elif descriptor.class_guid == '5A1BF548-241F-46FD-9FB5-E4B05126EB9D':
                profile = {'profile_kind': 'SketchOpenProfile',
                           **resolve_single_sketch_curve(data, records, proxy_id, owner, features, ('Line',))}
            else:
                raise ValueError('Unobserved surface extrusion profile kind')
            anchor_id = reference(payload, 151)
            anchors = [a for a in bodies['body_anchors'] if a['object_id'] == anchor_id and a['source_owner_object_id'] == owner]
            if len(anchors) != 1:
                raise ValueError('Surface extrusion explicitly owned result body anchor unresolved')
            anchor = anchors[0]
            decoded.append({'feature_object_id': owner, 'settings': fields, 'profile': profile,
                            'result_anchor_object_id': anchor_id, 'native_body_object_id': anchor['native_body_object_id'],
                            'body_scope': 'Explicit owned historical/result native body anchor; current visibility and persistent ASM topology not inferred',
                            'uninterpreted_feature_footer_hex': payload[cursor:].hex(), 'scope': SCOPE})
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            unresolved.append({'feature_object_id': owner, 'reason': str(error)})
    return {'decoded': decoded, 'unresolved': unresolved, 'scope': SCOPE}


def validate_fixtures(root, zstd_library=None):
    import copy
    import json
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records

    filenames = ['moretools-88a2cd6cad0b/Thicken.f3d',
                 'sweepprofiles-8d489fe02d2d/open_brep_edge_surface.f3d',
                 'sweepprofiles-b2b7a2774752/open_brep_edge_surface.f3d',
                 'sweepprofiles-f20861d6c5c2/open_brep_edge_partial.f3d',
                 'sweepprofiles-f20861d6c5c2/open_brep_edge_reversed.f3d']
    filenames += ['thickenmodes-17612e4ff890/'+case+'.f3d' for case in ('cut', 'intersect', 'join')]
    filenames += ['thickenmodes-552efbb83fca/'+case+'.f3d' for case in ('body_input', 'negative', 'positive', 'rounded', 'symmetric')]
    report = {'scope': SCOPE, 'samples': [], 'negative_checks': [],
              'is_solid_evidence': 'Four actual source-body isSolid getters in open-line Sweep captures; circle generators explicitly set isSolid=False. No actual completed Extrude.isSolid getter was saved.',
              'parameter_evidence': 'Actual model parameter name/role/value/createdBy getters, not display-unit converted requested strings',
              'interface': 'decode_surface_extrudes(data,records,features); no feature mutation'}
    for filename in filenames:
        archive = root/filename
        main = decode_basics(archive, zstd_library);stream = main['streams'][0]
        members = read_members(archive, zstd_library);data = members[stream['member']]
        records, _ = design_records(data, members.get(stream['member'].replace('BulkStream.dat', 'MetaStream.dat')))
        by = {r.object_id: r for r in records if r.is_primary}
        result = decode_surface_extrudes(data, records, stream['features'])
        assert len(result['decoded']) == 1 and not result['unresolved'], (filename, result['unresolved'])
        item = result['decoded'][0]
        feature = next(f for f in stream['features'] if f['object_id'] == item['feature_object_id'])
        truth = json.loads((archive.parent/'ground_truth.json').read_text())
        sample = next(s for s in truth['samples'] if s['file'] == archive.name)
        actual = [p for p in sample['parameters'] if p['created_by'] == feature['name']]
        checks = {'two_native_bindings_match_actual_parameter_getters':
                      len(actual) == 2 and all(any(p['name'] == native['parameter_name'] and p['role'] == native['role']
                          and p['value'] == native['raw_float64'] for p in actual) for native in feature['parameters']),
                  'profile_is_explicit_single_line_or_closed_circle': item['profile'].get('profile_kind') == 'SketchOpenProfile' or item['profile']['kind'] == 'SketchProfile',
                  'explicit_native_body_anchor_retained': item['native_body_object_id'] in by and by[item['native_body_object_id']].class_guid == BODY}
        # Native record IDs come from the anchor, then its checked property map.
        # An actual source-body name corroborates this join; names never choose IDs.
        if filename.startswith('sweepprofiles-'):
            prop = next(p for p in stream['body_properties']['bodies'] if p['object_id'] == item['native_body_object_id'])
            source_bodies = [s['body'] for s in sample['source_entities'] if s.get('body')]
            checks['actual_source_body_getter_is_sheet'] = len(source_bodies) == 1 and source_bodies[0]['is_solid'] is False
            checks['explicit_body_name_matches_actual_source_body'] = len(source_bodies) == 1 and prop['name'] == source_bodies[0]['name']
        assert all(checks.values()), (filename, checks)
        record = by[item['feature_object_id']]
        try:
            decode_extrude(data[record.body:record.end], feature)
        except ValueError as error:
            assert str(error) == 'Unsupported extrusion start prefix'
        else:
            raise AssertionError('Default solid-only parser widened unexpectedly')
        report['samples'].append({'archive': filename, 'checks': checks, 'expected_summary': result,
                                  'actual_parameters': actual, 'default_solid_only_guard': True})
        negative_case = data, records, stream, by, item
    data, records, stream, by, item = negative_case
    feature_id = item['feature_object_id'];record = by[feature_id]
    proxy_id = item['profile']['selection_record_object_id']
    descriptor_id = item['profile']['descriptor_object_id']
    mutations = [('Unknown surface flag', feature_id, 22, b'\2'),
                 ('Counted feature table contradicts profile reference', feature_id, 265, struct.pack('<Q', 999999)),
                 ('Profile proxy owner mismatch', proxy_id, by[proxy_id].end-by[proxy_id].body-10, struct.pack('<Q', 999999)),
                 ('Profile descriptor owner mismatch', descriptor_id, by[descriptor_id].end-by[descriptor_id].body-10, struct.pack('<Q', 999999))]
    for label, identity, offset, replacement in mutations:
        target = by[identity];changed = bytearray(data)
        changed[target.body+offset:target.body+offset+len(replacement)] = replacement
        result = decode_surface_extrudes(bytes(changed), records, copy.deepcopy(stream['features']))
        assert not any(i['feature_object_id'] == feature_id for i in result['decoded']), label
        report['negative_checks'].append({'check': label, 'rejected': True,
                                         'reason': result['unresolved'][0]['reason'] if result['unresolved'] else 'Not an observed surface candidate'})
    report['limitations'] = ['Only positive NewBody/ProfilePlane/OneSided/Distance/no-taper and one Circle or open Line observed.',
        'Solid-only parser defaults stay unchanged; new branch requires explicit opt-in after independent bounded source/owner validation.',
        'Owned result anchors establish historical native body identity, not current final solids or persistent ASM mapping.',
        'No surface generation, two-sided/symmetric/entity extents, thin extrusion, general profiles or history regeneration.']
    return report


if __name__ == '__main__':
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate', action='store_true', required=True)
    parser.add_argument('--zstd-library')
    parser.add_argument('--output', type=Path, default=Path(__file__).with_name('surface-extrude-decoding.json'))
    args = parser.parse_args()
    report = validate_fixtures(Path(__file__).resolve().parent, args.zstd_library)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'samples': len(report['samples']), 'negative_checks': len(report['negative_checks'])}))
