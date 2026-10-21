"""Eight saved Offset/source fixtures and bounded grammar/ownership guards."""
import argparse
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_one_face_edge_sources import _replay_recipe
from decode_selection import native_origin_entities
from decode_surface_offset_sources import decode_surface_offset_sources,decode_surface_offset_face_operands
from decode_surface_tools import decode_surface_tool
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
FILES = tuple('surfacetools-856ca50cf4c7/offset_'+n+'.f3d' for n in ('positive','negative','rounded'))+(
    'specialfillets-d50f7a4f04e0/rule_asymmetric.f3d','surfacebounds-ac801bb00fae/untrim_all.f3d',
    'surfacebounds-ac801bb00fae/extend_natural.f3d','patchcontinuity-b9b0be85a281/brep_tangent.f3d',
    'namedbodies-3c7c11fc2924/namedbodies.f3d')


def validate(root,zstd,baseline_path):
    baseline = json.loads(baseline_path.read_text())
    assert baseline['baseline_commit'] == '85a4b51'
    before = {Path(o['file']).relative_to(root).as_posix():o for o in baseline['before']}
    assert set(before) == set(FILES)
    truth_path = root/'surfacetools-856ca50cf4c7/ground_truth.json';truth = json.loads(truth_path.read_text())
    report = dict(interface='decode_surface_offset_sources(data,records,features,member,members,body_identifier_summary,body_selections=None)->associations/unresolved/scope',
        operand_interface='decode_surface_offset_face_operands(recipe)->bounded counted FACE/full-or-simple EDGE grammar with exact complete replay',
        integration=dict(stream='surface_offset_sources',owner_feature_list='surface_offset_sources',owner_field='owner_object_id',
            old_warning_clearances=0,old_tool_changes=0,old_ASM_changes=0),
        scope='Three actual nonzero planar Offset source captures. Counted grammar is bounded and names/typed topology qualify before geometry; future zero-offset API/VBL witness binding is unproved.',
        parser_bounds=dict(maximum_payload_bytes=16384,maximum_boundary_edges=32,observed_payload_bytes=364,
            observed_boundary_edges=4,observed_full_simple_children=[2,2],qualifier_semantics=None),
        baseline=dict(commit='85a4b51',path=str(baseline_path),sha256=hashlib.sha256(baseline_path.read_bytes()).hexdigest()),
        samples=[],guards=[],source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in (
            'decode_surface_offset_sources.py','validate_surface_offset_sources.py','decode_owned_surface_selection.py',
            'decode_face_selections.py','decode_body_selections.py','decode_body_asm_identifiers.py',
            'decode_selection_context_recipes.py','decode_recipe_components.py','decode_one_face_edge_sources.py',
            'decode_untrim_sources.py','decode_asm_recipe_tags.py','decode_asm_subtypes.py','decode_brep.py')})
    loaded = {};payloads=[];origin_count=0
    for archive in FILES:
        data,records,features,member,members = load(root,archive,zstd)
        loaded[archive] = data,records,features,member,members
        stream = before[archive]['streams'][0];ids,selections = stream['body_asm_identifiers'],stream['body_selections']
        original = copy.deepcopy((features,records,ids,selections))
        summary = decode_surface_offset_sources(data,records,features,member,members,ids,selections)
        assert not summary['unresolved'],(archive,summary)
        assert (features,records,ids,selections) == original
        sample = dict(archive=archive,archive_sha256=hashlib.sha256((root/archive).read_bytes()).hexdigest(),
            expected_summary=summary,inputs_unchanged=True)
        if '/offset_' in archive:
            assert len(summary['associations']) == 1
            row = summary['associations'][0]
            assert row['owner_object_id'] == 285 and row['selection_record_object_id'] == 289
            assert row['descriptor_object_id'] == 292 and row['recipe_object_id'] == 295
            assert row['historical_source_owner_object_id'] == 243 and row['native_body_object_id'] == 278
            assert row['body_anchor_object_id'] == 284 and row['mapping_record_object_id'] == 8
            assert row['explicit_asm_body_index'] == 3 and row['native_stored_body_identifier'] == 1
            assert row['result_anchor_object_id'] == 322
            assert all(row[k] is None for k in ('exact_selected_source_identity','API_handle_identity',
                'current_source_identity','persistent_source_identity','qualified_historical_state','traversal',
                'future_zero_offset_VBL_witness_binding'))
            assert row['source_geometry_diagnostics'] == []
            operation = row['operation_operands'];payloads.append(operation['payload_hex'])
            assert len(bytes.fromhex(operation['payload_hex'])) == 364
            assert operation == decode_surface_offset_face_operands(row['recipe'])
            assert operation['stored_direct_face_name_index'] == 0 and operation['stored_boundary_edge_count'] == 4
            assert operation['stored_boundary_name_order'] == [1,3,4,2]
            assert [len(c['endpoint_operands']) for c in operation['boundary_edges']] == [2,0,2,0]
            assert [len(bytes.fromhex(c['payload_hex'])) for c in operation['boundary_edges']] == [156,20,156,20]
            assert _replay_recipe(row['recipe']).hex() == row['full_counted_recipe_payload_hex']
            names = row['naming_correspondence']['name_entries']
            assert [e['candidate_count'] for e in names] == [1]*5
            assert [e['candidates'][0]['owner_kind'] for e in names] == ['face']+['edge']*4
            assert all(e['candidates'][0]['body_graph_membership'] == [3] for e in names)
            assert row['cached_face']['face_record_index'] == 19 and row['cached_face']['surface']['kind'] == 'plane-surface'
            assert len(row['cached_face']['boundary_edges']) == 4
            assert all(b['curve']['kind'] == 'straight-curve' for b in row['cached_face']['boundary_edges'])
            assert row['stored_boundary_order_relation'] == 'NextCoedge'
            assert [e['name_table_index'] for e in row['boundary_incidence']] == [1,3,4,2]
            assert [len(e['endpoint_incidence']) for e in row['boundary_incidence']] == [2,0,2,0]
            assert all([v['stored_edge_endpoint_role'] for v in e['endpoint_incidence']] == ['Start','End'] for e in row['boundary_incidence'] if e['endpoint_incidence'])
            blob = members[row['history_blob_member']];parsed = inspect_asm(blob)
            for origin in row['source_record_origins']:
                record = parsed['records'][origin['record_index']]
                assert origin == dict(record_index=record['index'],kind=record['name'],section=record['section'],
                    record_offset=record['offset'],record_end_offset=record['end_offset'])
            origin_count += len(row['source_record_origins'])
            for entry in row['matched_name_attributes']:
                tag = entry['tag']
                assert bytes.fromhex(tag['payload_hex']) == blob[tag['payload_offset']:tag['payload_end_offset']]
            by = {r.object_id:r for r in records if r.is_primary}
            for origin in row['native_record_origins']:
                r = by[origin['object_id']]
                assert origin == dict(object_id=r.object_id,class_guid=r.class_guid,record_offset=r.start,body_offset=r.body,end_offset=r.end)
            feature = next(f for f in features if f['object_id'] == 285);rec = by[285]
            controls = decode_surface_tool(data,records,data[rec.body:rec.end],feature,native_origin_entities(data,records))
            expected = next(f for f in stream['features'] if f['object_id'] == 285)['tool_settings']
            assert controls == expected
            actual = next(s for s in truth['samples'] if s['file'] == Path(archive).name)
            sample.update(expected_prior_tool_settings=controls,prior_control_dictionary_exact=True,
                API_evidence=dict(ground_truth_sha256=hashlib.sha256(truth_path.read_bytes()).hexdigest(),
                    actual_saved_settings=actual['settings'],actual_saved_parameters=actual['parameters'],
                    source_geometry_getters_captured=False,native_API_handle_assignment=None,
                    scope='Saved singleton/control observations; no independent API FACE/native record or VBL witness binding'))
        else:
            assert summary['associations'] == []
            sample['control_status'] = 'Outside native SurfaceOffset gate; full empty summary'
        report['samples'].append(sample)
    assert len(set(payloads)) == 1

    data,records,features,member,members = loaded[FILES[0]]
    stream = before[FILES[0]]['streams'][0];ids,selections = stream['body_asm_identifiers'],stream['body_selections']
    row = report['samples'][0]['expected_summary']['associations'][0];by = {r.object_id:r for r in records if r.is_primary};rr = by[295]
    def reject(label,changed_data=data,changed_records=records,changed_features=features,changed_ids=ids,changed_members=None,successes=0):
        mm = dict(members) if changed_members is None else dict(changed_members);mm[member] = changed_data
        out = decode_surface_offset_sources(changed_data,changed_records,changed_features,member,mm,changed_ids,selections)
        assert len(out['associations']) == successes and out['unresolved'],(label,out)
        report['guards'].append(dict(label=label,successful_owner_ids=[r['owner_object_id'] for r in out['associations']],diagnostics=out['unresolved']))
    start = rr.end-364
    mutations = (('Outer counted boundary/table mismatch',start+8,struct.pack('<i',5)),
        ('Full child endpoint count outside observed branch',start+32,struct.pack('<i',3)),
        ('Child opaque qualifier corruption',start+164,struct.pack('<i',0)),
        ('Descriptor trailer marker',by[292].body+223,b'\0'),
        ('Proxy source owner backlink',by[289].body+95,struct.pack('<Q',999999)))
    for label,offset,value in mutations:
        raw = bytearray(data);raw[offset:offset+len(value)] = value;reject(label,bytes(raw))
    reject('Duplicate primary descriptor',changed_records=records+[by[292]])
    fake = copy.deepcopy(ids)
    for mapping in fake['decoded']:
        for binding in mapping['bindings']:
            if binding['native_body_object_id'] == 278:binding['asm_body_index'] = 1
    reject('Forged supplied mapped BODY index',changed_ids=fake)
    # Change actual initial FACE generic name only; source coordinates and
    # mapping remain intact, so no geometry or order fallback is admissible.
    blob_member = row['history_blob_member'];parsed = inspect_asm(members[blob_member])
    face = row['naming_correspondence']['name_entries'][0]['candidates'][0]
    tag_record = parsed['records'][face['attribute_record_index']]
    names = [t for t in tag_record['tokens'] if t['kind'] == 'string' and t['value'] == '5']
    assert len(names) == 1 and names[0]['tag'] == 7
    mm = dict(members);raw = bytearray(mm[blob_member]);raw[names[0]['offset']+2] = ord('9');mm[blob_member] = bytes(raw)
    reject('Changed complete FACE tuple has no coordinate fallback',changed_members=mm)
    fakeid = 900000;fr = replace(by[285],object_id=fakeid)
    ff = copy.deepcopy(next(f for f in features if f['object_id'] == 285));ff['object_id'] = fakeid
    reject('Valid first Offset owner then invalid second remains handled',changed_records=records+[fr],changed_features=features+[ff],successes=1)
    # A consistent renumbering proves that operand names are read from counted
    # references instead of hardcoded face0/edge1,3,4,2 positions.
    renamed = copy.deepcopy(row['recipe']);permutation = {0:4,1:2,2:0,3:3,4:1}
    reordered = [None]*5
    for entry in renamed['name_table']:
        entry['table_index'] = permutation[entry['table_index']];reordered[entry['table_index']] = entry
    renamed['name_table'] = reordered;raw = bytearray.fromhex(renamed['payload_hex'])
    offsets = {0}
    for child in row['operation_operands']['boundary_edges']:
        offsets.add(child['relative_offset'])
        if child['stored_face_count']:offsets.add(child['relative_offset']+12)
        for vertex in child['endpoint_operands']:
            offsets.add(vertex['relative_offset']+8)
            offsets.update(e['relative_offset'] for e in vertex['nested_edges'])
    for offset in offsets:
        old = struct.unpack_from('<i',raw,offset)[0];struct.pack_into('<i',raw,offset,permutation[old])
    renamed['payload_hex'] = raw.hex();operation = decode_surface_offset_face_operands(renamed)
    assert operation['stored_direct_face_name_index'] == 4
    assert operation['stored_boundary_name_order'] == [2,3,1,0]
    report['counted_index_control'] = dict(consistent_name_table_permutation=permutation,
        complete_operation_replay=True,hardcoded_FACE_or_EDGE_indices=False,
        scope='Pure grammar control; no synthetic API/VBL source success claimed')
    report['summary'] = dict(focused_archives=8,Offset_owners=3,complete_bounded_face_recipe_replays=3,
        observed_payload_bytes=364,observed_full_edge_children=6,observed_simple_edge_children=6,
        complete_named_operand_matches=15,boundary_edge_incidence_routes=12,endpoint_intersections=12,
        named_attribute_payload_replays=15,source_origin_rows=origin_count,prior_tool_settings_exact=3,
        empty_controls=5,focused_guards=len(report['guards']),counted_name_index_permutation_control=1,
        future_zero_offset_VBL_witness_binding_proven=False,API_geometry_corroboration=False,main_runs=0,live_calls=0)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--zstd-library',required=True)
    p.add_argument('--baseline-cache',type=Path,default=Path('/private/tmp/fusion-surface-offset-source-baseline.json'))
    p.add_argument('--output',type=Path,default=ROOT/'surface-offset-source-decoding.json');args = p.parse_args()
    report = validate(args.root.resolve(),args.zstd_library,args.baseline_cache)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report['summary']))
