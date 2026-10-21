"""VBL component-to-boundary cache correspondences, not VBL reconstruction.

Association requires a reciprocal face ring, literal plane-definition equality
or typed inline-surface namespace identity, and algebraic UV coefficient
equality after knot insertion and independent domain normalization. No sampled
point, nearest geometry, ordinal, or fitted curve chooses a boundary edge.
"""
import hashlib
import math
from collections import Counter

from decode_asm_subtypes import (decode_asm_subtypes, expand_asm_subtype_record,
                                 resolve_asm_subtype, _record_fingerprint)
from decode_bspline import evaluate_curve, evaluate_surface
from decode_parameter_curve_cache import decode_parameter_curve_cache
from decode_rule_blend_cache import decode_rule_blend_definition, decode_rule_blend_inline

SCOPE = ('Bounded VBL support/UV component correspondences to saved face-boundary caches; '
         'no VBL interior, persistent topology identity, native edge-parameter mapping or global approximation bound')


def _signature(tokens):
    return [(t['kind'], t['value']) for t in tokens]


def _expanded(record, catalog, records):
    return (expand_asm_subtype_record(record, catalog, records)['record']
            if record['tokens'][5]['value'] == 'ref' else record)


def _verify_host(record, catalog, blob):
    stored = catalog['record_fingerprints'].get(str(record['index']))
    if stored is not None:
        if stored != _record_fingerprint(record):
            raise ValueError('Stale VBL source/support namespace host')
        return
    # The subtype catalog fingerprints only bracket-containing hosts. Planes
    # have no bracket: validate their complete typed source record against blob
    # bytes rather than treating an absent catalog entry as either fresh/stale.
    from decode_pcurve_variants import encode_pcurve_fields
    if record['name'] != 'plane-surface':
        raise ValueError('VBL nonnamespace host has no admitted source replay')
    replay = b'\x0e\x05plane\x0d\x07surface'+encode_pcurve_fields(record['tokens'])+b'\x11'
    if replay != blob[record['offset']:record['end_offset']]:
        raise ValueError('Stale VBL plane host differs from original serialized record')


def _namespace(tokens, catalog, records):
    starts = [t for t in tokens if t['kind'] == 'subtype_start']
    if not starts:
        raise ValueError('VBL spline support has no explicit original subtype span')
    blocks = [b for b in catalog['blocks'] if b['byte_start'] == starts[0]['offset']]
    if len(blocks) != 1:
        raise ValueError('VBL support namespace span missing or ambiguous')
    block = blocks[0]
    proof = resolve_asm_subtype(catalog, block['record_index'], block['token_start'], expected_kind='surface')
    by = {r['index']: r for r in records}
    for index in {block['record_index'], proof['target_definition']['record_index']}:
        if catalog['record_fingerprints'].get(str(index)) != _record_fingerprint(by[index]):
            raise ValueError('Stale VBL support namespace host')
    return proof


def _support_identity(support, catalog, records):
    tokens = support['stored_definition']
    if support['kind'] == 'plane':
        return ('plane', _signature(tokens)), {'method': 'Exact complete serialized plane/support-bound fields',
                                             'scope': 'Definition equality only; no native persistent plane identity'}
    if support['kind'] == 'spline':
        proof = _namespace(tokens, catalog, records)
        return ('spline', proof['target_definition']['definition_index']), proof
    raise ValueError('Unobserved VBL component support kind')


def _insert_once(points, knots, degree, value):
    """One standard knot insertion on the full polynomial knot vector."""
    n = len(points)-1
    span = next((i for i in range(degree, n+1) if knots[i] <= value < knots[i+1]), None)
    if span is None:
        raise ValueError('VBL refinement knot outside interior domain')
    multiplicity = knots.count(value)
    if multiplicity >= degree:
        raise ValueError('VBL refinement would exceed interior multiplicity')
    result = [None]*(n+2)
    for i in range(span-degree+1):
        result[i] = points[i][:]
    for i in range(span-multiplicity, n+1):
        result[i+1] = points[i][:]
    for i in range(span-degree+1, span-multiplicity+1):
        denominator = knots[i+degree]-knots[i]
        if denominator <= 0:
            raise ValueError('Invalid VBL knot-insertion span')
        alpha = (value-knots[i])/denominator
        result[i] = [(1-alpha)*a+alpha*b for a, b in zip(points[i-1], points[i])]
    if any(p is None for p in result):
        raise ValueError('Incomplete VBL knot refinement')
    return result, knots[:span+1]+[value]+knots[span+1:]


