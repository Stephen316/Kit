"""Focused main-reader checks for Fillet/context caches and scaled line vectors."""

import json
from pathlib import Path
import re

from decode_basics import decode_basics
from validate_history_cache_integration import baseline_outputs, differences
from validate_scaled_line_directions import FILES as SCALED_FILES

ROOT = Path(__file__).resolve().parent
SURFACES = {'edgemodes-87edbf67527b/fillet_asymmetric.f3d',
            'edgemodes-87edbf67527b/fillet_chord.f3d'}


def inputs():
    contexts = json.loads((ROOT/'fpm-context-cache-decoding.json').read_text())
    context_cases = {row['file']: row for row in contexts['samples']+contexts['controls']}
    files = list(dict.fromkeys(list(SCALED_FILES)+list(context_cases)))
    return files, context_cases


def validate_outputs(files, baseline, current):
    expected_files, contexts = inputs()
    assert files == expected_files and len(baseline) == len(current) == len(files)
    surface_evidence = {row['file']: row for row in
                        json.loads((ROOT/'variable-blend-cache-decoding.json').read_text())['samples']}
    spring_evidence = {row['file']: row for row in
                       json.loads((ROOT/'spring-curve-cache-decoding.json').read_text())['samples']}
    report = {'scope': 'Seventeen saved main-reader archives, compared with local baseline b6372ab; geometry caches and role-qualified context fields only, without live Fusion capture',
              'baseline_commit': 'b6372ab', 'samples': []}
    cache_count = surfaces = curves = 0
    for filename, before, after in zip(files, baseline, current):
        assert (ROOT/before['file']).resolve() == (ROOT/after['file']).resolve() == ROOT/filename
        old_stream, = before['streams']
        stream, = after['streams']
        context = stream['fpm_context_line_caches']
        if filename in contexts:
            assert context == contexts[filename]['expected_summary']
        else:
            assert not context['decoded'] and not context['unresolved']
        cache_count += len(context['decoded'])
        assert stream['fpm_selection_tracking'] == old_stream['fpm_selection_tracking']
        # Geometry recovery improves diagnostics without supplying a historical
        # selected-source identity or clearing other tool/context failures.
        old_selection, selection = (s['selection_recipe_incidence'] for s in (old_stream, stream))
        assert selection['associations'] == old_selection['associations']
        assert len(selection['unresolved']) == len(old_selection['unresolved'])
        paths = differences(before, after)
        admitted = []
        for path in paths:
            if path in ('/file', '/streams/0/fpm_context_line_caches'):
                admitted.append(path)
                continue
            if filename in set(SCALED_FILES) | SURFACES:
                if re.fullmatch(r'/asm_decoding/streams/\d+/topology/unresolved\(length\)', path):
                    admitted.append(path)
                    continue
                if path in ('/streams/0/selection_recipe_incidence/unresolved/0/reason',
                            '/streams/0/selection_recipe_incidence/unresolved/0/bounded_operand_evidence'):
                    admitted.append(path)
                    continue
            if filename in SURFACES and re.fullmatch(
                    r'/asm_decoding/streams/\d+/topology/body_graphs/0/(?:analytic_surfaces/0/geometry_status|spline_curves\(length\)|spline_surfaces\(length\))', path):
                admitted.append(path)
                continue
            raise AssertionError((filename, path, 'Unexpected prior-output change'))
        for asm in after['asm_decoding']['streams']:
            if filename in set(SCALED_FILES) | SURFACES:
                assert not asm['topology']['unresolved'], (filename, asm['member'])
            if filename in SURFACES and asm['member'].endswith('.smbh'):
                graph, = asm['topology']['body_graphs']
                surface, = graph['spline_surfaces']
                assert surface['cache'] == surface_evidence[filename]['cache']
                actual = {c['curve_index']: c['cache'] for c in graph['spline_curves']}
                for curve in spring_evidence[filename]['curves']:
                    assert actual[curve['record_index']] == curve['cache']
                    curves += 1
                surfaces += 1
        report['samples'].append({'file': filename, 'role_qualified_context_caches': len(context['decoded']),
            'new_geometry_matches_focused_reports': filename in SURFACES,
            'allowed_prior_output_changes': [p for p in admitted if p != '/file'],
            'all_other_prior_output_unchanged': True, 'source_selection_failure_counts_unchanged': True})
    assert len(files) == 17 and cache_count == 10 and surfaces == 2 and curves == 4
    report['summary'] = {'saved_files': len(files), 'context_caches': cache_count,
                         'new_surface_caches': surfaces, 'new_spring_curve_caches': curves,
                         'unexpected_prior_output_changes': 0, 'new_API_calls': 0,
                         'source_selection_failures_cleared': 0}
    return report


def validate(zstd):
    files, _ = inputs()
    baseline = baseline_outputs(files, zstd, revision='b6372ab')
    current = [json.loads(json.dumps(decode_basics(ROOT/name, zstd))) for name in files]
    return validate_outputs(files, baseline, current)


if __name__ == '__main__':
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    result = validate(str(zstd))
    (ROOT/'fillet-followup-integration.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['summary'], sort_keys=True))
