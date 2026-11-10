"""Bounded compact UV seam offsets, without implicit periodic wrapping.

Reuse the existing typed topology/namespace proof on an offset-neutral view.
Only the captured two-chart circular sweep seam is admitted for nonzero shifts.
"""
import copy
import math
from collections import Counter

from decode_asm_subtypes import _record_fingerprint, resolve_asm_subtype
from decode_bspline import read_token
from decode_pcurve import evaluate_pcurve
from decode_pcurve_variants import decode_compact_pcurve, _finite, _header


def _endpoints(cache):
    return [evaluate_pcurve(cache, value) for value in cache['parameter_domain']]


def _incidence(caches):
    return Counter(tuple(point) for cache in caches for point in _endpoints(cache))


def decode_compact_pcurve_offsets(record, records, nodes, subtype_catalog):
    """Same interface as decode_compact_pcurve; zero shifts preserve its output.

    Nonzero admission requires literal source namespace identity, reciprocal seam
    partners, exact bounded chart coordinates and a four-segment closed UV chart.
    No cache samples or proximity criteria select a support or a shift.
    """
    tokens = _header(record)
    if len(tokens) != 7:
        raise ValueError('Unobserved compact offset field count')
    offset = [read_token(tokens, 5+i, 'double') for i in range(2)]
    _finite(offset)
    if offset == [0., 0.]:
        return decode_compact_pcurve(record, records, nodes, subtype_catalog)
    selector = read_token(tokens, 3, 'integer')
    if selector != -1 or offset != [-2*math.pi, 0.]:
        raise ValueError('Unobserved compact offset selector/vector')
    # This derived view is used only to reuse the strict support/topology proof.
    # Original fields, records, namespace allocations and byte origins stay intact.
    neutral = copy.deepcopy(record)
    for token in neutral['tokens'][5:]:
        token['value'] = 0.
    base = decode_compact_pcurve(neutral, records, nodes, subtype_catalog)
    surface = nodes[base['parent_surface_record_index']].get('bspline_surface', {})
    parent = nodes[base['stored_intcurve_record_pointer']].get('bspline_curve', {})
    if (parent.get('procedural_subtype') != 'par_int_cur' or base['degree'] != 1
            or len(base['raw_control_points_uv']) != 2 or base['stored_selected_support_slot'] != 0
            or surface.get('procedural_subtype') != 'sweep_sur'
            or surface.get('stored_sweep_mode_code') != 1
            or surface.get('stored_axis_flags') != [2, 0, 0, 0]
            or surface.get('stored_profile_description', {}).get('kind') != 'ellipse'
            or surface.get('stored_profile_bounds') != [-math.pi, math.pi]
            or surface.get('parameter_domain_u') != [-math.pi, math.pi]
            or surface.get('parameter_domain_v') != [0., 1.]):
        raise ValueError('Unobserved compact offset parent/cache chart layout')
    profile = surface['stored_profile_description']['token_fields']
    if len(profile) != 7 or read_token(profile, 4, 'double') != 1.:
        raise ValueError('Unobserved compact offset profile layout')
    raw = base['raw_control_points_uv']
    if raw != [[math.pi, 0.], [math.pi, 1.]] or base['parameter_domain'] != [0., 1.]:
        raise ValueError('Compact offset source is not the captured upper seam UV segment')
    coedge = nodes[base['owning_coedge_index']]
    partner = nodes.get(coedge['partner_index'])
    if (partner is None or partner.get('partner_index') != coedge['index']
            or partner.get('edge_index') != coedge['edge_index']
            or partner.get('loop_index') != coedge['loop_index']
            or coedge.get('is_reversed') is not True or partner.get('is_reversed') is not False):
        raise ValueError('Compact offset seam lacks captured reciprocal same-loop partner')
    partner_record = next((r for r in records if r['index'] == partner.get('pcurve_index')), None)
    if partner_record is None:
        raise ValueError('Compact offset partner pcurve absent')
    partner_cache = decode_compact_pcurve(partner_record, records, nodes, subtype_catalog)
    if (partner_cache['stored_prefix_integer'] != 1
            or partner_cache['stored_intcurve_record_pointer'] != base['stored_intcurve_record_pointer']
            or partner_cache['parent_face_index'] != base['parent_face_index']
            or partner_cache['selected_support_definition_index'] != base['selected_support_definition_index']
            or partner_cache['raw_control_points_uv'] != raw):
        raise ValueError('Compact offset partner does not repeat the same qualified upper seam')
    shifted = [[value+delta for value, delta in zip(point, offset)] for point in raw]
    result = dict(base, parameter_offset_uv=offset, control_points_uv=shifted)
    ring, current = [], nodes[base['parent_loop_index']]['first_coedge_index']
    while current not in ring:
        ring.append(current)
        current = nodes[current]['next_coedge_index']
    if len(ring) != 4:
        raise ValueError('Unobserved compact offset owning ring size')
    other, neighbor_proofs = [], []
    by_index = {r['index']: r for r in records}
    for index in ring:
        if index == coedge['index']:
            continue
        if index == partner['index']:
            cache = partner_cache
        else:
            node = nodes.get(nodes[index].get('pcurve_index'))
            cache = node.get('uv_curve') if node else None
        if cache is None:
            raise ValueError('Compact offset neighboring UV cache unresolved')
        if len(cache.get('control_points_uv', [])) != 2 or cache['degree'] != 1:
            raise ValueError('Unobserved compact offset neighboring UV segment')
        if index != partner['index']:
            pcurve_id = nodes[index]['pcurve_index']
            blocks = [b for b in subtype_catalog['blocks']
                      if b['record_index'] == pcurve_id and b['context_kind'] == 'surface']
            if len(blocks) != 1:
                raise ValueError('Compact offset neighbor lacks one explicit surface namespace block')
            proof = resolve_asm_subtype(subtype_catalog, pcurve_id, blocks[0]['token_start'], expected_kind='surface')
            for source_id in {pcurve_id, proof['target_definition']['record_index']}:
                source = by_index.get(source_id)
                if source is None or subtype_catalog['record_fingerprints'].get(str(source_id)) != _record_fingerprint(source):
                    raise ValueError('Compact offset neighbor namespace host is stale')
            if proof['target_definition']['definition_index'] != base['selected_support_definition_index']:
                raise ValueError('Compact offset neighbor uses a different support surface definition')
            neighbor_proofs.append({'coedge_index': index, 'pcurve_index': pcurve_id, 'namespace_proof': proof})
        other.append(cache)
    expected = {(u, v): 2 for u in (-math.pi, math.pi) for v in (0., 1.)}
    closed = _incidence(other+[result])
    dropped = _incidence(other+[base])
    if dict(closed) != expected or sorted(dropped.values()) != [1, 1, 3, 3]:
        raise ValueError('Compact offset does not close the literal four-corner UV chart')
    result.update(
        representation='Stored embedded UV cache plus literal compact offset; bounded circular sweep seam chart',
        coordinate_system='Qualified support UV chart; stored offsets are added directly without modulo or domain wrapping',
        compact_offset_evidence={
            'rule': 'control_points_uv = raw_control_points_uv + parameter_offset_uv',
            'qualification': 'Observed selector -1, [-2*pi,0] offset, par_int_cur support slot0, circular sweep U=[-pi,pi], V=[0,1] and reciprocal same-loop seam partner',
            'partner_coedge_index': partner['index'], 'partner_pcurve_index': partner_record['index'],
            'owning_ring_indices': ring, 'neighbor_support_namespaces': neighbor_proofs,
            'shifted_corner_incidence_counts': sorted(closed.values()),
            'offset_dropped_corner_incidence_counts': sorted(dropped.values()),
            'source_record_is_unchanged': True,
            'source_pcurve_record_index': record['index'], 'source_byte_offset': record['offset'],
            'stored_offset_tokens': copy.deepcopy(tokens[5:]),
            'derived_zero_offset_view_scope': 'Used only to reuse independent topology/support qualification; not a serialized record or modified source',
            'scope': 'Literal UV chart translation only; no general periodic evaluator, sign-based reversal or exact procedural geometry claim'},
        scope='Strict observed compact circular-sweep seam offset with existing typed topology and blob-local subtype identity proof')
    return result
