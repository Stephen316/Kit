"""Default-preservation and native support-role checks for Offset variants."""
import argparse
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct

from decode_body_selections import decode_body_selections
from decode_parameters import read_string
from decode_sketch import reference
from decode_surface_offset_sources import decode_surface_offset_sources as strict_decode
from decode_surface_offset_source_variants import decode_surface_offset_sources as variant_decode
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
BASELINE = Path('/private/tmp/fusion-surface-offset-intersection-baseline.json')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(zstd, baseline_path=BASELINE):
    baseline = json.loads(baseline_path.read_text())
    assert baseline['baseline_commit'] == 'cf0ffb9'
    before = {Path(output['file']).relative_to(ROOT).as_posix(): output['streams'][0]
        for output in baseline['before']}
    historical_path = ROOT/'surface-offset-source-decoding.json'
    historical = json.loads(historical_path.read_text())
    checks, defaults, variants, guards, positives = [], [], [], [], []

    def check(label, value):
        if not value:
            raise AssertionError(label)
        checks.append(label)

    def prepare(archive):
        loaded = load(ROOT, archive, zstd)
        data, records, features, member, members = loaded
        stream = before.get(archive)
        identifiers = stream['body_asm_identifiers'] if stream else dict(decoded=[])
        selections = stream['body_selections'] if stream else decode_body_selections(data, records)
        return loaded+(identifiers, selections)

    for sample in historical['samples']:
        archive = sample['archive']
        data, records, features, member, members, identifiers, selections = prepare(archive)
        arguments = data, records, features, member, members, identifiers, selections
        default = strict_decode(*arguments)
        enabled = variant_decode(*arguments)
        check(archive+' entire historical strict dictionary exact', default == sample['expected_summary'])
        check(archive+' inactive opt-in entire dictionary exact', enabled == default)
        defaults.append(dict(archive=archive, expected_default=default,
            entire_historical_dictionary_exact=True, inactive_optin_dictionary_exact=True))

    saved = None
    for archive in baseline['files'][:2]:
        arguments = prepare(archive)
        data, records, features, member, members, identifiers, selections = arguments
        original = copy.deepcopy((features, identifiers, selections))
        default = strict_decode(*arguments)
        check(archive+' default eight old failures exact', default == before[archive]['surface_offset_sources']
            and default['associations'] == [] and len(default['unresolved']) == 8
            and all(row['reason'] == 'Offset descriptor/source support reciprocity differs'
                for row in default['unresolved']))
        defaults.append(dict(archive=archive, expected_default=default,
            entire_pinned_baseline_dictionary_exact=True))
        enabled = variant_decode(*arguments)
        check(archive+' eight qualified variant owners no new unresolved',
            len(enabled['associations']) == 8 and enabled['unresolved'] == [])
        check(archive+' caller feature/identifier/selection metadata unchanged',
            (features, identifiers, selections) == original)
        by = {r.object_id: r for r in records if r.is_primary}
        proofs = []
        for row in enabled['associations']:
            proof = row['support_source_provenance']
            count = proof['stored_source_count']
            source_ids = [r['source_feature_object_id'] for r in proof['support_sources']]
            anchor_owner = row['historical_source_owner_object_id']
            source_classes = [by[identity].class_guid for identity in source_ids]
            check(archive+' owner'+str(row['owner_object_id'])+' literal typed distinct source roles',
                count in (2, 3) and len(set(source_ids)) == count
                and source_classes == ['DD405BC2-D673-44F0-8833-5CB2A1C186C7']*(count-1)
                    +['A07D5F17-68CB-464D-9935-BF68E98A865F']
                and (anchor_owner not in source_ids if count == 2 else source_ids[0] == anchor_owner))
            support = by[proof['descriptor_support_object_id']]
            raw = data[support.body:support.end]
            check(archive+' owner'+str(row['owner_object_id'])+' complete support bytes/raw refs replay',
                len(raw) == 39+19*count and raw.hex() == proof['exact_support_payload_hex']
                and struct.unpack_from('<I',raw,8)[0] == count
                and [reference(raw,12+19*i) for i in range(count)] == source_ids
                and reference(raw,12+19*count) == row['descriptor_object_id']
                and proof['exact_support_payload_replay'] is True)
            check(archive+' owner'+str(row['owner_object_id'])+' component proof retains independent owner roles',
                len({p['body_properties']['component_object_id'] for p in proof['body_ownership']}) == 1
                and all(s['component_object_id'] == proof['component_object_id'] for s in proof['dependency_scopes'])
                and {s['object_id'] for s in proof['dependency_scopes']}
                    == {row['owner_object_id'],anchor_owner,*source_ids})
            receiver = by[row['owner_object_id']]
            check(archive+' owner'+str(row['owner_object_id'])+' new metadata uint32 remains literal',
                struct.unpack_from('<I',data,receiver.body+row['stored_metadata_relative_offset'])[0]
                    == row['stored_metadata_uint32'] and row['stored_metadata_semantics'] is None)
            proofs.append(dict(owner_object_id=row['owner_object_id'],
                expected_support_source_provenance=proof, stored_metadata_uint32=row['stored_metadata_uint32'],
                stored_metadata_relative_offset=row['stored_metadata_relative_offset']))
        check(archive+' both support variants observed independently',
            sorted(p['expected_support_source_provenance']['stored_source_count'] for p in proofs) == [2]*4+[3]*4)
        variants.append(dict(archive=archive, archive_sha256=sha(ROOT/archive), native_owner_proofs=proofs))
        if saved is None:
            saved = arguments, enabled

    arguments, enabled = saved
    data, records, features, member, members, identifiers, selections = arguments
    by = {r.object_id:r for r in records if r.is_primary}
    row = enabled['associations'][0]
    owner = row['owner_object_id']
    support_id = row['descriptor_support_object_id']
    support = by[support_id]
    sources = row['support_source_provenance']['support_sources']

    def modified(offset, value):
        raw = bytearray(data)
        raw[offset:offset+len(value)] = value
        return bytes(raw)

    def exercise(label, changed_data=data, changed_records=records, failures=1, positive=False):
        changed_members = dict(members)
        changed_members[member] = changed_data
        out = variant_decode(changed_data,changed_records,features,member,changed_members,identifiers,selections)
        if positive:
            check(label+' remains qualified', len(out['associations']) == 8 and not out['unresolved'])
            positives.append(dict(label=label, successful_owner_count=8))
        else:
            check(label+' rejects only scoped attempted owners', len(out['associations']) == 8-failures
                and len(out['unresolved']) == failures)
            guards.append(dict(label=label, diagnostics=out['unresolved']))
        return out

    exercise('Support count/byte extent mismatch', modified(support.body+8,struct.pack('<I',3)))
    exercise('Support descriptor backlink changed', modified(support.body+51,struct.pack('<Q',owner)))
    exercise('Count-two support cannot substitute historical anchor-owner role',
        modified(support.body+13,struct.pack('<Q',row['historical_source_owner_object_id'])))
    source_id = sources[0]['source_feature_object_id']
    exercise('Support source concrete class changed', changed_records=[replace(r,class_guid='A07D5F17-68CB-464D-9935-BF68E98A865F')
        if r.object_id == source_id and r.is_primary else r for r in records], failures=8)
    exercise('Duplicate primary support source', changed_records=records+[by[source_id]], failures=8)
    exercise('Duplicate primary descriptor support', changed_records=records+[support], failures=8)
    receiver = by[owner]
    marker = receiver.body+row['stored_metadata_relative_offset']
    exercise('Changed repeated SurfaceOffset label', modified(marker+8,b'X'))
    _, index_offset = read_string(data[receiver.body:receiver.end],row['stored_metadata_relative_offset']+4)
    exercise('Changed repeated stored feature index', modified(receiver.body+index_offset,struct.pack('<Q',999999)))
    exercise('Changed repeated feature metadata name', modified(receiver.body+index_offset+12,b'X'))
    changed = exercise('Opaque uint32 marker has no identity/enum semantics',
        modified(marker,struct.pack('<I',0xffffffff)),positive=True)
    check('Changed opaque marker is retained literally', next(r for r in changed['associations']
        if r['owner_object_id'] == owner)['stored_metadata_uint32'] == 0xffffffff)
    exercise('Opaque support slot bytes retained without inferred semantics',
        modified(support.body+23,bytes([data[support.body+23]^1])),positive=True)

    return dict(interface='Strict historical reader plus allow_face_intersection_sources=False; facade enables only typed support/face-intersection variants',
        scope='Native source role/default proof only; separate C full cache goldens and API corroboration. No API face/VBL identity assignment.',
        baseline=dict(commit='cf0ffb9',path=str(baseline_path),sha256=sha(baseline_path)),
        historical_report_sha256=sha(historical_path), default_controls=defaults,
        variant_samples=variants, guards=guards, positive_literal_controls=positives, checks=checks,
        source_sha256={name:sha(ROOT/name) for name in ('decode_surface_offset_sources.py',
            'decode_surface_offset_source_variants.py','decode_surface_offset_intersections.py',
            'validate_surface_offset_source_variants.py','decode_owned_surface_selection.py',
            'decode_assembly.py','decode_body_properties.py','decode_dependencies.py')},
        validation=dict(historical_full_dictionaries_exact=8,new_default_failure_rows_exact=16,
            qualified_variant_owners=16,support_count_two=8,support_count_three=8,
            focused_checks=len(checks),negative_guards=len(guards),positive_literal_controls=len(positives),
            main_reader_calls=0,live_API_calls=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--zstd', default=str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))))
    parser.add_argument('--baseline',type=Path,default=BASELINE)
    parser.add_argument('--output',type=Path,default=ROOT/'surface-offset-source-variant-decoding.json')
    args = parser.parse_args()
    report = validate(args.zstd,args.baseline)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report['validation'],sort_keys=True))
