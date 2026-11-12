"""Default dictionary preservation and bounded circular feature callback checks."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from decode_body_bindings import decode_body_bindings
from decode_circular_feature_caches import _feature_source, _face_names
from decode_circular_placement_evidence import decode_circular_placement_evidence
from fusion_archive import read_members
from fusion_metadata import design_records
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
BASELINE = Path('/private/tmp/fusion-circular-cache-hook-baseline.json')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(zstd, baseline_path=BASELINE):
    if baseline_path.is_file():
        frozen = json.loads(baseline_path.read_text())
    else:
        frozen = json.loads((ROOT/'circular-cache-hook-decoding.json').read_text())['frozen_pre_hook_defaults']
    expected_files = ['circularmodes-45f859c1f1b6/'+name+'.f3d' for name in
        ('body_full', 'body_negative', 'body_suppressed', 'body_symmetric', 'multiple_customaxis',
         'feature_optimized', 'feature_identical', 'feature_adjust')]
    if [s['archive'] for s in frozen['samples']] != expected_files:
        raise AssertionError('Fixed eight pre-hook controls differ')
    checks, controls, guards = [], [], []

    def check(label, value):
        if not value:
            raise AssertionError(label)
        checks.append(label)

    def forbidden(*_args):
        raise AssertionError('Body/default feature branch must not invoke opt-in callbacks')

    for sample in frozen['samples']:
        archive = sample['archive']
        members = read_members(ROOT/archive, zstd)
        member = sample['member']
        data = members[member]
        records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
        features = copy.deepcopy(sample['features'])
        raw = decode_body_bindings(data, records, member, dict(streams=[dict(member=n,
            complete_token_stream=True, declared_root_records=[]) for n in members if n.endswith('.smbh')]))
        output = decode_circular_placement_evidence(data, records, features, member, members, raw)
        check(archive+' complete pre-hook default dictionary exact', output == sample['expected_default'])
        if '/feature_' in archive:
            # A face hook alone cannot activate source semantics.
            hooked = decode_circular_placement_evidence(data, records, features, member, members, raw,
                face_name_resolver=forbidden)
        else:
            hooked = decode_circular_placement_evidence(data, records, features, member, members, raw,
                feature_source_resolver=forbidden, face_name_resolver=forbidden)
        check(archive+' inactive callbacks preserve complete dictionary', hooked == output)
        controls.append(dict(archive=archive, archive_sha256=sha(ROOT/archive),
            member=member, expected_default=output, inactive_callbacks_exact=True))

    archive = expected_files[5]
    data, records, features, member, members = load(ROOT, archive, zstd)
    raw = decode_body_bindings(data, records, member, dict(streams=[dict(member=n,
        complete_token_stream=True, declared_root_records=[]) for n in members if n.endswith('.smbh')]))
    saved_features = copy.deepcopy(features)

    def source(d, r, f, p, c):
        return _feature_source(d, r, f, p, c, features=features)

    positive = decode_circular_placement_evidence(data, records, features, member, members, raw,
        feature_source_resolver=source, face_name_resolver=_face_names)
    check('Feature opt-in retains Features type and distinct source proof', len(positive['decoded']) == 1
        and not positive['unresolved'] and positive['decoded'][0]['pattern_entity_type_code'] == 1
        and positive['decoded'][0]['source_feature_object_ids'] == [243]
        and positive['decoded'][0]['source_native_body_object_ids'] == [275])
    check('Source BODY explicit stored-ID proof retained', any(p['native_body_object_id'] == 275
        and p['binding']['asm_body_index'] == 1 and p['binding']['asm_stored_entity_id'] == 6
        for p in positive['decoded'][0]['source_feature_face_naming_proofs']))
    check('No feature/settings mutation through callbacks', features == saved_features)

    def rejected(label, source_mutator=None, face_mutator=None):
        def altered_source(*args):
            out = source(*args)
            if source_mutator:
                source_mutator(out)
            return out
        def altered_face(*args):
            out = _face_names(*args)
            if face_mutator:
                face_mutator(out)
            return out
        out = decode_circular_placement_evidence(data, records, features, member, members, raw,
            feature_source_resolver=altered_source, face_name_resolver=altered_face)
        check(label, not out['decoded'] and len(out['unresolved']) == 1)
        guards.append(dict(guard=label, rejected=True, reason=out['unresolved'][0]['reason']))

    rejected('Reject feature-source callback missing provenance', lambda out: out.pop('provenance'))
    rejected('Reject source/body count disagreement', lambda out: out['source_native_body_object_ids'].append(999999))
    rejected('Reject source ID differing from explicit descriptor leaf',
        lambda out: out['source_feature_object_ids'].__setitem__(0, 201))
    rejected('Reject source BODY not owned by selected feature',
        lambda out: out['source_native_body_object_ids'].__setitem__(0, 325))
    rejected('Reject incomplete six-face coverage', face_mutator=lambda out: out['names'].pop(next(iter(out['names']))))
    def wrong_tuple(out):
        first = next(iter(out['names']))
        text, index = out['names'][first]['name_key']
        out['names'][first]['name_key'] = (text, index+1)
    rejected('Reject callback name tuple differing from exact payload', face_mutator=wrong_tuple)
    return dict(scope='Eight complete pre-hook standalone default dictionaries plus bounded feature callback validation; no existing body settings, placements or getter warnings changed',
        interface='decode_circular_placement_evidence(..., *, feature_source_resolver=None, face_name_resolver=None)',
        frozen_pre_hook_defaults=frozen, default_controls=controls,
        feature_hook_positive=dict(archive=archive, expected_summary=positive,
            scope='Hook/schema acceptance only; complete native/API feature association evidence is in circular-feature-cache-decoding.json'),
        callback_contract=dict(feature_source_resolver='(data,records,feature,input_proxy_id,collection_id) -> descriptor_object_ids/source_feature_object_ids/source_native_body_object_ids/provenance',
            face_name_resolver='(blob,parsed,graph) -> names/proof; names require six complete serialized face tuples, typed generic attribute owners and exact payload replay',
            activation='Callbacks are invoked only for explicit feature-input mode1; body mode2 remains exact',
            proof_scope='Canonical reciprocal generic/FPM owner-chain proof belongs to the strict callback; FPM numbers are never promoted into native IDs'),
        validation=dict(default_controls=8, complete_body_defaults_exact=5, complete_feature_defaults_exact=3,
            inactive_callback_dictionaries_exact=8, positive_feature_hook_cases=1,
            focused_checks=len(checks), malformed_callback_guards=len(guards), main_calls=0, live_API_calls=0),
        checks=checks, malformed_guards=guards,
        source_sha256={name: sha(ROOT/name) for name in ('decode_circular_placement_evidence.py',
            'validate_circular_cache_hooks.py', 'decode_circular_feature_caches.py', 'decode_circular_patterns.py',
            'decode_asm_recipe_tags.py', 'decode_counted_asm_names.py', 'decode_body_selections.py', 'decode_body_asm_identifiers.py')},
        limitations=['The new resolver does not reinterpret Features as Bodies or alter tool settings',
            'Proper rigid matrices are measured from identity-fixed cached vertices, not serialized per-element transforms',
            'Existing API getter/placement disagreement, current lifecycle and regeneration remain unresolved'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--zstd-library')
    parser.add_argument('--baseline', default=str(BASELINE))
    parser.add_argument('--output', default='circular-cache-hook-decoding.json')
    args = parser.parse_args()
    zstd = args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report = validate(zstd, Path(args.baseline))
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['validation'], sort_keys=True))


if __name__ == '__main__':
    main()
