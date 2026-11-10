"""Typed datum membership, independent API caches and native mutation guards."""

import copy
import json
from pathlib import Path
import struct

from decode_basics import decode_basics
from decode_mirror_datum_reflections import decode_mirror_datum_reflections
from decode_sketch import attributes, same
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT = Path(__file__).resolve().parent
FILES = ('mirrorassemblydatum-65c867cc41d9/plane_xy_positive_offset.f3d',
         'mirrorassemblydatum-65c867cc41d9/plane_xz_negative_offset.f3d',
         'remainingbodyinputs-7b3357274e85/mirror_construction_plane.f3d')


def validate(zstd):
    rows, guards = [], []
    for filename in FILES:
        path = ROOT/filename
        decoded = decode_basics(path, zstd)['streams'][0]
        members = read_members(path, zstd); data = members[decoded['member']]
        records, _ = design_records(data, members.get(decoded['member'].replace('BulkStream.dat', 'MetaStream.dat')))
        before = copy.deepcopy(decoded)
        actual = decode_mirror_datum_reflections(data, records, decoded['features'], decoded['assembly_decoding'])
        assert decoded == before and not actual['unresolved'] and len(actual['decoded']) == 1
        value, = actual['decoded']
        assert value['maximum_frame_difference'] == 0.
        matrix = value['computed_reflection_matrix']
        square = [sum(matrix[4*r+k]*matrix[4*k+c] for k in range(4)) for r in range(4) for c in range(4)]
        assert same(square, [float(r == c) for r in range(4) for c in range(4)])
        assert value['is_combine'] is value['stitch_tolerance_cm'] is None
        truth = json.loads((path.parent/'ground_truth.json').read_text())
        sample = next(s for s in truth['samples'] if s['file'] == path.name)
        source, = sample['actual_inputs']
        native = value['source_output_provenance']
        assert same(native['source_plane']['origin_cm'], source['origin_cm'])
        assert same(native['source_plane']['normal'], source['normal'])
        evidence = {'actual_source_API_geometry_matches': True, 'actual_output_API_geometry_available': False}
        if 'construction_planes_after' in sample:
            output, = [p for p in sample['construction_planes_after'] if p['name'] != source['name']]
            assert same(output['transform'], value['computed_output_plane_frame'])
            assert same(output['origin_cm'], native['output_plane']['origin_cm'])
            assert same(output['normal'], native['output_plane']['normal'])
            evidence['actual_output_API_geometry_available'] = True
            evidence['actual_output_API_matrix_matches'] = True
        else:
            assert len(sample['root_construction_plane_names_after']) == 2
            assert sample['actual_mirror_plane'] is None
            assert native['mirror_plane']['entity']['name'] == sample['requested_mirror_plane']['name']
            evidence['mirror_plane_API_getter_unavailable_requested_only_corroboration'] = True
            evidence['output_geometry_scope'] = 'Typed native output cache and independent reflection only; no missing API geometry getter invented'
        rows.append({'file': filename, 'member': decoded['member'], 'expected_summary': actual, 'API_evidence': evidence,
                     'actual_getter_errors': sample['getter_errors'], 'input_output_frame_involution': True})
        if len(rows) == 1:
            fixture = data, records, decoded, value
    data, records, decoded, value = fixture
    primary = {r.object_id: r for r in records if r.is_primary}
    output_id = value['output_plane_object_id']
    output = primary[output_id]; chunk = data[output.body:output.end]
    _, cursor = attributes(chunk, 2)
    collection_id = value['native_component_evidence']['plane_collection_object_id']
    scope_id = value['native_component_evidence']['dependency_scopes'][0]['scope_object_id']
    terminal_id = value['mirror_plane_selection']['terminal_object_id']
    modifications = (
        ('Repeated collection membership disagrees', collection_id, 63, struct.pack('<Q', 999999)),
        ('Selected origin-plane identity changes independently of output', terminal_id, 2, struct.pack('<Q', 44)),
        ('Typed dependency component scope missing', scope_id, 4, struct.pack('<Q', 999999)),
        ('Output cache origin no longer reflects source', output_id, cursor+21, struct.pack('<d', .25)),
        ('Unobserved datum input kind code', value['control_record_object_id'], 31, struct.pack('<I', 3)),
    )
    for label, identity, offset, payload in modifications:
        changed = bytearray(data); position = primary[identity].body+offset
        changed[position:position+len(payload)] = payload
        result = decode_mirror_datum_reflections(bytes(changed), records, decoded['features'], decoded['assembly_decoding'])
        assert not result['decoded'] and len(result['unresolved']) == 1, label
        guards.append({'case': label, 'reason': result['unresolved'][0]['reason']})
    return {'scope': 'Three observed construction-plane Mirror fixtures; native membership and bounded computed reflection, no live Fusion access',
            'samples': rows, 'guards': guards,
            'summary': {'saved_files': len(FILES), 'datum_reflections': len(rows),
                        'independent_actual_API_output_matrices': sum(r['API_evidence']['actual_output_API_geometry_available'] for r in rows),
                        'maximum_stored_frame_difference': max(r['expected_summary']['decoded'][0]['maximum_frame_difference'] for r in rows),
                        'malformed_guards': len(guards), 'new_API_calls': 0},
            'limitations': ['The selected component-origin plane and two-member datum collection are bounded observed layouts.',
                           'The computed matrix reverses orientation; it is not a proper rigid assembly occurrence transform or stored matrix.',
                           'Combine/stitch controls remain null and tool-level warnings stay explicit.',
                           'Native output association is independent of unavailable API resultFeatures/timeline getters; those are never fabricated.',
                           'General datum types/supports, feature lifecycle replay, native writing and assembly solving remain unfinished.']}


if __name__ == '__main__':
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    result = validate(str(zstd))
    (ROOT/'mirror-datum-reflection-decoding.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['summary'], sort_keys=True))
