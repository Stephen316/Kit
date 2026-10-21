"""Nine saved Untrim/source fixtures, exact prior outputs and focused guards."""
import argparse
import copy
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_one_face_edge_sources import _replay_recipe
from decode_recipe_components import decode_counted_recipe
from decode_selection import native_origin_entities
from decode_selection_context_recipes import decode_selection_context_recipes
from decode_selection_recipe_incidence import decode_selection_recipe_incidence
from decode_surface_tools import decode_surface_tool
from decode_untrim_sources import decode_untrim_sources
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
FILES = tuple('surfacebounds-ac801bb00fae/untrim_'+mode+'.f3d' for mode in ('internal','external','all','manual'))+(
    'surfacebounds-ac801bb00fae/extend_natural.f3d','surfacebounds-ac801bb00fae/ruled_tangent.f3d',
    'patchcontinuity-b9b0be85a281/brep_tangent.f3d','namedbodies-3c7c11fc2924/namedbodies.f3d',
    'edgemodes-52695761f185/fillet_curvature.f3d')


def validate(root,zstd,baseline_path):
    baseline = json.loads(baseline_path.read_text())
    assert baseline['baseline_commit'] == '8a636ec'
    before = {Path(o['file']).relative_to(root).as_posix():o for o in baseline['before']}
    assert set(before) == set(FILES)
    truth_path = root/'surfacebounds-ac801bb00fae/ground_truth.json'
    truth = json.loads(truth_path.read_text())
    report = dict(interface='decode_untrim_sources(data,records,features,member,members,body_identifier_summary,body_selections=None)->associations/unresolved/scope',
        integration=dict(stream='untrim_sources',owner_feature_list='untrim_sources',owner_field='owner_object_id',
            old_warning_clearances=0,old_tool_changes=0,old_ASM_replacements=0),
        scope='Owned Untrim face source and Manual edge-with-face operands; initial cache and strict nonserialized alternate candidates are distinct, with no chronology/current/API/persistent identity or semantic inner/outer-loop claim.',
        baseline=dict(commit='8a636ec',path=str(baseline_path),sha256=hashlib.sha256(baseline_path.read_bytes()).hexdigest()),
        samples=[],malformed_guards=[],source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in (
            'decode_untrim_sources.py','validate_untrim_sources.py','decode_asm_name_versions.py','materialize_untrim_cache.py',
            'decode_asm_history.py','decode_one_face_edge_sources.py','decode_surface_tools.py','decode_recipe_components.py',
            'decode_selection_context_recipes.py','decode_body_selections.py','decode_body_asm_identifiers.py',
            'decode_asm_recipe_tags.py','decode_asm_subtypes.py','decode_brep.py')})
    loaded = {}; alternate_count = 0; manual_count = 0
    for archive in FILES:
        data,records,features,member,members = load(root,archive,zstd)
        loaded[archive] = data,records,features,member,members
        stream = before[archive]['streams'][0];ids,selections = stream['body_asm_identifiers'],stream['body_selections']
        original = copy.deepcopy((features,ids,selections))
        summary = decode_untrim_sources(data,records,features,member,members,ids,selections)
        assert not summary['unresolved'],(archive,summary)
        assert (features,ids,selections) == original
        incidence = decode_selection_recipe_incidence(data,records,features,member,members,ids,selections)
        contexts = decode_selection_context_recipes(data,records,selections)
        assert incidence == stream['selection_recipe_incidence'],archive
        if '/untrim_' in archive:
            assert contexts == stream['selection_context_recipes'],archive
        sample = dict(archive=archive,archive_sha256=hashlib.sha256((root/archive).read_bytes()).hexdigest(),
            expected_summary=summary,expected_prior_selection_recipe_incidence=incidence,
            prior_incidence_summary_exact=True,input_contexts_and_features_unchanged=True)
        if '/untrim_' in archive:
            sample['expected_prior_selection_context_recipes'] = contexts
            sample['prior_Untrim_context_summary_exact'] = True
            assert len(summary['associations']) == 1
            source = summary['associations'][0];face = source['face_operand']
            assert source['owner_object_id'] == 274 and source['historical_source_owner_object_id'] == 240
            assert source['native_body_object_id'] == 267 and source['explicit_asm_body_index'] == 3
            assert all(source[k] is None for k in ('exact_selected_source_identity','current_source_identity',
                'persistent_source_identity','qualified_historical_state','API_handle_identity'))
            assert face['selection_record_object_id'] == 278 and face['descriptor_object_id'] == 281 and face['recipe_object_id'] == 284
            assert face['stored_initial_operand_cache']['face_record_index'] == 14
            by = {r.object_id:r for r in records if r.is_primary}
            rr = by[face['recipe_object_id']]
            assert _replay_recipe(decode_counted_recipe(data,rr)) == data[rr.body:rr.end]
            assert bytes.fromhex(face['recipe']['payload_hex']) == struct.pack('<2i',0,-1)
            is_alternate = any(mode in archive for mode in ('untrim_internal','untrim_manual'))
            assert (face['alternate_cache_status']['status'] == 'QualifiedLiteralAlternateCache') == is_alternate
            if is_alternate:
                alternate_count += 1
                ac = face['qualified_alternate_face_candidate'];ap = ac['alternate_cache_provenance']
                assert ac['qualified_historical_state'] is None and ac['exact_selected_source_identity'] is None
                assert len(ap['canonical_history']['journal_states']) == 5
                assert ap['stored_body_identifier'] == (4 if 'manual' in archive else 1)
                assert ac['cached_face']['face_record_index'] != face['stored_initial_operand_cache']['face_record_index']
                assert len({r['loop_record_index'] for r in ac['cached_face']['incidence_routes']}) == 2
                assert len(ac['selected_cache_origins']) == len({r['view_record_index'] for r in ac['selected_cache_origins']})
            else:
                assert 'qualified_alternate_face_candidate' not in face
                assert face['literal_face_name_version'] is not None
                assert face['literal_face_name_version']['owner_face_record_index'] == 14
                sample['unsupported_alternate_cache_status'] = face['alternate_cache_status']
            rec = by[274];feature = next(f for f in features if f['object_id'] == 274)
            settings = decode_surface_tool(data,records,data[rec.body:rec.end],feature,native_origin_entities(data,records))
            expected = next(f for f in stream['features'] if f['object_id'] == 274)['tool_settings']
            assert settings == expected
            actual = next(s for s in truth['samples'] if s['file'] == Path(archive).name)
            sample.update(expected_prior_tool_settings=settings,API_evidence=dict(
                ground_truth_sha256=hashlib.sha256(truth_path.read_bytes()).hexdigest(),actual_saved_settings=actual['settings'],
                actual_saved_parameters=actual['parameters'],source_geometry_getters_captured=False,
                native_API_handle_assignment=None,scope='Saved mode/count/numeric controls only; no per-source face or Manual-loop API identity'))
            loops = source['manual_loop_operands']
            if 'manual' in archive:
                manual_count += 1
                assert len(loops) == 1
                loop = loops[0];candidate = loop['geometric_loop_candidate']
                assert loop['selection_record_object_id'] == 286 and loop['descriptor_object_id'] == 289 and loop['recipe_object_id'] == 292
                assert loop['initial_edge_alias'] is None and loop['qualified_historical_state'] is None
                assert loop['secondary_recipe']['object_id'] == 325
                assert bytes.fromhex(loop['recipe']['payload_hex']) == struct.pack('<7i',0,-1,1,1,-1,0,0)
                assert bytes.fromhex(loop['secondary_recipe']['payload_hex']) == struct.pack('<7i',0,-1,1,1,-1,0,-1)
                for rid in (292,325):
                    r = by[rid];assert _replay_recipe(decode_counted_recipe(data,r)) == data[r.body:r.end]
                assert candidate['semantic_loop_role'] is None and candidate['API_manual_loop_identity'] is None
                origin = next(o for o in loop['selected_cache_origins'] if o['view_record_index'] == candidate['edge_view_record_index'])
                assert origin['geometry_entity_ordinal'] == 65 and origin['inspection_record_index'] == 73 and origin['section'] == 'trailing_states'
                entry = loop['named_edge_literal_journal_context']
                assert entry['delta_state_slot'] == 0 and [x['stored_geometry_entity_ordinal'] for x in entry['pointer_sides']] == [65,-1]
                # Independent stored point/curve copies corroborate the cache,
                # not an API handle or an inferred inner/outer loop role.
                curve = candidate['geometry'];axis,normal,center = curve['stored_reference_axis'],curve['normal'],curve['raw_origin']
                cross = [normal[1]*axis[2]-normal[2]*axis[1],normal[2]*axis[0]-normal[0]*axis[2],normal[0]*axis[1]-normal[1]*axis[0]]
                checks = []
                for t in candidate['parameter_domain']:
                    point = [center[i]+math.cos(t)*axis[i]+math.sin(t)*cross[i] for i in range(3)]
                    error = max(abs(a-b) for a,b in zip(point,candidate['raw_endpoint_point']))
                    assert error < 1e-12
                    checks.append(dict(parameter=t,derived_cache_point=point,stored_point=candidate['raw_endpoint_point'],maximum_coordinate_error=error))
                sample['stored_circle_endpoint_corroboration'] = dict(checks=checks,API_geometry_comparison=False,semantic_loop_role=None)
            else: assert loops == []
        else:
            assert summary['associations'] == []
            sample['control_status'] = 'Outside native SurfaceUntrim owner gate; full empty summary'
        report['samples'].append(sample)
    assert alternate_count == 2 and manual_count == 1

    archive = FILES[0];data,records,features,member,members = loaded[archive]
    s = before[archive]['streams'][0];ids,selections = s['body_asm_identifiers'],s['body_selections']
    by = {r.object_id:r for r in records if r.is_primary};source = report['samples'][0]['expected_summary']['associations'][0]
    face = source['face_operand']
    def reject(label,changed_data=data,changed_records=records,changed_features=features,changed_ids=ids,successes=0):
        mm = dict(members);mm[member] = changed_data
        out = decode_untrim_sources(changed_data,changed_records,changed_features,member,mm,changed_ids,selections)
        assert len(out['associations']) == successes and out['unresolved'],(label,out)
        report['malformed_guards'].append(dict(label=label,successful_owner_ids=[r['owner_object_id'] for r in out['associations']],diagnostics=out['unresolved']))
    rr = by[284]
    changes = (('Face operation opaque qualifier',rr.end-4,struct.pack('<i',0)),
        ('Face proxy owner backlink',by[278].body+95,struct.pack('<Q',999999)),
        ('Descriptor trailer marker',by[281].body+223,b'\0'),
        ('Descriptor support backlink',by[face['descriptor_support_object_id']].body+32,struct.pack('<Q',999999)))
    for label,offset,value in changes:
        altered = bytearray(data);altered[offset:offset+len(value)] = value;reject(label,bytes(altered))
    reject('Duplicate primary face descriptor',changed_records=records+[by[281]])
    fake = copy.deepcopy(ids)
    for mapping in fake['decoded']:
        for binding in mapping['bindings']:
            if binding['native_body_object_id'] == 267: binding['asm_body_index'] = 1
    reject('Forged supplied source BODY identity',changed_ids=fake)
    fakeid = 900000;fr = replace(by[274],object_id=fakeid)
    ff = copy.deepcopy(next(f for f in features if f['object_id'] == 274));ff['object_id'] = fakeid
    reject('Valid first owner followed by invalid second remains handled',changed_records=records+[fr],changed_features=features+[ff],successes=1)
    # Two Manual-specific guards: its primary qualifier is0, while its typed
    # secondary recipe qualifier is-1. Neither can be silently substituted.
    d,rs,fs,m,ms = loaded[FILES[3]];stream = before[FILES[3]]['streams'][0];by = {r.object_id:r for r in rs if r.is_primary}
    for label,rid,value in (('Manual primary qualifier is not the secondary qualifier',292,-1),
                           ('Manual secondary qualifier is not the primary qualifier',325,0)):
        altered = bytearray(d);altered[by[rid].end-4:by[rid].end] = struct.pack('<i',value)
        mm = dict(ms);mm[m] = bytes(altered)
        out = decode_untrim_sources(bytes(altered),rs,fs,m,mm,stream['body_asm_identifiers'],stream['body_selections'])
        assert not out['associations'] and out['unresolved'],label
        report['malformed_guards'].append(dict(label=label,successful_owner_ids=[],diagnostics=out['unresolved']))
    report['summary'] = dict(focused_archives=9,Untrim_owners=4,face_operands=4,
        direct_initial_face_names=2,modified_paired_face_names=2,qualified_alternate_FACE_candidates=2,
        unsupported_six_state_alternate_caches=2,Manual_named_loop_candidates=1,Manual_initial_edge_aliases=0,
        full_counted_recipe_replays=6,stored_circle_endpoint_checks=2,prior_tool_settings_exact=4,
        prior_incidence_summaries_exact=9,prior_Untrim_context_summaries_exact=4,empty_controls=5,
        malformed_guards=len(report['malformed_guards']),API_geometry_corroboration=False,main_runs=0,live_calls=0)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--zstd-library',required=True)
    p.add_argument('--baseline-cache',type=Path,default=Path('/private/tmp/fusion-untrim-source-baseline.json'))
    p.add_argument('--output',type=Path,default=ROOT/'untrim-source-decoding.json');args = p.parse_args()
    report = validate(args.root.resolve(),args.zstd_library,args.baseline_cache)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report['summary']))
