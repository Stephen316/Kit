"""Scoped explicit pcurve cache validation for fifteen saved edge-tool archives."""

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess

from asm_records import inspect_asm
from decode_pcurve import decode_pcurve, evaluate_pcurve
from fusion_archive import read_members

ROOT = Path(__file__).resolve().parent
TRUTH_FOLDERS = ('edgemodes-52695761f185', 'edgemodes-87edbf67527b')
BASELINE_REVISION = '508b426'


def encode_token(token):
    """Independent literal encoder of the typed fields observed here."""
    tag, kind, value = token['tag'], token['kind'], token['value']
    if kind in ('integer', 'pointer', 'enum'):
        assert tag == {'integer': 4, 'pointer': 12, 'enum': 21}[kind]
        return bytes([tag])+struct.pack('<q', value)
    if kind == 'double':
        assert tag == 6 and math.isfinite(value)
        return bytes([tag])+struct.pack('<d', value)
    if kind == 'boolean_token':
        assert tag == (10 if value else 11)
        return bytes([tag])
    if kind in ('subtype_start', 'subtype_end'):
        assert tag == {'subtype_start': 15, 'subtype_end': 16}[kind] and value is None
        return bytes([tag])
    if kind == 'entity_name':
        assert tag == 13
        encoded = value.encode('utf-8')
        assert len(encoded) < 256
        return bytes([tag, len(encoded)])+encoded
    raise AssertionError('Unexpected pcurve replay token '+kind)


def replay(record, raw):
    """Recreate name, every typed field and the exact record terminator."""
    assert record['name'] == 'pcurve'
    name = b'\x0d\x06pcurve'
    pieces = [encode_token(token) for token in record['tokens']]
    cursor = record['offset']+len(name)
    for token, piece in zip(record['tokens'], pieces):
        assert token['offset'] == cursor
        assert raw[cursor:cursor+len(piece)] == piece
        cursor += len(piece)
    expected = name+b''.join(pieces)+b'\x11'
    assert cursor+1 == record['end_offset']
    assert raw[record['offset']:record['end_offset']] == expected
    return {'full_record_bytes': len(expected), 'typed_fields_replayed': len(pieces),
            'sha256': hashlib.sha256(expected).hexdigest(), 'exact_name_fields_and_terminator': True}


def bernstein(points, fraction):
    """Independent explicit cubic Bernstein formula; no knots/de Boor calls."""
    assert len(points) == 4
    t, s = fraction, 1-fraction
    factors = (s*s*s, 3*s*s*t, 3*s*t*t, t*t*t)
    return [sum(w*p[axis] for w, p in zip(factors, points)) for axis in (0, 1)]


def independent_evaluations(cache):
    points = cache['control_points_uv']
    compact = cache['stored_compact_knots']
    degree = cache['degree']
    tests = []
    if degree == 3:
        # Repeated interior knots of multiplicity degree produce C0 joins:
        # each adjacent span is directly represented by four Bernstein points.
        assert all(multiplicity == 3 for _, multiplicity in compact)
        assert len(points) == 3*(len(compact)-1)+1
        for span in range(len(compact)-1):
            a, b = compact[span][0], compact[span+1][0]
            span_points = points[3*span:3*span+4]
            for fraction in (.25, .5, .75):
                parameter = a+(b-a)*fraction
                expected = bernstein(span_points, fraction)
                actual = evaluate_pcurve(cache, parameter)
                error = math.dist(expected, actual)
                assert error < 1e-12
                tests.append({'span': span, 'fraction': fraction, 'parameter': parameter,
                              'independent_uv': expected, 'deboor_uv': actual, 'error_uv': error})
        method = 'Independent cubic Bernstein evaluation at three interior points of every C0 span'
    else:
        assert degree == 1 and len(points) == 2 and len(compact) == 2
        a, b = cache['parameter_domain']
        for fraction in (.25, .5, .75):
            expected = [(1-fraction)*points[0][axis]+fraction*points[1][axis] for axis in (0, 1)]
            actual = evaluate_pcurve(cache, a+(b-a)*fraction)
            error = math.dist(expected, actual)
            assert error < 1e-12
            tests.append({'fraction': fraction, 'independent_uv': expected, 'deboor_uv': actual, 'error_uv': error})
        method = 'Independent linear interpolation at three interior parameters'
    return {'method': method, 'sample_count': len(tests), 'maximum_error_uv': max(t['error_uv'] for t in tests),
            'samples': tests}


