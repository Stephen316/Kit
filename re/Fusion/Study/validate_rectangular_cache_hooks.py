"""Committed rectangular defaults and bounded Feature-source callback guards."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from decode_body_bindings import decode_body_bindings
from decode_rectangular_cache_evidence import decode_rectangular_cache_evidence
from decode_rectangular_feature_caches import _feature_source
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
FEATURE_CONTROLS = ('rectmodes-a069f8f4b8a2/feature_optimized.f3d',
    'rectmodes-a069f8f4b8a2/feature_identical.f3d',
    'rectmodes-a069f8f4b8a2/feature_adjust.f3d',
    'rectsymholdouts-cf85ce4a0382/feature_input.f3d')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(zstd):
    frozen_path = ROOT/'rectangular-cache-evidence-decoding.json'
    frozen = json.loads(frozen_path.read_text())
    if len(frozen['samples']) != 12:
        raise AssertionError('Committed ccd06a7 twelve default controls differ')
    cases, checks, guards = [], [], []
    feature_empty = next(s['expected_summary'] for s in frozen['samples']
        if s['archive'] == FEATURE_CONTROLS[0])

    def check(label, value):
        if not value:
            raise AssertionError(label)
        checks.append(label)

    def forbidden(*_args):
        raise AssertionError('BODY input invoked the opt-in Feature callback')

    archives = [s['archive'] for s in frozen['samples']]
    archives += [a for a in FEATURE_CONTROLS if a not in archives]
    expectations = {s['archive']: s['expected_summary'] for s in frozen['samples']}
    for archive in archives:
        data, records, features, member, members = load(ROOT, archive, zstd)
        raw = decode_body_bindings(data, records, member, dict(streams=[dict(member=n,
            complete_token_stream=True, declared_root_records=[]) for n in members if n.endswith('.smbh')]))
        before = copy.deepcopy((features, raw))
        actual = decode_rectangular_cache_evidence(data, records, features, member, members, raw)
        expected = expectations.get(archive, feature_empty)
        check(archive+' full default dictionary exact', actual == expected)
        check(archive+' input metadata/bindings unchanged', (features, raw) == before)
        is_feature = archive in FEATURE_CONTROLS
        if actual['decoded']:
            hooked = decode_rectangular_cache_evidence(data, records, features, member, members, raw,
                feature_source_resolver=forbidden)
            check(archive+' BODY callback inactive and whole dictionary exact', hooked == actual)
        cases.append(dict(archive=archive, archive_sha256=sha(ROOT/archive), member=member,
            expected_default=actual, committed_twelve_control=archive in expectations,
            default_feature_skip=is_feature,
            expected_basis='Committed full ccd06a7 sample' if archive in expectations else
                'Same prior BODY-only Feature skip, using committed Feature empty dictionary; pinned main baseline independently records absence'))

    archive = FEATURE_CONTROLS[0]
    data, records, features, member, members = load(ROOT, archive, zstd)
    raw = decode_body_bindings(data, records, member, dict(streams=[dict(member=n,
        complete_token_stream=True, declared_root_records=[]) for n in members if n.endswith('.smbh')]))
    before = copy.deepcopy(features)

    def source(*args):
        return _feature_source(*args, features=features)

    positive = decode_rectangular_cache_evidence(data, records, features, member, members, raw,
        feature_source_resolver=source)
    check('Opt-in Features type and actual source route retained', len(positive['decoded']) == 1
        and not positive['unresolved'] and positive['decoded'][0]['pattern_entity_type'] == 'Features'
        and positive['decoded'][0]['stored_entity_type_code'] == 1
        and positive['decoded'][0]['source_feature_object_ids'] == [243]
        and positive['decoded'][0]['source_native_body_object_ids'] == [275])
    row = positive['decoded'][0]
    check('Feature source descriptor is not labeled BODY selection',
        'source_feature_descriptor' in row['source_cache_bodies'][0]
        and 'source_descriptor' not in row['source_cache_bodies'][0])
    check('Full source generic/FPM chain and explicit BODY binding retained',
        any(p['native_body_object_id'] == 275 and p['asm_body_index'] == 1
            and p['binding']['asm_stored_entity_id'] == p['binding']['stored_handle']
            and p['proof']['FPM_literal_identity'] is None
            and sum(len(f['opaque_FPM_attributes']) for f in p['proof']['faces']) == 6
            for p in row['source_feature_face_naming_proofs']))
    check('Feature settings and parameters unchanged', features == before)

    def rejected(label, mutator):
        def altered(*args):
            out = source(*args)
            mutator(out)
            return out
        out = decode_rectangular_cache_evidence(data, records, features, member, members, raw,
            feature_source_resolver=altered)
        check(label, not out['decoded'] and len(out['unresolved']) == 1)
        guards.append(dict(guard=label, rejected=True, reason=out['unresolved'][0]['reason']))

    rejected('Reject callback missing source provenance', lambda out: out.pop('provenance'))
    rejected('Reject callback BODY count disagreeing with Feature descriptors',
        lambda out: out['source_native_body_object_ids'].append(999999))
    rejected('Reject callback descriptor differing from actual owned proxy',
        lambda out: out['descriptor_object_ids'].__setitem__(0, 1))
    rejected('Reject callback source Feature differing from descriptor leaf',
        lambda out: out['source_feature_object_ids'].__setitem__(0, row['feature_object_id']))
    rejected('Reject callback BODY not owned by selected source Feature',
        lambda out: out['source_native_body_object_ids'].__setitem__(0,
            row['element_cache_groups'][0]['cache_bodies'][0]['result_native_body_object_id']))
    def duplicates(out):
        for field in ('descriptor_object_ids', 'source_feature_object_ids', 'source_native_body_object_ids'):
            out[field].append(out[field][0])
    rejected('Reject duplicate callback source identities', duplicates)
    return dict(scope='Committed BODY cache/default outputs remain exact; Feature inputs require an explicit source resolver and reuse canonical complete generic/FPM FACE chains without new naming grammar',
        interface='decode_rectangular_cache_evidence(..., *, feature_source_resolver=None)',
        baseline=dict(commit='ccd06a7', committed_report=frozen_path.name,
            committed_report_sha256=sha(frozen_path), committed_core_sha256=frozen['source_sha256']['decode_rectangular_cache_evidence.py']),
        default_controls=cases,
        feature_hook_positive=dict(archive=archive, expected_summary=positive,
            scope='Hook/source schema acceptance; complete four-fixture native/API evidence belongs to rectangular-feature-cache-decoding.json'),
        validation=dict(committed_default_dictionaries_exact=12, body_defaults_exact=8,
            existing_empty_controls_exact=4, default_feature_skip_cases=4,
            additional_default_feature_skip_checks=3, total_default_controls=len(cases),
            inactive_BODY_callback_dictionaries_exact=8, positive_feature_hook_cases=1,
            focused_checks=len(checks), malformed_callback_guards=len(guards), main_calls=0, live_API_calls=0),
        checks=checks, malformed_guards=guards,
        callback_contract='(data,records,feature,input_proxy_id,collection_id) -> exact descriptor_object_ids/source_feature_object_ids/source_native_body_object_ids/provenance dictionary',
        source_sha256={f: sha(ROOT/f) for f in ('decode_rectangular_cache_evidence.py',
            'validate_rectangular_cache_hooks.py', 'decode_rectangular_feature_caches.py',
            'decode_rectangular_pattern_modes.py', 'decode_circular_feature_caches.py',
            'decode_body_selections.py', 'decode_body_asm_identifiers.py')},
        limitations=['Features remain Features, and BODY mode never invokes the callback',
            'Only successful Feature rows expand top-level scope; default summaries and all BODY dictionaries retain prior scope',
            'FPM literals remain opaque and do not supply source feature IDs',
            'Measured relative cache fits are not serialized transforms, logical/API element IDs, current placement or regeneration'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--zstd-library')
    parser.add_argument('--output', default='rectangular-cache-hook-decoding.json')
    args = parser.parse_args()
    zstd = args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report = validate(zstd)
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['validation'], sort_keys=True))


if __name__ == '__main__':
    main()
