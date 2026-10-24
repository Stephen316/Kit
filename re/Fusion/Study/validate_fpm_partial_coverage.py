"""Saved BODY-owned FPM correspondence and partial-coverage guards."""
import argparse
import copy
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags
from decode_basics import decode_basics
from decode_fpm_partial_coverage import decode_fpm_partial_coverage
from decode_fpm_tracking import decode_fpm_selection_tracking, encode_fpm_attribute
from fusion_archive import read_members
from fusion_metadata import design_records


def validate(root, zstd):
    checks, samples, guards = 0, [], []
    files = sorted(root.joinpath('boundaryfills-a0953038318b').glob('*.f3d')) + [
        root/'edgemodes-87edbf67527b/chamfer_angle.f3d',
        root/'edgemodes-87edbf67527b/fillet_multiple.f3d',
        root/'pipeedgecontrasts-5bd287323ae7/circle_full.f3d']
    saved = None
    associations = 0

    def check(test, reason):
        nonlocal checks
        if not test:
            raise AssertionError(reason)
        checks += 1

    for filename in files:
        members = read_members(filename, zstd)
        main = decode_basics(filename, zstd)
        truth = json.loads(filename.parent.joinpath('ground_truth.json').read_text())
        actual = next(s for s in truth['samples'] if s['file'] == filename.name)
        for stream in main['streams']:
            member = stream['member']
            data = members[member]
            records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
            mapping = stream['body_asm_identifiers']
            original_mapping = copy.deepcopy(mapping)
            before = decode_fpm_selection_tracking(data, records, stream['features'], member, members, mapping, stream['body_selections'])
            output = decode_fpm_partial_coverage(data, records, member, members, mapping)
            after = decode_fpm_selection_tracking(data, records, stream['features'], member, members, mapping, stream['body_selections'])
            check(before == after and mapping == original_mapping, 'existing trailing-edge reader and supplied mapping unchanged')
            check(not output['unresolved'], 'new helper has no framing/association failures on saved supported/empty fixtures')
            row = {'file': str(filename.relative_to(root)), 'member': member, 'expected_summary': output,
                   'legacy_FPM_tracking_literals': [t['stored_tracking_literal'] for t in before['tracks']],
                   'legacy_FPM_unresolved_retained': before['unresolved']}
            if filename.name != 'new_middle_remove.f3d':
                check(output['associations'] == [] and output['coverage'] == [], 'non-BODY-FPM fixtures do not acquire associations')
            else:
                check([a['stored_tracking_literal'] for a in output['associations']] == [391, 402], 'both actual BODY-owned literals recovered')
                check([a['native_body_object_id'] for a in output['associations']] == [275, 354], 'explicit mapped native tool identities recovered')
                check(actual['is_remove_tools'] is True, 'saved API remove-tools getter independently confirms enabled parent action')
                check(len(actual['tool_names']) == 2, 'saved API records two source tool names')
                coverage, = output['coverage']
                check(coverage['initial_BODY_record_indices'] == [1,2,3] and coverage['initial_BODY_naming_complete'], 'all three mapped initial BODY roots have complete scoped naming')
                check(coverage['global_generic_tag_coverage_complete'], 'shared counted-name follow-up now frames the complete initial generic namespace')
                check(coverage['remaining_other_kind_generic_tag_failures'] == [], 'no obsolete FACE framing failures retained after their typed grammar recovery')
                props = {b['object_id']: b for b in stream['body_properties']['bodies']}
                for assoc in output['associations']:
                    attr = assoc['FPM_attribute']
                    check(encode_fpm_attribute(attr).hex() == attr['payload_hex'], 'full original FPM payload byte replay exact')
                    check(assoc['native_body_object_id'] != attr['owner_body_record_index'], 'native BODY ID is separate from ASM record index')
                    check(assoc['same_asset_mapping']['stored_native_handle'] != attr['owner_body_record_index'], 'stored handle does not use an ordinal identity fallback')
                    check(assoc['literal_is_serialized_native_reference'] is False and assoc['exact_selected_source_identity'] is None
                          and assoc['qualified_historical_state'] is None and assoc['source_curve_geometry'] is None,
                          'literal/reference, exact selection, history and curve geometry claims remain separate')
                    check(props[assoc['native_body_object_id']]['name'] in actual['tool_names'], 'independently mapped source BODY stored name matches actual API tool list')
                    check(assoc['owned_removal_action']['parent_boundary_fill_object_id'] == 359,
                          'native removal parent backlink agrees with actual BoundaryFill owner')
                # Independently check the six formerly rejected FACE payloads.
                # Framing does not itself establish their source/result meaning.
                blob_member = output['associations'][0]['same_asset_mapping']['history_blob_member']
                parsed = inspect_asm(members[blob_member])
                current_tags = decode_asm_generic_tags(members[blob_member], parsed, allow_fpm_tracking=True)
                check(not current_tags['unresolved'], 'shared naming reader validates all current initial attributes')
                faces = {t['attribute_record_index']: t for t in current_tags['tags'] if t['owner_kind'] == 'face'}
                framing = []
                for identity in (29,43,68,117,188,254):
                    rec = parsed['records'][identity]
                    check(identity in faces, 'formerly rejected attribute now has an independently typed FACE owner')
                    ts, cursor, terms = rec['tokens'], 11, []
                    for _ in range(ts[10]['value']):
                        size, name, index, count = [t['value'] for t in ts[cursor:cursor+4]]
                        components = [t['value'] for t in ts[cursor+4:cursor+4+count]]
                        check(len(name.encode('ascii')) == size and count == 2 and ts[cursor+4+count]['value'] == 0,
                              'diagnostic face tuple is length/count/terminator framed')
                        terms.append({'name': name, 'stored_index': index, 'component_count': count, 'components': components})
                        cursor += 5+count
                    check(cursor == len(ts) == 18, 'diagnostic face tuple consumes all 18 fields')
                    framing.append({'attribute_record_index': rec['index'], 'owner_record_index': ts[4]['value'],
                                    'owner_kind': 'face', 'term_count': ts[10]['value'], 'terms': terms,
                                    'status': 'Complete production counted-name framing and FACE ownership; source/result semantic correspondence is validated separately'})
                row['counted_FACE_naming_followup'] = framing
                row['actual_API_controls'] = {'is_remove_tools': actual['is_remove_tools'], 'tool_names': actual['tool_names'],
                    'scope': 'Independent saved getters corroborate parent mode/source names only; no API tracking literal or persistent body identity getter.'}
                saved = data, records, member, members, mapping, output
            associations += len(output['associations'])
            samples.append(row)
    data, records, member, members, mapping, output = saved
    blob_member = output['associations'][0]['same_asset_mapping']['history_blob_member']
    blob = members[blob_member]
    parsed = inspect_asm(blob)

    def check_failure(label, changed_members=None, changed_data=None, changed_mapping=None, expected_literals=()):
        result = decode_fpm_partial_coverage(data if changed_data is None else changed_data, records, member,
            members if changed_members is None else changed_members, mapping if changed_mapping is None else changed_mapping)
        check([a['stored_tracking_literal'] for a in result['associations']] == list(expected_literals) and bool(result['unresolved']), label)
        guards.append({'guard': label, 'retained_unaffected_literals': list(expected_literals), 'unresolved': result['unresolved']})

    def mutated_blob(token, value):
        changed = bytearray(blob)
        struct.pack_into('<q', changed, token['offset']+1, value)
        return dict(members, **{blob_member: bytes(changed)})

    a4, a6 = parsed['records'][4], parsed['records'][6]
    check_failure('Duplicate literal cannot establish numeric uniqueness', changed_members=mutated_blob(a4['tokens'][7], 402))
    check_failure('BODY attribute owner no longer reciprocal', changed_members=mutated_blob(a4['tokens'][4], 3))
    # Full naming disagreement remains blocked even though literal 391 still
    # matches the native descriptor and all typed native body chains remain.
    tag = parsed['records'][16]
    changed = bytearray(blob)
    name_token = tag['tokens'][12]
    check(name_token['value'] == '301', 'target body naming mutation uses an actual stored string')
    changed[name_token['offset']+2:name_token['offset']+5] = b'999'
    check_failure('Independent BODY naming disagrees despite unchanged literal and native references',
                  changed_members=dict(members, **{blob_member: bytes(changed)}), expected_literals=(402,))
    check_failure('Unparsed BODY naming prevents kind-complete scope', changed_members=mutated_blob(tag['tokens'][6], 2))
    changed_mapping = copy.deepcopy(mapping)
    changed_mapping['decoded'][0]['history_blob_member'] = 'OtherAsset/Breps.BlobParts/BREP.fake.smbh'
    check_failure('Cross-asset history mapping rejected', changed_mapping=changed_mapping)
    primary = {r.object_id:r for r in records if r.is_primary}
    anchor = primary[281]
    changed_data = bytearray(data)
    struct.pack_into('<Q', changed_data, anchor.body+81, 354)
    changed_members = dict(members, **{member:bytes(changed_data)})
    check_failure('Native anchor BODY disagrees with independent ASM handle mapping', changed_data=bytes(changed_data),
                  changed_members=changed_members, expected_literals=(402,))
    return {'stage': 'Initial BODY-owned FPM coverage and independently corroborated removal provenance',
        'interface': 'decode_fpm_partial_coverage(data, records, member, members, body_identifier_summary) -> associations/coverage/unresolved/scope',
        'integration': 'Add separate late summary after body identifier/direct-body decoding. Each success carries attribute_record_index and mapping_record_object_id. Preserve old trailing-edge tracks. The old mapping-level Incomplete FPM attribute coverage diagnostic can be replaced only when every rejected FPM attribute ID appears in successful associations here; retain any new unresolved records and all global generic-tag or exact-source failures.',
        'validation': {'checks': checks, 'saved_files': len(files), 'saved_streams': len(samples),
                       'new_BODY_attribute_associations': associations, 'complete_BODY_kind_namespaces': 1,
                       'global_FACE_naming_failures_retained': 0, 'newly_framed_other_FACE_tags': 6, 'malformed_guards': guards, 'new_API_calls': 0},
        'findings': ['The two rejected attributes are initial BODY-owned FPM records, not malformed trailing EDGE records. Their reciprocal owner chains and full payload bytes are valid.',
            'Positive literals 391/402 correspond to actual RemoveBody descriptors only after independent native anchor/BODY, explicit same-asset stored handle, parent BoundaryFill ownership and complete BODY-kind naming tuples all agree.',
            'Three initial typed BODY roots have exactly one validated BODY naming tag each. Every initial custom attribute has a bounded typed owner; the shared follow-up reader also frames the six previously rejected FACE tuples and BODY-owned FPM literals.',
            'Those six FACE layouts each contain one term with two counted components and a zero terminator. Framing/ownership completeness does not itself assign source/result component semantics.',
            'The naming mismatch guard changes 301 to 999 while preserving literal 391 and all native reference chains; that association is rejected while the unaffected 402 association survives.'],
        'limitations': ['FPM literals remain stored integers, not serialized typed references. The independent native BODY association does not promote an exact selected-source or persistent ASM identity.',
            'Only initial BODY-owned FPM attributes attached to validated BoundaryFill-owned removal actions are admitted. Trailing EDGE provenance remains the existing reader responsibility.',
            'Generic FACE framing now succeeds, while source/result semantics require separate typed correspondence evidence. History direction/current state and actual tool removal lifecycle remain unresolved. Actual API source names and remove-tools flags corroborate scope only.'],
        'samples': samples}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    p.add_argument('--zstd-library', type=Path, required=True)
    p.add_argument('--report', type=Path)
    args = p.parse_args()
    report = validate(args.root, args.zstd_library)
    (args.report or args.root/'fpm-partial-coverage-decoding.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['validation'],indent=2))