def validate(zstd_library):
    # Read-only historical source comparison, explicitly requested for this task.
    source = subprocess.run(['git', 'show', BASELINE_REVISION+':decode_pcurve.py'],
                            cwd=ROOT, check=True, capture_output=True, text=True).stdout
    old = {'__name__': 'historical_decode_pcurve'}
    exec(compile(source, BASELINE_REVISION+':decode_pcurve.py', 'exec'), old)
    old_decode = old['decode_pcurve']
    files = []
    for folder in TRUTH_FOLDERS:
        truth = json.loads((ROOT / folder / 'ground_truth.json').read_text())
        files.extend(str(Path(folder) / sample['file']) for sample in truth['samples'])
    assert len(files) == len(set(files)) == 15
    report = {'scope': 'Exactly15 saved archives named by the two edgemodes ground_truth sample lists; not the full559-file corpus',
              'files_inspected': files,
              'baseline': {'revision': BASELINE_REVISION, 'source': 'git show508b426:decode_pcurve.py',
                           'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
                           'comparison': 'Exact full successful result-dictionary equality, not selected fields or sample coordinates'},
              'integration': {'reader': 'decode_pcurve.decode_pcurve(record)',
                              'validator': '/usr/bin/python3 validate_pcurve_cache_modes.py',
                              'reader_changes_by_this_task': False},
              'new_caches': [], 'previous_outputs': [], 'unresolved': [], 'guards': [],
              'limitations': [
                  'Only stored non-rational degree-one/cubic exp_par_cur caches are evaluated.',
                  'Wrapper flags are literal stored booleans. No reversal, parameter remapping, active/final lifecycle or coedge sense is inferred.',
                  'Inline support ref remains in its unresolved namespace; it is not treated as an ASM entity index.',
                  'Independent Bernstein agreement validates cached polynomial evaluation, not exact procedural trimmed-face geometry or an API evaluator match.',
                  'Full typed record bytes are replayed exactly; this is validation of existing stored payloads, not a native CAD writer.',
                  'No direct API UV-cache/evaluator getters were captured for the new layouts. Native offset fields are applied exactly as the existing cache reader specifies.'
              ]}
    records_by_key = {}
    for relative in files:
        for member, raw in read_members(ROOT / relative, zstd_library).items():
            if not member.endswith(('.smb', '.smbh')):
                continue
            parsed = inspect_asm(raw)
            assert parsed['complete_token_stream']
            for record in parsed['records']:
                if record['record_kind'] != 'entity' or record['name'] != 'pcurve' or record['section'] != 'geometry':
                    continue
                key = (relative, member, record['index'])
                records_by_key[key] = record
                literal_replay = replay(record, raw)
                try:
                    cache = decode_pcurve(record)
                except (ValueError, IndexError) as error:
                    report['unresolved'].append({'file': relative, 'member': member, 'record_index': record['index'],
                                                 'reason': str(error), 'payload_replay': literal_replay})
                    continue
                entry = {'file': relative, 'member': member, 'record_index': record['index'],
                         'record_offset': record['offset'], 'payload_replay': literal_replay,
                         'cache': cache, 'evaluation_check': independent_evaluations(cache)}
                try:
                    previous = old_decode(record)
                except (ValueError, IndexError) as error:
                    entry['previous_failure'] = str(error)
                    assert cache['stored_prefix_flag_4'] == record['tokens'][4]['value']
                    # The independently measured exact trailer length identifies
                    # its literal support flag without relying on cached semantics.
                    trailer = len(record['tokens'])-14
                    assert cache['stored_support_surface_flag'] == record['tokens'][trailer+2]['value']
                    assert cache['stored_span_count'] == len(cache['stored_compact_knots'])-1
                    report['new_caches'].append(entry)
                else:
                    assert cache == previous
                    entry['exact_previous_dictionary_equality'] = True
                    report['previous_outputs'].append(entry)
    assert len(report['new_caches']) == 10
    assert len({c['file'] for c in report['new_caches']}) == 3
    assert len(report['previous_outputs']) == 2 and not report['unresolved']
    expected = {(TRUTH_FOLDERS[0]+'/fillet_curvature.f3d', i) for i in (25, 34, 37, 55)}
    expected |= {(TRUTH_FOLDERS[1]+'/'+f, i) for f in ('fillet_chord.f3d', 'fillet_asymmetric.f3d') for i in (25, 34, 55)}
    assert {(e['file'], e['record_index']) for e in report['new_caches']} == expected
    base_key = next(key for key in records_by_key if key[0] == files[0] and key[2] == 25)
    base = records_by_key[base_key]
    def reject(label, mutate):
        changed = copy.deepcopy(base)
        mutate(changed['tokens'])
        try:
            decode_pcurve(changed)
        except (ValueError, IndexError) as error:
            report['guards'].append({'case': label, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError('Malformed pcurve accepted: '+label)
    reject('Unsupported degree/form pair', lambda t: t[8].update(value=2))
    reject('Non-increasing compact knots', lambda t: t[13].update(value=t[11]['value']))
    reject('Compact multiplicity exceeds degree', lambda t: t[12].update(value=4))
    reject('Unexpected trailing field', lambda t: t.append({'kind': 'integer', 'value': 0}))
    reject('Control point must have double type', lambda t: t[23].update(kind='integer'))
    trailer = len(base['tokens'])-14
    reject('Support ref wrapper has wrong closing token', lambda t: t[trailer+6].update(kind='subtype_start'))
    cubic = [e for e in report['new_caches'] if e['cache']['degree'] == 3]
    linear = [e for e in report['new_caches'] if e['cache']['degree'] == 1]
    report['summary'] = {
        'archives_inspected': len(files), 'new_caches': len(report['new_caches']),
        'files_with_new_caches': len({e['file'] for e in report['new_caches']}),
        'new_cubic_multispan_caches': len(cubic), 'new_linear_flag_variants': len(linear),
        'previous_dictionary_outputs_unchanged': len(report['previous_outputs']),
        'complete_typed_record_replays': len(records_by_key),
        'cubic_spans_bernstein_checked': sum(e['cache']['stored_span_count'] for e in cubic),
        'independent_cubic_interior_evaluations': sum(e['evaluation_check']['sample_count'] for e in cubic),
        'independent_linear_interior_evaluations': sum(e['evaluation_check']['sample_count'] for e in linear+report['previous_outputs']),
        'maximum_independent_evaluation_error_uv': max(e['evaluation_check']['maximum_error_uv'] for e in report['new_caches']+report['previous_outputs']),
        'malformed_guards': len(report['guards']), 'unresolved_pcurves_in_scope': len(report['unresolved'])}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='pcurve-cache-mode-decoding.json')
    args = parser.parse_args()
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report = validate(str(zstd))
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