def prove_uv_refinement(component, boundary):
    """Prove coefficient equality, without fitting or choosing by coordinates.

    Each independently stored domain is normalized to [0,1] solely for this
    polynomial comparison; the resulting affine map is not an edge evaluator.
    """
    degree = component['degree']
    if (degree != boundary['degree'] or degree not in (1, 5)
            or component['weights'] or boundary['weights']
            or component['is_rational'] or boundary['is_rational']):
        raise ValueError('VBL UV refinement requires equal observed polynomial degrees')
    def normalize(cache):
        a, b = cache['parameter_domain']
        if not math.isfinite(a+b) or b <= a:
            raise ValueError('Invalid VBL UV parameter domain')
        points = cache['raw_control_points']
        if any(len(p) != 2 or any(not math.isfinite(x) for x in p) for p in points):
            raise ValueError('Invalid VBL UV control point')
        if len(cache['knots']) != len(points)+degree+1:
            raise ValueError('Inconsistent VBL UV knot/control counts')
        return [(x-a)/(b-a) for x in cache['knots']]
    target, source = normalize(component), normalize(boundary)
    if target != sorted(target) or source != sorted(source):
        raise ValueError('VBL UV knots not ordered')
    # The captured coefficient relation is exact knot refinement, not a degree
    # elevation, least-squares fit, tolerance-driven knot removal or sample fit.
    points = [p[:] for p in boundary['raw_control_points']]
    inserted = []
    target_counts, source_counts = Counter(target), Counter(source)
    if any(value not in target_counts or count > target_counts[value] for value, count in source_counts.items()):
        raise ValueError('Boundary UV knots are not a literal subset of normalized VBL knots')
    for value, count in sorted(target_counts.items()):
        for _ in range(count-source_counts[value]):
            points, source = _insert_once(points, source, degree, value)
            inserted.append(value)
    if source != target or len(points) != len(component['raw_control_points']):
        raise ValueError('VBL refined knot/control layout differs')
    maximum = max(abs(a-b) for p, q in zip(points, component['raw_control_points']) for a, b in zip(p, q))
    scale = max(1., *(abs(x) for p in component['raw_control_points'] for x in p))
    if maximum > 2e-12*scale:
        raise ValueError('VBL UV coefficients do not equal algebraic knot refinement')
    ca, cb = component['parameter_domain']; ba, bb = boundary['parameter_domain']
    return dict(method='Full polynomial coefficient equality after standard knot insertion and separate domain normalization',
                inserted_normalized_knots=inserted, degree=degree,
                boundary_control_count=len(boundary['raw_control_points']), component_control_count=len(points),
                maximum_coefficient_roundoff=maximum,
                component_parameter_domain=component['parameter_domain'], boundary_UV_parameter_domain=boundary['parameter_domain'],
                normalized_domain_parameter_map={'boundary_UV_scale': (bb-ba)/(cb-ca),
                                                 'boundary_UV_offset': ba-ca*(bb-ba)/(cb-ca)},
                scope='Algebraic relation between these stored UV polynomials only; not native edge or VBL interior parameterization')


def _face_ring(face, nodes):
    loop = nodes.get(face['first_loop_index'])
    if not loop or loop['kind'] != 'loop' or loop['face_index'] != face['index'] or loop['next_loop_index'] is not None:
        raise ValueError('VBL boundary requires one explicit reciprocal loop')
    result, current = [], loop['first_coedge_index']
    while current not in result:
        coedge = nodes.get(current)
        if not coedge or coedge['kind'] != 'coedge' or coedge['loop_index'] != loop['index'] or len(result) >= 6:
            raise ValueError('VBL boundary coedge ring not bounded to six')
        following = nodes.get(coedge['next_coedge_index'])
        previous = nodes.get(coedge['previous_coedge_index'])
        if (not following or not previous or following.get('previous_coedge_index') != current
                or previous.get('next_coedge_index') != current):
            raise ValueError('VBL coedge next/previous ownership not reciprocal')
        result.append(current); current = coedge['next_coedge_index']
    if current != loop['first_coedge_index'] or len(result) != 6:
        raise ValueError('VBL boundary ring does not close at its first coedge')
    return loop, [nodes[i] for i in result]


