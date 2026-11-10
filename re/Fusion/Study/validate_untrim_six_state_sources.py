"""Ten-file Untrim six-state refinement proof; no main or live calls."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_untrim_sources import decode_untrim_sources
from decode_surface_tools import decode_surface_tool
from decode_selection import native_origin_entities
from decode_one_face_edge_sources import _replay_recipe
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
FILES = tuple('surfacebounds-ac801bb00fae/untrim_'+m+'.f3d' for m in ('internal','external','all','manual'))+(
    'surfacebounds-ac801bb00fae/extend_natural.f3d','surfacebounds-ac801bb00fae/extend_two_edges.f3d',
    'surfacebounds-ac801bb00fae/ruled_tangent.f3d','patchcontinuity-b9b0be85a281/brep_tangent.f3d',
    'namedbodies-3c7c11fc2924/namedbodies.f3d','edgemodes-52695761f185/fillet_curvature.f3d')


def validate(root,zstd,baseline_path):
    baseline = json.loads(baseline_path.read_text())
    assert baseline['baseline_commit'] == 'd673008'
    before = {Path(o['file']).relative_to(root).as_posix():o for o in baseline['before']}
    assert set(before) == set(FILES)
    report = dict(interface='Existing decode_untrim_sources(...)->associations/unresolved/scope; canonical six-state dispatch to materialize_untrim_six_state_cache',
        integration=dict(stream='untrim_sources',owner_feature_list='untrim_sources',owner_field='owner_object_id',
            refined_fields=['face_operand.alternate_cache_status','face_operand.qualified_alternate_face_candidate'],
            refined_modes=['External','All'],old_warning_clearances=0,old_initial_source_replacements=0,new_parallel_stream=False),
        scope='Two additional literal alternate FACE cache candidates; initial/native source, five-state candidates, controls and diagnostics preserved. No chronology, current/API/persistent identity or semantic inner/outer-loop assignment.',
        baseline=dict(commit='d673008',path=str(baseline_path),sha256=hashlib.sha256(baseline_path.read_bytes()).hexdigest()),
        samples=[],guards=[],source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in (
            'decode_untrim_sources.py','validate_untrim_six_state_sources.py','materialize_untrim_six_state_cache.py',
            'materialize_untrim_cache.py','materialize_asm_literal_view.py','decode_asm_history.py',
            'decode_asm_name_versions.py','decode_asm_recipe_tags.py','decode_brep.py')})
    loaded = {};new_candidates = 0;reused_five = 0;published_edges = 0
    for archive in FILES:
        data,records,features,member,members = load(root,archive,zstd)
        loaded[archive] = data,records,features,member,members
        stream = before[archive]['streams'][0];ids,selections = stream['body_asm_identifiers'],stream['body_selections']
        saved = copy.deepcopy((features,records,ids,selections))
        summary = decode_untrim_sources(data,records,features,member,members,ids,selections)
        assert not summary['unresolved'],(archive,summary)
        assert (features,records,ids,selections) == saved
        sample = dict(archive=archive,archive_sha256=hashlib.sha256((root/archive).read_bytes()).hexdigest(),
            expected_summary=summary,inputs_unchanged=True)
        prior = stream.get('untrim_sources')
        if any(mode in archive for mode in ('untrim_external','untrim_all')):
            new_candidates += 1;assert prior is not None
            assert len(summary['associations']) == len(prior['associations']) == 1
            row = summary['associations'][0];old = prior['associations'][0]
            face = row['face_operand'];oldface = old['face_operand']
            assert oldface['alternate_cache_status']['status'] == 'UnsupportedAlternateCache'
            assert 'qualified_alternate_face_candidate' not in oldface
            assert face['alternate_cache_status'] == dict(status='QualifiedLiteralAlternateCache',qualified_historical_state=None)
            candidate = face['qualified_alternate_face_candidate']
            restored = copy.deepcopy(summary)
            changed = restored['associations'][0]['face_operand']
            changed['alternate_cache_status'] = oldface['alternate_cache_status']
            del changed['qualified_alternate_face_candidate']
            assert restored == prior,archive
            sample['exact_after_only_status_candidate_restore'] = True
            assert row['owner_object_id'] == 274 and row['native_body_object_id'] == 267
            assert row['explicit_asm_body_index'] == 3
            assert face['recipe'] == oldface['recipe'] and face['operation_operands'] == oldface['operation_operands']
            assert face['stored_initial_operand_cache'] == oldface['stored_initial_operand_cache']
            assert face['literal_face_name_version'] == oldface['literal_face_name_version']
            assert _replay_recipe(face['recipe']).hex() == face['full_counted_recipe_payload_hex']
            assert all(candidate[k] is None for k in ('exact_selected_source_identity','current_source_identity',
                'persistent_source_identity','qualified_historical_state','API_handle_identity'))
            provenance = candidate['alternate_cache_provenance'];cache = candidate['cached_face']
            assert len(provenance['canonical_history']['journal_states']) == 6
            assert provenance['stored_body_identifier'] == 1 and provenance['initial_body_record_index'] == 3
            assert provenance['qualified_dangling_pointer_count'] == 0
            assert provenance['geometry_before_feature'] is None and provenance['current_state'] is None
            assert provenance['semantic_loop_roles'] is None and provenance['native_historical_BODY_identity'] is None
            assert cache['body_record_index'] == provenance['qualified_body_view_record_index']
            assert cache['surface']['kind'] == 'plane-surface'
            curves = [b['curve']['kind'] for b in cache['boundary_edges']]
            assert curves.count('straight-curve') == 4
            assert curves.count('ellipse-curve') == (1 if 'external' in archive else 0)
            assert len({r['loop_record_index'] for r in cache['incidence_routes']}) == (2 if 'external' in archive else 1)
            assert provenance['derived_stored_geometry_consistency']['optional_circle_count'] == curves.count('ellipse-curve')
            assert provenance['derived_stored_geometry_consistency']['oriented_four_vertex_cycle_closed'] is True
            entries = candidate['naming_correspondence']['name_entries']
            assert len(entries) == 1 and entries[0]['candidate_count'] == 1
            named = entries[0]['candidates'][0]
            assert named['owner_kind'] == 'face' and named['owner_record_index'] == cache['face_record_index']
            assert named['body_graph_membership'] == [cache['body_record_index']]
            assert cache['face_record_index'] == 11
            all_origins = {o['view_record_index']:o for o in provenance['origin_map']}
            origins = candidate['selected_cache_origins']
            assert len(origins) == len({o['view_record_index'] for o in origins})
            assert all(o == all_origins[o['view_record_index']] for o in origins)
            selected = {cache['body_record_index'],cache['face_record_index'],cache['surface']['index'],named['attribute_record_index']}
            for route in cache['incidence_routes']: selected.update(route.values())
            for boundary in cache['boundary_edges']:
                selected.update([boundary['edge']['index'],boundary['curve']['index']])
                selected.update(n['index'] for n in boundary['vertices']+boundary['points'])
            assert selected == {o['view_record_index'] for o in origins}
            published_edges += len(cache['boundary_edges'])
            sample.update(qualified_complete_face_names=1,published_boundary_edges=len(cache['boundary_edges']),
                identity_or_state_inferred=False)
        elif prior is not None:
            reused_five += 1;assert summary == prior,archive
            sample['whole_five_state_summary_exact'] = True
        else:
            assert not summary['associations'] and not summary['unresolved']
            sample['control_status'] = 'Outside native Untrim gate; full empty helper summary'
        if '/untrim_' in archive:
            by = {r.object_id:r for r in records if r.is_primary};rec = by[274]
            feature = next(f for f in features if f['object_id'] == 274)
            controls = decode_surface_tool(data,records,data[rec.body:rec.end],feature,native_origin_entities(data,records))
            expected = next(f for f in stream['features'] if f['object_id'] == 274)['tool_settings']
            assert controls == expected
            sample['expected_prior_tool_settings'] = controls
        report['samples'].append(sample)
    assert new_candidates == 2 and reused_five == 2 and published_edges == 9

    # Corrupt only trailing geometry: native face/name provenance remains valid,
    # while the optional alternate candidate must fall back to an explicit error.
    archive = FILES[1];data,records,features,member,members = loaded[archive]
    stream = before[archive]['streams'][0];ids,selections = stream['body_asm_identifiers'],stream['body_selections']
    good = report['samples'][1]['expected_summary'];row = good['associations'][0]
    candidate = row['face_operand']['qualified_alternate_face_candidate'];blob_member = row['history_blob_member']
    boundary = next(b for b in candidate['cached_face']['boundary_edges'] if b['curve']['kind'] == 'straight-curve')
    point_id = boundary['points'][0]['index']
    origin = next(o for o in candidate['selected_cache_origins'] if o['view_record_index'] == point_id)
    assert origin['section'] == 'trailing_states'
    parsed = inspect_asm(members[blob_member]);record = parsed['records'][origin['inspection_record_index']]
    vectors = [t for t in record['tokens'] if t['kind'] == 'position_vector']
    assert len(vectors) == 1 and vectors[0]['tag'] == 19
    mm = dict(members);raw = bytearray(mm[blob_member]);token = vectors[0]
    raw[token['offset']+1:token['offset']+9] = struct.pack('<d',token['value'][0]+0.25);mm[blob_member] = bytes(raw)
    damaged = decode_untrim_sources(data,records,features,member,mm,ids,selections)
    assert len(damaged['associations']) == 1 and not damaged['unresolved']
    badface = damaged['associations'][0]['face_operand']
    assert badface['alternate_cache_status']['status'] == 'UnsupportedAlternateCache'
    assert 'qualified_alternate_face_candidate' not in badface
    restored = copy.deepcopy(damaged);restored['associations'][0]['face_operand']['alternate_cache_status'] = row['face_operand']['alternate_cache_status']
    restored['associations'][0]['face_operand']['qualified_alternate_face_candidate'] = candidate
    assert restored == good
    report['guards'].append(dict(label='Trailing point corruption rejects only alternate geometry qualification',
        native_source_associations=1,source_unresolved=[],alternate_cache_status=badface['alternate_cache_status'],
        all_other_native_initial_fields_exact=True))

    # Corrupt native source proof: no source association can be manufactured by
    # otherwise valid alternate geometry.
    by = {r.object_id:r for r in records if r.is_primary}
    for label,offset,value in (
        ('Native face recipe qualifier corruption',by[284].end-4,struct.pack('<i',0)),
        ('Native proxy owner corruption',by[278].body+95,struct.pack('<Q',999999))):
        altered = bytearray(data);altered[offset:offset+len(value)] = value
        mm = dict(members);mm[member] = bytes(altered)
        out = decode_untrim_sources(bytes(altered),records,features,member,mm,ids,selections)
        assert not out['associations'] and out['unresolved'],label
        report['guards'].append(dict(label=label,native_source_associations=0,diagnostics=out['unresolved']))
    # Changing the unique complete trailing FACE name cannot be rescued by its
    # unchanged coordinates or by a different tag in the same BODY.
    attr = candidate['naming_correspondence']['name_entries'][0]['candidates'][0]['attribute_record_index']
    origin = next(o for o in candidate['selected_cache_origins'] if o['view_record_index'] == attr)
    assert origin['section'] == 'trailing_states'
    record = parsed['records'][origin['inspection_record_index']]
    names = [t for t in record['tokens'] if t['kind'] == 'string' and t['value'] == '3']
    assert len(names) == 1 and names[0]['tag'] == 7
    mm = dict(members);raw = bytearray(mm[blob_member]);raw[names[0]['offset']+2] = ord('9');mm[blob_member] = bytes(raw)
    out = decode_untrim_sources(data,records,features,member,mm,ids,selections)
    assert not out['associations'] and out['unresolved']
    report['guards'].append(dict(label='Changed complete FACE tuple has no coordinate fallback',native_source_associations=0,diagnostics=out['unresolved']))
    report['summary'] = dict(focused_archives=10,refined_existing_FACE_candidates=2,qualified_six_state_views=2,
        complete_unique_FACE_names=2,published_boundary_edges=9,published_line_caches=8,published_circle_caches=1,
        prior_five_state_summaries_exact=2,unchanged_nonUntrim_controls=6,prior_Untrim_tool_settings_exact=4,
        refinements_limited_to_status_and_candidate=True,focused_guards=len(report['guards']),
        API_geometry_corroboration=False,main_runs=0,live_calls=0)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--zstd-library',required=True)
    p.add_argument('--baseline-cache',type=Path,default=Path('/private/tmp/fusion-untrim-six-state-source-baseline.json'))
    p.add_argument('--output',type=Path,default=ROOT/'untrim-six-state-source-decoding.json');args = p.parse_args()
    report = validate(args.root.resolve(),args.zstd_library,args.baseline_cache)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report['summary']))
