"""Typed VBL component boundary corners; no interior or UV orientation inference."""
import hashlib
import math

from decode_brep import LINKS
from decode_pcurve_variants import encode_pcurve_fields
from decode_vbl_components import decode_vbl_components

SCOPE = ('Observed six-component VBL boundary corner cycles through reciprocal initial BODY/face/loop/'
         'coedge/edge/vertex/point links. Coedge reversal orders native topological endpoints only; '
         'component UV direction, native curve parameter maps, persistent topology and VBL interior unresolved.')


def decode_vbl_boundary_corners(blob, *, parsed=None, subtype_catalog=None,
                                topology=None, component_boundaries=None):
    """Return decoded/unresolved/scope without modifying existing boundary proofs."""
    from asm_records import inspect_asm
    from decode_asm_subtypes import decode_asm_subtypes
    from decode_brep import decode_topology
    if parsed is None:
        parsed = inspect_asm(blob)
    if subtype_catalog is None:
        subtype_catalog = decode_asm_subtypes(blob, parsed=parsed)
    if subtype_catalog['source_blob_sha256'] != hashlib.sha256(blob).hexdigest():
        raise ValueError('VBL corner subtype catalog belongs to another blob')
    if topology is None:
        topology = decode_topology(parsed, subtype_catalog=subtype_catalog)
    fresh = decode_vbl_components(blob, parsed=parsed, subtype_catalog=subtype_catalog, topology=topology)
    if component_boundaries is not None and component_boundaries != fresh:
        raise ValueError('VBL corner component associations are stale or differ from typed source')
    result = dict(decoded=[], unresolved=[], scope=SCOPE)
    if not fresh['decoded']:
        return result
    if not parsed.get('complete_token_stream'):
        raise ValueError('VBL corner initial token stream is incomplete')
    records = parsed['records']
    limit = next((i for i, r in enumerate(records) if r.get('record_kind') == 'marker'), len(records))
    groups = {}
    for node in topology['nodes']:
        groups.setdefault(node['index'], []).append(node)
    verified = {}

    def node(identity, kind):
        if type(identity) is not int or not 0 <= identity < limit:
            raise ValueError('VBL corner pointer outside bounded initial geometry')
        matches = groups.get(identity, [])
        if len(matches) != 1 or matches[0]['kind'] != kind:
            raise ValueError('VBL corner typed node missing, ambiguous or wrong class')
        value = matches[0]
        if identity in verified:
            return value
        record = records[identity]
        if record['index'] != identity or record['name'] != kind or record['section'] != 'geometry':
            raise ValueError('VBL corner node differs from initial typed record')
        tokens = record['tokens']
        # These admitted topology records have a single literal entity name.
        # Replay every typed field, including attributes and stored IDs, against
        # the original bytes so a supplied parsed/topology view cannot redirect links.
        replay = bytes((13, len(kind)))+kind.encode('ascii')+encode_pcurve_fields(tokens)+b'\x11'
        if replay != blob[record['offset']:record['end_offset']]:
            raise ValueError('VBL corner typed record replay differs from original blob')
        for field, (offset, expected) in LINKS.get(kind, {}).items():
            token = tokens[offset]
            if token['kind'] != 'pointer':
                raise ValueError('VBL corner link is not a typed pointer')
            target = token['value']
            target = None if target == -1 else target
            if value[field+'_index'] != target:
                raise ValueError('VBL corner node link differs from serialized pointer')
            if target is not None:
                if type(target) is not int or not 0 <= target < limit:
                    raise ValueError('VBL corner linked record outside initial geometry')
                actual = records[target]['name']
                if expected and actual != expected and not actual.endswith('-'+expected):
                    raise ValueError('VBL corner linked record has wrong typed class')
        if kind == 'coedge':
            if tokens[7]['kind'] != 'boolean_token' or type(value['is_reversed']) is not bool or value['is_reversed'] is not tokens[7]['value']:
                raise ValueError('VBL corner coedge reversal differs from literal Boolean')
        if kind == 'point':
            if (tokens[3]['kind'] != 'position_vector' or value['raw_origin'] != tokens[3]['value']
                    or len(value['raw_origin']) != 3 or any(not math.isfinite(x) for x in value['raw_origin'])):
                raise ValueError('VBL corner point differs from finite serialized position')
        verified[identity] = record
        return value

    def chain(first, kind, next_field, owner_field, owner):
        ids = []
        while first is not None:
            if first in ids or len(ids) >= limit:
                raise ValueError('VBL corner ownership chain repeats or exceeds initial bounds')
            item = node(first, kind)
            if item[owner_field] != owner:
                raise ValueError('VBL corner ownership chain backlink disagrees')
            ids.append(first)
            first = item[next_field]
        return ids

    def body_owner(face_id, graph):
        face = node(face_id, 'face')
        if face.get('subshell_index') is not None:
            raise ValueError('VBL corner subshell ownership is unobserved')
        shell = node(face['shell_index'], 'shell')
        if shell.get('subshell_index') is not None:
            raise ValueError('VBL corner nested shell ownership is unobserved')
        lump = node(shell['lump_index'], 'lump')
        body = node(lump['body_index'], 'body')
        if body['index'] != graph['body_index']:
            raise ValueError('VBL corner face owner differs from BODY graph')
        lumps = chain(body['first_lump_index'], 'lump', 'next_lump_index', 'body_index', body['index'])
        shells = chain(lump['first_shell_index'], 'shell', 'next_shell_index', 'lump_index', lump['index'])
        faces = chain(shell['first_face_index'], 'face', 'next_face_index', 'shell_index', shell['index'])
        if lump['index'] not in lumps or shell['index'] not in shells or face_id not in faces:
            raise ValueError('VBL corner parent missing from reciprocal BODY ownership chains')
        if face_id not in graph['face_indices'] or shell['index'] not in graph['shell_indices'] or lump['index'] not in graph['lump_indices']:
            raise ValueError('VBL corner parent absent from owning BODY graph')
        return dict(body_index=body['index'], lump_index=lump['index'], shell_index=shell['index'], face_index=face_id)

    for source in fresh['decoded']:
        try:
            face_id, loop_id = source['face_index'], source['loop_index']
            graphs = [g for g in topology['body_graphs'] if face_id in g['face_indices']]
            if len(graphs) != 1:
                raise ValueError('VBL corner face BODY ownership missing or ambiguous')
            graph = graphs[0]
            owner = body_owner(face_id, graph)
            face = node(face_id, 'face')
            loop = node(loop_id, 'loop')
            if face['surface_index'] != source['surface_record_index'] or face['first_loop_index'] != loop_id or loop['face_index'] != face_id or loop['next_loop_index'] is not None or loop_id not in graph['loop_indices']:
                raise ValueError('VBL corner owning face/loop/surface links disagree')
            components = source['components']
            if len(components) != 6 or [c['slot'] for c in components] != list(range(6)):
                raise ValueError('VBL corner requires exact six ordered component slots')
            edges = []
            for component in components:
                coedge = node(component['coedge_index'], 'coedge')
                edge = node(component['edge_index'], 'edge')
                partner = node(coedge['partner_index'], 'coedge')
                if (coedge['loop_index'] != loop_id or coedge['edge_index'] != edge['index']
                        or partner['index'] != component['partner_coedge_index']
                        or partner['partner_index'] != coedge['index'] or partner['edge_index'] != edge['index']
                        or edge['first_coedge_index'] not in (coedge['index'], partner['index'])
                        or coedge['index'] not in graph['coedge_indices'] or partner['index'] not in graph['coedge_indices']
                        or edge['index'] not in graph['edge_indices']):
                    raise ValueError('VBL corner component coedge/edge/partner membership disagrees')
                previous = node(coedge['previous_coedge_index'], 'coedge')
                following = node(coedge['next_coedge_index'], 'coedge')
                if previous['next_coedge_index'] != coedge['index'] or following['previous_coedge_index'] != coedge['index']:
                    raise ValueError('VBL corner coedge previous/next links are not reciprocal')
                other_loop = node(partner['loop_index'], 'loop')
                if other_loop['face_index'] != component['adjacent_face_index']:
                    raise ValueError('VBL corner adjacent support face differs from partner loop')
                body_owner(other_loop['face_index'], graph)
                other_face = node(other_loop['face_index'], 'face')
                other_loops = chain(other_face['first_loop_index'], 'loop', 'next_loop_index', 'face_index', other_face['index'])
                if other_loop['index'] not in other_loops or other_loop['index'] not in graph['loop_indices']:
                    raise ValueError('VBL corner partner loop absent from adjacent face ownership chain')
                partner_ring = []
                current = other_loop['first_coedge_index']
                while current not in partner_ring:
                    if current is None or len(partner_ring) >= limit:
                        raise ValueError('VBL corner adjacent coedge ring exceeds initial bounds')
                    item = node(current, 'coedge')
                    following_item = node(item['next_coedge_index'], 'coedge')
                    if item['loop_index'] != other_loop['index'] or following_item['previous_coedge_index'] != current:
                        raise ValueError('VBL corner adjacent coedge ring backlink disagrees')
                    partner_ring.append(current)
                    current = item['next_coedge_index']
                if current != other_loop['first_coedge_index'] or partner['index'] not in partner_ring:
                    raise ValueError('VBL corner partner missing from closed adjacent face ring')
                pair = [edge['start_vertex_index'], edge['end_vertex_index']]
                if None in pair or pair[0] == pair[1]:
                    raise ValueError('VBL corner requires two distinct typed endpoint vertices')
                endpoints = []
                for vertex_id in pair:
                    vertex = node(vertex_id, 'vertex')
                    point = node(vertex['point_index'], 'point')
                    first_edge = node(vertex['first_edge_index'], 'edge')
                    if vertex_id not in (first_edge['start_vertex_index'], first_edge['end_vertex_index']) or first_edge['index'] not in graph['edge_indices'] or vertex_id not in graph['vertex_indices']:
                        raise ValueError('VBL corner vertex first-edge/BODY backlink disagrees')
                    endpoints.append(dict(vertex_index=vertex_id, point_index=point['index'], raw_point=point['raw_origin']))
                if coedge['is_reversed']:
                    endpoints.reverse()
                edges.append(dict(component_slot=component['slot'], coedge_index=coedge['index'], edge_index=edge['index'],
                    partner_coedge_index=partner['index'], adjacent_face_index=component['adjacent_face_index'],
                    stored_coedge_reversal=coedge['is_reversed'], entry=endpoints[0], exit=endpoints[1],
                    traversal_scope='Native topological traversal only; component UV/cache direction and edge parameter map unassigned'))
            if len({e['edge_index'] for e in edges}) != 6 or len({e['entry']['vertex_index'] for e in edges}) != 6:
                raise ValueError('VBL corner edge/entry vertices are not a six-element cycle')
            for incoming, outgoing in zip(edges[-1:]+edges[:-1], edges):
                if incoming['exit'] != outgoing['entry'] or node(incoming['coedge_index'], 'coedge')['next_coedge_index'] != outgoing['coedge_index']:
                    raise ValueError('VBL corner oriented vertex IDs do not close in component/coedge order')
            if loop['first_coedge_index'] not in {e['coedge_index'] for e in edges}:
                raise ValueError('VBL corner cycle omits owning loop first coedge')
            corners = [dict(corner_slot=i, vertex_index=outgoing['entry']['vertex_index'],
                point_index=outgoing['entry']['point_index'], raw_point=outgoing['entry']['raw_point'],
                incoming_component_slot=edges[i-1]['component_slot'], outgoing_component_slot=outgoing['component_slot'],
                incoming_coedge_index=edges[i-1]['coedge_index'], outgoing_coedge_index=outgoing['coedge_index'],
                adjacent_support_face_indices=[edges[i-1]['adjacent_face_index'], outgoing['adjacent_face_index']])
                for i, outgoing in enumerate(edges)]
            result['decoded'].append(dict(surface_record_index=source['surface_record_index'], **owner,
                loop_index=loop_id, boundary_edges=edges, corners=corners,
                ordered_vertex_cycle=[e['entry']['vertex_index'] for e in edges]+[edges[0]['entry']['vertex_index']],
                component_parameter_orientation=None, native_edge_parameter_mapping=None, VBL_interior_geometry=None,
                coordinate_scope='Raw ASM stored point records; no body transform/units/context applied', scope=SCOPE))
        except (ValueError, KeyError, IndexError, TypeError) as error:
            result['unresolved'].append(dict(surface_record_index=source['surface_record_index'], reason=str(error)))
    return result
