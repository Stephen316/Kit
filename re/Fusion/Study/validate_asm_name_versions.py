"""Focused literal name-version evidence in seven saved Extend archives."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_asm_history import decode_asm_history
from decode_asm_name_versions import decode_asm_name_versions, SCOPE
from decode_asm_recipe_tags import decode_asm_generic_tags
from decode_brep import decode_topology
from decode_fpm_tracking import decode_fpm_attributes
from fusion_archive import read_members

ROOT = Path(__file__).resolve().parent
POSITIVES = tuple('surfacebounds-ac801bb00fae/extend_'+v+'.f3d' for v in
    ('natural', 'tangent', 'perpendicular', 'perpendicular_negative', 'aligned', 'two_edges')) + (
    'surfacebounds-8804bbf80755/extend_no_chain.f3d',)
CONTROLS = ('surfacebounds-ac801bb00fae/ruled_tangent.f3d',
    'surfacebounds-ac801bb00fae/untrim_manual.f3d',
    'patchcontinuity-b9b0be85a281/brep_tangent.f3d',
    'namedbodies-3c7c11fc2924/namedbodies.f3d')
FILES = POSITIVES + CONTROLS
UNTRIM = 'surfacebounds-ac801bb00fae/untrim_manual.f3d'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(zstd):
    checks, guards, samples = [], [], []
    fixture = nested_fixture = None
    pairs = states = 0
    contrasts = {}

    def check(label, value):
        if not value:
            raise AssertionError(label)
        checks.append(label)

    for filename in FILES:
        path = ROOT/filename
        positive = filename in POSITIVES or filename == UNTRIM
        actual = None
        if positive:
            truth_path = path.parent/'ground_truth.json'
            truth = json.loads(truth_path.read_text())
            source = next(s for s in truth['samples'] if s['file'] == path.name)
            actual = dict(source=str(truth_path.relative_to(ROOT)), source_sha256=sha(truth_path),
                saved_API_settings=source.get('settings'), saved_kind=source.get('kind'),
                scope='Existing actual getters corroborate the saved modeling scenario only; API naming tuples, journal sides and historical source identity were not captured')
        archive_pairs = 0
        for member, blob in read_members(path, zstd).items():
            if not member.endswith(('.smb', '.smbh')):
                continue
            parsed = inspect_asm(blob)
            before = copy.deepcopy(parsed)
            topology_before = decode_topology(parsed)
            tags_before = decode_asm_generic_tags(blob, parsed, allow_fpm_tracking=True)
            result = decode_asm_name_versions(blob, parsed=parsed)
            check(filename+' '+member+' parsed copy unchanged', parsed == before)
            check(filename+' '+member+' initial naming and topology unchanged',
                tags_before == decode_asm_generic_tags(blob, parsed, allow_fpm_tracking=True)
                and topology_before == decode_topology(parsed))
            check(filename+' '+member+' no unqualified positive family errors',
                not result['unresolved'] if positive else not result['decoded'])
            evidence = []
            for row in result['decoded']:
                archive_pairs += 1; pairs += 1
                history = decode_asm_history(blob, parsed=parsed)
                expected_chain = [0, 2, 4, 3, 1] if filename == UNTRIM else [0, 2, 4, 5, 3, 1]
                check(filename+' exact complete literal history',
                    result['journal_history'] == history and history['neighbor_chain'] == expected_chain)
                states += len(history['journal_states'])
                table = history['geometry_entities']
                initial, trailing = row['initial_attribute'], row['trailing_attribute']
                face = parsed['records'][row['owner_face_record_index']]
                owner = row['owner_face_geometry_entity_ordinal']
                check(filename+' typed same FACE owner and initial head', face['name'] == 'face'
                    and table[owner]['inspection_record_index'] == face['index']
                    and face['tokens'][0]['value'] == initial['geometry_entity_ordinal']
                    and initial['owner_geometry_entity_ordinal'] == trailing['owner_geometry_entity_ordinal'] == owner)
                expected_initial = [('3', 0, [301])] if filename == UNTRIM else [('5', 0, [301, -302])]
                expected_trailing = [('3', 0, [301])] if filename == UNTRIM else [('5', 0, [301])]
                check(filename+' exact complete literal tuples',
                    [(t['name'], t['stored_index'], t['stored_reference_components_int32']) for t in initial['terms']]
                    == expected_initial and [(t['name'], t['stored_index'], t['stored_reference_components_int32']) for t in trailing['terms']]
                    == expected_trailing)
                if filename == UNTRIM:
                    child = initial['validated_nested_metadata']
                    check(filename+' existing nested empty-name metadata owns initial parent',
                        child['record_index'] == 26 and child['stored_header_fields'] == [-1, -1, -1, -1, initial['geometry_entity_ordinal']]
                        and child['terms'][0]['name'] == '' and child['terms'][0]['stored_reference_component_count'] == 1
                        and child['existing_initial_catalog_proof']['parent_topology_owner_record_index'] == face['index'])
                    check(filename+' nested complete raw payload replay', child['exact_full_payload_replay']
                        and blob[child['full_payload_offset']:child['full_payload_end_offset']].hex() == child['full_payload_hex'])
                    nested_fixture = blob, parsed, row
                for attr in (initial, trailing):
                    check(filename+' '+attr['section']+' complete attribute byte replay',
                        blob[attr['full_payload_offset']:attr['full_payload_end_offset']].hex() == attr['full_payload_hex']
                        and attr['exact_full_payload_replay'])
                pair = row['journal_pair']
                journal = history['journal_states'][pair['delta_state_slot']]
                check(filename+' exact stored pointer pair and ordinal namespaces',
                    journal['entries'][pair['entry_ordinal']] == {k:v for k,v in pair.items() if k != 'delta_state_slot'}
                    and pair['pointer_sides'][0]['stored_geometry_entity_ordinal'] == trailing['geometry_entity_ordinal']
                    and pair['pointer_sides'][1]['stored_geometry_entity_ordinal'] == initial['geometry_entity_ordinal'])
                for side in pair['pointer_sides']:
                    off = side['token_offset']
                    check(filename+' raw journal pointer at'+str(off), blob[off] == 12
                        and struct.unpack_from('<q', blob, off+1)[0] == side['stored_geometry_entity_ordinal'])
                graph = [g for g in topology_before['body_graphs'] if face['index'] in g['face_indices']]
                check(filename+' initial typed BODY membership independent of naming version',
                    len(graph) == 1 and graph[0]['body_index'] == row['initial_body_record_index']
                    and row['initial_face_body_graph_membership'] == [graph[0]['body_index']])
                body_pair = row['paired_body_version']
                check(filename+' BODY stored identifiers remain literal non-identity evidence',
                    body_pair['initial_record_index'] == row['initial_body_record_index']
                    and body_pair['initial_stored_entity_id'] == row['initial_body_stored_entity_id']
                    and body_pair['stored_ids_equal'] == (body_pair['initial_stored_entity_id'] == body_pair['trailing_stored_entity_id'])
                    and body_pair['identity_upgrade'] is False)
                check(filename+' no state or native FPM identity promoted',
                    row['canonical_tag_catalog_unchanged'] and row['materialized_state'] is None
                    and row['chronological_state'] is None and row['persistent_face_identity'] is None
                    and row['native_FPM_descriptor_bridge'] is None)
                fpm = decode_fpm_attributes(blob, parsed=parsed)
                check(filename+' existing unqualified FPM evidence stays separate',
                    not fpm['attributes'] and (not fpm['unresolved'] if filename == UNTRIM else
                    bool(fpm['unresolved']) and all(e['reason'] == 'FPM attribute absent from claimed owner chain' for e in fpm['unresolved'])))
                evidence.append(dict(initial_attribute_head_record_index=initial['record_index'],
                    trailing_attribute_record_index=trailing['record_index'],
                    face_owner_record_index=face['index'], initial_and_trailing_body_stored_identifiers=[
                        body_pair['initial_stored_entity_id'], body_pair['trailing_stored_entity_id']],
                    independent_existing_FPM_summary=fpm))
                contrasts[filename] = [body_pair['initial_stored_entity_id'], body_pair['trailing_stored_entity_id']]
                if fixture is None:
                    fixture = blob, parsed, row
            if not result['decoded'] and not result['unresolved']:
                check(filename+' '+member+' no candidate means no literal history publication', result['journal_history'] is None)
            samples.append(dict(archive=filename, archive_sha256=sha(path), member=member,
                blob_sha256=hashlib.sha256(blob).hexdigest(), expected_summary=result,
                initial_naming_and_topology_unchanged=True, independent_evidence=evidence,
                saved_API_context=actual))
        check(filename+' exactly expected targeted pair count', archive_pairs == int(positive))

    check('Seven Extend plus neutral Untrim provenance and literal BODY identifier controls', pairs == 8
        and contrasts[POSITIVES[0]] == [1, 1] and contrasts[POSITIVES[5]] == [2, 2])
    blob, parsed, row = fixture
    initial = parsed['records'][row['initial_attribute']['record_index']]
    trailing = parsed['records'][row['trailing_attribute']['record_index']]
    owner = parsed['records'][row['owner_face_record_index']]

    def guard(label, mutate):
        raw = bytearray(blob)
        mutate(raw)
        try:
            answer = decode_asm_name_versions(bytes(raw))
        except (ValueError, KeyError, IndexError, TypeError, struct.error) as error:
            reason = str(error)
        else:
            check(label+' no false version association', not answer['decoded'])
            reason = '; '.join(r['reason'] for r in answer['unresolved']) or 'No qualifying literal FACE version pair'
        guards.append(dict(guard=label, rejected=True, reason=reason))

    def field(raw, token, value):
        struct.pack_into('<q', raw, token['offset']+1, value)

    guard('Reject changed trailing FACE owner', lambda raw:field(raw, trailing['tokens'][4], 3))
    guard('Reject nonpointer trailing owner kind', lambda raw:raw.__setitem__(trailing['tokens'][4]['offset'], 4))
    guard('Reject absent initial FACE attribute head', lambda raw:field(raw, owner['tokens'][0], -1))
    guard('Reject nonnull trailing previous attribute', lambda raw:field(raw, trailing['tokens'][3], initial['index']))
    guard('Reject changed trailing complete component tuple', lambda raw:field(raw, trailing['tokens'][-2], 999))
    guard('Reject unsupported trailing component count', lambda raw:field(raw, trailing['tokens'][14], 4))
    def duplicate_pair(raw):
        pair = row['journal_pair']
        history = decode_asm_history(blob, parsed=parsed)
        state = parsed['records'][history['journal_states'][0]['inspection_record_index']]
        first = 12+3*pair['entry_ordinal']
        start = state['tokens'][first]['offset'];end = state['tokens'][first+3]['offset']
        raw[state['tokens'][-3]['offset']:state['tokens'][-3]['offset']] = blob[start:end]
    guard('Reject duplicate whole journal FACE version pair', duplicate_pair)
    bp = row['paired_body_version']['journal_pair']['pointer_sides'][0]
    guard('Reject BODY pair target with FACE kind', lambda raw:struct.pack_into('<q', raw, bp['token_offset']+1, row['owner_face_geometry_entity_ordinal']))
    stale = copy.deepcopy(parsed);stale['records'][initial['index']]['tokens'][4]['value'] = 3
    try:
        decode_asm_name_versions(blob, parsed=stale)
    except ValueError as error:
        guards.append(dict(guard='Reject stale supplied parsed record owner', rejected=True, reason=str(error)))
    else:
        raise AssertionError('Stale supplied parsed owner was admitted')
    original_fixture = blob, parsed, row
    blob, parsed, row = nested_fixture
    nested = row['initial_attribute']['validated_nested_metadata']
    child = parsed['records'][nested['record_index']]
    guard('Reject initial nested metadata child with wrong parent backlink',
        lambda raw:field(raw, child['tokens'][4], row['owner_face_geometry_entity_ordinal']))
    guard('Reject nonpositive initial empty-name metadata component',
        lambda raw:field(raw, child['tokens'][-2], 0))
    blob, parsed, row = original_fixture
    return dict(scope=SCOPE, files=list(FILES), samples=samples,
        validation=dict(saved_archives=len(FILES), Extend_positive_archives=len(POSITIVES),
            additional_neutral_Untrim_provenance_archives=1, no_provenance_control_archives=len(CONTROLS)-1,
            ASM_members=len(samples), literal_FACE_version_pairs=pairs,
            retained_literal_journal_states=states, focused_checks=len(checks), malformed_guards=len(guards),
            main_reader_calls=0, live_API_calls=0, materialized_states=0),
        checks=checks, malformed_guards=guards, paired_BODY_identifier_controls=contrasts,
        integration=dict(callable='decode_asm_name_versions(blob, *, parsed=None)',
            result='decoded/unresolved/scope + journal_history; canonical initial tags never modified',
            golden='samples[].archive/member/expected_summary contains the full independent helper output',
            caller_requirement='Exact complete trailing_attribute.terms query must be unique and initial_body_record_index must independently match the native same-asset BODY mapping; paired trailing BODY is not substituted'),
        source_sha256={p:sha(ROOT/p) for p in ('decode_asm_name_versions.py','validate_asm_name_versions.py',
            'decode_asm_history.py','decode_asm_recipe_tags.py','decode_counted_asm_names.py','decode_brep.py')},
        limitations=['Only unique literal slot0 FACE pairs with complete initial owner/head proof are qualified; canonical history parsing validates every retained state and neighbor link',
            'Extend uses singleton headers and two/one component tuples; the additional Untrim family requires existing validated initial nested empty-name metadata and identical complete FACE tuples',
            'Journal side labels and initial/trailing sections are literal; no chronological or pre-feature state is selected',
            'Natural stores BODY identifiers1/1 while TwoEdges stores2/2; equal identifiers still do not establish a native BODY identity upgrade',
            'FPM owner-chain failures remain independent; positive numeric literals are not typed native descriptor references',
            'Actual API getters corroborate the saved Extend scenarios, not internal naming tuples or API/native source identity',
            'This helper does not mutate tags, materialize geometry, change tool settings or clear existing diagnostics'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library');parser.add_argument('--output',default='asm-name-version-decoding.json');args=parser.parse_args()
    zstd=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd);Path(args.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['validation'],sort_keys=True))


if __name__ == '__main__':
    main()
