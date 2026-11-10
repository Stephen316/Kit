"""Corrupt only a typed additional asset's first raw LZMA byte; preserve valid current geometry."""
import argparse
import copy
import hashlib
import json
import lzma
from pathlib import Path
import struct

from decode_mesh_contents import decode_paramesh_header, decode_paramesh_geometry
from decode_mesh_geometry_variants import decode_mesh_asset, decode_mesh_contents_variants, decode_geometry_layout
from decode_mesh_reduce import decode_mesh_reduce
from decode_mesh_remesh import decode_mesh_remesh
from decode_mesh_smooth import decode_mesh_smooth
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
CASES = (
    ('meshreduces-780954a23308/adaptive_count_six.f3d',decode_mesh_reduce,'mesh-reduce-decoding.json'),
    ('meshremeshes-f07f97514069/adaptive_edge_two.f3d',decode_mesh_remesh,'mesh-remesh-decoding.json'),
    ('meshsmooths-56f38f13430a/smooth_point_one.f3d',decode_mesh_smooth,'mesh-smooth-decoding.json'),
)


def canonical(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def validate(root,zstd):
    report = dict(scope='Three actual saved additional assets with one raw LZMA payload byte changed in memory; native records/current assets unchanged, no main decoder or live API calls',
        samples=[],source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in (
            'validate_mesh_asset_errors.py','decode_mesh_contents.py','decode_mesh_geometry_variants.py',
            'decode_mesh_reduce.py','decode_mesh_remesh.py','decode_mesh_smooth.py','validate_mesh_remesh.py')})
    for archive,decoder,golden_name in CASES:
        data,records,features,member,members = load(root,archive,zstd)
        meshes = decode_mesh_contents_variants(data,records,member,members)
        valid = decoder(data,records,features,member,members,meshes)
        assert len(valid['decoded']) == 1 and not valid['unresolved']
        golden = next(s for s in json.loads((root/golden_name).read_text())['samples'] if s['archive'] == archive)
        assert valid == golden['expected_decoded']
        settings = valid['decoded'][0]['settings'];additional = settings['additional_stored_asset']
        identity = additional['asset_object_id'];path = additional['asset_member'];blob = members[path]
        assert path != settings['current_mesh_asset']['asset_member']
        typed_before = decode_mesh_asset(data,records,identity,member,members)
        assert typed_before == additional
        header,header_end = decode_paramesh_header(blob)
        block = additional['geometry']['buffers'][0]
        offset = block['asset_offset']
        length,kind,descriptor_length = struct.unpack_from('<QIH',blob,offset)
        compression_offset = offset+14+descriptor_length+4
        mutation_offset = compression_offset+2
        assert kind == 4 and blob[compression_offset:mutation_offset] == bytes.fromhex('5d14')
        assert blob[mutation_offset] == 0 and block['compressed_payload_hex'].startswith('00')
        assert compression_offset < offset+12+length and header_end <= offset
        altered = bytearray(blob);altered[mutation_offset] = 255;altered = bytes(altered)
        assert len(altered) == len(blob) and [i for i,(a,b) in enumerate(zip(blob,altered)) if a != b] == [mutation_offset]
        bad_members = dict(members);bad_members[path] = altered
        assert [name for name in members if members[name] != bad_members[name]] == [path]
        assert bad_members[member] == data and altered[offset:compression_offset] == blob[offset:compression_offset]
        changed_header,changed_header_end = decode_paramesh_header(altered)
        assert header_end == changed_header_end and all(header[k] == changed_header[k] for k in header if k != 'asset_sha256')
        # The raw geometry reader raises LZMAError. The typed asset boundary must
        # translate only that exception type and retain the original reason.
        try:
            decode_paramesh_geometry(altered,geometry_decoder=decode_geometry_layout,allow_index_zero_suffix=True)
        except lzma.LZMAError as error:
            raw_reason = str(error)
        else:
            raise AssertionError('Expected actual raw LZMA corruption rejection')
        try:
            decode_mesh_asset(data,records,identity,member,bad_members)
        except ValueError as error:
            assert type(error) is ValueError and isinstance(error.__cause__,lzma.LZMAError)
            assert str(error) == raw_reason == str(error.__cause__)
            typed_reason = str(error)
        else:
            raise AssertionError('Typed asset must raise bounded ValueError')
        original_features = copy.deepcopy(features);original_meshes = copy.deepcopy(meshes);original_valid = copy.deepcopy(valid)
        failed = decoder(data,records,features,member,bad_members,meshes)
        assert not failed['decoded'] and len(failed['unresolved']) == 1
        assert failed['unresolved'][0]['feature_object_id'] == valid['decoded'][0]['feature_object_id']
        assert failed['unresolved'][0]['reason'] == typed_reason
        assert features == original_features and meshes == original_meshes and valid == original_valid
        # The corrupt additional asset is not silently substituted for current geometry.
        current_after = decode_mesh_contents_variants(data,records,member,bad_members)
        assert current_after == meshes
        clean_again = decoder(data,records,features,member,members,meshes)
        assert clean_again == valid
        report['samples'].append(dict(archive=archive,archive_sha256=hashlib.sha256((root/archive).read_bytes()).hexdigest(),
            feature_object_id=valid['decoded'][0]['feature_object_id'],kind=valid['decoded'][0]['kind'],
            additional_asset_object_id=identity,additional_asset_member=path,
            original_asset_sha256=hashlib.sha256(blob).hexdigest(),altered_asset_sha256=hashlib.sha256(altered).hexdigest(),
            mutation=dict(asset_offset=mutation_offset,original_byte_hex='00',altered_byte_hex='ff',
                preceding_LZMA_properties_hex='5d14',buffer_ordinal=0,framed_buffer_asset_offset=offset),
            exact_unchanged_header_metadata_dictionary_hex=header['stored_header_metadata_dictionary_hex'],
            raw_exception_type='LZMAError',typed_exception_type='ValueError',exception_reason=typed_reason,
            typed_exception_cause='LZMAError',expected_corrupt_decoded=failed,
            expected_valid_summary_sha256=canonical(valid),expected_current_mesh_summary_sha256=canonical(meshes),
            checks=dict(single_byte_change_only=True,native_records_UUIDs_frame_headers_unchanged=True,
                typed_error_reason_and_cause_preserved=True,operation_returns_unresolved_not_exception=True,
                current_mesh_full_dictionary_unchanged=True,input_features_and_valid_controls_unchanged=True,
                original_clean_decode_unchanged=True)))
    report['counts'] = dict(actual_saved_archives=3,additional_asset_LZMA_corruptions=3,
        raw_LZMAErrors=3,typed_ValueErrors=3,structured_operation_failures=3,
        current_mesh_dictionaries_unchanged=3,valid_control_summaries_unchanged=3,full_main_runs=0,live_API_calls=0)
    report['limits'] = ['One deliberate compressed-payload corruption per captured operation family; does not establish universal malformed-archive handling.',
        'Typed source/current/additional asset provenance and geometry semantics remain unchanged; no recovery of corrupted geometry or mutation of saved captures.']
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__);parser.add_argument('--zstd-library',required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'mesh-asset-error-decoding.json')
    args=parser.parse_args();report=validate(ROOT,args.zstd_library)
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['counts']))
