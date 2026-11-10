"""Observed profile-reference selector literals and qualified cached boundaries.

Selectors are opaque stored controls. No selector-to-angle/end-parameter rule is
inferred; actual cached edge intervals are exposed only after a complete native
profile/Sketch/BODY route and all-six-field COEDGE naming correspondence.
"""
import copy
import struct

from asm_records import inspect_asm
from decode_brep import decode_topology
from decode_profile_cache_correspondence import decode_profile_cache_correspondence
from decode_profiles import PROFILE_DESCRIPTOR_GUID, PROFILE_LOOP_GUID, read_loops
from decode_sketch import reference

OBSERVED_SELECTOR_PAIRS = frozenset(((1, 1), (1, 2), (2, 2)))
SCOPE = 'Observed selected Line/Circle profile selector literals and whole six-field naming correspondence to stored result-BODY boundaries; selector geometry semantics, source-trim evaluator and lifecycle unresolved'


def read_trimmed_profile_loops(body, descriptor_id, sketch):
    """Extend only captured selector pairs; core framing/identity guards stay strict."""
    seen = set()
    has_new_selector = False

    def details(fields, geometry):
        nonlocal has_new_selector
        code, tag, secondary, direction, first, second, opaque = fields
        if (first, second) not in OBSERVED_SELECTOR_PAIRS:
            raise ValueError('Uncaptured trimmed profile reference selector layout')
        if geometry['kind'] not in ('Line', 'Circle'):
            raise ValueError('Only captured trimmed Line/Circle source kinds supported')
        if tag in seen:
            raise ValueError('Repeated source tag needs an unobserved per-portion association')
        seen.add(tag)
        has_new_selector |= (first, second) != (1, 1)
        return {'stored_tuple_code': code, 'stored_reference_selector_pair': [first, second],
                'stored_opaque_u64': opaque, 'stored_tuple_fields': list(fields),
                'stored_coedge_text_fields': [str(tag), str(secondary), str(direction), str(opaque), str(first), str(second)],
                'geometry_scope': 'Underlying sketch entity membership only; these literals do not supply source trim parameters'}

    loops = read_loops(body, descriptor_id, sketch, curve_reference_details=details)
    if not has_new_selector:
        raise ValueError('Whole-reference selector family belongs to the unchanged original reader')
    cursor = 21
    for loop in loops:
        cursor += 4
        for ref in loop['curve_references']:
            if struct.pack('<IQQIIIQ', *ref['stored_tuple_fields']) != body[cursor:cursor+40]:
                raise ValueError('Trimmed reference literal replay disagrees')
            ref['stored_tuple_offset_in_definition'] = cursor
            cursor += 40
        cursor += 1
    return loops


