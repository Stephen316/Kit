"""Focused eleven-file Extend operand/version/cache proof; no main or live calls."""
import argparse
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct

from decode_extend_edge_sources import decode_extend_edge_sources, decode_extend_edge_operands
from decode_one_face_edge_sources import _replay_recipe
from decode_recipe_components import decode_counted_recipe
from decode_selection import native_origin_entities
from decode_selection_recipe_incidence import decode_selection_recipe_incidence
from decode_surface_tools import decode_surface_tool
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
FILES = tuple('surfacebounds-ac801bb00fae/'+n+'.f3d' for n in (
    'extend_natural','extend_tangent','extend_perpendicular','extend_perpendicular_negative',
    'extend_aligned','extend_two_edges'))+('surfacebounds-8804bbf80755/extend_no_chain.f3d',
    'surfacebounds-ac801bb00fae/ruled_tangent.f3d','surfacebounds-ac801bb00fae/untrim_manual.f3d',
    'patchcontinuity-b9b0be85a281/brep_tangent.f3d','namedbodies-3c7c11fc2924/namedbodies.f3d')


def validate(root, zstd, baseline_path):
    baseline = json.loads(baseline_path.read_text())
    assert baseline['baseline_commit'] == 'd0caf99'
    before = {Path(o['file']).relative_to(root).as_posix():o for o in baseline['before']}
    assert set(before) == set(FILES)
    report = dict(interface='decode_extend_edge_sources(data,records,features,member,members,body_identifier_summary,body_selections=None)->associations/unresolved/scope',
        operand_interface='decode_extend_edge_operands(recipe)->complete156-byte grammar retaining literal inline order',
        integration=dict(stream='extend_edge_sources',owner_feature_list='extend_edge_sources',owner_field='owner_object_id',operand_list='descriptor_operands',old_warning_clearances=0,old_tool_changes=0),
        scope='Literal named operands and journal-paired naming versions joined to the mapped initial cache. No verified pre-Extend state, API handle, persistent identity, traversal or lifecycle.',
        baseline=dict(commit='d0caf99',path=str(baseline_path),sha256=hashlib.sha256(baseline_path.read_bytes()).hexdigest()),
        samples=[],malformed_guards=[],source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in (
            'decode_extend_edge_sources.py','validate_extend_edge_sources.py','decode_asm_name_versions.py',
            'decode_asm_history.py','decode_one_face_edge_sources.py','decode_selection.py','decode_surface_tools.py',
            'decode_body_selections.py','decode_body_asm_identifiers.py','decode_recipe_components.py',
            'decode_asm_recipe_tags.py','decode_asm_subtypes.py','decode_brep.py')})
    loaded = {};reversals=[];orders=[];body_contrasts=[]
    for archive in FILES:
        data,records,features,member,members = load(root,archive,zstd)
        loaded[archive]=(data,records,features,member,members)
        stream=before[archive]['streams'][0]
        identities,selections=stream['body_asm_identifiers'],stream['body_selections']
        inputs=copy.deepcopy((features,identities,selections))
        summary=decode_extend_edge_sources(data,records,features,member,members,identities,selections)
        assert not summary['unresolved'],(archive,summary)
        assert (features,identities,selections)==inputs
        old=decode_selection_recipe_incidence(data,records,features,member,members,identities,selections)
        assert old==stream['selection_recipe_incidence'],archive
        row=dict(archive=archive,archive_sha256=hashlib.sha256((root/archive).read_bytes()).hexdigest(),
            expected_summary=summary,expected_prior_selection_recipe_incidence=old,
            expected_prior_body_asm_identifiers=identities,prior_outputs_and_inputs_unchanged=True)
        if '/extend_' in archive:
            assert len(summary['associations'])==1
            association=summary['associations'][0]
            assert association['owner_object_id']==285
            operands=association['descriptor_operands']
            assert len(operands)==(2 if 'two_edges' in archive else 1)
            assert len({o['descriptor_object_id'] for o in operands})==len(operands)
            assert len({o['recipe_object_id'] for o in operands})==len(operands)
            assert len({o['stored_initial_operand_cache']['edge_record_index'] for o in operands})==len(operands)
            primary={r.object_id:r for r in records if r.is_primary}
            for operand in operands:
                cache=operand['stored_initial_operand_cache']
                assert operand['historical_source_owner_object_id']==243
                assert operand['native_body_object_id']==278 and operand['explicit_asm_body_index']==3
                assert operand['qualification']=='Literal paired naming-version to initial-cache operand correspondence'
                assert all(operand[k] is None for k in ('exact_selected_source_identity','API_handle_identity',
                    'current_source_identity','persistent_source_identity','qualified_historical_state','traversal'))
                recipe_rec=primary[operand['recipe_object_id']]
                recipe=decode_counted_recipe(data,recipe_rec)
                assert _replay_recipe(recipe)==data[recipe_rec.body:recipe_rec.end]
                assert decode_extend_edge_operands(recipe)==operand['operation_operands']
                assert {e['vertex_record_index'] for e in operand['endpoint_incidence']}=={cache['stored_start_vertex_index'],cache['stored_end_vertex_index']}
                assert len({e['vertex_record_index'] for e in operand['endpoint_incidence']})==2
                for endpoint in operand['endpoint_incidence']:
                    orders.append(endpoint['stored_inline_edge_name_order'])
                reversals.append(cache['stored_edge_reversal'])
                face=operand['literal_face_name_version']
                assert face['owner_face_record_index']==(20 if any(k in archive for k in ('tangent','perpendicular')) else 14) and face['initial_body_record_index']==3
                assert face['initial_attribute']['exact_full_payload_replay'] and face['trailing_attribute']['exact_full_payload_replay']
                blob=members[operand['history_blob_member']]
                for attribute in (face['initial_attribute'],face['trailing_attribute']):
                    assert bytes.fromhex(attribute['full_payload_hex'])==blob[attribute['full_payload_offset']:attribute['full_payload_end_offset']]
                paired=face['paired_body_version']
                body_contrasts.append(paired)
                # Shared edge cases explicitly disprove treating one named face
                # as the complete initial-cache incidence set.
                if any(k in archive for k in ('tangent','perpendicular')):
                    assert cache['selected_edge_incident_face_indices']==[14,20]
                    assert cache['boundary_in_initial_cache'] is False
                    assert {r['face_record_index'] for r in cache['incidence_routes'] if r['edge_record_index']!=cache['edge_record_index']}=={20}
                else:
                    assert cache['selected_edge_incident_face_indices']==[14] and cache['boundary_in_initial_cache'] is True
            feature=next(f for f in features if f['object_id']==285);rec=primary[285]
            controls=decode_surface_tool(data,records,data[rec.body:rec.end],feature,native_origin_entities(data,records))
            expected=next(f for f in stream['features'] if f['object_id']==285)['tool_settings']
            assert controls==expected
            truth_path=root/Path(archive).parent/'ground_truth.json';truth=json.loads(truth_path.read_text())
            actual=next(s for s in truth['samples'] if s['file']==Path(archive).name)
            row.update(expected_prior_tool_settings=controls,API_evidence=dict(
                ground_truth_sha256=hashlib.sha256(truth_path.read_bytes()).hexdigest(),actual_saved_settings=actual['settings'],
                actual_saved_parameters=actual['parameters'],source_edge_geometry_getters_captured=False,
                native_API_handle_assignment=None,scope='Saved controls only; no independent API edge geometry or version/state identity'))
        else:
            assert summary['associations']==[]
            row['control_status']='Outside native SurfaceExtend owner gate; complete empty helper summary'
        report['samples'].append(row)
    assert reversals.count(True)==4 and reversals.count(False)==4
    assert [2,0] in orders
    # The paired literal BODY stored-ID contrast is retained, never substituted
    # into the explicit native->initial BODY association.
    assert all(x is not None for x in body_contrasts)
    report['paired_BODY_literal_contrasts']=body_contrasts

    archive=FILES[0];data,records,features,member,members=loaded[archive]
    stream=before[archive]['streams'][0];identities,selections=stream['body_asm_identifiers'],stream['body_selections']
    by={r.object_id:r for r in records if r.is_primary};source=report['samples'][0]['expected_summary']['associations'][0]
    operand=source['descriptor_operands'][0];recipe=by[operand['recipe_object_id']]
    def reject(label,changed_data=data,changed_records=records,changed_features=features,
               changed_identities=identities,changed_members=None,successes=0):
        mm=dict(members) if changed_members is None else dict(changed_members);mm[member]=changed_data
        out=decode_extend_edge_sources(changed_data,changed_records,changed_features,member,mm,changed_identities,selections)
        assert len(out['associations'])==successes and out['unresolved'],(label,out)
        report['malformed_guards'].append(dict(label=label,successful_owner_ids=[r['owner_object_id'] for r in out['associations']],diagnostics=out['unresolved']))
    mutations=(('Opaque outer qualifier must remain observed -1',recipe.end-4,struct.pack('<i',0)),
        ('Nested endpoint count corruption',recipe.end-156+40,struct.pack('<i',3)),
        ('Repeated feature descriptor alias corruption',by[285].body+159,struct.pack('<Q',999999)),
        ('Descriptor trailer marker corruption',by[operand['descriptor_object_id']].body+223,b'\0'),
        ('Reciprocal descriptor support owner corruption',by[operand['descriptor_support_object_id']].body+32,struct.pack('<Q',999999)))
    for label,offset,value in mutations:
        altered=bytearray(data);altered[offset:offset+len(value)]=value;reject(label,bytes(altered))
    reject('Duplicate primary descriptor identity',changed_records=records+[by[operand['descriptor_object_id']]])
    forged=copy.deepcopy(identities)
    for mapping in forged['decoded']:
        for binding in mapping['bindings']:
            if binding['native_body_object_id']==278:binding['asm_body_index']=1
    reject('Supplied mapped BODY differs from fresh native association',changed_identities=forged)
    # Corrupt actual trailing attribute owner while preserving Design bytes.
    version=operand['literal_face_name_version'];blob_member=operand['history_blob_member']
    mm=dict(members);raw=bytearray(mm[blob_member]);offset=version['trailing_attribute']['full_payload_offset']+37
    raw[offset:offset+8]=struct.pack('<q',1);mm[blob_member]=bytes(raw)
    reject('Trailing attribute no longer owns the paired FACE',changed_members=mm)
    fake_id=900000;fake=replace(by[285],object_id=fake_id)
    ff=copy.deepcopy(next(f for f in features if f['object_id']==285));ff['object_id']=fake_id
    reject('Valid first owner followed by invalid second remains handled',changed_records=records+[fake],changed_features=features+[ff],successes=1)
    # A literal nested-name permutation is admissible grammar, while its result
    # must still be established through actual topology rather than array order.
    original=decode_counted_recipe(data,recipe);permuted=copy.deepcopy(original)
    raw=bytearray.fromhex(permuted['payload_hex']);raw[44:64],raw[64:84]=raw[64:84],raw[44:64]
    permuted['payload_hex']=raw.hex()
    decoded=decode_extend_edge_operands(permuted)
    assert decoded['endpoint_operands'][0]['stored_inline_edge_name_order']==[2,0]
    report['literal_order_control']=dict(original_order=[0,2],permuted_order=[2,0],
        both_complete_grammar_replays=True,topology_or_API_order_not_inferred=True)
    report['summary']=dict(focused_archives=11,Extend_owners=7,descriptor_operands=8,
        complete_counted_recipe_replays=8,endpoint_intersections=16,
        literal_FACE_attribute_replays=16,shared_initial_cache_edges=3,
        boundary_initial_cache_edges=5,stored_reversed_edges=4,stored_nonreversed_edges=4,
        prior_tool_settings_exact=7,prior_incidence_summaries_exact=11,empty_controls=4,
        malformed_guards=len(report['malformed_guards']),API_geometry_corroboration=False,
        main_runs=0,live_calls=0)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--zstd-library',required=True)
    p.add_argument('--baseline-cache',type=Path,default=Path('/private/tmp/fusion-extend-edge-baseline.json'))
    p.add_argument('--output',type=Path,default=ROOT/'extend-edge-source-decoding.json');args=p.parse_args()
    report=validate(args.root.resolve(),args.zstd_library,args.baseline_cache)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report['summary']))
