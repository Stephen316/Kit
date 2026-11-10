"""Inventory saved initial ASM topology/cache diagnostics, without live Fusion."""

from collections import Counter, defaultdict
import json
from pathlib import Path
import time

from asm_records import inspect_asm_members
from fusion_archive import read_members

ROOT = Path(__file__).resolve().parent


def audit(zstd):
    started = time.monotonic()
    files = sorted(ROOT.glob('*/*.f3d'))
    groups, initial_kinds = defaultdict(list), Counter()
    failures, blobs, graphs, partial_boundaries = [], 0, 0, 0
    for path in files:
        inspected = inspect_asm_members(read_members(path, zstd), include_records=True)
        for stream in inspected['streams']:
            blobs += 1
            if not stream.get('complete_token_stream'):
                failures.append({'file': str(path.relative_to(ROOT)), 'member': stream['member'],
                                 'reason': stream.get('unresolved_reason', stream.get('failure'))})
                continue
            records = stream['records']
            for record in records:
                if record['section'] == 'geometry' and record['record_kind'] == 'entity':
                    initial_kinds[record['name']] += 1
            topology = stream['topology']
            graphs += len(topology['body_graphs'])
            boundaries = topology.get('vbl_component_boundaries', {})
            partial_boundaries += sum(len(row['components']) for row in boundaries.get('decoded', []))
            for error in topology['unresolved']:
                index = error.get('index')
                record = records[index] if isinstance(index, int) and 0 <= index < len(records) else None
                subtype = (record['tokens'][5]['value'] if record and len(record['tokens']) > 5
                           and record['name'] in ('spline-surface', 'intcurve-curve') else None)
                key = (error.get('kind'), subtype, error['reason'])
                groups[key].append({'file': str(path.relative_to(ROOT)), 'member': stream['member'], **error,
                                    'subtype': subtype})
    baseline = json.loads((ROOT/'asm-geometry-frontier-b6372ab.json').read_text())
    return {'scope': 'Read-only inventory of reported initial ASM body-graph/geometry diagnostics; feature definitions, unknown classes, opaque fields and trailing-state geometry are outside these counts',
            'baseline_snapshot': {'commit': baseline['baseline_commit'], 'report': 'asm-geometry-frontier-b6372ab.json',
                                  'archive_count': baseline['archive_count'], 'blob_count': baseline['blob_count'],
                                  'unresolved_diagnostic_count': baseline['unresolved_diagnostic_count']},
            'archive_count': len(files), 'blob_count': blobs, 'decoded_initial_BODY_graphs': graphs,
            'unresolved_diagnostic_count': sum(len(rows) for rows in groups.values()),
            'groups': [{'kind': kind, 'subtype': subtype, 'reason': reason, 'count': len(rows), 'entries': rows}
                       for (kind, subtype, reason), rows in sorted(groups.items(), key=lambda item: (-len(item[1]), str(item[0])))],
            'initial_entity_record_types': dict(sorted(initial_kinds.items())),
            'bounded_VBL_boundary_components': partial_boundaries, 'incomplete_token_streams': failures,
            'elapsed_seconds': round(time.monotonic()-started, 3),
            'limits': ['A diagnostic can represent multiple unimplemented fields; counts are not feature or format coverage percentages.',
                       'Zero diagnostics on a record does not imply all its procedural/trailer/parameter semantics are known.',
                       'Raw record-type counts include metadata and partially decoded types, without classifying them as complete support.',
                       'Current/final lifecycle, complete translation, native writing and history regeneration remain unresolved.',
                       'No live Fusion API call or full main-reader corpus rerun occurs.']}


if __name__ == '__main__':
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    result = audit(str(zstd))
    (ROOT/'asm-geometry-frontier-current.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in ('archive_count', 'blob_count', 'unresolved_diagnostic_count',
          'bounded_VBL_boundary_components', 'elapsed_seconds', 'incomplete_token_streams')}, sort_keys=True))
