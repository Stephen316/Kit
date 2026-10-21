"""Saved main-reader boundaries for optional ASM attribute JSON exposure."""
import argparse
import copy
import json
from pathlib import Path
import struct
import subprocess

from asm_records import inspect_asm, inspect_asm_members
from decode_asm_recipe_tags import decode_asm_generic_tags
from decode_basics import decode_basics
from fusion_archive import read_members
from validate_history_cache_integration import baseline_outputs, differences

ROOT = Path(__file__).resolve().parent
BASELINE = 'efef90b'
FILES = ['advanced-627f7fe095f4/advanced.f3d', 'moretools-88a2cd6cad0b/MoveRotate.f3d',
         'movemodes-0dd2f72dd9a7/point_to_position_nested_design.f3d',
         'splitfacemodes-4fc4adf2a868/along_vector.f3d', 'splitfacemodes-4fc4adf2a868/plane.f3d',
         'splinepatches-900d152c2380/splinepatches.f3d', 'splinepatches-ac5e846e59c0/splinepatches.f3d',
         'loftbrepends-e07e3859ed20/edge_both_tangent.f3d',
         'pipeedgecontrasts-5bd287323ae7/circle_full.f3d',
         'circularmodes-45f859c1f1b6/feature_adjust.f3d',
         'parameterexpressions-3ddbef2b20bd/product_sum.f3d']


