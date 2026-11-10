"""Observed directed SketchLine Revolve axes and cached BRep edge source axes.

Construction axes remain in the existing selection pass. Native edge recipes
identify historical source bodies; a typed line cache supplies source axis geometry
without establishing persistent ASM edge identity or effective rotation direction.
"""

import math
import struct
import uuid

from decode_placement import rigid_matrix, transform_point
from decode_selection import resolve_single_sketch_curve, native_proxy_references
from decode_body_selections import decode_body_selections
from decode_brep_recipes import decode_recipe
from decode_parameters import read_string
from decode_sketch import numbers, reference



def _edge_axis(data, records, identity, owner):
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {i: items[0] for i,items in grouped.items() if len(items) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Revolve edge-axis typed identity missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    record, proxy = typed(identity, '2CA5A1CD-C99B-4C9B-91AF-57989148E841')
    ids, props = native_proxy_references(data, record)
    if props or len(ids) != 1 or reference(proxy,len(proxy)-11) != owner:
        raise ValueError('Only observed one owned Revolve edge-axis descriptor supported')
    descriptor_id = ids[0]
    _, descriptor = typed(descriptor_id, '5662F619-2281-4AD9-93DC-1FCFDA1062E7')
    if (len(descriptor) != 276 or descriptor[:4] != bytes(4)
            or struct.unpack_from('<I',descriptor,15)[0] != 1 or reference(descriptor,265) != owner):
        raise ValueError('Unobserved Revolve edge-axis topology descriptor')
    recipe_record, _ = typed(reference(descriptor,4),'7ACC2A03-0261-4879-A14A-A93D661A5BDC')
    recipe = decode_recipe(data,recipe_record,primary)
    if recipe['payload_kind'] != 'edge_recipe_data':
        raise ValueError('Revolve edge-axis descriptor requires explicit edge recipe')
    namespace,cursor = read_string(descriptor,19)
    entity_guid,cursor = read_string(descriptor,cursor)
    uuid.UUID(namespace)
    uuid.UUID(entity_guid)
    if descriptor[cursor:cursor+12] != struct.pack('<QI',2,1):
        raise ValueError('Unobserved Revolve edge-axis context count')
    context_id = reference(descriptor,cursor+12)
    _, context = typed(context_id,'50AEE8B4-9456-4DD7-847D-6F6C909BBB9D')
    if len(context) != 55 or context[:2] != bytes(2) or context[50:] != bytes.fromhex('0000000100'):
        raise ValueError('Unobserved Revolve edge-axis cached line context')
    values = numbers(context,2,6)
    start,delta = values[:3],values[3:]
    length = math.sqrt(sum(x*x for x in delta))
    if not math.isfinite(length) or length <= 1e-12:
        raise ValueError('Degenerate cached edge-axis line')
    cursor += 23
    if struct.unpack_from('<I',descriptor,cursor)[0] != 1 or len(descriptor)-(cursor+15) != 67:
        raise ValueError('Unobserved Revolve edge-axis body anchor/trailer')
    anchor_id = reference(descriptor,cursor+4)
    anchors = [a for a in decode_body_selections(data,records)['body_anchors'] if a['object_id'] == anchor_id]
    if len(anchors) != 1:
        raise ValueError('Revolve edge-axis historical body anchor unavailable')
    anchor = anchors[0]
    return {'selection_object_id':identity,'descriptor_object_id':descriptor_id,'context_record_object_id':context_id,
            'namespace_text':namespace,'entity_guid_text':entity_guid,'recipe':recipe,
            'entity':{'kind':'BRepEdge','native_body_object_id':anchor['native_body_object_id'],
                      'source_owner_object_id':anchor['source_owner_object_id'],'body_anchor_object_id':anchor_id,
                      'origin_cm':start,'start_cm':start,'end_cm':[a+b for a,b in zip(start,delta)],
                      'stored_direction_vector':delta,'direction':[x/length for x in delta]},
            'association':'Owned edge recipe and historical body anchor plus explicitly referenced typed cached line context',
            'coordinate_scope':'Cached source line agrees with root-component API X/Y edge contrasts in cm; occurrence frames and effective feature orientation unverified',
            'topology_status':'Persistent recipe-to-ASM edge mapping remains unresolved; cached source axis is separate evidence'}


def decode_revolve_axes(data, records, features):
    decoded, unresolved = [], []
    for feature in features:
        if feature['kind'] != 'Revolve' or 'revolve' not in feature:
            continue
        settings = feature['revolve']
        if settings['axis_selection'] != 'Undecoded':
            continue
        identity, owner = settings['axis_selection_record_object_id'], feature['object_id']
        try:
            if feature['is_project_axis']:
                raise ValueError('Projected selected-axis transform is outside the captured variants')
            try:
                source = resolve_single_sketch_curve(data, records, identity, owner, features, ('Line',))
            except (ValueError, KeyError, IndexError, struct.error) as sketch_error:
                try:
                    selected = _edge_axis(data,records,identity,owner)
                except (ValueError, KeyError, IndexError, struct.error) as edge_error:
                    raise ValueError('Sketch axis: '+str(sketch_error)+'; edge provenance: '+str(edge_error)) from edge_error
                decoded.append({'feature_object_id': owner, 'selection_object_id': identity, 'axis': selected})
                continue
            sketches = [f for f in features if f['kind'] == 'Sketch' and f['sketch_object_id'] == source['sketch_object_id']]
            if len(sketches) != 1:
                raise ValueError('Unique source axis sketch unavailable')
            sketch = sketches[0]
            curve = next(g for g in sketch['geometry'] if g['object_id'] == source['curve_object_id'])
            matrix = rigid_matrix(sketch['placement']['sketch_to_component_matrix'])
            start, end = (transform_point(matrix, curve[k]) for k in ('start_cm', 'end_cm'))
            delta = [b-a for a,b in zip(start,end)]
            length = math.sqrt(sum(x*x for x in delta))
            if not math.isfinite(length) or length <= 1e-12:
                raise ValueError('Degenerate selected sketch-line axis')
            selection = {'selection_object_id': identity, 'descriptor_object_id': source['descriptor_object_id'],
                         'terminal_object_id': source['terminal_object_id'],
                         'entity': {'kind': 'SketchLine', 'object_id': curve['object_id'],
                                    'sketch_object_id': source['sketch_object_id'], 'sketch_name': sketch['name'],
                                    'entity_tag': source['curve_entity_tag'], 'start_cm': start, 'end_cm': end,
                                    'origin_cm': start, 'direction': [x/length for x in delta]},
                         'association': 'Owned proxy/descriptor selects explicit sketch ID and line tag; source endpoint order preserved',
                         'coordinate_scope': 'Original line in parent component coordinates; no projected-axis or occurrence transform inferred'}
            decoded.append({'feature_object_id': owner, 'selection_object_id': identity, 'axis': selection})
        except (ValueError, KeyError, IndexError, StopIteration, struct.error) as error:
            unresolved.append({'feature_object_id': owner, 'selection_object_id': identity, 'reason': str(error)})
    return {'decoded': decoded, 'unresolved': unresolved,
            'scope': 'Observed unprojected directed SketchLine axes and typed cached BRep source lines; persistent edge identity and effective feature orientation unresolved'}
