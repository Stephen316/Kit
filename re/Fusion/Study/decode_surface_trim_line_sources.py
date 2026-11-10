"""Owned native SketchLine SurfaceTrim source; no kept-cell semantics."""
import copy
import math

from decode_assembly import decode_assembly, SKETCH_BASE_GUID
from decode_mesh_contents import _require
from decode_parameters import read_string
from decode_placement import IDENTITY, rigid_matrix, transform_point, transform_vector
from decode_selection import native_proxy_references, resolve_single_sketch_curve
from decode_sketch import attributes, numbers, reference, same

TRIM = 'FF1741AE-E78B-4A5F-8418-751899E12F66'
SCOPE = ('Observed singleton SurfaceTrim SketchLine source through owned proxy/descriptor/leaf '
         'and native sketch ID/entity tag, endpoint references and canonical Sketch-to-component placement. '
         'Natural line evaluations are derived; native/API handle identity, Trim cell/side selection, '
         'persistent face identity, result geometry, lifecycle and regeneration unresolved.')


def resolve_surface_trim_line_source(data, records, tool_id, owner_id, features):
    """Pure source callback; common Trim target and opaque recipe remain independent."""
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)

    def typed(identity, guid):
        rows = grouped.get(identity, [])
        _require(len(rows) == 1 and rows[0].class_guid == guid,
                 'SurfaceTrim Line typed identity missing/ambiguous/wrong class')
        record = rows[0]
        return record, data[record.body:record.end]

    feature, payload = typed(owner_id, TRIM)
    _require(payload[:2] == bytes(2) and len(payload) >= 55 and reference(payload, 17) == tool_id,
             'SurfaceTrim Line source operand differs from native feature field')
    proxy, proxy_payload = typed(tool_id, '2CA5A1CD-C99B-4C9B-91AF-57989148E841')
    ids, props = native_proxy_references(data, proxy)
    _require(not props and len(ids) == 1 and reference(proxy_payload, len(proxy_payload)-11) == owner_id,
             'SurfaceTrim Line owned singleton proxy differs')
    selected = resolve_single_sketch_curve(data, records, tool_id, owner_id, features, ('Line',))
    sketches = [s for s in features if s['kind'] == 'Sketch' and s['sketch_object_id'] == selected['sketch_object_id']]
    _require(len(sketches) == 1, 'SurfaceTrim Line canonical sketch ambiguous')
    sketch = sketches[0]
    curves = [c for c in sketch['geometry'] if c['object_id'] == selected['curve_object_id']
              and c.get('entity_tag') == selected['curve_entity_tag'] and c['kind'] == 'Line']
    _require(len(curves) == 1, 'SurfaceTrim Line canonical source identity ambiguous')
    curve = curves[0]
    line, raw_line = typed(curve['object_id'], 'DCA267ED-D615-4934-B64F-AD805E8003E2')
    line_props, cursor = attributes(raw_line, 2)
    _require(raw_line[:2] == b'\0\1' and line_props.get('EntityGenesis') == 2
             and line_props.get('crv_primary_id') == selected['curve_entity_tag']
             and line_props.get('crv_secondary_id') == 0 and len(raw_line)-cursor == 171
             and reference(raw_line, cursor+107) == curve['start_point_id']
             and reference(raw_line, cursor+96) == curve['end_point_id']
             and reference(raw_line, len(raw_line)-11) == sketch['sketch_object_id'],
             'SurfaceTrim Line native primary/endpoints/owner framing differs')
    values = numbers(raw_line, cursor, 12)
    endpoints = []
    for role in ('start', 'end'):
        point, raw_point = typed(curve[role+'_point_id'], 'C2CEDAE7-1716-47C1-B7B1-07B70081D0FB')
        point_props, point_cursor = attributes(raw_point, 2)
        _require(raw_point[:2] == b'\0\1' and point_props.get('EntityGenesis') == 2
                 and len(raw_point)-point_cursor == 99 and 'pt_tag' in point_props
                 and reference(raw_point, len(raw_point)-11) == sketch['sketch_object_id']
                 and same(numbers(raw_point, point_cursor+19, 3), curve[role+'_cm']),
                 'SurfaceTrim Line typed endpoint/cache/Sketch ownership differs')
        endpoints.append(dict(role=role, point_object_id=point.object_id, native_record_offset=point.start,
                              entity_tag=point_props['pt_tag'], point_sketch_local_cm=list(curve[role+'_cm'])))
    start, end = curve['start_cm'], curve['end_cm']
    displacement = [b-a for a,b in zip(start,end)]
    _require(all(math.isfinite(x) for x in start+end) and not same(start,end)
             and same(values[:3],start) and same(values[3:6],displacement),
             'SurfaceTrim Line stored origin/displacement and typed endpoints disagree')
    typed(sketch['sketch_object_id'], '44A64366-4BD3-4B24-881A-F94C206E8F2D')
    bases = [r for r in records if not r.is_primary and r.object_id == sketch['sketch_object_id'] and r.class_guid == SKETCH_BASE_GUID]
    _require(len(bases) == 1, 'SurfaceTrim Line Sketch base ambiguous')
    base = bases[0]; raw_base = data[base.body:base.end]
    name, _ = read_string(raw_base, 28)
    _require(name == (sketch.get('name') or ''), 'SurfaceTrim Line Sketch base/canonical name differs')
    transform_id = reference(raw_base, 0)
    transform, raw_transform = typed(transform_id, 'F47A46FB-DA27-4AFA-8A72-1B38FA596E23')
    placement = sketch.get('placement', {})
    _require(placement.get('transform_object_id') == transform_id and placement.get('record_offset') == transform.start,
             'SurfaceTrim Line canonical transform identity differs')
    matrix = rigid_matrix(placement.get('sketch_to_component_matrix', []))
    if len(raw_transform) == 15:
        _require(raw_transform[:4] == bytes.fromhex('00000100') and placement.get('encoding') == 'ImplicitIdentity'
                 and matrix == IDENTITY, 'SurfaceTrim Line implicit transform framing differs')
    else:
        _require(len(raw_transform) == 143 and raw_transform[:3] == bytes(3) and raw_transform[-12] == 0
                 and placement.get('encoding') == 'ExplicitFloat64Matrix' and numbers(raw_transform,3,16) == matrix,
                 'SurfaceTrim Line explicit transform framing differs')
    component_id = reference(raw_transform, len(raw_transform)-11)
    typed(component_id, 'E03784ED-5E19-4E14-B9F2-3B07017018CD')
    owned_sketch = copy.deepcopy(sketch)
    decode_assembly(data, records, [owned_sketch])
    _require(owned_sketch.get('component_object_id') == component_id,
             'SurfaceTrim Line Sketch collection/component ownership disagrees')
    samples = [dict(natural_segment_fraction=t,
                    point_sketch_local_cm=[a+t*d for a,d in zip(start,displacement)],
                    point_component_cm=transform_point(matrix,[a+t*d for a,d in zip(start,displacement)]))
               for t in (0.,.25,.5,.75,1.)]
    evidence = dict(feature_object_id=owner_id, tool_selection_record_object_id=tool_id,
        source_kind='SketchLine', selection=selected, source_endpoints=endpoints,
        source_start_sketch_local_cm=list(start), source_end_sketch_local_cm=list(end),
        natural_displacement_sketch_local_cm=displacement,
        natural_displacement_component_cm=transform_vector(matrix,displacement),
        natural_derived_samples=samples, native_curve_primary_record_offset=line.start,
        stored_curve_primary_payload_hex=raw_line.hex(), native_feature_record_offset=feature.start,
        stored_tool_operand_hex=payload[17:28].hex(), source_sketch_base_record_offset=base.start,
        source_sketch_collection_object_id=reference(raw_base,len(raw_base)-11),
        native_transform_object_id=transform_id, native_transform_record_offset=transform.start,
        stored_transform_payload_hex=raw_transform.hex(), canonical_placement=copy.deepcopy(placement),
        source_component_object_id=component_id, source_component_association=owned_sketch['component_association'],
        native_API_source_assignment=None, selected_asm_face_id=None, native_trim_cell_assignment=None,
        direction_scope='Natural native start/end order only; no Trim kept/removed side, traversal or selected-cell interpretation',
        evaluator_scope='Derived finite full line segment fractions in sketch-local and parent-component coordinates; no occurrence/world or API evaluator-parameter claim',
        scope=SCOPE)
    return dict(selection_record_object_id=tool_id,
                entity=dict(kind='SketchLine',sketch_object_id=selected['sketch_object_id'],curve_object_id=curve['object_id']),
                native_source_evidence=evidence,scope=SCOPE)
