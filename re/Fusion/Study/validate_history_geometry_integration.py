"""Cached-only 193-file integration of stored feature/history and geometry recoveries."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from validate_history_cache_integration import differences

ROOT=Path(__file__).resolve().parent
BASELINE='4587d9e'
LEVEL='Observed historical MeshGenerateFaceGroups controls and stored feature cache before CombineFaceGroups; current asset ownership and general lifecycle remain separate'
OLD_REASON='FaceGroups selected mesh current asset route unresolved'
REPORTS=('historical-mesh-face-group-decoding.json','interp-blend-cache-decoding.json','closed-parameter-curve-decoding.json','interp-blend-downstream-decoding.json')
FILES=('meshcontrasts-10c2557c91a3/stl_centimeter.f3d',
 'meshcontrasts-10c2557c91a3/stl_millimeter.f3d',
 'meshcontrasts-10c2557c91a3/triangle_data_centimeter.f3d',
 'meshplanecuts-18f2683c83f5/split_body_minimal_fill.f3d',
 'meshplanecuts-18f2683c83f5/trim_minimal_fill.f3d',
 'meshplanecuts-18f2683c83f5/trim_no_fill.f3d',
 'meshreduces-780954a23308/adaptive_count_six.f3d',
 'meshreduces-780954a23308/adaptive_proportion_fifty.f3d',
 'meshreduces-780954a23308/uniform_count_six.f3d',
 'meshreduces-8f01528f7f21/adaptive_proportion_fifty.f3d',
 'meshconverts-4b42d39fb1d5/faceted_closed.f3d',
 'meshconverts-4b42d39fb1d5/faceted_open.f3d',
 'meshconverts-4b42d39fb1d5/prismatic_closed.f3d',
 'meshremeshes-f07f97514069/adaptive_edge_one_point_five.f3d',
 'meshremeshes-f07f97514069/adaptive_edge_two.f3d',
 'meshremeshes-f07f97514069/uniform_edge_two.f3d',
 'meshcombines-541ebb6cc93f/cut.f3d',
 'meshcombines-541ebb6cc93f/intersect.f3d',
 'meshcombines-541ebb6cc93f/join.f3d',
 'splinepatches-ac5e846e59c0/splinepatches.f3d',
 'splinepatches-900d152c2380/splinepatches.f3d',
 'assembly-acc48a9dc05d/assembly.f3d',
 'meshreversenormals-2bc2dd3780cc/closed_once.f3d',
 'meshreversenormals-2bc2dd3780cc/closed_twice.f3d',
 'meshreversenormals-2bc2dd3780cc/open_once.f3d',
 'meshsmooths-56f38f13430a/smooth_default_point_zero_two.f3d',
 'meshsmooths-56f38f13430a/smooth_point_one.f3d',
 'meshsmooths-56f38f13430a/smooth_point_two_five.f3d',
 'meshshells-f5a2d6730f62/closed_thickness_point_one.f3d',
 'meshshells-f5a2d6730f62/open_thickness_point_one.f3d',
 'meshshells-f5a2d6730f62/open_thickness_point_two.f3d',
 'meshfacegroups-0b682fa7d749/accurate_boundary_point_zero_zero_one.f3d',
 'meshfacegroups-0b682fa7d749/fast_eighty_degrees.f3d',
 'meshfacegroups-0b682fa7d749/fast_twenty_degrees.f3d',
 'meshseparates-41126250c03f/connected_shell_control.f3d',
 'meshseparates-41126250c03f/two_face_groups.f3d',
 'meshseparates-41126250c03f/two_shells.f3d',
 'meshremoves-8b2188cd274d/one_remove_one.f3d',
 'meshremoves-8b2188cd274d/two_remove_both.f3d',
 'meshremoves-8b2188cd274d/two_remove_first.f3d',
 'meshcombinefacegroups-33142f03b86e/adjacent_pair.f3d',
 'meshcombinefacegroups-33142f03b86e/adjacent_pair_reversed.f3d',
 'meshcombinefacegroups-33142f03b86e/connected_triple.f3d',
 'meshrepairs-2387e4f9c2d2/closed_close_holes_control.f3d',
 'meshrepairs-2387e4f9c2d2/open_close_holes.f3d',
 'meshrepairs-2387e4f9c2d2/open_stitch_remove.f3d',
 'meshrepairrebuilds-66d4316c2e8d/accurate_density_eight_offset_point_zero_five.f3d',
 'meshrepairrebuilds-66d4316c2e8d/accurate_density_eight_offset_zero.f3d',
 'meshrepairrebuilds-66d4316c2e8d/fast_density_eight.f3d',
 'meshreducedeviations-05a5d48e46d0/adaptive_deviation_point_one.f3d',
 'meshreducedeviations-05a5d48e46d0/adaptive_deviation_point_zero_five.f3d',
 'meshreducedeviations-05a5d48e46d0/requested_uniform_deviation_point_one.f3d',
 'meshconvertoperations-5af73924aa60/base_feature_closed.f3d',
 'meshconvertoperations-5af73924aa60/base_feature_open.f3d',
 'meshconvertoperations-5af73924aa60/two_mesh_parametric.f3d',
 'thinextrudeoperations-edb76642a509/cut.f3d',
 'thinextrudeoperations-edb76642a509/intersect.f3d',
 'thinextrudeoperations-edb76642a509/join.f3d',
 'threadmodes-d51d2ae60564/cosmetic_full.f3d',
 'threadmodes-d51d2ae60564/modeled_full.f3d',
 'threadmodes-d51d2ae60564/partial_high.f3d',
 'threadmodes-d51d2ae60564/partial_low.f3d',
 'threadmodes-d51d2ae60564/left_handed.f3d',
 'threadmodes-d51d2ae60564/internal.f3d',
 'threadmodes-9574579d310b/left_handed.f3d',
 'threadmultifaces-e4bc4a120fbf/external_two_full.f3d',
 'threadmultifaces-e4bc4a120fbf/external_two_partial.f3d',
 'threadmultifaces-e4bc4a120fbf/internal_two_full.f3d',
 'tappedholes-409e96788503/cosmetic_full.f3d',
 'tappedholes-409e96788503/cosmetic_partial.f3d',
 'tappedholes-409e96788503/modeled_full.f3d',
 'threadfamilies-459264fae49b/ansi_unified_external.f3d',
 'threadfamilies-459264fae49b/bsp_pipe_internal.f3d',
 'threadfamilies-459264fae49b/iso_trapezoidal_external.f3d',
 'faceedits-3f120cbee8d9/offset_positive.f3d',
 'faceedits-3f120cbee8d9/offset_negative.f3d',
 'faceedits-3f120cbee8d9/offset_two_faces.f3d',
 'faceedits-3f120cbee8d9/offset_cylinder.f3d',
 'faceedits-3f120cbee8d9/replace_plane.f3d',
 'faceedits-3f120cbee8d9/replace_plane_tangent.f3d',
 'faceedits-3f120cbee8d9/delete_hole_face.f3d',
 'replacefacetargets-670e35eedbc8/sheet_body.f3d',
 'replacefacetargets-670e35eedbc8/sheet_face.f3d',
 'replacefacetargets-670e35eedbc8/sheet_face_tangent.f3d',
 'splits-efce4ef164c9/yz_extend.f3d',
 'splits-efce4ef164c9/yz_no_extend.f3d',
 'splits-efce4ef164c9/xz_extend.f3d',
 'splits-efce4ef164c9/offset_plane.f3d',
 'splits-efce4ef164c9/multiple_bodies.f3d',
 'splitbodysheets-b7548618fb65/sheet_body_no_extend.f3d',
 'splitbodysheets-b7548618fb65/sheet_face_no_extend.f3d',
 'splitbodysheets-b7548618fb65/small_sheet_face_extend.f3d',
 'splitbodyprofiles-be9787c7a7d8/full_profile_one_body.f3d',
 'splitbodyprofiles-be9787c7a7d8/full_profile_two_bodies.f3d',
 'splitbodyprofiles-be9787c7a7d8/small_profile_extended.f3d',
 'splitbodymultisheets-c78bec32dc3f/sheet_body_no_extend.f3d',
 'splitbodymultisheets-c78bec32dc3f/sheet_face_no_extend.f3d',
 'splitbodymultisheets-c78bec32dc3f/small_sheet_face_extend.f3d',
 'sweeps-5f87eff25e24/line_perpendicular.f3d',
 'sweeps-5f87eff25e24/arc_perpendicular.f3d',
 'sweeps-5f87eff25e24/arc_parallel.f3d',
 'sweeps-5f87eff25e24/arc_partial.f3d',
 'sweeps-5f87eff25e24/line_taper.f3d',
 'sweeps-5f87eff25e24/line_twist.f3d',
 'sweeps-5f87eff25e24/line_surface.f3d',
 'sweeps-5f87eff25e24/line_cut.f3d',
 'moretools-88a2cd6cad0b/Sweep.f3d',
 'moretools-380212ab6368/SweepPartial.f3d',
 'sweepguides-db118be14bfe/composite_line_arc.f3d',
 'sweepguides-db118be14bfe/closed_circle.f3d',
 'sweepguides-9887de71bf9e/rail_scale.f3d',
 'sweepguides-9887de71bf9e/rail_stretch.f3d',
 'sweepguides-9887de71bf9e/rail_no_scaling.f3d',
 'sweepguides-9887de71bf9e/rail_full_extents.f3d',
 'sweepguides-9887de71bf9e/guide_surface.f3d',
 'sweepguides-9887de71bf9e/guide_surface_chain.f3d',
 'sweepoperations-62378e7c0294/join.f3d',
 'sweepoperations-62378e7c0294/intersect.f3d',
 'sweepoperations-62378e7c0294/two_sided.f3d',
 'sweepoperations-62378e7c0294/rail_flip_false.f3d',
 'sweepoperations-62378e7c0294/rail_flip_true.f3d',
 'sweepoperations-62378e7c0294/guided_cut.f3d',
 'sweepprofiles-b2b7a2774752/planar_face.f3d',
 'sweepprofiles-b2b7a2774752/open_sketch_surface.f3d',
 'sweepprofiles-b2b7a2774752/open_brep_edge_surface.f3d',
 'sweepprofiles-b2b7a2774752/two_profile_collection.f3d',
 'sweepprofiles-8d489fe02d2d/open_sketch_surface.f3d',
 'sweepprofiles-8d489fe02d2d/open_brep_edge_surface.f3d',
 'sweepprofiles-f20861d6c5c2/open_brep_edge_partial.f3d',
 'sweepprofiles-f20861d6c5c2/open_brep_edge_reversed.f3d',
 'solidsweeps-7d2677669e3d/solid_perpendicular.f3d',
 'solidsweeps-7d2677669e3d/solid_rigid.f3d',
 'solidsweeps-7d2677669e3d/solid_aligned.f3d',
 'solidsweeps-7d2677669e3d/solid_twist.f3d',
 'solidsweeps-5b5ecd5e01b9/solid_twist_zero.f3d',
 'solidsweeps-5b5ecd5e01b9/solid_twist_sixty.f3d',
 'sweepnurbspaths-7ded30a4b9ae/polynomial_cubic.f3d',
 'sweepnurbspaths-7ded30a4b9ae/polynomial_multispan.f3d',
 'sweepnurbspaths-7ded30a4b9ae/rational_cubic.f3d',
 'surfacebounds-ac801bb00fae/extend_natural.f3d',
 'surfacebounds-ac801bb00fae/extend_tangent.f3d',
 'surfacebounds-ac801bb00fae/extend_perpendicular.f3d',
 'surfacebounds-ac801bb00fae/extend_perpendicular_negative.f3d',
 'surfacebounds-ac801bb00fae/extend_aligned.f3d',
 'surfacebounds-ac801bb00fae/extend_two_edges.f3d',
 'surfacebounds-ac801bb00fae/untrim_internal.f3d',
 'surfacebounds-ac801bb00fae/untrim_external.f3d',
 'surfacebounds-ac801bb00fae/untrim_all.f3d',
 'surfacebounds-ac801bb00fae/untrim_manual.f3d',
 'surfacebounds-ac801bb00fae/ruled_tangent.f3d',
 'surfacebounds-ac801bb00fae/ruled_normal.f3d',
 'surfacebounds-ac801bb00fae/ruled_direction.f3d',
 'surfacebounds-ac801bb00fae/ruled_mitered.f3d',
 'surfacebounds-ac801bb00fae/trim_positive.f3d',
 'surfacebounds-ac801bb00fae/trim_negative.f3d',
 'surfacebounds-8804bbf80755/extend_no_chain.f3d',
 'surfacetools-856ca50cf4c7/patch_rectangle.f3d',
 'surfacetools-856ca50cf4c7/patch_circle.f3d',
 'surfacetools-856ca50cf4c7/offset_positive.f3d',
 'surfacetools-856ca50cf4c7/offset_negative.f3d',
 'surfacetools-856ca50cf4c7/offset_rounded.f3d',
 'surfacetools-856ca50cf4c7/stitch_tight.f3d',
 'surfacetools-856ca50cf4c7/stitch_loose.f3d',
 'surfacetools-856ca50cf4c7/unstitch_face.f3d',
 'surfacetools-856ca50cf4c7/unstitch_chain.f3d',
 'surfacetools-856ca50cf4c7/reverse_normal.f3d',
 'surfacetools-856ca50cf4c7/delete_opening.f3d',
 'surfacetrimtools-c507461585b5/sheet_face.f3d',
 'surfacetrimtools-ce3c7e1c703e/sheet_body.f3d',
 'surfacetrimtools-560510587441/sheet_face.f3d',
 'surfacetrimtools-ca26d21e7ad9/sheet_body.f3d',
 'surfacetrimtools-ca26d21e7ad9/sketch_line.f3d',
 'surfacetrimtools-650ca09579b1/sketch_line_offset_positive.f3d',
 'surfacetrimtools-650ca09579b1/sketch_line_reversed_negative.f3d',
 'loftcompositeguides-8ea2ef593872/centerline_connected_chain.f3d',
 'loftcompositeguides-8ea2ef593872/centerline_explicit_members.f3d',
 'loftcompositeguides-8ea2ef593872/rail_line_arc.f3d',
 'loftcompositeguides-8ea2ef593872/spline_centerline.f3d',
 'loftcurvedguides-79a1266af54e/quarter_arc_centerline.f3d',
 'lofts-03b4a6f1ce2f/centerline.f3d',
 'moretools-380212ab6368/LoftThreeSections.f3d',
 'pipepaths-3d11bd427946/spline_circular.f3d',
 'specialfillets-d50f7a4f04e0/rule_asymmetric.f3d',
 'splines-9a18bae21127/splines.f3d',
 'edgemodes-87edbf67527b/fillet_asymmetric.f3d',
 'edgemodes-87edbf67527b/fillet_chord.f3d',
 'patchcontinuity-b9b0be85a281/brep_curvature.f3d',
 'patchcontinuity-b9b0be85a281/brep_free.f3d',
 'patchcontinuity-b9b0be85a281/brep_tangent.f3d',
 'variablefillets-a5080b076434/endpoint_only_control.f3d',
 'variablefillets-a5080b076434/one_quarter.f3d',
 'variablefillets-a5080b076434/one_three_quarters.f3d',
 'variablefillets-a5080b076434/two_intermediates.f3d')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def restore(value,old,keys):
    for key in keys:
        if key in old:value[key]=copy.deepcopy(old[key])
        else:value.pop(key,None)


def evidence():
    reports={name:json.loads((ROOT/name).read_text()) for name in REPORTS}
    mesh={s['archive']:s['expected_decoded'] for s in reports[REPORTS[0]]['samples']}
    surfaces={};curves={};uv={};surface_faces={};curve_parents={};uv_parents={}
    for sample in reports[REPORTS[1]]['samples']:
        key=(sample['archive'],sample['member'],sample['record_index'])
        assert key not in surfaces;surfaces[key]=sample['expected_cache']
        surface_faces[key]={row['face_index'] for row in sample['explicit_parent_boundary_checks']}
        assert len(surface_faces[key])==1
    for sample in reports[REPORTS[2]]['samples']:
        key=(sample['archive'],sample['member'],sample['curve_record_index'])
        assert key not in curves;curves[key]=sample['expected_cache'];curve_parents[key]=sample['typed_parent_chain']
        key=(sample['archive'],sample['member'],sample['pcurve_record_index'])
        assert key not in uv;uv[key]=sample['expected_pcurve'];uv_parents[key]=sample['typed_parent_chain']
    assert len(mesh)==3 and len(surfaces)==3 and len(curves)==len(uv)==4
    downstream={row['archive']:row for row in reports[REPORTS[3]]['samples']}
    assert len(downstream)==3 and set(downstream)=={key[0] for key in surfaces}
    return dict(reports=reports,mesh=mesh,surfaces=surfaces,curves=curves,uv=uv,downstream=downstream,surface_faces=surface_faces,curve_parents=curve_parents,uv_parents=uv_parents)


def strip_mesh(prior,stream,filename,golden):
    assert stream['historical_mesh_face_groups']==golden
    features={f['object_id']:f for f in stream['features']};old={f['object_id']:f for f in prior['features']}
    assert features.keys()==old.keys();changed=set()
    for row in golden['decoded']:
        identity=row['feature_object_id'];feature=features[identity];before=old[identity]
        assert before['kind']=='UnsupportedFeature' and feature['kind']==row['kind']=='MeshGenerateFaceGroups'
        assert feature['class_guid']==before['class_guid']=='CA2AE956-FD81-4EBD-A601-F93A0F335722'
        assert feature.get('name')==before.get('name')==row['name']
        assert feature['tool_settings']==row['settings'] and feature['historical_mesh_face_group_route']==row['route']
        assert feature['decode_level']==LEVEL
        assert row['settings']['stored_feature_asset_is_current'] is False and 'current_mesh_asset' not in row['settings']
        assert row['route']['stored_feature_asset_object_id']!=row['route']['selected_current_asset_object_id']
        restore(feature,before,('kind','tool_settings','historical_mesh_face_group_route','decode_level'))
        entry=dict(object_id=identity,kind=row['kind'])
        assert entry not in prior['tool_decoding']['decoded'] and stream['tool_decoding']['decoded'].count(entry)==1
        stream['tool_decoding']['decoded'].remove(entry);changed.add(identity)
    assert not golden['unresolved'] and len(changed)==1
    original=prior['mesh_face_groups'];expected=copy.deepcopy(original)
    removed=[r for r in original['unresolved'] if r['feature_object_id'] in changed and r['reason']==OLD_REASON]
    assert len(removed)==len(changed)
    expected['unresolved']=[r for r in original['unresolved'] if r not in removed]
    assert stream['mesh_face_groups']==expected and 'mesh_face_groups' in stream
    restore(stream,prior,('mesh_face_groups','historical_mesh_face_groups'))
    discovery,old_discovery=stream['feature_discovery'],prior['feature_discovery']
    counter='class_decoded_historical_mesh_face_group_count';assert discovery[counter]==len(changed)
    unsupported=[r for r in old_discovery['unsupported_features'] if r['object_id'] not in changed]
    assert discovery['unsupported_features']==unsupported and discovery['unsupported_feature_count']==len(unsupported)
    assert {r['object_id'] for r in old_discovery['unsupported_features']}-{r['object_id'] for r in unsupported}==changed
    restore(discovery,old_discovery,(counter,'unsupported_features','unsupported_feature_count'))
    def strip_entry(entry):
        if entry['object_id'] in changed:
            assert entry['kind']=='MeshGenerateFaceGroups';entry['kind']=old[entry['object_id']]['kind']
        for child in entry.get('children',[]):strip_entry(child)
    for sequence in stream['timeline_decoding']['sequences']:
        for entry in sequence['visible_entries']:strip_entry(entry)
    return len(changed)


def strip_geometry(before,after,filename,proof):
    counts=dict(surface_cache_rows=0,curve_cache_rows=0,uv_cache_rows=0,removed_geometry_diagnostics=0)
    old_streams={s['member']:s for s in before['asm_decoding']['streams']}
    streams={s['member']:s for s in after['asm_decoding']['streams']}
    assert streams.keys()==old_streams.keys()
    matched=set()
    for member,stream in streams.items():
        previous=old_streams[member];prior=previous['topology'];topology=stream['topology']
        graphs={g['body_index']:g for g in topology['body_graphs']};old_graphs={g['body_index']:g for g in prior['body_graphs']}
        assert graphs.keys()==old_graphs.keys()
        new_surfaces=set();new_curves=set();new_uv=set()
        for body_id,graph in graphs.items():
            original=old_graphs[body_id]
            for field,index_key,kind,mapping in (('spline_surfaces','surface_index','surface',proof['surfaces']),('spline_curves','curve_index','curve',proof['curves'])):
                old_rows={r[index_key]:r for r in original[field]}
                actual_rows={r[index_key]:r for r in graph[field]}
                # Multiple edges can share a curve; qualify each full row while
                # retaining the native edge/face index, rather than choosing by geometry.
                assert set(old_rows)<=set(actual_rows)
                for old_row in original[field]:assert old_row in graph[field]
                for row in graph[field]:
                    if row in original[field]:continue
                    identity=row[index_key];key=(filename,member,identity)
                    assert key in mapping and row['cache']==mapping[key],(filename,member,kind,identity,'cache golden')
                    assert identity not in old_rows
                    if kind=='surface':
                        assert set(row)=={'face_index','surface_index','cache'} and row['face_index'] in original['face_indices'] and row['face_index'] in proof['surface_faces'][key];new_surfaces.add(identity)
                        assert any(a['face_index']==row['face_index'] and a['surface_index']==identity for a in original['analytic_surfaces'])
                        counts['surface_cache_rows']+=1
                    else:
                        assert set(row)=={'edge_index','curve_index','cache'} and row['edge_index'] in original['edge_indices']
                        assert row['edge_index']==proof['curve_parents'][key]['edge']['index'] and identity==proof['curve_parents'][key]['edge']['curve_index']
                        new_curves.add(identity);counts['curve_cache_rows']+=1
                    matched.add((kind,key))
                graph[field]=copy.deepcopy(original[field])
            for old_surface,surface in zip(original['analytic_surfaces'],graph['analytic_surfaces']):
                if surface!=old_surface:
                    assert surface['surface_index'] in new_surfaces
                    assert old_surface['geometry'] is surface['geometry'] is None
                    assert old_surface['geometry_status']=='Surface geometry schema unresolved'
                    assert surface['geometry_status']=='Cached spline surface decoded separately'
                    restore(surface,old_surface,('geometry_status',))
            assert len(graph['analytic_surfaces'])==len(original['analytic_surfaces'])
            assert len(graph['face_trim_loops'])==len(original['face_trim_loops'])
            for old_loop,loop in zip(original['face_trim_loops'],graph['face_trim_loops']):
                assert len(loop['trims'])==len(old_loop['trims']);uv_changed=False
                for old_trim,trim in zip(old_loop['trims'],loop['trims']):
                    if trim['uv_curve']==old_trim['uv_curve']:continue
                    key=(filename,member,trim['pcurve_index'])
                    assert old_trim['uv_curve'] is None and trim['uv_curve'] is not None and key in proof['uv'] and trim['uv_curve']==proof['uv'][key]
                    assert trim['pcurve_index'] in original['pcurve_indices']
                    parent=proof['uv_parents'][key]
                    assert trim['coedge_index']==parent['coedge']['index'] and trim['edge_index']==parent['edge']['index']
                    assert loop['loop_index']==parent['loop']['index'] and loop['face_index']==parent['face']['index'] and loop['surface_index']==parent['face']['surface_index']
                    new_uv.add(trim['pcurve_index']);matched.add(('uv',key));counts['uv_cache_rows']+=1;uv_changed=True
                    restore(trim,old_trim,('uv_curve',))
                if loop['uv_endpoints_close_in_this_chart']!=old_loop['uv_endpoints_close_in_this_chart']:
                    # Reconstruct from the report-qualified UV dictionaries,
                    # with the same documented endpoint-only closure criterion.
                    assert uv_changed and old_loop['uv_endpoints_close_in_this_chart'] is None
                    curves=[proof['uv'].get((filename,member,t['pcurve_index']),t['uv_curve']) for t in old_loop['trims']]
                    assert all(c is not None for c in curves)
                    closed=all(all(math.isclose(x,y,abs_tol=1e-8) for x,y in zip(a['control_points_uv'][-1],b['control_points_uv'][0])) for a,b in zip(curves,curves[1:]+curves[:1]))
                    assert loop['uv_endpoints_close_in_this_chart']==closed
                    restore(loop,old_loop,('uv_endpoints_close_in_this_chart',))
        expected=[]
        for rejection in prior['unresolved']:
            kind,index=rejection.get('kind'),rejection.get('index')
            qualified=(kind=='spline-surface' and index in new_surfaces) or (kind=='intcurve-curve' and index in new_curves) or (kind=='pcurve' and index in new_uv)
            if qualified:
                expected_reason={'spline-surface':'Rule blend fallback requires captured unbounded spine','intcurve-curve':'Unsupported procedural cache field 10','pcurve':'Compact pcurve parent XYZ/UV caches unresolved'}[kind]
                assert rejection['reason']==expected_reason
                counts['removed_geometry_diagnostics']+=1
            else:expected.append(rejection)
        assert topology['unresolved']==expected,(filename,member,'Unexpected geometry rejection change')
        topology['unresolved']=copy.deepcopy(prior['unresolved'])
    expected_matches={(kind,key) for kind,mapping in (('surface',proof['surfaces']),('curve',proof['curves']),('uv',proof['uv'])) for key in mapping if key[0]==filename}
    assert matched==expected_matches,(filename,'Missing or extra public cache golden',matched^expected_matches)
    return counts


def strip_downstream(before,after,filename,proof):
    golden=proof['downstream'][filename]
    matched=0
    for prior,stream in zip(before['streams'],after['streams']):
        assert stream['member']==prior['member']
        profile=golden['expected_profile_cache_correspondences']
        if stream.get('profile_cache_correspondences')!=profile:continue
        old_profile=prior['profile_cache_correspondences']
        assert len(profile['decoded'])==1 and not profile['unresolved'] and not old_profile['decoded']
        row=profile['decoded'][0];identity=row['source_feature_object_id']
        assert old_profile['unresolved']==[dict(source_feature_object_id=identity,reason='Profile-cache initial typed topology incomplete')]
        assert old_profile['scope']==profile['scope']
        key=(filename,row['history_blob_member'],10)
        assert key in proof['surfaces'] and row['asm_body_index']==1
        current_feature=next(f for f in stream['features'] if f['object_id']==identity)
        old_feature=next(f for f in prior['features'] if f['object_id']==identity)
        assert current_feature['profile_cache_correspondences']==golden['expected_profile_feature_attachment']==[row]
        assert 'profile_cache_correspondences' not in old_feature
        restore(current_feature,old_feature,('profile_cache_correspondences',))
        selection=stream['selection_recipe_incidence'];old_selection=prior['selection_recipe_incidence']
        assert selection==golden['expected_selection_recipe_incidence']
        assert selection['associations']==old_selection['associations'] and selection['scope']==old_selection['scope']
        assert len(selection['unresolved'])==len(old_selection['unresolved'])==1
        previous=old_selection['unresolved'][0];current=selection['unresolved'][0]
        assert previous['descriptor_object_id']==current['descriptor_object_id']
        assert previous['reason']=='Incomplete cached initial BODY topology prevents incidence uniqueness' and previous['bounded_operand_evidence'] is None
        assert current['reason']=='Named source operands do not identify exactly one surviving initial-cache entity; historical state replay unresolved'
        operand=current['bounded_operand_evidence']
        assert operand['history_blob_member']==row['history_blob_member'] and operand['native_body_object_id']==row['native_body_object_id']
        assert operand['initial_incidence_candidate_record_indices']==[] and operand['payload_kind']=='edge_recipe_data'
        # Preserve descriptor identity and the unresolved selection, admitting
        # only a more complete bounded proof and its exact reason.
        restored=copy.deepcopy(current);restore(restored,previous,('reason','bounded_operand_evidence'));assert restored==previous
        restore(stream,prior,('profile_cache_correspondences','selection_recipe_incidence'));matched+=1
    assert matched==1
    return dict(profile_source_correspondences=1,refined_retained_selection_warnings=1)


def compare(before,current,filename,proof):
    after=copy.deepcopy(current);counts=dict(historical_mesh_features=0,profile_source_correspondences=0,refined_retained_selection_warnings=0)
    if filename in proof['mesh']:
        relevant=[]
        for previous,stream in zip(before['streams'],after['streams']):
            assert previous['member']==stream['member']
            if 'historical_mesh_face_groups' in stream:relevant.append((previous,stream))
        assert len(relevant)==1
        counts['historical_mesh_features']=strip_mesh(*relevant[0],filename,proof['mesh'][filename])
    if filename in proof['downstream']:
        counts.update(strip_downstream(before,after,filename,proof))
    counts.update(strip_geometry(before,after,filename,proof))
    assert after==before,(filename,'Unqualified main output change',differences(before,after))
    return dict(archive=filename,archive_sha256=sha(ROOT/filename),**counts,
        whole_output_exact_after_qualified_restoration=True,stored_placement_labels_and_all_unqualified_geometry_exact=True,
        baseline_output_sha256=canonical(before),current_output_sha256=canonical(current),qualified_difference_paths=differences(before,current))


def read_cache(path,side):
    value=json.loads(Path(path).read_text())
    if isinstance(value,list):return value
    assert value['baseline_commit']==BASELINE and value['files']==list(FILES)
    return value[side]


def validate(baseline_cache,current_cache):
    before=read_cache(baseline_cache,'before');current=read_cache(current_cache,'after')
    assert len(before)==len(current)==len(FILES)==193
    assert [v['file'] for v in before]==[str(ROOT/name) for name in FILES]==[v['file'] for v in current]
    proof=evidence();rows=[compare(a,b,name,proof) for a,b,name in zip(before,current,FILES)]
    keys=('historical_mesh_features','surface_cache_rows','curve_cache_rows','uv_cache_rows','removed_geometry_diagnostics','profile_source_correspondences','refined_retained_selection_warnings')
    summary={key:sum(row[key] for row in rows) for key in keys}
    assert summary['historical_mesh_features']==3 and summary['surface_cache_rows']==3 and summary['curve_cache_rows']==summary['uv_cache_rows']==4
    assert summary['profile_source_correspondences']==summary['refined_retained_selection_warnings']==3
    assert sum(a==b for a,b in zip(before,current))==185
    summary.update(saved_files=len(FILES),whole_unchanged_controls=sum(a==b for a,b in zip(before,current)),unexpected_changes=0,no_main_calls=True,no_live_calls=True)
    return dict(scope='Fixed193 saved-file cached main comparison; only report-qualified historical feature publication and stored geometry cache recoveries are restored before whole-output equality',baseline_commit=BASELINE,files=list(FILES),samples=rows,summary=summary,cache_sha256=dict(baseline=sha(baseline_cache),current=sha(current_cache)),evidence_sha256={n:sha(ROOT/n) for n in REPORTS},source_sha256={n:sha(ROOT/n) for n in ('validate_history_geometry_integration.py','decode_mesh_face_groups.py','decode_historical_mesh_face_groups.py','decode_interp_blend_cache.py','decode_closed_parameter_curve_cache.py','decode_profile_cache_correspondence.py','decode_selection_recipe_incidence.py','decode_bspline.py','decode_brep.py','decode_basics.py')},limitations=['Cached comparisons establish only these saved exports and exact qualified fields; they do not measure complete format coverage.','Stored cache approximations and explicit feature assets do not imply exact procedural reconstruction, persistent topology, current historical geometry or regeneration.','All unrelated warnings, raw ASM framing/namespaces, native topology structure, stored placement labels, selections and current mesh associations remain exact.'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--baseline-cache',default='/private/tmp/fusion-history-geometry-baseline.json');p.add_argument('--current-cache',default='/private/tmp/fusion-history-geometry-current.json');p.add_argument('--output',default='history-geometry-integration.json');a=p.parse_args()
    result=validate(a.baseline_cache,a.current_cache);Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],sort_keys=True))