def _composition(support, catalog, records):
    if support['kind'] == 'plane':
        ts = support['stored_definition']
        if (len(ts) != 9 or ts[4]['value'] is not False or any(t['value'] for t in ts[5:])):
            raise ValueError('VBL plane composition requires captured false-sense unbounded plane')
        origin, normal, axis = [ts[i]['value'] for i in (1, 2, 3)]
        if any(not math.isclose(sum(x*x for x in v), 1., abs_tol=1e-10) for v in (normal, axis)) or not math.isclose(sum(a*b for a,b in zip(normal,axis)),0.,abs_tol=1e-10):
            raise ValueError('VBL plane frame not orthonormal')
        second = [normal[1]*axis[2]-normal[2]*axis[1],normal[2]*axis[0]-normal[0]*axis[2],normal[0]*axis[1]-normal[1]*axis[0]]
        return dict(kind='plane', raw_origin=origin, raw_axis_u=axis, raw_axis_v=second,
                    plane_frame_scope='Stored false-sense orthonormal frame; U=reference axis, V=normal cross U')
    proof = _namespace(support['stored_definition'], catalog, records)
    target = proof['target_definition']; by = {r['index']:r for r in records}
    host = by[target['record_index']]
    if target['subtype_name'] != 'srf_srf_v_bl_spl_sur':
        raise ValueError('VBL boundary support has no admitted evaluable blend patch')
    cache, end = decode_rule_blend_inline(host['tokens'], target['token_start']-1)
    if end <= target['token_end']:
        raise ValueError('VBL inline blend support did not consume its bounds')
    return dict(kind='stored_rational_blend_patch', stored_surface_cache=cache, namespace_proof=proof,
                scope='Evaluation of the separately stored rational approximation, not the exact procedural support')


def evaluate_vbl_component(component, parameter):
    """Evaluate an admitted component support(UV(t)) inside its stored domain."""
    uv = evaluate_curve(component['stored_uv_cache'], parameter)
    support = component['evaluable_support']
    if support['kind'] == 'plane':
        return [o+uv[0]*u+uv[1]*v for o,u,v in zip(support['raw_origin'], support['raw_axis_u'], support['raw_axis_v'])]
    if support['kind'] == 'stored_rational_blend_patch':
        return evaluate_surface(support['stored_surface_cache'], *uv)
    raise ValueError('Unadmitted VBL component support evaluator')


