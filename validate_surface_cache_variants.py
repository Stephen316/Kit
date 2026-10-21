"""Independent stored-grid validation for the46 targeted surface variants."""

import argparse
from collections import Counter
import copy
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path

from asm_records import inspect_asm
from decode_bspline import decode_bspline, evaluate_surface
from decode_surface_cache_variants import decode_surface_cache_variants
from fusion_archive import read_members
from validate_fillet_spline_caches import OLD_CACHE_HASHES

ROOT = Path(__file__).resolve().parent


def raw_grid(record, start):
    """Read independent raw U-fast tensor arrays at the saved typed header."""
    t = record['tokens']
    rational = t[start]['value'] == 'nurbs'
    assert t[start]['kind'] == 'entity_name' and t[start]['value'] in ('nubs', 'nurbs')
    du, dv = t[start+1]['value'], t[start+2]['value']
    assert t[start+1]['kind'] == t[start+2]['kind'] == 'integer'
    header = start+3+int(rational)
    if rational:
        assert t[start+3]['value'] == 'both'
    cursor = header+6
    knots, pairs = [], []
    for count_field, degree in ((header+4, du), (header+5, dv)):
        compact = []
        for _ in range(t[count_field]['value']):
            assert t[cursor]['kind'] == 'double' and t[cursor+1]['kind'] == 'integer'
            compact.append([t[cursor]['value'], t[cursor+1]['value']])
            cursor += 2
        expanded = [v for v, count in compact for _ in range(count)]
        full = [expanded[0]]+expanded+[expanded[-1]]
        assert full[:degree+1] == [full[0]]*(degree+1) and full[-degree-1:] == [full[-1]]*(degree+1)
        knots.append(full); pairs.append(compact)
    ku, kv = knots
    nu, nv = len(ku)-du-1, len(kv)-dv-1
    stride = 4 if rational else 3
    control_start = cursor
    flat = [t[cursor+i]['value'] for i in range(stride*nu*nv)]
    assert all(t[cursor+i]['kind'] == 'double' for i in range(len(flat)))
    return {'du': du, 'dv': dv, 'ku': ku, 'kv': kv, 'nu': nu, 'nv': nv,
            'points': [flat[i:i+3] for i in range(0, len(flat), stride)],
            'weights': flat[3::4] if rational else [1.]*(nu*nv),
            'control_token_start': control_start, 'grid_end': cursor+len(flat), 'header': header}


def cox_basis(knots, degree, count, parameter):
    """Independent Cox-de Boor basis recursion, not the reader's de Boor evaluator."""
    assert knots[degree] <= parameter <= knots[-degree-1]
    if parameter == knots[-degree-1]:
        return [0.]*(count-1)+[1.]
    @lru_cache(None)
    def value(i, order):
        if order == 0:
            return float(knots[i] <= parameter < knots[i+1])
        left_span = knots[i+order]-knots[i]
        right_span = knots[i+order+1]-knots[i+1]
        left = (parameter-knots[i])/left_span*value(i, order-1) if left_span else 0.
        right = (knots[i+order+1]-parameter)/right_span*value(i+1, order-1) if right_span else 0.
        return left+right
    result = [value(i, degree) for i in range(count)]
    assert math.isclose(sum(result), 1., abs_tol=1e-12)
    return result


def independent_surface(grid, u, v):
    bu = cox_basis(grid['ku'], grid['du'], grid['nu'], u)
    bv = cox_basis(grid['kv'], grid['dv'], grid['nv'], v)
    values, denominator = [0., 0., 0.], 0.
    # Read source U-fast controls directly; do not reuse normalized cache order.
    for row in range(grid['nv']):
        for col in range(grid['nu']):
            index = row*grid['nu']+col
            factor = bu[col]*bv[row]*grid['weights'][index]
            denominator += factor
            for axis in range(3):
                values[axis] += factor*grid['points'][index][axis]
    assert denominator > 0 and math.isfinite(denominator)
    return [value/denominator for value in values]


