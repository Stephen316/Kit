"""Focused main-reader integration against saved evidence and a fixed baseline."""

import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile

from decode_basics import decode_basics

ROOT = Path(__file__).resolve().parent
BASELINE = '508b426'
GEOMETRY_TARGETS = {
    'edgemodes-52695761f185/fillet_curvature.f3d',
    'edgemodes-87edbf67527b/fillet_asymmetric.f3d',
    'edgemodes-87edbf67527b/fillet_chord.f3d',
}


def differences(before, after, path=''):
    if type(before) is not type(after):
        return [path]
    if isinstance(before, dict):
        return sorted([path+'/'+key for key in before.keys() ^ after.keys()]+[
            p for key in before.keys() & after.keys()
            for p in differences(before[key], after[key], path+'/'+key)])
    if isinstance(before, list):
        if len(before) != len(after):
            return [path+'(length)']
        return [p for i, (a, b) in enumerate(zip(before, after))
                for p in differences(a, b, path+'/'+str(i))]
    return [] if before == after else [path]


def baseline_outputs(files, zstd):
    """Use only trusted Python sources from the recorded local Git baseline."""
    payload = subprocess.check_output(['git', 'archive', BASELINE, '--', '*.py'], cwd=ROOT)
    with tempfile.TemporaryDirectory(prefix='fusion-history-baseline-') as folder:
        with tarfile.open(fileobj=io.BytesIO(payload)) as archive:
            for item in archive:
                relative = Path(item.name)
                if not item.isfile() or relative.is_absolute() or '..' in relative.parts:
                    raise ValueError('Unexpected baseline source archive entry')
                target = Path(folder)/relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.extractfile(item).read())
        script = ('import json,sys; from decode_basics import decode_basics; '
                  'print(json.dumps([decode_basics(p,sys.argv[1]) for p in sys.argv[2:]]))')
        return json.loads(subprocess.check_output(
            ['/usr/bin/python3', '-c', script, zstd, *[str(ROOT/name) for name in files]], cwd=folder))


def validate(zstd):
    evidence = json.loads((ROOT/'fpm-tracking-decoding.json').read_text())
    cases = evidence['samples']+evidence['controls']
    files = [row['file'] for row in cases]
    old_outputs = baseline_outputs(files, zstd)
    report = {'scope': 'Nine saved archives; main-reader integration of qualified alternate-cache correspondences and stored spline geometry, without live Fusion access or exact historical source claims',
              'baseline_commit': BASELINE, 'samples': [],
              'limitations': ['No complete-format percentage, native writer or history regeneration.',
                              'Alternative views remain separately scoped; initial geometry is not replaced.',
                              'Approximation cache evaluations are not direct Fusion API evaluator comparisons.']}
    tracks = qualified = 0
    for case, before in zip(cases, old_outputs):
        filename = case['file']
        current = json.loads(json.dumps(decode_basics(ROOT/filename, zstd)))
        stream, = current['streams']
        summary = stream['fpm_selection_tracking']
        assert summary == case['expected_summary'], filename
        for track in summary['tracks']:
            assert track['qualified_historical_state'] is None
            assert track['exact_selected_source_identity'] is None
            assert track['source_curve_geometry'] is None
            assert track['alternative_view_correspondence']['recipe_and_FPM_owner_agree'] is True
            tracks += 1
            qualified += 1
        paths = differences(before, current)
        for path in paths:
            if path == '/streams/0/fpm_selection_tracking':
                continue
            if filename in GEOMETRY_TARGETS:
                # Admit only the newly decoded caches and their geometry-only
                # status/UV closure fields. Structural graph fields stay exact.
                if re.fullmatch(r'/asm_decoding/streams/\d+/topology/(?:unresolved\(length\)|body_graphs/0/(?:spline_curves\(length\)|spline_surfaces\(length\)|analytic_surfaces/0/geometry_status|face_trim_loops/0/(?:uv_endpoints_close_in_this_chart|trims/\d+/uv_curve)))', path):
                    continue
                if (filename.endswith('/fillet_curvature.f3d') and path in (
                        '/streams/0/selection_recipe_incidence/unresolved/0/bounded_operand_evidence',
                        '/streams/0/selection_recipe_incidence/unresolved/0/reason')):
                    continue
            raise AssertionError((filename, 'Unexpected prior-output change', path))
        initial = before['streams'][0]['selection_recipe_incidence']
        actual = stream['selection_recipe_incidence']
        assert actual['associations'] == initial['associations']
        assert len(actual['unresolved']) == len(initial['unresolved'])
        if filename.endswith('/fillet_curvature.f3d'):
            assert not next(s for s in current['asm_decoding']['streams'] if s['member'].endswith('.smbh'))['topology']['unresolved']
            assert actual['unresolved'], 'A decoded cache must not clear source-selection failure'
        report['samples'].append({'file': filename, 'tracks': len(summary['tracks']),
                                  'qualified_alternate_correspondences': len(summary['tracks']),
                                  'matches_focused_evidence': True, 'prior_output_difference_paths': paths,
                                  'all_other_prior_output_unchanged': True,
                                  'original_source_selection_failures_retained': True})
    assert len(cases) == 9 and tracks == qualified == 9
    report['summary'] = {'saved_files': len(cases), 'unrelated_controls': len(evidence['controls']),
                         'tracking_correspondences': tracks, 'qualified_alternate_correspondences': qualified,
                         'unexpected_prior_output_changes': 0, 'live_fusion_captures': 0}
    return report


if __name__ == '__main__':
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    result = validate(str(zstd))
    (ROOT/'history-cache-integration.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['summary'], sort_keys=True))