def validate(zstd, *, saved_outputs=None):
    if saved_outputs is None:
        before = baseline_outputs(FILES, zstd, revision=BASELINE)
        after = [json.loads(json.dumps(decode_basics(ROOT/f, zstd, include_asm_attributes=True))) for f in FILES]
    else:
        assert saved_outputs['files'] == FILES
        before, after = saved_outputs['before'], saved_outputs['after']
    samples = []
    totals = dict(attribute_streams=0, topology_naming_tags=0, validated_metadata_attributes=0,
                  nested_metadata_attributes=0, sketch_attributes=0, retained_attribute_diagnostics=0)
    for filename, old, current in zip(FILES, before, after):
        stripped = copy.deepcopy(current)
        members = read_members(ROOT/filename, zstd)
        rows = []
        for stream in stripped['asm_decoding']['streams']:
            summary = stream.pop('custom_attributes', None)
            blob = members[stream['member']]
            parsed = inspect_asm(blob)
            has_attributes = any(r['name'] == 'ATTRIB_CUSTOM-attrib' and r['section'] == 'geometry' for r in parsed['records'])
            assert (summary is not None) == has_attributes
            if summary is None:
                continue
            assert summary == decode_asm_generic_tags(blob, parsed, allow_fpm_tracking=True)
            limit = next(r['index'] for r in parsed['records'] if r['record_kind'] == 'marker')
            expected_indices = {r['index'] for r in parsed['records'][:limit] if r['name'] == 'ATTRIB_CUSTOM-attrib'}
            identities = [r['attribute_record_index'] for key in ('tags', 'ignored_validated_other_definition_attributes', 'unresolved') for r in summary[key]]
            assert len(identities) == len(set(identities)) and set(identities) == expected_indices
            nested = [r for r in summary['ignored_validated_other_definition_attributes'] if r['owner_kind'] == 'ATTRIB_CUSTOM-attrib']
            assert all(t['owner_kind'] in ('body', 'face', 'edge', 'vertex') for t in summary['tags'])
            assert not {r['attribute_record_index'] for r in nested} & {r['attribute_record_index'] for r in summary['tags']}
            for tag in summary['tags']+nested:
                assert bytes.fromhex(tag['payload_hex']) == blob[tag['payload_offset']:tag['payload_end_offset']]
            count = {'attribute_streams': 1, 'topology_naming_tags': len(summary['tags']),
                     'validated_metadata_attributes': len(summary['ignored_validated_other_definition_attributes']),
                     'nested_metadata_attributes': len(nested),
                     'sketch_attributes': sum(r['definition_name'] == 'sketch_attrib_def' for r in summary['ignored_validated_other_definition_attributes']),
                     'retained_attribute_diagnostics': len(summary['unresolved'])}
            for k, v in count.items(): totals[k] += v
            rows.append({'member': stream['member'], **count, 'all_initial_custom_attributes_accounted_once': True,
                         'exposed_naming_payloads_match_actual_member_bytes': True})
        assert stripped == old, (filename, 'Unexpected existing output change', differences(old, stripped))
        samples.append({'file': filename, 'all_prior_output_unchanged': True, 'ASM_attribute_streams': rows})
    # The default output remains the existing compact reader result. This checks
    # the public entry point, not merely the lower-level inspector option.
    example = FILES[1]
    ordinary = json.loads(json.dumps(decode_basics(ROOT/example, zstd)))
    assert ordinary == before[FILES.index(example)]
    command = ['/usr/bin/python3', str(ROOT/'decode_basics.py'), '--asm-attributes']
    if zstd is not None:
        command += ['--zstd-library', zstd]
    command.append(str(ROOT/example))
    cli, = json.loads(subprocess.check_output(command, cwd=ROOT, text=True))
    assert cli == after[FILES.index(example)]
    # A damaged metadata field must remain an attribute diagnostic without
    # discarding the independently decoded geometry or token stream.
    members = read_members(ROOT/example, zstd)
    member = next(n for n in members if n.endswith('.smbh'))
    blob = members[member]; parsed = inspect_asm(blob)
    child = next(r for r in parsed['records'] if r['name'] == 'ATTRIB_CUSTOM-attrib'
                 and len(r['tokens']) == 17 and r['tokens'][12]['kind'] == 'string' and r['tokens'][12]['value'] == '')
    changed = bytearray(blob)
    struct.pack_into('<q', changed, child['tokens'][13]['offset']+1, 1)
    original = inspect_asm_members({member: blob}, include_custom_attributes=True)['streams'][0]
    damaged = inspect_asm_members({member: bytes(changed)}, include_custom_attributes=True)['streams'][0]
    assert original['topology'] == damaged['topology']
    assert damaged['complete_token_stream'] is True
    assert any(r['attribute_record_index'] == child['index'] for r in damaged['custom_attributes']['unresolved'])
    assert child['index'] not in {r['attribute_record_index'] for key in ('tags', 'ignored_validated_other_definition_attributes') for r in damaged['custom_attributes'][key]}
    return {'scope': 'Eleven saved main-reader designs against efef90b; optional complete initial custom-attribute JSON exposure, no live Fusion or whole-corpus main-reader run',
            'baseline_commit': BASELINE, 'interfaces': {'main': 'decode_basics(path,zstd_library=None,*,include_asm_attributes=False); CLI --asm-attributes',
                'inspector': 'inspect_asm_members(members,include_records=False,*,include_custom_attributes=False); CLI --custom-attributes'},
            'samples': samples, 'summary': {'saved_files': len(FILES), **totals,
                'unexpected_prior_output_changes': 0, 'default_output_control_exact': True, 'optional_CLI_matches_API': True,
                'corrupted_metadata_retains_topology_and_token_framing': True, 'new_API_calls': 0},
            'malformed_guard': {'file': example, 'member': member, 'attribute_record_index': child['index'],
                'changed_field': 'Empty-child stored index changed from0 to1', 'rejected_as_metadata': True,
                'topology_unchanged': True, 'token_stream_complete': True},
            'limitations': ['The attributes option exposes bounded literal naming/metadata records, not persistent identities or a full history model.',
                'Six sketch text fields and FPM/nested metadata components retain opaque literal semantics.',
                'Native writing, translation and general feature regeneration remain unfinished.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zstd-library')
    args = parser.parse_args()
    zstd = args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report = validate(zstd)
    (ROOT/'attribute-integration.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
