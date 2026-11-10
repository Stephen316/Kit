"""Exact counted ASM naming payloads, signed bits and prior dictionaries."""

import argparse
from collections import Counter
import copy
import json
from pathlib import Path

from asm_records import inspect_asm
from decode_counted_asm_names import decode_counted_asm_name
from fusion_archive import read_members

ROOT = Path(__file__).resolve().parent
CIRCULAR = ['circularmodes-45f859c1f1b6/'+name+'.f3d' for name in
            ('body_full', 'body_negative', 'body_suppressed', 'body_symmetric', 'multiple_customaxis')]
RELATED = ['boundaryfills-a0953038318b/new_middle_remove.f3d',
           'boundaryfills-a0953038318b/new_middle.f3d', 'boundaryfills-a0953038318b/new_two.f3d',
           'rectmodes-a069f8f4b8a2/body_one.f3d', 'rectmodes-a069f8f4b8a2/body_multiple_customaxis.f3d',
           'rectmodes-a069f8f4b8a2/feature_optimized.f3d', 'bodymodes-df9b7113539f/mirror_xy.f3d',
           'mirrorfeatures-1ffa1b15c612/body_brep_face_plane.f3d',
           'embosstext-cd769aa41cdf/two_texts.f3d']


def validate(zstd_library):
    golden = json.loads((ROOT / 'asm-recipe-tag-decoding.json').read_text())
    files = sorted(set(CIRCULAR+RELATED+[s['file'] for s in golden['samples']]))
    contexts = {}
    def load(relative):
        if relative not in contexts:
            contexts[relative] = {member: (raw, inspect_asm(raw)) for member, raw in
                                  read_members(ROOT / relative, zstd_library).items() if member.endswith(('.smb', '.smbh'))}
        return contexts[relative]
    report = {'scope': 'Twenty-archive related payload survey plus seven fixed term-count representatives; ownership, topology and coverage remain outside this payload helper',
              'integration': {'function': 'decode_counted_asm_names.decode_counted_asm_name(record)',
                              'returns': 'Existing generic-tag payload keys definition_name,stored_definition_schema_fields,stored_namespace_text,stored_term_count,terms,payload_offset,payload_end_offset,payload_hex.',
                              'term_fields': 'Existing exact name/stored_index/count/int32/uint32/zero-terminator dictionary; no extra semantic ID keys.',
                              'shared_callsite': 'decode_asm_recipe_tags retains typed owner checks, reciprocal attribute chains, initial-geometry scope, other-definition framing, coverage and exact actual-blob replay; substitute only counted definition/schema/namespace/terms parsing.',
                              'validation_command': '/usr/bin/python3 validate_counted_asm_names.py', 'shared_reader_changes_by_this_task': False},
              'grammar': {'definition': 'generic_tag_attrib_def; typed integer schema3,3,-1; literal namespace generic_tag_attrib_def followed by one space.',
                          'term_counts': [1, 2, 3, 4, 5, 6, 8], 'component_counts': [0, 1, 2, 3],
                          'term': 'Typed integer ASCII byte length; bounded printable ASCII name; uint32-range stored index in integer64 token; component count; signed32-range typed integer components; separate typed integer zero terminator.',
                          'replay': 'Exact token4+signed64 integer and token7+u8-length ASCII string bytes; source payload extent checked, then compared byte-for-byte with the stored blob by this validator.'},
              'files_inspected': sorted(set(files+[value[0] for value in INVENTORY['examples'].values()])),
              'inventory_provenance': {'source': 'Parent read-only initial-ASM custom framing inventory; only its fixed representatives are replayed here', 'snapshot': INVENTORY},
              'survey': [], 'representative_payloads': [], 'inventory_term_count_representatives': [], 'boundaryfill_six_faces': [],
              'prior_dictionary_controls': [], 'guards': [],
              'limitations': ['This helper parses payload framing only. It does not validate an attribute owner, reciprocal chain, entity kind, whole-blob coverage or native selection identity.',
                              'Component integers remain literal counted naming fields, with signed and unsigned views of the same32 bits; no numeric component becomes a design-object or topology ID.',
                              'Term count7 and counts beyond8, or component counts beyond0/1/2/3, are unsupported until independently observed and framed.',
                              'Exact typed replay confirms stored bytes for the inspected payloads, not native geometry regeneration or a writer.',
                              'Scope is the explicit directly related survey; unrelated opaque attribute definitions and other unresolved CAD semantics remain unchanged.']}
    totals = Counter(); negative = 0; examples = set(); parsed_records = []
    for relative in files:
        local = Counter(); local_negative = 0
        for member, (raw, parsed) in load(relative).items():
            assert parsed['complete_token_stream']
            for record in parsed['records']:
                t = record['tokens']
                if record['section'] != 'geometry' or record['name'] != 'ATTRIB_CUSTOM-attrib' or len(t) <= 5 or t[5].get('value') != 'generic_tag_attrib_def':
                    continue
                payload = decode_counted_asm_name(record)
                assert bytes.fromhex(payload['payload_hex']) == raw[payload['payload_offset']:payload['payload_end_offset']]
                shape = (payload['stored_term_count'], tuple(term['stored_reference_component_count'] for term in payload['terms']))
                totals[shape] += 1; local[shape] += 1
                parsed_records.append(record)
                for term in payload['terms']:
                    for signed, unsigned in zip(term['stored_reference_components_int32'], term['stored_reference_components_uint32']):
                        assert unsigned == signed & 0xffffffff
                        if signed < 0:
                            negative += 1; local_negative += 1
                            assert unsigned >= 0x80000000
                if shape not in examples:
                    examples.add(shape)
                    report['representative_payloads'].append({'file': relative, 'member': member,
                        'record_index': record['index'], 'owner_record_index_unqualified': t[4]['value'],
                        'payload': payload, 'exact_actual_blob_replay': True})
                if relative == 'boundaryfills-a0953038318b/new_middle_remove.f3d' and member.endswith('.smbh') and record['index'] in (29, 43, 68, 117, 188, 254):
                    assert parsed['records'][t[4]['value']]['name'] == 'face'
                    assert payload['stored_term_count'] == 1 and payload['terms'][0]['stored_reference_component_count'] == 2
                    report['boundaryfill_six_faces'].append({'file': relative, 'member': member,
                        'attribute_record_index': record['index'], 'face_record_index_raw_owner': t[4]['value'],
                        'payload': payload, 'owner_scope': 'Raw owner is typed FACE here; reciprocal owner proof remains the separate owner reader\'s responsibility'})
        report['survey'].append({'file': relative, 'shape_counts': [{'term_count': k[0], 'component_counts_by_term': list(k[1]), 'payload_count': count} for k, count in sorted(local.items())],
                                 'negative_signed32_components_preserved': local_negative})
    for count_text, (relative, member, index) in sorted(INVENTORY['examples'].items(), key=lambda item: int(item[0])):
        raw, parsed = load(relative)[member]
        record = parsed['records'][index]
        payload = decode_counted_asm_name(record)
        assert payload['stored_term_count'] == int(count_text)
        assert bytes.fromhex(payload['payload_hex']) == raw[payload['payload_offset']:payload['payload_end_offset']]
        report['inventory_term_count_representatives'].append({'file': relative, 'member': member,
            'record_index': index, 'observed_term_count': int(count_text), 'payload': payload,
            'exact_actual_blob_replay': True, 'scope': 'Framing representative only; no owner-chain or semantic ID inference'})
    # Historical saved dictionaries are the comparison baseline. Reconstructing
    # with the new payload fields must not add, remove or alter any prior key.
    old_payloads = 0
    for sample in golden['samples']:
        previous = sample['expected_tag_catalog']
        member = sample['expected_pipe_evidence']['history_blob_member']
        raw, parsed = load(sample['file'])[member]
        for tag in previous['tags']:
            record = parsed['records'][tag['attribute_record_index']]
            current = decode_counted_asm_name(record)
            assert {**tag, **current} == tag
            assert current == {key: tag[key] for key in current}
            assert bytes.fromhex(current['payload_hex']) == raw[current['payload_offset']:current['payload_end_offset']]
            old_payloads += 1
        report['prior_dictionary_controls'].append({'file': sample['file'], 'member': member,
                                                   'prior_exact_tag_dictionaries_preserved': len(previous['tags'])})
    assert len(report['boundaryfill_six_faces']) == 6
    assert {(1, (i,)) for i in range(4)}.issubset(totals)
    assert (8, (0,)*8) in totals and any(k[0] == 2 for k in totals) and negative
    base = next(record for record in parsed_records if decode_counted_asm_name(record)['terms'][0]['stored_reference_component_count'] == 3)
    def reject(label, mutate):
        changed = copy.deepcopy(base); mutate(changed['tokens'])
        try:
            decode_counted_asm_name(changed)
        except (ValueError, IndexError) as error:
            report['guards'].append({'case': label, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError('Malformed counted naming payload accepted: '+label)
    reject('Explicit ASCII byte length disagrees', lambda t: t[11].update(value=t[11]['value']+1))
    reject('Component exceeds signed32 range', lambda t: t[15].update(value=0x80000000))
    reject('Term count must be positive and observed', lambda t: t[10].update(value=0))
    reject('Unobserved term count7 remains rejected', lambda t: t[10].update(value=7))
    reject('Unobserved oversized component count', lambda t: t[14].update(value=65536))
    reject('Separate component terminator must be zero', lambda t: t[18].update(value=1))
    reject('Unconsumed payload token', lambda t: t.append({'kind': 'integer', 'tag': 4, 'value': 0, 'offset': t[-1]['offset']+9}))
    report['summary'] = {'saved_archives': len(report['files_inspected']), 'related_survey_archives': len(files),
                         'additional_count_representatives_replayed': len(report['inventory_term_count_representatives']),
                         'generic_payloads_replayed': sum(totals.values()),
                         'component_count0_terms': sum(k[1].count(0)*v for k, v in totals.items()),
                         'component_count1_terms': sum(k[1].count(1)*v for k, v in totals.items()),
                         'component_count2_terms': sum(k[1].count(2)*v for k, v in totals.items()),
                         'component_count3_terms': sum(k[1].count(3)*v for k, v in totals.items()),
                         'negative_signed_components_bit_preserved': negative,
                         'actual_eight_term_payloads': sum(v for k, v in totals.items() if k[0] == 8),
                         'old_dictionary_payloads_preserved': old_payloads,
                         'boundaryfill_count2_face_payloads': len(report['boundaryfill_six_faces']),
                         'malformed_guards': len(report['guards'])}
    return report


INVENTORY = {'archives': 559,
 'blobs': 959,
 'component_counts': {'0': 1101, '1': 8108, '2': 830, '3': 1954},
 'definitions': {'FDM_feature_attrib_def': 19,
                 'FPM_tracked_attrib_def': 84,
                 'Timestamp_attrib_def': 1053,
                 'generic_tag_attrib_def': 11463,
                 'sketch_attrib_def': 17175},
 'elapsed': 4.986826167,
 'examples': {'1': ['analytic-86a12b291d0a/analytic.f3d',
                    'FusionAssetName[Active]/Breps.BlobParts/BREP.66dea2e4-f2cf-4d43-8c2d-62117e12e1a6.smbh',
                    10],
              '2': ['bodymodes-d696a14d5f0b/mirror_xy_combine.f3d',
                    'FusionAssetName[Active]/Breps.BlobParts/BREP.c6c36581-0df2-4557-8c90-230ed6d810fb.smbh',
                    11],
              '3': ['embossmodes-e40cc931d978/multiple_profiles.f3d',
                    'FusionAssetName[Active]/Breps.BlobParts/BREP.815e6a98-deb3-4882-984d-e2cd220d4b43.smbh',
                    4],
              '4': ['embosstext-cd769aa41cdf/text_emboss.f3d',
                    'FusionAssetName[Active]/Breps.BlobParts/BREP.96d67556-0ea0-4cdc-8805-fe58c0c194a6.smbh',
                    4],
              '5': ['embosstext-cd769aa41cdf/mixed_text_profile.f3d',
                    'FusionAssetName[Active]/Breps.BlobParts/BREP.455a830f-efa1-49f8-b65f-011cdc432290.smbh',
                    4],
              '6': ['solidsweeps-7d2677669e3d/solid_aligned.f3d',
                    'FusionAssetName[Active]/Breps.BlobParts/BREP.2851a5f0-aeff-450e-b46f-7c589764658c.smbh',
                    304],
              '8': ['embosstext-cd769aa41cdf/two_texts.f3d',
                    'FusionAssetName[Active]/Breps.BlobParts/BREP.c1988ba3-752f-42d2-babe-839d8495e61c.smbh',
                    4]},
 'term_counts': {'1': 11031, '2': 364, '3': 49, '4': 13, '5': 3, '6': 2, '8': 1},
 'unframed': []}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='counted-asm-name-decoding.json')
    args = parser.parse_args()
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report = validate(str(zstd))
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
