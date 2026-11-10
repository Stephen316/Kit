"""Bounded Cut index payload, emitted suffix, API arrays and framing evidence.

This research validator never changes shared framing or truncates a source
stream. It retains all emitted bytes and distinguishes declared payload from an
unexplained surplus zero. Runtime opt-in validation is explicitly requested.
"""
import argparse
import copy
import hashlib
import json
import lzma
import math
from pathlib import Path
import struct
from unittest.mock import patch

import decode_mesh_contents as mesh_reader
from decode_mesh_combine import decode_mesh_combine
from decode_mesh_contents import DESCRIPTORS, decode_mesh_contents, decode_paramesh_framing, decode_paramesh_header
from decode_mesh_geometry_variants import decode_geometry_layout, decode_mesh_contents_variants, native_layout
from decode_mesh_selections import decode_mesh_selection
from decode_parameters import read_string
from decode_placement import transform_point
from decode_sketch import reference
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT = Path(__file__).resolve().parent
ARCHIVE = 'meshcombines-541ebb6cc93f/cut.f3d'
CUT_SHAPE = [312, 576, 744, 268, 208, 192]
STRICT_ERROR = 'Mesh LZMA decoded extent/end-marker disagrees'


def digest(value):
    return hashlib.sha256(value).hexdigest()


def probe(compressed, cap):
    decoder = lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=[
        {'id': lzma.FILTER_LZMA1, 'dict_size': 1 << 20, 'lc': 3, 'lp': 0, 'pb': 2}])
    raw = decoder.decompress(compressed, max_length=cap)
    state = {'decoded_byte_count': len(raw), 'needs_input': decoder.needs_input,
             'eof': decoder.eof, 'unused_data_byte_count': len(decoder.unused_data)}
    drains = []
    for _ in range(3):
        if decoder.needs_input or decoder.eof:
            break
        emitted = decoder.decompress(b'', max_length=1)
        drains.append({'emitted_hex': emitted.hex(), 'needs_input': decoder.needs_input,
            'eof': decoder.eof, 'unused_data_byte_count': len(decoder.unused_data)})
    return raw, {'output_cap': cap, 'initial_state': state, 'empty_input_drains': drains}


def frames(blob):
    header, cursor = decode_paramesh_header(blob)
    result = []
    for ordinal, expected_descriptor in enumerate(DESCRIPTORS):
        length, kind, descriptor_size = struct.unpack_from('<QIH', blob, cursor)
        end = cursor+12+length
        descriptor = blob[cursor+14:cursor+14+descriptor_size]
        assert kind == 4 and descriptor.hex() == expected_descriptor
        assert cursor+18+descriptor_size < end <= len(blob)
        size_offset = cursor+14+descriptor_size
        declared = struct.unpack_from('<I', blob, size_offset)[0]
        compressed = blob[size_offset+4:end]
        assert 0 < declared <= 65536 and compressed[:2] == b'\x5d\x14'
        raw, full_probe = probe(compressed[2:], declared+1024)
        assert len(raw) <= declared+1 and full_probe['initial_state']['needs_input'] is True
        assert full_probe['initial_state']['eof'] is False and full_probe['initial_state']['unused_data_byte_count'] == 0
        result.append({'ordinal': ordinal, 'asset_offset': cursor, 'asset_end_offset': end,
            'stored_length': length, 'stored_kind': kind, 'descriptor_hex': descriptor.hex(),
            'declared_size_offset': size_offset, 'declared_uncompressed_size': declared,
            'compressed_properties_hex': compressed[:2].hex(), 'compressed_payload_hex': compressed[2:].hex(),
            'stored_frame_hex': blob[cursor:end].hex(), 'full_available_output_hex': raw.hex(),
            'full_bounded_probe': full_probe})
        cursor = end
    assert cursor == len(blob)
    replay = bytes.fromhex(header['stored_header_metadata_dictionary_hex'])+b''.join(bytes.fromhex(f['stored_frame_hex']) for f in result)
    assert replay == blob
    return header, result


