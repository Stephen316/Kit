"""Thirteen-file Extend alternate-cache source proof with focused guards."""
import argparse
import copy
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_extend_cache_sources import decode_extend_cache_sources
from decode_extend_edge_sources import decode_extend_edge_sources
from decode_one_face_edge_sources import _replay_recipe
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
FILES = tuple('surfacebounds-ac801bb00fae/'+n+'.f3d' for n in (
    'extend_natural','extend_tangent','extend_perpendicular','extend_perpendicular_negative','extend_aligned','extend_two_edges'))+(
    'surfacebounds-8804bbf80755/extend_no_chain.f3d','surfacebounds-ac801bb00fae/untrim_manual.f3d',
    'surfacebounds-ac801bb00fae/untrim_internal.f3d','surfacebounds-ac801bb00fae/ruled_tangent.f3d',
    'patchcontinuity-b9b0be85a281/brep_tangent.f3d','namedbodies-3c7c11fc2924/namedbodies.f3d',
    'edgemodes-52695761f185/fillet_curvature.f3d')


def validate(root,zstd,baseline_path):
    baseline = json.loads(baseline_path.read_text())
    assert baseline['baseline_commit'] == '4c20419'
    before = {Path(o['file']).relative_to(root).as_posix():o for o in baseline['before']}
    assert set(before) == set(FILES)
    report = dict(interface='decode_extend_cache_sources(data,records,features,member,members,body_identifier_summary,body_selections=None)->associations/unresolved/scope',
        integration=dict(stream='extend_cache_sources',owner_feature_list='extend_cache_sources',owner_field='owner_object_id',
            operand_list='descriptor_operands',provenance_field='alternate_cache_provenance',old_warning_clearances=0,old_initial_source_replacements=0),
        scope='New literal alternate-cache operand correspondence supplementing preserved initial rows; no chronology, pre-feature/current/persistent/API source or traversal claim',
        baseline=dict(commit='4c20419',path=str(baseline_path),sha256=hashlib.sha256(baseline_path.read_bytes()).hexdigest()),
        samples=[],malformed_guards=[],source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in (
            'decode_extend_cache_sources.py','validate_extend_cache_sources.py','materialize_extend_cache.py',
            'materialize_asm_literal_view.py','decode_extend_edge_sources.py','decode_untrim_sources.py',
            'decode_asm_name_versions.py','decode_one_face_edge_sources.py','decode_asm_recipe_tags.py','decode_brep.py')})
    loaded = {};operand_count = 0;origin_count = 0;initial_reversed = 0
    for archive in FILES:
        data,records,features,member,members = load(root,archive,zstd)
        loaded[archive] = data,records,features,member,members
        stream = before[archive]['streams'][0];ids,selections = stream['body_asm_identifiers'],stream['body_selections']
        saved = copy.deepcopy((features,ids,selections))
        summary = decode_extend_cache_sources(data,records,features,member,members,ids,selections)
        assert not summary['unresolved'],(archive,summary)
        assert (features,ids,selections) == saved
        prior = decode_extend_edge_sources(data,records,features,member,members,ids,selections)
        if 'extend_edge_sources' in stream: assert prior == stream['extend_edge_sources'],archive
        else: assert not prior['associations'] and not prior['unresolved']
        sample = dict(archive=archive,archive_sha256=hashlib.sha256((root/archive).read_bytes()).hexdigest(),
            expected_summary=summary,expected_prior_extend_edge_sources=prior,prior_initial_sources_exact=True,
            input_features_and_contexts_unchanged=True)
        if '/extend_' in archive:
            assert len(summary['associations']) == 1
            row = summary['associations'][0];oldrow = prior['associations'][0]
            assert row['owner_object_id'] == 285 and row['native_body_object_id'] == 278
            assert row['body_anchor_object_id'] == 284 and row['historical_source_owner_object_id'] == 243
            assert row['explicit_initial_asm_body_index'] == 3
            assert all(row[k] is None for k in ('exact_selected_source_identity','current_source_identity',
                'persistent_source_identity','API_handle_identity','qualified_historical_state','traversal'))
            provenance = row['alternate_cache_provenance']
            assert provenance['qualified_body_view_record_index'] == row['qualified_body_view_record_index']
            assert provenance['stored_body_identifier'] == row['native_stored_body_identifier'] == (2 if 'two_edges' in archive else 1)
            assert len(provenance['canonical_history']['journal_states']) == 6
            assert provenance['qualified_dangling_pointer_count'] == 0
            assert provenance['current_state'] is None and provenance['geometry_before_feature'] is None
            assert provenance['native_historical_BODY_identity'] is None
            pairs = row['descriptor_operands'];assert len(pairs) == (2 if 'two_edges' in archive else 1)
            assert len({p['descriptor_object_id'] for p in pairs}) == len(pairs)
            assert len({p['cached_operand']['edge']['index'] for p in pairs}) == len(pairs)
            contrast = []
            for operand,old in zip(pairs,oldrow['descriptor_operands']):
                operand_count += 1
                assert operand['descriptor_object_id'] == old['descriptor_object_id']
                assert operand['selection_record_object_id'] == old['selection_record_object_id']
                assert operand['recipe'] == old['recipe'] and operand['operation_operands'] == old['operation_operands']
                assert _replay_recipe(operand['recipe']).hex() == operand['full_counted_recipe_payload_hex']
                entries = operand['alternate_naming_correspondence']['name_entries']
                assert [e['candidate_count'] for e in entries] == [1,1,1,1]
                assert [e['candidates'][0]['owner_kind'] for e in entries] == ['edge','face','edge','edge']
                assert all(e['candidates'][0]['body_graph_membership'] == [row['qualified_body_view_record_index']] for e in entries)
                cached = operand['cached_operand'];face = cached['face']
                assert len(face['boundary_edges']) == 4 and face['surface']['kind'] == 'plane-surface'
                assert all(b['curve']['kind'] == 'straight-curve' for b in face['boundary_edges'])
                assert cached['stored_edge_reversal'] is False
                assert operand['operand_to_stored_endpoint_order'] == ['Start','End']
                assert operand['operand_vertex_order'] == operand['stored_edge_vertex_order']
                assert len(set(operand['operand_vertex_order'])) == 2
                assert [v['operand_ordinal'] for v in operand['ordered_endpoint_intersections']] == [0,1]
                assert all(operand[k] is None for k in ('exact_selected_source_identity','current_source_identity',
                    'persistent_source_identity','API_handle_identity','qualified_historical_state','traversal'))
                origins = operand['selected_cache_origins'];origin_count += len(origins)
                assert len(origins) == len({o['view_record_index'] for o in origins})
                all_origins = {o['view_record_index']:o for o in provenance['origin_map']}
                assert all(o == all_origins[o['view_record_index']] for o in origins)
                published = {cached['edge']['index'],cached['curve']['index'],face['face_record_index'],face['surface']['index']}
                for boundary in face['boundary_edges']:
                    published.update([boundary['edge']['index'],boundary['curve']['index']])
                    published.update(n['index'] for n in boundary['vertices']+boundary['points'])
                assert published <= {o['view_record_index'] for o in origins}
                initial = old['stored_initial_operand_cache'];initial_reversed += initial['stored_edge_reversal']
                contrast.append(dict(descriptor_object_id=operand['descriptor_object_id'],
                    initial_edge_record_index=initial['edge_record_index'],initial_stored_reversal=initial['stored_edge_reversal'],
                    alternate_edge_view_record_index=cached['edge']['index'],alternate_stored_reversal=cached['stored_edge_reversal'],
                    scope='Two independent literal cache representations; no chronological transition or API traversal inferred'))
            sample['initial_alternate_literal_contrasts'] = contrast
            feature = next(f for f in stream['features'] if f['object_id'] == 285)
            sample['expected_prior_tool_settings'] = feature['tool_settings']
            truth_path = root/Path(archive).parent/'ground_truth.json';truth = json.loads(truth_path.read_text())
            actual = next(s for s in truth['samples'] if s['file'] == Path(archive).name)
            sample['API_evidence'] = dict(ground_truth_sha256=hashlib.sha256(truth_path.read_bytes()).hexdigest(),
                actual_saved_settings=actual['settings'],actual_saved_parameters=actual['parameters'],
                source_edge_geometry_getters_captured=False,native_API_handle_assignment=None,
                scope='Previously captured controls only; new cache geometry has no independent API identity or state assignment')
        else:
            assert summary['associations'] == []
            sample['control_status'] = 'Outside native SurfaceExtend owner gate; full empty summary'
        report['samples'].append(sample)
    assert operand_count == 8 and initial_reversed == 4

    archive = FILES[0];data,records,features,member,members = loaded[archive]
    stream = before[archive]['streams'][0];ids,selections = stream['body_asm_identifiers'],stream['body_selections']
    by = {r.object_id:r for r in records if r.is_primary}
    source = report['samples'][0]['expected_summary']['associations'][0]
    operand = source['descriptor_operands'][0];recipe = by[operand['recipe_object_id']]
    def reject(label,changed_data=data,changed_records=records,changed_features=features,
               changed_ids=ids,changed_members=None,successes=0):
        mm = dict(members) if changed_members is None else dict(changed_members);mm[member] = changed_data
        out = decode_extend_cache_sources(changed_data,changed_records,changed_features,member,mm,changed_ids,selections)
        assert len(out['associations']) == successes and out['unresolved'],(label,out)
        report['malformed_guards'].append(dict(label=label,successful_owner_ids=[r['owner_object_id'] for r in out['associations']],diagnostics=out['unresolved']))
    changes = (('Unobserved outer recipe qualifier',recipe.end-4,struct.pack('<i',0)),
        ('Nested endpoint count corruption',recipe.end-156+40,struct.pack('<i',3)),
        ('Native proxy owner corruption',by[operand['selection_record_object_id']].body+95,struct.pack('<Q',999999)))
    for label,offset,value in changes:
        altered = bytearray(data);altered[offset:offset+len(value)] = value;reject(label,bytes(altered))
    reject('Duplicate primary descriptor',changed_records=records+[by[operand['descriptor_object_id']]])
    fake = copy.deepcopy(ids)
    for mapping in fake['decoded']:
        for binding in mapping['bindings']:
            if binding['native_body_object_id'] == 278: binding['stored_handle'] = 99
    reject('Forged caller stored BODY identifier',changed_ids=fake)
    fake = copy.deepcopy(ids)
    for mapping in fake['decoded']:
        for binding in mapping['bindings']:
            if binding['native_body_object_id'] == 278: binding['asm_body_index'] = 1
    reject('Forged caller initial BODY index',changed_ids=fake)
    # Change a trailing direct-edge tag while leaving all typed geometry and
    # native Design recipe bytes intact; coordinates cannot rescue its name.
    entry = operand['alternate_naming_correspondence']['name_entries'][0]
    attr = entry['candidates'][0]['attribute_record_index']
    origin = next(o for o in operand['selected_cache_origins'] if o['view_record_index'] == attr)
    assert origin['section'] == 'trailing_states'
    blob_member = source['history_blob_member'];parsed = inspect_asm(members[blob_member])
    record = parsed['records'][origin['inspection_record_index']]
    name = operand['recipe']['name_table'][0]['terms'][0]['name']
    tokens = [t for t in record['tokens'] if t['kind'] == 'string' and t['value'] == name]
    assert len(tokens) == 1 and tokens[0]['tag'] == 7 and len(name) == 1
    mm = dict(members);raw = bytearray(mm[blob_member]);raw[tokens[0]['offset']+2] = ord('9');mm[blob_member] = bytes(raw)
    reject('Changed alternate direct-edge complete name has no coordinate fallback',changed_members=mm)
    fakeid = 900000;fr = replace(by[285],object_id=fakeid)
    ff = copy.deepcopy(next(f for f in features if f['object_id'] == 285));ff['object_id'] = fakeid
    reject('Valid first native owner then invalid second remains handled',changed_records=records+[fr],changed_features=features+[ff],successes=1)
    report['summary'] = dict(focused_archives=13,Extend_owners=7,alternate_descriptor_operands=8,
        complete_recipe_replays=8,complete_named_operand_matches=32,ordered_endpoint_intersections=16,
        published_face_boundary_edges=32,selected_origin_rows=origin_count,
        initial_stored_reversal_true=initial_reversed,alternate_stored_reversal_false=8,
        prior_initial_source_summaries_exact=13,empty_controls=6,malformed_guards=len(report['malformed_guards']),
        API_geometry_corroboration=False,main_runs=0,live_calls=0)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--zstd-library',required=True)
    p.add_argument('--baseline-cache',type=Path,default=Path('/private/tmp/fusion-extend-cache-source-baseline.json'))
    p.add_argument('--output',type=Path,default=ROOT/'extend-cache-source-decoding.json');args = p.parse_args()
    report = validate(args.root.resolve(),args.zstd_library,args.baseline_cache)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report['summary']))
