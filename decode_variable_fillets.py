"""Counted intermediate variable-fillet controls, using shared edge-set framing.

The native position/radius list order matches actual API getters, which need not
match setter request order. Fractions have no assigned ASM edge orientation.
"""
import math
import struct

from decode_edge_tools import decode_edge_tool
from decode_sketch import reference

FILLET = 'A07D5F17-68CB-464D-9935-BF68E98A865F'
SCOPE = 'Counted intermediate-radius fillet settings and existing owned selection proxy; no fillet regeneration, ASM edge orientation or exact selected topology inferred'


def decode_variable_radius_payload(chunk, value):
    """Optional shared-reader callback; returns patch, selection ID, weight offset.

    Shared reader retains feature/set identity, flags, index, selection ownership,
    tangency-weight and trailer checks. Only the new nonempty counted branch is
    admitted here; the old endpoint-only branch retains its exact output.
    """
    if (len(chunk) < 112 or chunk[:7] != bytes(7) or chunk[7] not in (0, 1)
            or chunk[8:10] != bytes(2) or chunk[21:28] != bytes(7)):
        raise ValueError('Unsupported intermediate variable-fillet prefix')
    count = struct.unpack_from('<I', chunk, 28)[0]
    if not 1 <= count <= 1024 or len(chunk) != 90+22*count:
        raise ValueError('Variable-fillet midpoint count/payload extent disagrees')
    positions = [reference(chunk, 32+11*i) for i in range(count)]
    cursor = 32+11*count
    if chunk[cursor:cursor+4] != bytes(4) or struct.unpack_from('<I', chunk, cursor+4)[0] != count+2:
        raise ValueError('Variable-fillet radius/position list counts disagree')
    radii = [reference(chunk, cursor+8+11*i) for i in range(count+2)]
    cursor += 8+11*(count+2)
    if chunk[cursor:cursor+9] != bytes(9):
        raise ValueError('Unsupported variable-fillet post-list fields')
    if len(set(positions+radii)) != len(positions+radii):
        raise ValueError('Variable-fillet parameter bindings repeat across lists')
    start, end = value(radii[0], 'StartRadius'), value(radii[1], 'EndRadius')
    mid_radii = [value(identity, 'MidRadius') for identity in radii[2:]]
    mid_positions = [value(identity, 'MidParams') for identity in positions]
    if any(not math.isfinite(p['value']) or p['value'] <= 0 for p in [start,end]+mid_radii):
        raise ValueError('Variable-fillet radius must be positive finite')
    fractions = [p['value'] for p in mid_positions]
    if any(not math.isfinite(p) or not 0 < p < 1 for p in fractions) or len(set(fractions)) != count:
        raise ValueError('Variable-fillet midpoint fractions must be distinct and interior')
    patch = {'kind':'VariableRadiusFilletEdgeSet','startRadius':start,'endRadius':end,
        'midRadii':mid_radii,'midPositions':mid_positions,
        'radius_scope':'Observed counted intermediate-radius/position bindings; native order matches actual API getter order',
        'midpoint_order_scope':'Stored list order retained; API getters may reorder setter request, no ASM traversal sign assigned',
        'midpoint_position_scope':'Unitless fractions along API selected curve; source-to-ASM orientation and nonlinear distance parameterization unresolved'}
    return patch, reference(chunk,10), cursor+13


def decode_variable_fillet(data, records, body, feature):
    """Reuse shared fillet controls/ownership with only new variable-list branch."""
    if feature.get('kind') != 'Fillet' or feature.get('class_guid') != FILLET:
        raise ValueError('Variable fillet requires typed native Fillet feature')
    matches = [r for r in records if r.is_primary and r.object_id == feature['object_id']]
    if len(matches) != 1 or matches[0].class_guid != FILLET or data[matches[0].body:matches[0].end] != body:
        raise ValueError('Variable fillet feature identity/payload disagrees')
    return decode_edge_tool(data, records, body, feature, variable_radius_decoder=decode_variable_radius_payload)


def decode_variable_fillets(data, records, features):
    """Additional intermediate-only summary; old fillets get no new sidecars."""
    decoded, unresolved = [], []
    for feature in features:
        if feature.get('kind') != 'Fillet' or not any(p.get('role') in ('MidRadius','MidParams') for p in feature.get('parameters',[])):
            continue
        try:
            matches = [r for r in records if r.is_primary and r.object_id == feature['object_id']]
            if len(matches) != 1: raise ValueError('Variable fillet primary feature ambiguous')
            record = matches[0]
            settings = decode_variable_fillet(data,records,data[record.body:record.end],feature)
            if not any(s.get('midRadii') for s in settings['edge_sets']):
                raise ValueError('Intermediate parameter roles have no decoded intermediate edge set')
            decoded.append({'feature_object_id':feature['object_id'],'tool_settings':settings,'scope':SCOPE})
        except (ValueError,KeyError,IndexError,TypeError,struct.error) as error:
            unresolved.append({'feature_object_id':feature['object_id'],'reason':str(error)})
    return {'decoded':decoded,'unresolved':unresolved,'scope':SCOPE}
