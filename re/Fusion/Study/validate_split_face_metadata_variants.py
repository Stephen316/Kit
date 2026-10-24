"""Three captured setup SplitFace variants, typed owner guards and old defaults."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess

from decode_basics import decode_basics
from decode_body_properties import decode_body_properties
from decode_selection import known_construction_entities
from decode_sketch import reference
from decode_split_face import decode_split_face
from decode_split_face_metadata_variants import decode_split_face_metadata_variants
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT = Path(__file__).resolve().parent
DIRECTORY = 'partinglinedrafts-c4d07c76fcd5'
BASELINE = 'e3b3c24'
OLD_ERROR = 'Unsupported SplitFace table metadata or kind label'


def validate(zstd):
    # Read-only frozen common parser; its imported selection/recipe dependencies
    # are current, so this proves the narrow common-parser change, not a claim
    # that all intervening recipe dictionaries equal old historical reports.
    old_source = subprocess.check_output(['git', 'show', BASELINE+':decode_split_face.py'], cwd=ROOT).decode()
    namespace = {}
    exec(compile(old_source, '<frozen '+BASELINE+' SplitFace>', 'exec'), namespace)
    old_decode = namespace['decode_split_face']
    truth_path = ROOT/DIRECTORY/'ground_truth.json'
    truth = json.loads(truth_path.read_text())
    assert truth['terminal_status'] == 'complete' and not truth['errors'] and len(truth['samples']) == 3
    snapshot = ROOT/DIRECTORY/'executed-generator-source.txt'
    assert hashlib.sha256(snapshot.read_bytes()).hexdigest() == truth['executed_generator_sha256']
    source = snapshot.read_text()
    assert 'createInput(split_faces,middle,False)' in source and "middle.name='PartingDraftMiddlePlane'" in source
    report = {
        'scope': 'Three saved parting-line Draft setup SplitFace records; raw metadata 8/12 opt-in for the captured nonextended single-plane/single-target family',
        'interface': 'decode_split_face_metadata_variants(data,records,features)->decoded/unresolved/scope; rows feature_object_id/settings/stored_table_metadata/table_metadata_layout/source_feature_object_id',
        'shared_hook': 'decode_split_face(..., *, allowed_table_metadata=(4,)); default fields and errors unchanged; new wrapper opts into (8,12) only under further captured-family checks',
        'integration': {'summary_key': 'split_face_metadata_variants',
            'feature_settings': 'row.settings; stored metadata remains a separate uninterpreted attachment',
            'recover_only_old_tool_error': OLD_ERROR,
            'limits': 'Do not clear target recipe, geometry, persistent identity or lifecycle warnings'},
        'provenance': {'ground_truth': DIRECTORY+'/ground_truth.json',
            'ground_truth_sha256': hashlib.sha256(truth_path.read_bytes()).hexdigest(),
            'executed_source_snapshot': DIRECTORY+'/executed-generator-source.txt',
            'executed_generator_sha256': truth['executed_generator_sha256'],
            'frozen_common_parser_commit': BASELINE,
            'frozen_common_parser_sha256': hashlib.sha256(old_source.encode()).hexdigest()},
        'findings': ['All existing frame/proxy/descriptor/recipe and ordered-table checks succeed before the old metadata gate.',
            'fixed_three and fixed_seven store uint32 12; moving_both_three stores 8. Their setup SplitFace API requests are identical. No metadata enum or bit meaning is assigned.',
            'The label remains SplitFace, and all three raw selection tables contain tool proxy/descriptor followed by target proxy/descriptor.',
            'Actual saved setup evidence is add health and later wall-face/edge getters. SplitFace definition-property getters were not captured; setup tool/type/extension are source requests, corroborated by explicit native ownership and mode fields.'],
        'samples': [], 'malformed_guards': [], 'old_controls': [],
        'limitations': ['Exact selected/result ASM face identities and split geometry regeneration remain unresolved.',
            'An explicit historical native BODY anchor and its custom name do not establish current/final body visibility or persistent topology.',
            'The newly admitted metadata integers remain literal; no role is inferred from later Draft mode, names or geometric coincidence.',
            'Only nonextended singleton constructed-plane intersection and Extrude-owned bounded target recipes are qualified. Other input kinds, counts, directions and metadata values retain unsupported status.']}
    contexts = {}

    def load(relative):
        path = ROOT/relative
        members = read_members(path, zstd)
        stream = decode_basics(path, zstd)['streams'][0]
        data = members[stream['member']]
        records, _ = design_records(data, members[stream['member'].replace('BulkStream.dat', 'MetaStream.dat')])
        return data, records, stream['features']

    for sample in truth['samples']:
        relative = DIRECTORY+'/'+sample['file']
        path = ROOT/relative
        assert sample['export']['byte_count'] == path.stat().st_size
        assert sample['export']['sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
        assert not sample['getter_errors'] and not sample['setter_errors'] and sample['close_owned_document_returned'] is True
        assert sample['setup_split_health'] == 0 and sample['setup_split_warning'] == ''
        data, records, features = load(relative)
        before = copy.deepcopy(features)
        summary = decode_split_face_metadata_variants(data, records, features)
        assert features == before and not summary['unresolved']
        row, = summary['decoded']
        feature, = [f for f in features if f['object_id'] == row['feature_object_id']]
        record, = [r for r in records if r.is_primary and r.object_id == feature['object_id']]
        body = data[record.body:record.end]
        known = known_construction_entities(data, records, features)
        for decoder in (old_decode, decode_split_face):
            try:
                decoder(data, records, body, feature, known, features)
            except ValueError as error:
                assert str(error) == OLD_ERROR
            else:
                raise AssertionError('Default parser unexpectedly admitted metadata8/12')
        settings = row['settings']
        assert settings['split_type'] == 'SurfaceIntersection' and settings['is_tool_extended'] is False
        assert row['stored_table_metadata'] == (8 if sample['case'].startswith('moving') else 12)
        tool = settings['tool']['entity']
        assert tool['name'] == 'PartingDraftMiddlePlane' and tool['origin_cm'] == [0., 0., 1.] and tool['normal'] == [0., 0., 1.]
        target, = settings['target_faces']
        props = decode_body_properties(data, records, {'components': []})
        selected_body, = [b for b in props['bodies'] if b['object_id'] == target['native_body_object_id']]
        assert selected_body['name'] == sample['unsplit_wall']['body_name'] == 'PartingDraftSeedBody'
        layout = row['table_metadata_layout']
        offset = layout['body_relative_offset']
        encoded = struct.pack('<I', row['stored_table_metadata'])+struct.pack('<I', len('SplitFace'))+'SplitFace'.encode('utf-16le')
        assert bytes.fromhex(layout['metadata_and_label_hex']) == encoded == body[offset:offset+len(encoded)]
        assert layout['absolute_offset'] == record.body+offset
        start = layout['reference_table_body_relative_offset']
        assert [reference(body, start+11*i) for i in range(4)] == settings['ordered_selection_reference_ids']
        expected_refs = b''.join(b'\x01'+struct.pack('<Q', identity)+bytes(2) for identity in settings['ordered_selection_reference_ids'])
        assert body[start:start+44] == expected_refs
        # Later actual API wall/edge getters corroborate a healthy partition;
        # they are not used to identify any cached target or result face.
        faces = sample['requested']['input_faces']
        assert len(faces) == 2 and sorted(f['area_cm2'] for f in faces) == [3., 3.]
        assert sum(f['area_cm2'] for f in faces) == sample['unsplit_wall']['area_cm2'] == 6.
        assert sorted(f['centroid_cm'][2] for f in faces) == [.5, 1.5]
        edge, = sample['requested']['parting_line_curves']
        assert edge['start_vertex_cm'][2] == edge['end_vertex_cm'][2] == 1. and edge['length_cm'] == 3.
        report['samples'].append({'archive': relative, 'expected_decoded': summary,
            'exact_metadata_label_and_ordered_reference_byte_replays': True,
            'default_and_frozen_parser_error': OLD_ERROR,
            'typed_source_body_name': selected_body['name'],
            'setup_evidence': {'definition_getters_captured': False,
                'executed_source_request': 'splitFaceFeatures.createInput(one actual source wall face, constructed plane offset XY by10mm, False)',
                'actual_setup_health': sample['setup_split_health'], 'actual_setup_warning': sample['setup_split_warning'],
                'actual_later_wall_areas_cm2': [f['area_cm2'] for f in faces],
                'actual_later_wall_centroid_z_cm': sorted(f['centroid_cm'][2] for f in faces),
                'actual_parting_edge_length_cm': edge['length_cm'],
                'scope': 'API setup request plus healthy observed wall partition, not saved SplitFace definition getters or selected/result ASM identity'},
            'owned_document_closed_true': True})
        contexts[sample['case']] = data, records, features, feature, record, row

    data, records, features, feature, record, row = contexts['fixed_three']
    def reject(label, mutate):
        bad = bytearray(data)
        mutate(bad)
        result = decode_split_face_metadata_variants(bytes(bad), records, features)
        assert not result['decoded'] and len(result['unresolved']) == 1
        report['malformed_guards'].append({'case': label, 'reason': result['unresolved'][0]['reason']})
    offset = record.body
    metadata_offset = offset+row['table_metadata_layout']['body_relative_offset']
    reject('Unobserved table metadata', lambda b: struct.pack_into('<I', b, metadata_offset, 13))
    reject('Kind label differs', lambda b: b.__setitem__(metadata_offset+8, ord('X')))
    reject('Extended plane intersection not captured for metadata8/12', lambda b: b.__setitem__(offset+8, 1))
    table_start = offset+row['table_metadata_layout']['reference_table_body_relative_offset']
    reject('Repeated table count differs', lambda b: struct.pack_into('<I', b, table_start-4, 3))
    reject('Repeated descriptor reference differs', lambda b: struct.pack_into('<Q', b, table_start+12, feature['object_id']))
    primary = {r.object_id:r for r in records if r.is_primary}
    proxy = primary[row['settings']['tool_selection_record_object_id']]
    reject('Tool proxy owner differs', lambda b: struct.pack_into('<Q', b, proxy.end-10, feature['object_id']+1))
    descriptor = primary[row['settings']['tool']['descriptor_object_id']]
    reject('Tool descriptor owner differs', lambda b: struct.pack_into('<Q', b, descriptor.body+253, feature['object_id']+1))
    frame = primary[row['settings']['frame_record_object_id']]
    reject('Frame owner differs', lambda b: struct.pack_into('<Q', b, frame.body+41, feature['object_id']+1))
    for filename in ('plane.f3d', 'along_vector.f3d', 'multiple_faces.f3d'):
        relative = 'splitfacemodes-4fc4adf2a868/'+filename
        data, records, features = load(relative)
        feature, = [f for f in features if f.get('kind') == 'SplitFace']
        record, = [r for r in records if r.is_primary and r.object_id == feature['object_id']]
        body = data[record.body:record.end]
        known = known_construction_entities(data, records, features)
        old = old_decode(data, records, body, feature, known, features)
        current = decode_split_face(data, records, body, feature, known, features)
        assert old == current and current == feature['tool_settings']
        before = copy.deepcopy(features)
        summary = decode_split_face_metadata_variants(data, records, features)
        assert not summary['decoded'] and not summary['unresolved'] and features == before
        report['old_controls'].append({'archive': relative, 'default_common_settings_exact_against_frozen_parser': True,
            'new_helper_has_no_rows_diagnostics_or_mutation': True,
            'scope': 'Frozen common parser with current selection/recipe dependencies; historical recipe-label corrections remain intact'})
    report['summary'] = {'actual_saved_exports': 3, 'metadata12_records': 2, 'metadata8_records': 1,
        'qualified_settings': 3, 'exact_metadata_label_replays': 3, 'exact_ordered_reference_table_replays': 3,
        'default_and_frozen_rejections_retained': 3, 'typed_source_body_name_corroborations': 3,
        'healthy_observed_wall_partition_controls': 3, 'captured_SplitFace_definition_getters': 0,
        'malformed_guards': len(report['malformed_guards']), 'old_default_controls_exact': 3,
        'feature_mutations': 0, 'live_calls': 0}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--zstd')
    parser.add_argument('--output', default=str(ROOT/'split-face-metadata-variant-decoding.json'))
    args = parser.parse_args()
    zstd = args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result = validate(zstd)
    Path(args.output).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['summary'], indent=2))