def validate(zstd_library):
    contexts = {}
    def load(relative):
        if relative not in contexts:
            contexts[relative] = {member: inspect_asm(raw) for member, raw in read_members(ROOT / relative, zstd_library).items()
                                  if member.endswith(('.smb', '.smbh'))}
        return contexts[relative]
    report = {'scope': 'Exactly46 saved baseline target records across23 explicit archives; tensor caches only, not complete procedural surface interpretation or a full corpus audit',
              'integration': {'reader': 'decode_surface_cache_variants.decode_surface_cache_variants(record)',
                              'dispatch': 'Existing base-first decode_bspline fallback; all46 targets match the helper result exactly',
                              'validator': '/usr/bin/python3 validate_surface_cache_variants.py',
                              'reader_changes_by_this_task': False},
              'method': 'Independently read raw U-fast controls/weights and compact knots from exact saved record headers; independently expand knots; evaluate Cox-de Boor tensor basis and compare with normalized-grid de Boor evaluator at three interior U/V pairs.',
              'files_inspected': sorted({target[0] for target in TARGETS}),
              'records': [], 'closed_surface_seams': [], 'old_output_controls': [], 'guards': [],
              'limitations': ['Procedural loft prefix and centerline-loft post-cache fields remain explicitly opaque, bounded source tokens. Passing grid validation does not decode their construction semantics.',
                              'All evaluations remain inside each stored clamped U/V domain. Literal axis flags are not interpreted as periodic extension or parameter remapping rules.',
                              'Independent evaluator agreement validates the explicit tensor cache; no exact loft geometry or global approximation-error bound is claimed.',
                              'The API isClosed getter corroborates one closed-loft capture. Seam coincidence is stored-cache evidence, not an API surface-evaluator comparison.',
                              'Finite exact-surface optional bounds remain literal stored fields; trim topology and active/final lifecycle are not inferred.',
                              'Body/component placement, assembly solving, exact procedural regeneration and a native writer remain outside this report.']}
    sources, grids, caches = [], [], []
    seam_errors = []
    for relative, member, index, start, expected_flags in TARGETS:
        source = load(relative)[member]['records'][index]
        cache = decode_surface_cache_variants(source)
        assert decode_bspline(source) == cache
        grid = raw_grid(source, start)
        assert cache['stored_axis_flags'] == expected_flags
        assert cache['knots_u'] == grid['ku'] and cache['knots_v'] == grid['kv']
        assert (cache['degree_u'], cache['degree_v'], cache['control_count_u'], cache['control_count_v']) == (grid['du'], grid['dv'], grid['nu'], grid['nv'])
        sources.append(source); grids.append(grid); caches.append(cache)
        ua, ub = cache['parameter_domain_u']; va, vb = cache['parameter_domain_v']
        tests = []
        for fu, fv in ((.2, .3), (.5, .5), (.8, .7)):
            u, v = ua+(ub-ua)*fu, va+(vb-va)*fv
            independent = independent_surface(grid, u, v)
            actual = evaluate_surface(cache, u, v)
            error = math.dist(actual, independent)
            assert error < 1e-10 and all(math.isfinite(p) for p in actual+independent)
            tests.append({'u': u, 'v': v, 'independent_raw_point': independent, 'reader_raw_point': actual, 'error_raw': error})
        root_one_dimensional_headers = 0
        depth = 0
        for i, token in enumerate(source['tokens']):
            depth += int(token['kind'] == 'subtype_start')-int(token['kind'] == 'subtype_end')
            if (depth == 1 and token['kind'] == 'entity_name' and token['value'] in ('nubs', 'nurbs')
                    and [t['kind'] for t in source['tokens'][i+1:i+3]] == ['integer', 'enum']):
                root_one_dimensional_headers += 1
        report['records'].append({'file': relative, 'member': member, 'record_index': index,
                                  'procedural_subtype': cache['procedural_subtype'], 'axis_flags': expected_flags,
                                  'grid_start_token': start, 'grid_degrees': [grid['du'], grid['dv']],
                                  'grid_counts': [grid['nu'], grid['nv']], 'rational': cache['is_rational'],
                                  'domain_u': cache['parameter_domain_u'], 'domain_v': cache['parameter_domain_v'],
                                  'outer_flags': cache['stored_outer_interval_flags'],
                                  'stored_outer_u_bounds': cache['stored_parameter_interval_u'],
                                  'stored_outer_v_bounds': cache['stored_parameter_interval_v'],
                                  'stored_inner_flags': cache['stored_inner_optional_flags'],
                                  'stored_inner_values': cache['stored_inner_optional_values'],
                                  'opaque_prefix_token_count': len(cache['stored_uninterpreted_prefix_fields']),
                                  'opaque_post_cache_token_count': len(cache['stored_uninterpreted_post_cache_fields']),
                                  'opaque_status': cache['procedural_definition_status'],
                                  'root_level_one_dimensional_headers_kept_separate': root_one_dimensional_headers,
                                  'independent_tensor_checks': tests})
        if relative.endswith('/closure_closed_surface.f3d'):
            truth = json.loads((ROOT / Path(relative).parent / 'ground_truth.json').read_text())
            api = next(s for s in truth['samples'] if s['file'] == 'closure_closed_surface.f3d')['settings']
            assert api['is_closed'] is True and api['is_solid'] is False
            u_errors = [math.dist(evaluate_surface(cache, ua, va+(vb-va)*f), evaluate_surface(cache, ub, va+(vb-va)*f)) for f in (.1, .5, .9)]
            v_errors = [math.dist(evaluate_surface(cache, ua+(ub-ua)*f, va), evaluate_surface(cache, ua+(ub-ua)*f, vb)) for f in (.1, .5, .9)]
            assert max(u_errors+v_errors) < 1e-10
            seam_errors.extend(u_errors+v_errors)
            report['closed_surface_seams'].append({'file': relative, 'member': member, 'record_index': index,
                                                  'actual_api_is_closed': api['is_closed'], 'actual_api_is_solid': api['is_solid'],
                                                  'three_u_boundary_seam_errors_raw': u_errors, 'three_v_boundary_seam_errors_raw': v_errors,
                                                  'scope': 'Stored domain boundary coincidence corroborates this closed capture; no periodic extension or API evaluator identity inferred'})
    counts = Counter(c['procedural_subtype'] for c in caches)
    assert counts == {'loft_spl_sur': 34, 'cl_loft_spl_sur': 10, 'exact_spl_sur': 2}
    assert len(report['files_inspected']) == 23 and len(TARGETS) == 46
    for control in [next(c for c in OLD_CACHE_HASHES if c['file'].startswith('moretools') and c['index'] == 18),
                    next(c for c in OLD_CACHE_HASHES if c['file'].startswith('splinepatches') and c['index'] == 11),
                    next(c for c in OLD_CACHE_HASHES if c['file'].startswith('splines') and c['index'] == 18)]:
        record = load(control['file'])[control['member']]['records'][control['index']]
        actual_hash = hashlib.sha256(json.dumps(decode_bspline(record), sort_keys=True).encode()).hexdigest()
        assert actual_hash == control['sha256']
        report['old_output_controls'].append(dict(control, exact_previous_dictionary_unchanged=True))
    base, grid = sources[0], grids[0]
    def reject(label, source, mutate):
        changed = copy.deepcopy(source); mutate(changed['tokens'])
        try:
            decode_surface_cache_variants(changed)
        except (ValueError, IndexError) as error:
            report['guards'].append({'case': label, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError('Malformed surface variant accepted: '+label)
    start = TARGETS[0][3]; header = grid['header']
    reject('Ambiguous second root-level tensor header', base, lambda t: t.__setitem__(slice(start, start), copy.deepcopy(t[start:header+6])))
    reject('Compact knot multiplicity exceeds degree', base, lambda t: t[header+7].update(value=grid['du']+1))
    reject('Non-increasing compact knots', base, lambda t: t[header+8].update(value=t[header+6]['value']))
    reject('Nonfinite grid coordinate', base, lambda t: t[grid['control_token_start']].update(value=float('nan')))
    reject('Missing final outer bound field', base, lambda t: t.pop())
    reject('Unsupported axis-flag combination', base, lambda t: t[header].update(value=9))
    report['summary'] = {'target_records': len(TARGETS), 'saved_archives': len(report['files_inspected']),
                         'loft_spl_sur': counts['loft_spl_sur'], 'cl_loft_spl_sur': counts['cl_loft_spl_sur'],
                         'finite_bound_exact_spl_sur': counts['exact_spl_sur'],
                         'independent_tensor_evaluations': 3*len(TARGETS),
                         'maximum_independent_tensor_error_raw': max(t['error_raw'] for r in report['records'] for t in r['independent_tensor_checks']),
                         'closed_capture_cache_records': len(report['closed_surface_seams']), 'seam_checks': len(seam_errors),
                         'maximum_sampled_seam_error_raw': max(seam_errors),
                         'opaque_prefix_records': sum(bool(c['stored_uninterpreted_prefix_fields']) for c in caches),
                         'opaque_centerline_tail_records': sum(bool(c['stored_uninterpreted_post_cache_fields']) for c in caches),
                         'one_dimensional_headers_disambiguated': sum(r['root_level_one_dimensional_headers_kept_separate'] for r in report['records']),
                         'old_outputs_unchanged': len(report['old_output_controls']), 'malformed_guards': len(report['guards'])}
    return report


# Durable explicit target inventory copied from the saved family-only manifest.
TARGETS = [('loftfaces-055501f619c5/edge_path_tangent_weight2.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.3242f52d-d38a-4e17-b850-75852f4b371f.smbh',
  40,
  180,
  [2, 0, 0, 0]),
 ('loftfaces-055501f619c5/edge_path_tangent_weight2.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.ce2494d9-53e9-48b7-a07e-864c45db24c6.smb',
  82,
  180,
  [2, 0, 0, 0]),
 ('loftfaces-055501f619c5/edge_path_tangent_weight1.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.e99864a3-8092-4726-9203-714c612875f1.smb',
  82,
  180,
  [2, 0, 0, 0]),
 ('loftfaces-055501f619c5/edge_path_tangent_weight1.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.1dd5bd82-a356-40f5-b16e-1022bb0b37a6.smbh',
  40,
  180,
  [2, 0, 0, 0]),
 ('loftfaces-055501f619c5/edge_path_smooth_weight1.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.10044360-fa95-4241-ba20-395972bdb7fa.smb',
  82,
  420,
  [2, 0, 0, 0]),
 ('loftfaces-055501f619c5/edge_path_smooth_weight1.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.9b4d8d65-d32d-41ab-8034-b6da2c2d900a.smbh',
  40,
  420,
  [2, 0, 0, 0]),
 ('loftpointholdouts-35b5ac0d2f42/tangent_start_weight2.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.21ce2a1b-db1c-4536-8ebe-f8e58a175b7c.smbh',
  13,
  214,
  [2, 0, 0, 1]),
 ('loftpointholdouts-35b5ac0d2f42/tangent_start_weight2.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.077fa8eb-edaf-42b2-9eda-12fb6c24871b.smb',
  24,
  214,
  [2, 0, 0, 1]),
 ('loftcurvedguides-79a1266af54e/bowed_arc_rail.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.34f2b055-35c0-41df-8190-679502aaa921.smbh',
  18,
  232,
  [2, 0, 0, 0]),
 ('loftcurvedguides-79a1266af54e/bowed_arc_rail.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.95e73f51-3670-40ec-b728-a0e997e50ece.smb',
  45,
  232,
  [2, 0, 0, 0]),
 ('loftcurvedguides-79a1266af54e/quarter_arc_centerline.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.2e5141dd-e82e-4393-8b60-8016e015825a.smbh',
  18,
  8,
  [2, 0, 0, 0]),
 ('loftcurvedguides-79a1266af54e/quarter_arc_centerline.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.062efdaa-c5f2-4199-b4be-00effcba8ec7.smb',
  45,
  8,
  [2, 0, 0, 0]),
 ('solidsweeps-7d2677669e3d/solid_twist.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.dd4e60ad-b3a3-4f7d-a558-0afa7b5b531f.smb',
  142,
  8,
  [0, 0, 0, 0]),
 ('solidsweeps-7d2677669e3d/solid_twist.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.eb60ba60-41c6-457e-90d9-abbbf3544872.smbh',
  110,
  8,
  [0, 0, 0, 0]),
 ('loftpointholdouts-bb91509a13e4/tangent_start_weight1.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.5ffb5051-cea2-4bb0-b434-e6a0020292a7.smbh',
  13,
  214,
  [2, 0, 0, 1]),
 ('loftpointholdouts-bb91509a13e4/tangent_start_weight1.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.9b05fd42-bef6-4239-b3e5-079942b16f8c.smb',
  24,
  214,
  [2, 0, 0, 1]),
 ('loftbrepends-e07e3859ed20/edge_end_smooth_weight1_25.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.80cb298d-8ed8-4cf0-944c-0156a247260c.smbh',
  41,
  420,
  [2, 0, 0, 0]),
 ('loftbrepends-e07e3859ed20/edge_end_smooth_weight1_25.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.ac252160-149a-43db-a358-680b534e2a37.smb',
  83,
  420,
  [2, 0, 0, 0]),
 ('loftbrepends-e07e3859ed20/edge_end_tangent_weight1_5.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.e006f0f6-0574-4be8-bc64-55e9a22e2c25.smbh',
  41,
  180,
  [2, 0, 0, 0]),
 ('loftbrepends-e07e3859ed20/edge_end_tangent_weight1_5.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.c2deb29b-10fc-4229-8db8-9f3ef40b20b1.smb',
  83,
  180,
  [2, 0, 0, 0]),
 ('loftbrepends-e07e3859ed20/edge_both_tangent.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.52d1f5c3-fe81-4cc6-83f9-728fea894ddc.smbh',
  63,
  194,
  [2, 0, 0, 0]),
 ('loftbrepends-e07e3859ed20/edge_both_tangent.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.7a6b2b33-65bb-445c-a3a7-a09d8d107412.smb',
  120,
  194,
  [2, 0, 0, 0]),
 ('lofts-838ea6e83e97/both_direction.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.492cf2b2-c8cb-4db1-afdd-2025f403d468.smbh',
  18,
  166,
  [2, 0, 0, 0]),
 ('lofts-838ea6e83e97/both_direction.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.46cdd2fa-63f3-45e7-a81e-206aa3411857.smb',
  45,
  166,
  [2, 0, 0, 0]),
 ('loftguides-265bcb9af34a/closure_closed_surface.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.33aa6335-937f-44ff-a677-65a3ea2c9740.smbh',
  9,
  159,
  [2, 2, 0, 0]),
 ('loftguides-265bcb9af34a/closure_closed_surface.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.cc0e173c-4b68-42d3-b62a-448a58dad988.smb',
  43,
  159,
  [2, 2, 0, 0]),
 ('lofts-838ea6e83e97/start_direction.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.2394c3ef-74a0-4582-b800-9ce6fd29d7e5.smbh',
  18,
  166,
  [2, 0, 0, 0]),
 ('lofts-838ea6e83e97/start_direction.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.37994eeb-d006-457b-a3cf-9daf10f86479.smb',
  45,
  166,
  [2, 0, 0, 0]),
 ('lofts-838ea6e83e97/end_direction.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.7850f30c-499c-41f6-bdaf-22d00cb6ed40.smb',
  45,
  166,
  [2, 0, 0, 0]),
 ('lofts-838ea6e83e97/end_direction.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.2c056323-51a9-4496-a31c-a436de835092.smbh',
  18,
  166,
  [2, 0, 0, 0]),
 ('loftguides-265bcb9af34a/closure_closed_four.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.dcbf4aea-1380-43ad-98ba-73fb133aac46.smb',
  43,
  159,
  [2, 2, 0, 0]),
 ('loftguides-265bcb9af34a/closure_closed_four.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.47c60f73-5616-4c29-a53f-f0aef09585ef.smbh',
  9,
  159,
  [2, 2, 0, 0]),
 ('lofts-03b4a6f1ce2f/centerline.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.e2ec8122-563c-47cf-968b-14496c44119c.smbh',
  18,
  8,
  [2, 0, 0, 0]),
 ('lofts-03b4a6f1ce2f/centerline.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.22eccd34-b570-4a79-90eb-0023728adc78.smb',
  45,
  8,
  [2, 0, 0, 0]),
 ('loftpoints-f5bbdb97a568/tangent_end_weight1.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.aa1fd46b-8b79-460f-a30c-ee035a2b4b44.smbh',
  13,
  214,
  [2, 0, 0, 2]),
 ('loftpoints-f5bbdb97a568/tangent_end_weight1.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.2db7b6a7-7683-4809-94cf-7431c9b46c05.smb',
  23,
  214,
  [2, 0, 0, 2]),
 ('loftpoints-f5bbdb97a568/tangent_end_weight2.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.eed66366-3d26-4b7b-819f-0bbede421953.smbh',
  13,
  214,
  [2, 0, 0, 2]),
 ('loftpoints-f5bbdb97a568/tangent_end_weight2.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.8c7b62ca-9c6b-4852-8db3-7f7f1ec6d10c.smb',
  23,
  214,
  [2, 0, 0, 2]),
 ('loftcompositeguides-8ea2ef593872/centerline_explicit_members.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.878357e8-9d52-4397-ad94-ea625a55a6b9.smb',
  46,
  8,
  [2, 0, 0, 0]),
 ('loftcompositeguides-8ea2ef593872/centerline_explicit_members.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.9f2e4887-6d0e-46e3-93eb-4dc837383fe5.smbh',
  18,
  8,
  [2, 0, 0, 0]),
 ('loftcompositeguides-8ea2ef593872/spline_centerline.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.8365b2b2-ff79-40a3-a63c-83757a8de310.smbh',
  18,
  8,
  [2, 0, 0, 0]),
 ('loftcompositeguides-8ea2ef593872/spline_centerline.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.f8b4ba04-eaad-4f8f-af5f-00d6e1dcb45b.smb',
  46,
  8,
  [2, 0, 0, 0]),
 ('loftcompositeguides-8ea2ef593872/centerline_connected_chain.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.aa2b7205-c25d-4838-9a74-4471f3574047.smb',
  46,
  8,
  [2, 0, 0, 0]),
 ('loftcompositeguides-8ea2ef593872/centerline_connected_chain.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.0c158dea-ab35-465e-8663-1711f71f27a8.smbh',
  18,
  8,
  [2, 0, 0, 0]),
 ('loftcompositeguides-8ea2ef593872/rail_line_arc.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.d7e7e11f-de01-4f69-bc3d-dd55b2e4beca.smbh',
  18,
  392,
  [2, 0, 0, 0]),
 ('loftcompositeguides-8ea2ef593872/rail_line_arc.f3d',
  'FusionAssetName[Active]/Breps.BlobParts/BREP.ec1ca2e2-b546-4123-9ebd-e858ac7946cd.smb',
  45,
  392,
  [2, 0, 0, 0])]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='surface-cache-variant-decoding.json')
    args = parser.parse_args()
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report = validate(str(zstd))
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