def indices_from_differences(raw, endian='<'):
    assert len(raw) % 4 == 0
    values = struct.unpack(endian+str(len(raw)//4)+'i', raw)
    # Independent direct formula rather than the production backward loop.
    return [values[-1]-sum(values[i:-1]) for i in range(len(values))]


def qualify_index_frame(frame, shape):
    """Research qualification of only the observed shape and complete suffix state."""
    if shape != CUT_SHAPE or frame['ordinal'] != 1 or frame['declared_uncompressed_size'] != 576:
        raise ValueError('Not the observed Cut shape/ordinal/declared-size family')
    raw = bytes.fromhex(frame['full_available_output_hex'])
    if len(raw) != 577 or raw[576:] != b'\0':
        raise ValueError('Observed Cut index requires exactly one retained emitted zero suffix')
    compressed = bytes.fromhex(frame['compressed_payload_hex'])
    plus_one, evidence = probe(compressed, 577)
    if (plus_one != raw or evidence['initial_state'] != {'decoded_byte_count': 577,
            'needs_input': False, 'eof': False, 'unused_data_byte_count': 0}
            or evidence['empty_input_drains'] != [{'emitted_hex': '', 'needs_input': True,
                'eof': False, 'unused_data_byte_count': 0}]):
        raise ValueError('Observed Cut bounded output/drain state differs')
    declared = raw[:576]
    indices = indices_from_differences(declared)
    if len(indices) != 144 or any(not 0 <= i < 26 for i in indices):
        raise ValueError('Cut declared index payload has invalid count or node bounds')
    if any(len(set(indices[i:i+3])) != 3 for i in range(0, len(indices), 3)):
        raise ValueError('Cut declared index payload contains degenerate triangle')
    return indices, evidence


def validate(zstd, *, check_runtime=False):
    members = read_members(ROOT/ARCHIVE, zstd)
    member = next(m for m in members if m.endswith('/FusionDesignSegmentType1/BulkStream.dat'))
    data = members[member]
    records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
    features = [r for r in records if r.is_primary and r.class_guid == 'EE0E56E8-5894-4D65-BAF4-9DAAF811307F']
    feature, = features
    body = data[feature.body:feature.end]
    assert struct.unpack_from('<I', body, 2)[0] == 1  # Contrasted Cut code.
    selected = decode_mesh_selection(data, records, reference(body, 52), feature.object_id)
    metadata = decode_mesh_contents(data, records, member, members, native_layout_decoder=native_layout, metadata_only=True)
    target, = [r for r in metadata['decoded'] if r['mesh_object_id'] == selected['mesh_object_id']]
    assert selected['mesh_object_id'] == 213 and target['asset_object_id'] == reference(body, 26) == 331
    assert target['feature_object_id'] == 218 and target['collection_mesh_object_ids'] == [213]
    blob = members[target['asset_member']]
    header, blocks = frames(blob)
    shape = [b['declared_uncompressed_size'] for b in blocks]
    assert shape == CUT_SHAPE
    assert header['fusion_uuid'] == target['asset_fusion_uuid']
    index_frame = blocks[1]
    indices, plus_one_evidence = qualify_index_frame(index_frame, shape)
    prefix = bytes.fromhex(index_frame['full_available_output_hex'])[:576]
    probes = []
    for cap in (576, 577, 578, 1600):
        raw, evidence = probe(bytes.fromhex(index_frame['compressed_payload_hex']), cap)
        probes.append({**evidence, 'emitted_prefix_sha256': digest(raw),
            'bytes_beyond_declared_hex': raw[576:].hex()})
    truths = json.loads((ROOT/'meshcombines-541ebb6cc93f/ground_truth.json').read_text())
    sample, = [s for s in truths['samples'] if s['case'] == 'cut']
    api_body, = sample['component_meshes_after_combine']['meshes']
    api = api_body['original_polygon_mesh']
    assert sample['input_before_add']['meshCombineOperationType'] == sample['feature_before_node']['meshCombineOperationType'] == 1
    assert sample['input_target_equals_import_handle'] is True and sample['rolled_target_equals_import_handle'] is True
    assert target['name'] == sample['feature_before_node']['targetBody']['name'] == api_body['name']
    assert indices == api['triangleNodeIndices'] and len(indices) == 3*api['triangleCount'] == 144
    coordinates = struct.unpack('<78f', bytes.fromhex(blocks[0]['full_available_output_hex']))
    points = [transform_point(target['asset_coordinates_to_component_matrix'], coordinates[i:i+3]) for i in range(0, 78, 3)]
    assert [v for p in points for v in p] == api['nodeCoordinatesAsDouble'] and len(points) == api['nodeCount'] == 26
    encoded_api = struct.pack('<144i', *([indices[i+1]-indices[i] for i in range(143)]+[indices[-1]]))
    assert encoded_api == prefix and indices[-1] == 20
    directed = {}
    terms = []
    for start in range(0, len(indices), 3):
        tri = indices[start:start+3]
        a, b, c = [points[i] for i in tri]
        terms.append((a[0]*b[1]*c[2]+a[1]*b[2]*c[0]+a[2]*b[0]*c[1]
            -a[2]*b[1]*c[0]-a[1]*b[0]*c[2]-a[0]*b[2]*c[1])/6.)
        for i in range(3):
            edge = tri[i], tri[(i+1)%3]
            directed[edge] = directed.get(edge, 0)+1
    assert all(n == 1 and directed.get((b, a)) == 1 for (a, b), n in directed.items())
    assert len(directed)//2 == 72 and 26-72+48 == 2
    derived_volume = abs(math.fsum(terms))
    assert math.isclose(derived_volume, api_body['volume'], rel_tol=0, abs_tol=2e-12)
    try:
        decode_paramesh_framing(blob, allow_auxiliary_prefix=True)
    except ValueError as error:
        assert str(error) == STRICT_ERROR
    else:
        raise AssertionError('Default framing unexpectedly accepted the index suffix')
    alternatives = []
    raw = bytes.fromhex(index_frame['full_available_output_hex'])
    for name, candidate in (('One-byte shifted int32 alignment', indices_from_differences(raw[1:])),
            ('Big-endian int32 interpretation', indices_from_differences(prefix, '>'))):
        assert candidate != indices and not all(0 <= i < 26 for i in candidate)
        alternatives.append({'case': name, 'matches_actual_API_indices': False,
            'out_of_bounds_index_count': sum(not 0 <= i < 26 for i in candidate)})
    truncated = []
    compressed = bytes.fromhex(index_frame['compressed_payload_hex'])
    for removed in (1, 2, 3, 4, 5):
        out, evidence = probe(compressed[:-removed], 1600)
        assert len(out) < 576 and out != prefix
        truncated.append({'removed_compressed_payload_bytes': removed, **evidence,
            'declared_index_payload_complete': False, 'output_tail_hex': out[-8:].hex()})
    guards = []
    for label, mutate in (
            ('Wrong buffer ordinal', lambda f, s: f.update(ordinal=2)),
            ('Wrong declared count580', lambda f, s: f.update(declared_uncompressed_size=580)),
            ('Nonzero decoded surplus', lambda f, s: f.update(full_available_output_hex=(raw[:-1]+b'\1').hex())),
            ('Two decoded surplus bytes', lambda f, s: f.update(full_available_output_hex=(raw+b'\0').hex())),
            ('Truncated compressed payload', lambda f, s: f.update(compressed_payload_hex=compressed[:-1].hex())),
            ('Unknown six-buffer shape', lambda f, s: s.__setitem__(2, s[2]+4))):
        altered, dimensions = copy.deepcopy(index_frame), list(shape)
        mutate(altered, dimensions)
        try:
            qualify_index_frame(altered, dimensions)
        except ValueError as error:
            guards.append({'case': label, 'reason': str(error)})
        else:
            raise AssertionError((label, 'Unsupported suffix variant accepted'))
    row = {'archive': ARCHIVE, 'member': target['asset_member'], 'native_feature_object_id': feature.object_id,
        'typed_target_selection': selected, 'current_target_metadata': target,
        'asset_sha256': digest(blob), 'asset_byte_count': len(blob), 'header': header,
        'declared_buffer_sizes': shape, 'framed_buffers': blocks,
        'index_cap_and_drain_probes': probes, 'index_577_cap_qualification': plus_one_evidence,
        'declared_index_payload_hex': prefix.hex(), 'emitted_surplus_hex': raw[576:].hex(),
        'decoded_triangle_indices': indices, 'decoded_component_points_cm': points,
        'exact_all_API_triangle_indices': True, 'exact_all_API_component_coordinates': True,
        'actual_API_node_count': 26, 'actual_API_triangle_count': 48, 'derived_edge_count': 72,
        'closed_oriented_directed_edge_incidence': True, 'Euler_characteristic': 2,
        'independent_derived_volume_cm3': derived_volume, 'actual_API_volume_cm3': api_body['volume'],
        'strict_default_error_retained': STRICT_ERROR, 'all_six_frames_and_header_replay_exact': True,
        'alternative_interpretations': alternatives, 'actual_compressed_truncation_counterexamples': truncated}
    controls, runtime_guards = [], []
    if check_runtime:
        framed, buffers = decode_paramesh_framing(blob, allow_auxiliary_prefix=True, allow_index_zero_suffix=True)
        suffix = framed['buffers'][1]
        assert suffix['emitted_suffix_hex'] == '00' and suffix['bounded_empty_drain_hex'] == ''
        assert suffix['bounded_empty_drain_needs_input'] is True and suffix['bounded_empty_drain_eof'] is False
        assert suffix['uncompressed_payload_hex'] == prefix.hex()
        assert bytes.fromhex(suffix['stored_frame_hex']) == blob[blocks[1]['asset_offset']:blocks[1]['asset_end_offset']]
        real_decoder = lzma.LZMADecompressor
        for label, mode in (('Production nonzero surplus rejection', 'nonzero'),
                ('Production nonempty drain rejection', 'extra_drain'),
                ('Production unexhausted drain rejection', 'unexhausted')):
            created = [0]
            class AlteredIndexDecoder:
                def __init__(self, *args, **kwargs):
                    self.inner = real_decoder(*args, **kwargs)
                    self.index = created[0] == 1
                    created[0] += 1
                    self.drained = False
                @property
                def needs_input(self):
                    if self.index and self.drained and mode == 'unexhausted':
                        return False
                    return self.inner.needs_input
                @property
                def eof(self):
                    return self.inner.eof
                @property
                def unused_data(self):
                    return self.inner.unused_data
                def decompress(self, value, max_length=-1):
                    emitted = self.inner.decompress(value, max_length=max_length)
                    if self.index and value == b'':
                        self.drained = True
                        if mode == 'extra_drain':
                            return b'\0'
                    if self.index and value and mode == 'nonzero':
                        return emitted[:-1]+b'\1'
                    return emitted
            with patch.object(mesh_reader.lzma, 'LZMADecompressor', AlteredIndexDecoder):
                try:
                    decode_paramesh_framing(blob, allow_auxiliary_prefix=True, allow_index_zero_suffix=True)
                except ValueError as error:
                    runtime_guards.append({'case': label, 'reason': str(error),
                        'scope': 'Controlled decoded-state injection at shared raw-LZMA interface; source asset bytes unchanged'})
                else:
                    raise AssertionError((label, 'Shared framing admitted unsupported suffix/drain'))
        for label, framing, raw_buffers in (
                ('Production Cut missing suffix evidence', copy.deepcopy(framed), list(buffers)),
                ('Production suffix attached to another known shape', copy.deepcopy(framed),
                    [bytes(n) for n in (48, 48, 96, 32, 48, 16)])):
            if label == 'Production Cut missing suffix evidence':
                framing['buffers'][1].pop('emitted_suffix_hex')
            try:
                decode_geometry_layout(framing, raw_buffers)
            except ValueError as error:
                runtime_guards.append({'case': label, 'reason': str(error)})
            else:
                raise AssertionError((label, 'Shared geometry admitted unqualified suffix family'))
        wrapped = decode_mesh_contents_variants(data, records, member, members)
        actual, = [r for r in wrapped['decoded'] if r['mesh_object_id'] == selected['mesh_object_id']]
        assert actual['geometry']['triangle_node_indices'] == indices
        assert actual['geometry']['component_node_coordinates_cm'] == points
        assert actual['geometry']['node_count'] == 26 and actual['geometry']['triangle_count'] == 48
        assert not any(e['mesh_object_id'] == 213 for e in wrapped['unresolved'])
        assert any(e['mesh_object_id'] == 226 for e in wrapped['unresolved'])
        row['expected_mesh_contents'] = wrapped
        row['expected_geometry'] = actual['geometry']
        # Read this one feature's bounded name/index metadata directly. The
        # operation helper needs no other feature settings; no main run needed.
        _, table_end = read_string(body, 64)
        label_start = table_end+7+44+4
        label, label_end = read_string(body, label_start)
        assert label == 'MeshCombine'
        stored_index = struct.unpack_from('<Q', body, label_end)[0]
        native_name, _ = read_string(body, label_end+8)
        feature_metadata = {'object_id': feature.object_id, 'class_guid': feature.class_guid,
            'record_offset': feature.start, 'stored_index': stored_index, 'name': native_name}
        combine = decode_mesh_combine(data, records, [feature_metadata], member, members, wrapped)
        assert not combine['unresolved'] and len(combine['decoded']) == 1
        settings = combine['decoded'][0]['settings']
        assert settings['operation'] == 'Cut' and not settings['geometry_unresolved']
        assert settings['current_target_asset_geometry']['geometry']['triangle_node_indices'] == indices
        assert settings['retained_tool_sources'][0]['retained_membership_status'] == 'NotInCountedMembers'
        assert settings['strict_current_mesh_diagnostics'] == wrapped['unresolved']
        row['expected_combine_summary'] = combine
        for report_name, filenames in (
                ('mesh-decoding.json', ('meshcontrasts-10c2557c91a3/stl_centimeter.f3d',
                    'meshcontrasts-10c2557c91a3/stl_millimeter.f3d',
                    'meshcontrasts-10c2557c91a3/triangle_data_centimeter.f3d')),
                ('mesh-combine-decoding.json', ('meshcombines-541ebb6cc93f/join.f3d',
                    'meshcombines-541ebb6cc93f/intersect.f3d'))):
            golden = {s['archive']: s for s in json.loads((ROOT/report_name).read_text())['samples']}
            for filename in filenames:
                members2 = read_members(ROOT/filename, zstd)
                stream = next(n for n in members2 if n.endswith('/FusionDesignSegmentType1/BulkStream.dat'))
                data2 = members2[stream]
                records2, _ = design_records(data2, members2[stream.replace('BulkStream.dat', 'MetaStream.dat')])
                result = decode_mesh_contents_variants(data2, records2, stream, members2)
                expected = golden[filename].get('expected_mesh_contents', golden[filename].get('expected_decoded'))
                assert result == expected, (filename, 'Prior successful mesh dictionaries changed')
                controls.append({'archive': filename, 'all_prior_mesh_dictionaries_exact': True, 'golden_report': report_name})
    return {'scope': 'One actual Cut asset: declared-size index payload and separately preserved surplus zero; no default relaxation or procedural geometry claim',
        'interface': 'validate(zstd,*,check_runtime=False); --runtime additionally checks explicitly enabled shared wrapper and old exact controls',
        'qualification_proposal': 'Explicit opt-in only: ordinal1 declared576, exact Cut six-buffer shape, 577cap output577+sole00, empty drain emits0 then needs_inputTrue/noEOF/noUnused. Retain full emitted bytes and continuation evidence; default strict rejection remains.',
        'samples': [row], 'malformed_guards': guards, 'production_runtime_guards': runtime_guards, 'old_controls': controls,
        'summary': {'saved_assets': 1, 'actual_API_indices_compared_exact': len(indices),
            'actual_API_points_compared_exact': len(points), 'all_six_frame_byte_replays': 6,
            'output_cap_and_drain_probes': len(probes), 'actual_truncation_counterexamples': len(truncated),
            'invalid_alignment_endian_alternatives': len(alternatives), 'malformed_guards': len(guards),
            'production_runtime_guards': len(runtime_guards),
            'runtime_optin_checked': check_runtime, 'old_exact_controls': len(controls),
            'default_strict_failure_preserved': True, 'source_bytes_changed': 0, 'live_API_calls': 0},
        'provenance': {'archive_sha256': digest((ROOT/ARCHIVE).read_bytes()),
            'ground_truth_sha256': digest((ROOT/'meshcombines-541ebb6cc93f/ground_truth.json').read_bytes()),
            'source_sha256': {n: digest((ROOT/n).read_bytes()) for n in
                ('decode_mesh_contents.py', 'decode_mesh_geometry_variants.py', 'validate_mesh_cut_index_stream.py')}},
        'limitations': ['The emitted00 may be encoder flush/padding or another unassigned artifact; its native meaning and universal raw-LZMA validity are not proved.',
            'NoEOF is retained; valid declared geometry is qualified by exact container boundaries, typed current asset association and all captured API arrays, not by claiming the compressed stream terminated.',
            'Observed truncated inputs produce incomplete index words/payload; this is a bounded counterexample, not a universal corruption detector.',
            'The suffix is retained separately, not silently discarded. Other sizes, shapes, nonzero suffixes, extra emitted data, alignment or unsupported states remain rejected.',
            'Current cache geometry and historical BaseMesh owner do not establish Combine regeneration, full lifecycle or persistent topology identity.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--zstd-library')
    parser.add_argument('--runtime', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT/'mesh-cut-index-stream-decoding.json')
    args = parser.parse_args()
    zstd = args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report = validate(zstd, check_runtime=args.runtime)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
