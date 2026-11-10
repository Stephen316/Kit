"""Captured API probe references joined to separately qualified native FACE caches.

Production decoding never reads ground_truth. This fixture-only corroboration
uses saved source/SDK/readback/export evidence, scoped native anchor UUIDs and
complete face names. Opaque API tokens only transport recorded probe references.
No coordinates, record ordinals, token text or tempId choose a native FACE.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import uuid

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags, match_recipe_tag_names, _terms_key
from decode_asm_subtypes import decode_asm_subtypes
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_bindings import decode_body_bindings
from decode_body_selections import decode_body_selections
from decode_brep import decode_topology
from decode_recipe_components import decode_counted_recipe
from decode_untrim_sources import _face_cache
from validate_mesh_remesh import load
from validate_rule_surface_native_observations import grid_comparison, VBL_REASON

ROOT=Path(__file__).resolve().parent
CAPTURE='rulefilletsurfaces-7b26b40f98f7'
EVIDENCE='surface-offset-intersection-decoding.json'
OFFSET='1589BC73-D484-4A6E-8E69-2A1531E845F5'
EXTRUDE='DD405BC2-D673-44F0-8833-5CB2A1C186C7'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def normalized(value):return json.loads(json.dumps(value))


def context(filename,zstd):
    data,records,features,member,members=load(ROOT,filename,zstd)
    grouped={}
    for r in records:
        if r.is_primary:grouped.setdefault(r.object_id,[]).append(r)
    if any(len(rows)!=1 for rows in grouped.values()):raise ValueError('Native primary IDs repeat')
    native={key:rows[0] for key,rows in grouped.items()}
    raw_bindings=decode_body_bindings(data,records,member,dict(streams=[dict(member=m) for m in members if m.endswith('.smbh')]))
    if raw_bindings['unresolved']:raise ValueError('Fresh native BODY mapping layout unresolved')
    maps=decode_body_asm_identifiers(data,records,member,members,raw_bindings)
    if maps['unresolved']:raise ValueError('Fresh native BODY/stored-ID association unresolved')
    return dict(filename=filename,data=data,records=records,features=features,member=member,members=members,
        native=native,maps=maps,anchors=decode_body_selections(data,records)['body_anchors'],cache={})


def anchor_payload(ctx,anchor):
    r=ctx['native'][anchor['object_id']]
    return ctx['data'][r.body:r.end]


def original_anchor(original,witness,source):
    matches=[a for a in witness['anchors'] if a['object_id']==source['body_anchor_object_id']]
    if len(matches)!=1:raise ValueError('Witness anchor missing or ambiguous')
    selected=matches[0];identity=selected['native_uuid_text'];uuid.UUID(identity)
    if sum(a['native_uuid_text']==identity for a in witness['anchors'])!=1:
        raise ValueError('Witness export has no unique native anchor UUID')
    matches=[a for a in original['anchors'] if a['native_uuid_text']==identity]
    if len(matches)!=1:raise ValueError('Original export has no unique same-run native anchor UUID')
    left=matches[0]
    for key in ('object_id','class_guid','native_body_object_id','source_owner_object_id','stored_flags'):
        if left[key]!=selected[key]:raise ValueError('Original/witness explicit anchor roles differ')
    if (selected['native_body_object_id']!=source['native_body_object_id']
            or selected['source_owner_object_id']!=source['historical_source_owner_object_id']
            or anchor_payload(original,left)!=anchor_payload(witness,selected)):
        raise ValueError('Same-run native anchor payload or source route differs')
    for ctx in (original,witness):
        if ctx['native'][left['source_owner_object_id']].class_guid!=EXTRUDE:
            raise ValueError('Historical source owner is not the independently typed Extrude')
    return left,selected


def cache_side(ctx,anchor,recipe,face_name_index):
    choices=[(m,b) for m in ctx['maps']['decoded'] for b in m['bindings']
        if b['native_body_object_id']==anchor['native_body_object_id']]
    if len(choices)!=1:raise ValueError('Source has no unique fresh native BODY/blob mapping')
    mapping,binding=choices[0];member=mapping['history_blob_member']
    if member not in ctx['cache']:
        blob=ctx['members'][member];parsed=inspect_asm(blob)
        topology=decode_topology(parsed,subtype_catalog=decode_asm_subtypes(blob,parsed=parsed))
        tags=decode_asm_generic_tags(blob,parsed=parsed,allow_fpm_tracking=True)
        if tags['unresolved']:raise ValueError('Initial complete naming coverage unresolved')
        ctx['cache'][member]=(blob,parsed,topology,tags)
    blob,parsed,topology,tags=ctx['cache'][member]
    nodes={n['index']:n for n in topology['nodes']}
    graphs=[g for g in topology['body_graphs'] if g['body_index']==binding['asm_body_index']]
    if len(graphs)!=1 or not graphs[0]['body_transform_is_identity']:
        raise ValueError('Source lacks a unique identity-transform BODY graph')
    graph=graphs[0];named=match_recipe_tag_names(recipe,tags,parsed=parsed)
    entries={e['name_table_index']:e for e in named['name_entries']}
    if set(entries)!=set(range(7)):raise ValueError('Expected seven complete named FACE operands')
    faces={}
    for index,entry in entries.items():
        if entry['candidate_count']!=1:raise ValueError('Complete FACE name globally absent or ambiguous')
        candidate=entry['candidates'][0];face=candidate['owner_record_index']
        if (candidate['owner_kind']!='face' or candidate['body_graph_membership']!=[graph['body_index']]
                or face not in graph['face_indices'] or nodes[face]['kind']!='face'):
            raise ValueError('Complete FACE name leaves the independently mapped source BODY')
        faces[index]=face
    face_id=faces[face_name_index];cache=_face_cache(topology,graph['body_index'],face_id)
    definition=cache['surface'].get('partial_surface_definition',{}).get('partial_surface_definition',{})
    if definition.get('procedural_subtype')!='VBL_SURF' or definition.get('stored_component_count')!=6:
        raise ValueError('Named source is not a decoded six-component partial VBL definition')
    if len(cache['incidence_routes'])!=6:raise ValueError('Named VBL FACE does not have six boundary uses')
    neighbors=set()
    for route in cache['incidence_routes']:
        coedge=nodes[route['coedge_record_index']];partner=nodes[coedge['partner_index']]
        if (partner['partner_index']!=coedge['index'] or partner['edge_index']!=coedge['edge_index']):
            raise ValueError('Source boundary partner ownership is not reciprocal')
        neighbors.add(nodes[partner['loop_index']]['face_index'])
    if neighbors!=set(faces.values())-{face_id} or len(neighbors)!=6:
        raise ValueError('Seven complete names do not exhaust selected FACE and its neighbors')
    names={faces[e['table_index']]:_terms_key(e['terms']) for e in recipe['name_table']}
    incidence={}
    for cid in graph['coedge_indices']:
        coedge=nodes[cid];face=nodes[coedge['loop_index']]['face_index'];edge=nodes[coedge['edge_index']]
        for vertex in (edge['start_vertex_index'],edge['end_vertex_index']):
            incidence.setdefault(vertex,set()).add(face)
    vertices={v['index'] for b in cache['boundary_edges'] for v in b['vertices']};points={}
    for vertex in vertices:
        incident=incidence[vertex]
        if len(incident)!=3 or not incident<=set(names):raise ValueError('Boundary vertex lacks a complete three-FACE signature')
        signature=tuple(sorted(names[f] for f in incident))
        if signature in points:raise ValueError('Boundary vertex three-FACE signature is ambiguous')
        point=nodes[nodes[vertex]['point_index']]
        if point['kind']!='point' or any(not math.isfinite(x) for x in point['raw_origin']):
            raise ValueError('Identity-fixed boundary point is not finite typed geometry')
        points[signature]=dict(vertex_index=vertex,point_index=point['index'],raw_position=point['raw_origin'])
    if len(points)!=6:raise ValueError('Expected six distinct identity-fixed boundary vertices')
    return dict(mapping=mapping,binding=binding,cache=cache,points=points,face_names=named,
        diagnostics=topology['unresolved'],partial_definition=definition)


def validate(zstd):
    golden=json.loads((ROOT/EVIDENCE).read_text())
    goldens={s['archive']:s['expected_summary'] for s in golden['samples']}
    folder=ROOT/CAPTURE;truth=json.loads((folder/'ground_truth.json').read_text())
    native_validation=json.loads((ROOT/'rule-surface-witness-native-validation.json').read_text())
    assert native_validation['validation']['witnesses']==16 and not truth['errors'] and (folder/'complete.txt').is_file()
    report=dict(scope='Fixture-only captured API probe reference plus complete typed native selection/cache correspondence, separately qualified in original and witness exports. No universal API handle, current/persistent state, full recipe-tail execution or VBL XYZ evaluator.',
        capture=CAPTURE,inputs_sha256={name:sha(ROOT/name) for name in (
            EVIDENCE,'rule-surface-witness-native-validation.json',CAPTURE+'/ground_truth.json',CAPTURE+'/journal.jsonl',CAPTURE+'/executed-generator-source.txt')},
        source_sha256={name:sha(ROOT/name) for name in ('validate_rule_surface_witness_bindings.py','validate_rule_surface_native_observations.py',
            'decode_body_asm_identifiers.py','decode_body_bindings.py','decode_asm_recipe_tags.py','decode_untrim_sources.py','decode_brep.py')},
        samples=[],cross_export_guards=[],native_API_handle_identity=None,complete_recipe_execution=None,native_VBL_XYZ_evaluator=None)
    contexts={};total=Counter();residuals=[];boundary_max=0.;pairs=[]
    for sample in truth['samples']:
        original_file=CAPTURE+'/'+sample['file'];witness_file=CAPTURE+'/'+sample['witness_archive']['file']
        assert sha(ROOT/original_file)==sample['archive_sha256'] and sha(ROOT/witness_file)==sample['witness_archive']['sha256']
        for filename in (original_file,witness_file):contexts[filename]=context(filename,zstd)
        report['inputs_sha256'][original_file]=sha(ROOT/original_file)
        report['inputs_sha256'][witness_file]=sha(ROOT/witness_file)
        original,witness=contexts[original_file],contexts[witness_file]
        sources=goldens[witness_file]['associations'];assert len(sources)==8 and not goldens[witness_file]['unresolved']
        by_name={}
        for f in witness['features']:
            if f.get('kind')=='SurfaceOffset':by_name.setdefault(f.get('name'),[]).append(f)
        probes={f['entity_token']:f for b in sample['result_bodies'] for f in b['faces'] if 'nurbs_data' in f}
        assert len(probes)==8
        rows=[];anchors=set()
        for observed in sample['witnesses']:
            features=by_name[observed['name']];assert len(features)==1;feature=features[0]
            assert feature['class_guid']==OFFSET
            candidates=[s for s in sources if s['owner_object_id']==feature['object_id']];assert len(candidates)==1;source=candidates[0]
            rec=witness['native'][source['recipe_object_id']];recipe=decode_counted_recipe(witness['data'],rec)
            assert normalized(recipe)==normalized(source['recipe']) and source['exact_full_counted_recipe_replay'] is True
            probe=probes[observed['source_face_token']]
            assert observed['input_entity_equals_resolved_source'] is True and observed['rolled_input']['entity_equals_resolved_source'] is True
            assert observed['actual_distance_cm']==0 and observed['actual_chain_selection'] is False and observed['feature_health_state']==0
            before_anchor,after_anchor=original_anchor(original,witness,source);anchors.add(before_anchor['native_uuid_text'])
            outer=source['operation_operands']['stored_direct_face_name_index']
            left=cache_side(original,before_anchor,recipe,outer);right=cache_side(witness,after_anchor,recipe,outer)
            assert right['cache']['face_record_index']==source['cached_face']['face_record_index']
            assert right['binding']['stored_handle']==source['native_stored_body_identifier']
            assert left['binding']['stored_handle']!=right['binding']['stored_handle']
            if set(left['points'])!=set(right['points']):raise ValueError('Original/witness complete boundary vertex signatures differ')
            boundary=[]
            for signature in sorted(left['points']):
                a,b=left['points'][signature],right['points'][signature];error=math.dist(a['raw_position'],b['raw_position'])
                assert math.isfinite(error), (observed['name'], a, b);boundary_max=max(boundary_max,error)
                boundary.append(dict(complete_incident_FACE_name_signature=signature,original=a,witness=b,residual_raw=error,
                    coincident_within_1e_9_raw=error<1e-9))
            observations=probe['samples'];assert len(observations)==3
            eligible=[o for o in observations if o and o['is_parameter_on_face'] and o['point_success'] and o['derivative_success']]
            excluded=[o for o in observations if o not in eligible]
            comparison=grid_comparison(dict(probe,samples=eligible))
            comparison['excluded_captured_observations']=excluded
            comparison['comparison_scope']='Only captured successful on-face samples qualify; excluded observations are retained verbatim.'
            errors=[x['residual_cm'] for x in comparison['evaluations']];residuals.extend(errors)
            assert len(errors)+len(excluded)==3
            rows.append(dict(witness_native_feature_object_id=feature['object_id'],unique_feature_metadata_name=feature['name'],
                name_scope='Candidate metadata only, qualified by typed owned selector, exact recipe and native BODY/name/incidence proofs plus immutable capture export/readback evidence',
                captured_API_probe_reference=dict(temp_id=probe['temp_id'],geometry_object_type=probe['geometry_object_type'],
                    actual_input_and_rolled_entity_equality=True,reference_scope='Same-run opaque token dataflow indexes the saved API probe only; actual native wrapper equality supplies the API readback proof. No token text or tempId is a native topology identity.'),
                native_anchor_UUID=before_anchor['native_uuid_text'],native_anchor_payload_sha256=hashlib.sha256(anchor_payload(original,before_anchor)).hexdigest(),
                original_native_cache=dict(archive=original_file,body_binding=left['binding'],face_record_index=left['cache']['face_record_index'],
                    surface_record_index=left['cache']['surface']['index'],complete_naming=left['face_names'],partial_VBL_subtype=left['partial_definition']['procedural_subtype']),
                witness_native_cache=dict(archive=witness_file,body_binding=right['binding'],face_record_index=right['cache']['face_record_index'],
                    surface_record_index=right['cache']['surface']['index'],descriptor_object_id=source['descriptor_object_id'],recipe_object_id=source['recipe_object_id']),
                cross_export_boundary_vertex_pairs=boundary,API_grid_vs_face_evaluator=comparison,
                geometry_scope='Complete names and anchor provenance qualify the cross-export cache association before geometry. Coordinate differences remain literal observations, not proof of identical geometry, a procedural interior, API parameter map or historical state',
                complete_recipe_tail_execution=None,native_VBL_XYZ_evaluator=None,persistent_topology_identity=None))
            total.update(qualified_probe_references=1,original_native_VBL_faces=1,witness_native_VBL_faces=1,identity_fixed_boundary_vertex_pairs=len(boundary),API_captured_samples=len(observations),API_successful_on_face_samples=len(errors),
                API_excluded_observations=len(excluded),coincident_boundary_vertex_pairs=sum(b['coincident_within_1e_9_raw'] for b in boundary),
                different_boundary_vertex_pairs=sum(not b['coincident_within_1e_9_raw'] for b in boundary))
        assert len(anchors)==1 and len(rows)==8
        original_diagnostics=next(iter(original['cache'].values()))[2]['unresolved'];witness_diagnostics=next(iter(witness['cache'].values()))[2]['unresolved']
        assert sum(d['reason']==VBL_REASON for d in original_diagnostics)==8
        assert sum(d['reason']==VBL_REASON for d in witness_diagnostics)==16
        report['samples'].append(dict(original_archive=original_file,witness_archive=witness_file,
            original_geometry_diagnostics=original_diagnostics,witness_geometry_diagnostics=witness_diagnostics,bindings=rows))
        pairs.append((original,witness,sources[0]))
    # The complete names overlap between these separately created documents;
    # matching those names alone must not permit a cross-case association.
    for original,(_,witness,source) in zip((p[0] for p in pairs),reversed(pairs)):
        try:original_anchor(original,witness,source)
        except ValueError as error:report['cross_export_guards'].append(dict(case='Swapped original from another captured document',reason=str(error)))
        else:raise AssertionError('Different captured document passed native anchor UUID qualification')
    assert len(report['cross_export_guards'])==2
    report['summary']=dict(total,original_exports=2,witness_exports=2,changed_local_BODY_handle_pairs=2,
        boundary_coordinate_scope='Measured after complete incident-FACE-name joins; differences do not invalidate naming correspondence or establish identical geometry',
        maximum_boundary_vertex_residual_raw=boundary_max,direct_API_grid_residual_range_cm=[min(residuals),max(residuals)],
        cross_case_UUID_guards=2,coordinate_identity_choices=0,native_VBL_XYZ_evaluators_added=0,main_reader_runs=0,live_calls=0)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--zstd-library');p.add_argument('--output',default='rule-surface-witness-binding-decoding.json');args=p.parse_args()
    zstd=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    out=validate(zstd);Path(args.output).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out['summary'],sort_keys=True))