def decode_trimmed_profiles(data, records, features, member, members, body_identifier_summary, *, profile_loops_reader=None):
    """Returns decoded/unresolved/scope; does not mutate or clear original features."""
    active_expected = {}

    def loops_reader(body, descriptor_id, sketch):
        loops = (profile_loops_reader or read_trimmed_profile_loops)(body, descriptor_id, sketch)
        active_expected.clear()
        for loop in loops:
            for ref in loop['curve_references']:
                active_expected.setdefault(ref['entity_tag'], []).append(ref['stored_coedge_text_fields'])
        return loops

    def fields_validator(fields, sources):
        return len(fields) == 6 and sum(fields == expected for tag, rows in active_expected.items()
                                        for expected in rows if tag in sources) == 1

    # Opt in only when an explicitly owned, counted native definition stores a
    # non-(1,1) selector. Ordinary whole-reference profiles keep their old output.
    primary = {record.object_id: record for record in records if record.is_primary}
    candidates = set()
    for descriptor in records:
        if not descriptor.is_primary or descriptor.class_guid != PROFILE_DESCRIPTOR_GUID:
            continue
        try:
            payload = data[descriptor.body:descriptor.end]
            owner = reference(payload, len(payload)-11)
            definition = primary[reference(payload, 2)]
            if definition.class_guid != PROFILE_LOOP_GUID:
                continue
            body = data[definition.body:definition.end]
            if body[:2] != bytes(2) or reference(body, 2) != descriptor.object_id or struct.unpack_from('<I', body, 13)[0] != 1:
                continue
            count = struct.unpack_from('<I', body, 17)[0]
            if not 1 <= count <= 1024:
                continue
            cursor, has_variant = 21, False
            for _ in range(count):
                size = struct.unpack_from('<I', body, cursor)[0]
                cursor += 4
                if not 1 <= size <= 100000 or cursor+40*size+1 > len(body):
                    raise ValueError('Unframed profile variant probe')
                for _ in range(size):
                    fields = struct.unpack_from('<IQQIIIQ', body, cursor)
                    has_variant |= fields[4:6] != (1, 1)
                    cursor += 40
                cursor += 1
            if body[cursor:] == bytes(4) and has_variant:
                candidates.add(owner)
        except (ValueError, KeyError, IndexError, struct.error):
            continue  # The canonical profile reader retains these unresolved cases.
    if not candidates:
        return {'decoded': [], 'unresolved': [], 'scope': SCOPE}
    selected_features = [feature for feature in features if feature['kind'] != 'Extrude' or feature['object_id'] in candidates]
    base = decode_profile_cache_correspondence(
        data, records, selected_features, member, members, body_identifier_summary,
        profile_loops_reader=loops_reader, coedge_fields_validator=fields_validator)
    decoded, unresolved = [], list(base['unresolved'])
    for item in base['decoded']:
        try:
            row = copy.deepcopy(item)
            parsed = inspect_asm(members[row['history_blob_member']])
            topology = decode_topology(parsed)
            if topology['unresolved']:
                raise ValueError('Trimmed boundary cache topology incomplete')
            nodes = {node['index']: node for node in topology['nodes']}
            refs = {}
            for loop in row['profile_loops']:
                for ref in loop['curve_references']:
                    refs.setdefault(ref['entity_tag'], []).append(ref)
            for source in row['source_curves']:
                references = refs[source['native_entity_tag']]
                if len(references) == 1:
                    source['stored_profile_reference'] = references[0]
                else:
                    source['stored_profile_references'] = references
                covered = set()
                for candidate in source['cached_coedge_candidates']:
                    matches = [ref for ref in references if candidate['stored_decimal_text_fields'] == ref['stored_coedge_text_fields']]
                    if not matches:
                        raise ValueError('Complete profile/cache tuple literal disagreement')
                    if len(matches) != 1:
                        raise ValueError('Complete profile/cache tuple literal ambiguity')
                    ref = matches[0]
                    covered.add(tuple(ref['stored_coedge_text_fields']))
                    if len(references) > 1:
                        candidate['stored_profile_reference'] = ref
                    coedge = nodes[candidate['coedge_record_index']]
                    partner = nodes.get(coedge['partner_index'])
                    if partner is None or partner['partner_index'] != coedge['index'] or partner['edge_index'] != coedge['edge_index']:
                        raise ValueError('Trimmed cache COEDGE partner/edge backlink disagrees')
                    edge = nodes[candidate['edge_record_index']]
                    curve = nodes[candidate['curve_record_index']]
                    expected_kind = 'straight-curve' if source['native_entity_kind'] == 'Line' else 'ellipse-curve'
                    if curve['kind'] != expected_kind:
                        raise ValueError('Trimmed source/cache primitive kinds disagree')
                    points = []
                    for vertex_id in candidate['endpoint_vertex_record_indices']:
                        vertex = nodes[vertex_id]
                        point = nodes[vertex['point_index']]
                        if vertex['kind'] != 'vertex' or point['kind'] != 'point':
                            raise ValueError('Trimmed cache endpoint vertex/point kinds disagree')
                        points.append({'vertex_record_index': vertex_id, 'point_record_index': point['index'],
                                       'raw_position': list(point['raw_origin'])})
                    literal_keys = ('kind', 'index', 'offset', 'raw_origin', 'direction', 'normal',
                                    'stored_reference_axis', 'stored_axis_ratio', 'parameter_interval',
                                    'raw_major_radius', 'raw_minor_radius')
                    candidate.update(stored_edge_parameter_interval=[edge['start_parameter'], edge['end_parameter']],
                                     stored_edge_is_reversed=edge['is_reversed'],
                                     stored_coedge_is_reversed=coedge['is_reversed'],
                                     cached_endpoint_points=points,
                                     stored_curve_geometry={key: copy.deepcopy(curve[key]) for key in literal_keys if key in curve},
                                     geometry_scope='Raw stored result-BODY primitive and edge interval after literal naming proof; no source-profile evaluator parameter conversion')
                if covered != {tuple(ref['stored_coedge_text_fields']) for ref in references}:
                    raise ValueError('A selected native portion lacks full-tuple COEDGE correspondence')
            row.update(comparison_basis='All six canonical decimal text literals exactly match the complete owned native profile reference tuple after independent typed source and same-asset BODY proof',
                       identity_status='Qualified source-reference to multiple cached COEDGE correspondences; no coordinate-based identity or unique persistent edge',
                       geometry_status='Raw stored result-BODY edge primitives/intervals retained separately from source SketchCurve geometry; native selectors remain opaque',
                       remaining_uncertainty=['Selector pair meaning and general source-profile trim construction',
                                              'Stored direction flag relation to profile/API traversal',
                                              'Repeated source curve portions, secondary tags and other selector values',
                                              'Modified/historical cache versus original source geometry and persistent topology lifecycle'])
            decoded.append(row)
        except (ValueError, KeyError, TypeError, IndexError) as error:
            unresolved.append({'source_feature_object_id': item['source_feature_object_id'], 'reason': str(error)})
    return {'decoded': decoded, 'unresolved': unresolved, 'scope': SCOPE}
