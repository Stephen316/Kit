"""Focused contextual int64 token replay and unchanged ASM framing controls."""

import argparse
import copy
import json
import math
from pathlib import Path
import struct
import subprocess

from asm_records import INT64_ATTRIBUTE, inspect_asm
from decode_basics import decode_basics
from decode_brep import decode_topology
from fusion_archive import read_members


def validate(zstd):
    root = Path(__file__).resolve().parent
    evidence = json.loads((root / 'asm-int64-investigation.json').read_text())
    previous_source = subprocess.check_output(['git', 'show', '766ffc9:asm_records.py'], text=True)
    namespace = {}
    exec(compile(previous_source, '766ffc9:asm_records.py', 'exec'), namespace)
    previous = namespace['inspect_asm']
    report = {'scope': 'Contextual signed int64 values in the observed typed attribute record; token completeness does not decode journal semantics',
              'files': [], 'guards': [], 'signed_boundary_controls': [], 'unknown_context_controls': [],
              'prior_token_semantics': 'Every prior complete record and token is unchanged except tag23 kind/value in the validated int64 attribute schema.',
              'limitations': ['Unknown tag23 contexts retain the previous uninterpreted finite-double representation.',
                              'SCULPT attribute values are not interpreted here as pointer indices, sides, global identities or current lifecycle.',
                              'History and trailing entities remain excluded from initial geometry graphs.']}
    replay_count, unchanged_records = 0, 0
    positive = negative = None
    for relative in sorted({o['file'] for o in evidence['observations']}):
        members = read_members(root / relative, zstd)
        observations = [o for o in evidence['observations'] if o['file'] == relative]
        for member in sorted({o['member'] for o in observations}):
            raw = members[member]
            parsed, old = inspect_asm(raw), previous(raw)
            assert parsed['complete_token_stream'] and parsed['unresolved_reason'] is None
            assert parsed['records'][-1]['name'] == 'End-of-ASM-data'
            wanted = [o for o in observations if o['member'] == member]
            actual = [r for r in parsed['records'] if r['name'] == INT64_ATTRIBUTE]
            assert len(actual) == len(wanted)
            for observed in wanted:
                record = parsed['records'][observed['record_index']]
                token = record['tokens'][10]
                assert record['name'] == INT64_ATTRIBUTE and record['section'] == observed['section']
                assert record['tokens'][9]['value'] == observed['attribute_name']
                assert token['tag'] == 23 and token['kind'] == 'integer64'
                assert token['value'] == observed['signed_int64'] and token['offset'] == observed['token_offset']
                assert raw[token['offset']:token['offset']+9] == b'\x17'+struct.pack('<q', token['value'])
                assert raw[token['offset']+1:token['offset']+9].hex() == observed['raw_64bit_hex']
                replay_count += 1
                if token['value'] < 0:
                    negative = raw, record
                elif old['complete_token_stream']:
                    positive = raw, record
            # Restore only the previous finite-double tag23 view for comparison.
            # The old parser's incomplete suffix is deliberately not fabricated.
            normalized = copy.deepcopy(parsed)
            for record in normalized['records'][:len(old['records'])]:
                for token in record['tokens']:
                    if token['tag'] == 23:
                        value = struct.unpack_from('<d', raw, token['offset']+1)[0]
                        assert math.isfinite(value)
                        token.update(kind='uninterpreted_double', value=value)
            assert normalized['records'][:len(old['records'])] == old['records']
            unchanged_records += len(old['records'])
            if old['complete_token_stream']:
                assert normalized == old
            else:
                assert relative == 'boundaryfills-a0953038318b/plane_first.f3d'
                assert old['unresolved_reason'] == 'Non-finite ASM numeric token'
                assert len(parsed['records']) == 702
                topology = decode_topology(parsed)
                historical = json.loads((root / 'auxiliary-body-root-decoding.json').read_text())
                target = next(t for t in historical['target_results'] if t['file'] == relative)
                old_graphs = target['decoded'][0]['initial_geometry_validation']['validated_initial_geometry_body_graphs']
                assert topology['body_graphs'] == old_graphs
                assert topology['initial_geometry_record_count'] == 213
            report['files'].append({'file': relative, 'member': member,
                                     'contextual_integer_values_replayed': len(actual),
                                     'record_count': len(parsed['records']),
                                     'prior_complete_record_prefix_unchanged_except_int64_values': True,
                                     'previous_stream_complete': old['complete_token_stream'],
                                     'whole_stream_now_complete': True,
                                     'history_semantics_claimed': False})
    assert replay_count == 297 and positive and negative

    for relative in ['analytic-86a12b291d0a/analytic.f3d', 'tools-fda3948848f4/RectangularPattern.f3d']:
        count = 0
        for member, raw in read_members(root / relative, zstd).items():
            if not member.endswith(('.smb', '.smbh')):
                continue
            parsed = inspect_asm(raw)
            assert parsed == previous(raw)
            count += 1
        report['unknown_context_controls'].append({'file': relative, 'unchanged_complete_blob_outputs': count})

    def rejected(label, raw, reason):
        parsed = inspect_asm(bytes(raw))
        assert not parsed['complete_token_stream'] and reason in parsed['unresolved_reason'], (label, parsed['unresolved_reason'])
        report['guards'].append({'case': label, 'rejected': True, 'reason': parsed['unresolved_reason']})

    raw, record = negative
    value = record['tokens'][10]
    for label, offset, replacement, reason in [
        ('Wrong enum schema cannot reinterpret the negative payload', record['tokens'][5]['offset']+1, struct.pack('<q', 9), 'prefix schema'),
        ('Integer attribute value requires an immediate record terminator', value['offset']+9, b'\x0b', 'record terminator'),
        ('Tag23 before its typed value field is rejected', record['tokens'][9]['offset'], b'\x17', 'prefix schema'),
        ('Real nonfinite tag6 double remains rejected', value['offset'], b'\x06', 'Non-finite ASM numeric token')]:
        changed = bytearray(raw)
        changed[offset:offset+len(replacement)] = replacement
        rejected(label, changed, reason)
    rejected('Truncated signed payload is rejected', raw[:value['offset']+5], 'Truncated ASM payload')
    changed = bytearray(raw)
    name_start = raw.index(b'int64_attrib', record['offset'], record['tokens'][0]['offset'])
    changed[name_start:name_start+len(b'int64_attrib')] = b'other_attrib'
    rejected('Unknown record context cannot reinterpret nonfinite tag23 bits as an integer', changed, 'Non-finite ASM numeric token')
    initial_double = next(t for r in inspect_asm(raw)['records'] if r['section'] == 'geometry'
                          for t in r['tokens'] if t['kind'] == 'double')
    changed = bytearray(raw)
    struct.pack_into('<d', changed, initial_double['offset']+1, float('nan'))
    rejected('A genuine nonfinite initial-geometry double stays rejected', changed, 'Non-finite ASM numeric token')

    raw, record = positive
    value = record['tokens'][10]
    changed = bytearray(raw)
    changed[value['offset']] = 6
    rejected('Finite double in the known integer schema is not silently accepted', changed, 'value schema')
    name_start = raw.index(b'int64_attrib', record['offset'], record['tokens'][0]['offset'])
    changed = bytearray(raw)
    changed[name_start:name_start+len(b'int64_attrib')] = b'other_attrib'
    parsed = inspect_asm(bytes(changed))
    old = previous(bytes(changed))
    assert parsed['complete_token_stream'] and old['complete_token_stream']
    assert parsed['records'][record['index']] == old['records'][record['index']]
    assert parsed['records'][record['index']]['tokens'][10]['kind'] == 'uninterpreted_double'
    report['unknown_context_controls'].append({'case': 'Unknown finite tag23 record preserves previous output exactly', 'passed': True})
    for boundary in [-(2**63), 2**63-1]:
        changed = bytearray(raw)
        struct.pack_into('<q', changed, value['offset']+1, boundary)
        parsed = inspect_asm(bytes(changed))
        assert parsed['complete_token_stream']
        token = parsed['records'][record['index']]['tokens'][10]
        assert token['kind'] == 'integer64' and token['value'] == boundary
        report['signed_boundary_controls'].append({'value': boundary, 'exact': True})

    model = decode_basics(root / 'boundaryfills-a0953038318b/plane_first.f3d', zstd)
    stream = next(s for s in model['streams'] if s['body_asm_identifiers']['decoded'])
    mapping, = stream['body_asm_identifiers']['decoded']
    assert 'initial_geometry_validation' not in mapping
    assert [b['native_body_object_id'] for b in mapping['bindings']] == [275, 355]
    assert len(stream['body_placement']['bodies']) == 2
    report['main_reader'] = {'plane_first_history_token_complete': True,
                             'native_BODY_associations': [275, 355], 'placed_bodies': 2,
                             'obsolete_initial_prefix_fallback_metadata_absent': True}
    report['summary'] = {'target_archives': len({f['file'] for f in report['files']}),
                         'contextual_integer_values_replayed': replay_count,
                         'prior_complete_records_preserved_except_int64_semantics': unchanged_records,
                         'recovered_whole_streams': sum(not f['previous_stream_complete'] for f in report['files']),
                         'malformed_or_unsupported_guards': len(report['guards']),
                         'signed_boundary_controls': len(report['signed_boundary_controls'])}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zstd-library')
    parser.add_argument('--output', default='asm-int64-decoding.json')
    args = parser.parse_args()
    zstd = args.zstd_library or next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report = validate(zstd)
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