def decode_vbl_components(blob, *, parsed=None, subtype_catalog=None, topology=None):
    """Return strict bounded associations; keep VBL interior geometry unresolved."""
    from asm_records import inspect_asm
    if parsed is None: parsed = inspect_asm(blob)
    if subtype_catalog is None: subtype_catalog = decode_asm_subtypes(blob, parsed=parsed)
    if subtype_catalog['source_blob_sha256'] != hashlib.sha256(blob).hexdigest():
        raise ValueError('VBL namespace catalog belongs to another blob')
    if topology is None:
        from decode_brep import decode_topology
        topology = decode_topology(parsed, subtype_catalog=subtype_catalog)
    records = parsed['records']; by = {r['index']:r for r in records}
    nodes = {n['index']:n for n in topology['nodes']}
    result = dict(decoded=[], unresolved=[], scope=SCOPE)
    for original in records:
        if original['name'] != 'spline-surface': continue
        try: record = _expanded(original, subtype_catalog, records)
        except (ValueError, IndexError): continue
        if record['tokens'][5]['value'] != 'VBL_SURF': continue
        try:
            if subtype_catalog['record_fingerprints'].get(str(original['index'])) != _record_fingerprint(original):
                raise ValueError('Stale VBL source record')
            definition = decode_rule_blend_definition(record)
            faces = [n for n in nodes.values() if n['kind']=='face' and n['surface_index']==original['index']]
            if len(faces) != 1: raise ValueError('VBL surface must have one explicitly linked parent face')
            face = faces[0]; loop, ring = _face_ring(face, nodes)
            candidates = []
            for coedge in ring:
                edge = nodes.get(coedge['edge_index']); partner = nodes.get(coedge['partner_index'])
                if (not edge or edge['kind']!='edge' or not partner or partner['kind']!='coedge'
                        or partner['partner_index']!=coedge['index'] or partner['edge_index']!=edge['index']):
                    raise ValueError('VBL boundary edge/partner relationships not reciprocal')
                other_loop = nodes.get(partner['loop_index'])
                other_face = nodes.get(other_loop['face_index']) if other_loop and other_loop['kind']=='loop' else None
                if not other_face or other_face['kind']!='face' or other_face['index']==face['index']:
                    raise ValueError('VBL boundary adjacent face unresolved')
                curve = by.get(edge['curve_index'])
                if not curve or curve['name']!='intcurve-curve': raise ValueError('VBL boundary curve is not typed intcurve')
                if subtype_catalog['record_fingerprints'].get(str(curve['index'])) != _record_fingerprint(curve):
                    raise ValueError('Stale VBL boundary curve namespace host')
                expanded_curve = _expanded(curve, subtype_catalog, records)
                cache = decode_parameter_curve_cache(expanded_curve)
                identity, proof = _support_identity(cache['stored_support_definition'], subtype_catalog, records)
                adjacent_surface = by[other_face['surface_index']]
                _verify_host(adjacent_surface, subtype_catalog, blob)
                if identity[0]=='plane':
                    if adjacent_surface['name']!='plane-surface' or identity[1][1:]!=_signature(adjacent_surface['tokens'][3:]):
                        raise ValueError('VBL boundary plane support differs from typed adjacent-face plane')
                    adjacent_proof = dict(method='Exact serialized plane frame/bounds equality on typed adjacent face',
                                          surface_record_index=adjacent_surface['index'])
                else:
                    if adjacent_surface['name']!='spline-surface': raise ValueError('VBL adjacent surface is not typed spline')
                    adjacent_proof = _namespace(adjacent_surface['tokens'][3:], subtype_catalog, records)
                    if adjacent_proof['target_definition']['definition_index']!=identity[1]:
                        raise ValueError('VBL boundary support namespace differs from typed adjacent face')
                candidates.append((coedge,edge,partner,other_face,cache,identity,proof,adjacent_proof))
            components=[]
            for source in definition['components']:
                identity, proof = _support_identity(source['stored_support'], subtype_catalog, records)
                matches=[]
                for candidate in candidates:
                    if candidate[5]!=identity: continue
                    try: algebra=prove_uv_refinement(source['stored_uv_cache'],candidate[4]['stored_embedded_uv_cache'])
                    except (ValueError,IndexError): continue
                    matches.append((candidate,algebra))
                if len(matches)!=1: raise ValueError('VBL component support/coefficient association missing or ambiguous')
                (coedge,edge,partner,other_face,cache,_,curve_proof,adjacent_proof),algebra=matches[0]
                components.append(dict(slot=source['slot'], source_token_start=source['token_start'],source_token_end=source['token_end'],
                    stored_wrapper_flag=source['stored_wrapper_flag'], stored_direction_vector=source['stored_direction_vector'],
                    stored_terminal_flag=source['stored_terminal_flag'], stored_uv_cache=source['stored_uv_cache'],
                    support_identity_evidence=proof, boundary_curve_support_evidence=curve_proof,
                    adjacent_face_support_evidence=adjacent_proof, UV_coefficient_correspondence=algebra,
                    coedge_index=coedge['index'], partner_coedge_index=partner['index'], edge_index=edge['index'],
                    boundary_curve_index=edge['curve_index'], adjacent_face_index=other_face['index'],
                    parent_face_pcurve_index=coedge['pcurve_index'],
                    stored_native_edge_parameters=[edge['start_parameter'],edge['end_parameter']],
                    boundary_XYZ_cache=cache, evaluable_support=_composition(source['stored_support'],subtype_catalog,records),
                    evaluation_scope='Bounded stored support(UV(t)) component; native edge parameter map, VBL interior and exact procedural boundary unresolved'))
            if len({c['edge_index'] for c in components})!=6:
                raise ValueError('VBL six components do not correspond bijectively to six boundary edges')
            slots = [c['coedge_index'] for c in components]
            ring_ids = [c['index'] for c in ring]
            rotation = ring_ids.index(slots[0])
            if ring_ids[rotation:]+ring_ids[:rotation] != slots:
                raise ValueError('VBL component order does not agree with cyclic face-boundary order')
            result['decoded'].append(dict(surface_record_index=original['index'],face_index=face['index'],loop_index=loop['index'],
                stored_component_count=6, components=components,
                boundary_ring_coedge_indices=ring_ids, component_slot_coedge_indices=slots,
                cyclic_boundary_order={'component_order_equals_ring_after_rotation': True,'ring_rotation_offset': rotation,
                                       'scope':'Correspondence of explicit component slots to reciprocal coedge links; no coordinate-based ordering'},
                VBL_interior_geometry=None, scope=SCOPE))
        except (ValueError,IndexError,KeyError) as error:
            result['unresolved'].append(dict(surface_record_index=original['index'],reason=str(error)))
    return result
