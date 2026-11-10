"""Native Sketch/Extrude/Scale operands for separately derived prism geometry.

BODY references remain historical native anchors mapped to the initial cache.
No Scale-owned result anchor, before-state or persistent identity is invented.
"""
import copy
import math
import struct

from decode_assembly import decode_assembly, SKETCH_BASE_GUID
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_properties import BODY, COLLECTION, decode_body_properties
from decode_body_selections import ANCHOR, decode_body_selections
from decode_body_tool_selections import decode_body_tool_selections
from decode_body_tools import decode_body_tool
from decode_construction import decode_construction
from decode_construction_definitions import decode_construction_definitions
from decode_dependencies import decode_dependencies
from decode_extrude import decode_extrude
from decode_parameters import decode_stream, read_string
from decode_placement import IDENTITY, decode_placement, rigid_matrix
from decode_profile_cache_correspondence import decode_profile_cache_correspondence
from decode_scale_inputs import SCALE, decode_scale_vertex_points
from decode_selection import known_construction_entities
from decode_selection_recipe_incidence import decode_selection_recipe_incidence
from decode_sketch import attributes, decode_sketches, numbers, reference, same

EXTRUDE = 'DD405BC2-D673-44F0-8833-5CB2A1C186C7'
SKETCH = '44A64366-4BD3-4B24-881A-F94C206E8F2D'
LINE = 'DCA267ED-D615-4934-B64F-AD805E8003E2'
POINT = 'C2CEDAE7-1716-47C1-B7B1-07B70081D0FB'
COMPONENT = 'E03784ED-5E19-4E14-B9F2-3B07017018CD'
SCOPE = ('Observed BODY Scale native controls/center and unique NewBody untapered one-sided '
    'Extrude sources with four-Line native Sketch profiles, complete profile/cache COEDGE '
    'correspondences and reciprocal component ownership. Source geometry is derived separately; '
    'the same mapped BODY anchor is not a Scale-owned result or qualified chronological state.')


def qualify_scale_reconstruction_sources(data, records, features, member, members,
                                         body_blob_bindings, feature):
    """Return a fresh source proof, None outside Scale, or scoped ValueError.

    Caller annotations are never used as source truth and are not modified.
    Sketch-input and non-Extrude-source Scales are explicitly outside this family.
    """
    if feature.get('class_guid') != SCALE:
        return None
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    if any(len(rows) != 1 for rows in grouped.values()):
        raise ValueError('Scale reconstruction duplicate primary namespace')

    def typed(identity, guid=None):
        rows = grouped.get(identity, [])
        if len(rows) != 1 or guid is not None and rows[0].class_guid != guid:
            raise ValueError('Scale reconstruction native identity missing, ambiguous or wrong class')
        record = rows[0]
        return record, data[record.body:record.end]

    def raw(identity, guid=None):
        record, payload = typed(identity, guid)
        return dict(object_id=identity, class_guid=record.class_guid, record_offset=record.start,
            body_offset=record.body, end_offset=record.end, payload_hex=payload.hex())

    receiver = feature['object_id']
    record, body = typed(receiver, SCALE)
    fs = [f for f in features if f['object_id'] == receiver]
    if (len(fs) != 1 or feature.get('record_offset') != record.start
            or fs[0].get('record_offset') != record.start or fs[0].get('kind') != 'Scale'):
        raise ValueError('Scale reconstruction receiving metadata inconsistent')
    if member not in members or members[member] != data or not member.endswith('/FusionDesignSegmentType1/BulkStream.dat'):
        raise ValueError('Scale reconstruction exact native member/bytes scope differs')
    # The direct descriptor list belongs to Sketch Scale, not a BODY proxy.
    if len(body) >= 37 and body[32] == 1 and struct.unpack_from('<I',body,33)[0] in (1,2):
        raise ValueError('Scale reconstruction requires BODY inputs; Sketch Scale is outside this family')
    from decode_basics import attach_parameters, named_features
    private = named_features(data, records)
    parameters, _ = decode_stream(data, records)
    attach_parameters(data, records, private, parameters)
    decode_sketches(data, records, private)
    decode_placement(data, records, private)
    decode_construction(data, records, private)
    definitions = decode_construction_definitions(data, records, private)
    assembly = decode_assembly(data, records, private)
    properties = decode_body_properties(data, records, assembly)
    fresh_rows = [f for f in private if f['object_id'] == receiver]
    if len(fresh_rows) != 1:
        raise ValueError('Scale reconstruction fresh native receiving feature label missing or ambiguous')
    fresh = fresh_rows[0]

    def parameters_equal(identity):
        supplied = [f for f in features if f['object_id'] == identity]
        decoded = [f for f in private if f['object_id'] == identity]
        if len(supplied) != 1 or len(decoded) != 1:
            raise ValueError('Scale reconstruction parameter owner metadata ambiguous')
        keys = ('binding_object_id', 'parameter_object_id', 'role', 'raw_float64', 'display_units')
        left = [{k:p.get(k) for k in keys} for p in supplied[0].get('parameters', [])]
        right = [{k:p.get(k) for k in keys} for p in decoded[0]['parameters']]
        if left != right:
            raise ValueError('Scale reconstruction supplied parameters disagree with fresh reciprocal bindings')

    parameters_equal(receiver)
    settings = decode_body_tool(data, records, body, fresh, known_construction_entities(data, records, private))
    fresh['tool_settings'] = settings
    selections = decode_body_selections(data, records)
    selected_summary = decode_body_tool_selections(data, records, private, selections)
    selected_rows = [r for r in selected_summary['decoded'] if r['feature_object_id'] == receiver]
    if len(selected_rows) != 1:
        raise ValueError('Scale reconstruction BODY input field/proxy/descriptor route unresolved')
    settings.update(selected_rows[0]['settings'])
    if not 1 <= settings['input_count'] <= 2 or settings['input_body_count'] != settings['input_count'] or settings['input_face_count']:
        raise ValueError('Scale reconstruction requires one or two distinct BODY selections')
    factors = [settings['factor']]*3 if settings['is_uniform'] else settings['factors']
    if len(factors) != 3 or any(not math.isfinite(v) or v <= 0 for v in factors):
        raise ValueError('Scale reconstruction factors must be finite and positive')
    settings['factors_xyz'] = list(factors)
    if settings['point'] is None:
        vertex_rows = decode_scale_vertex_points(data, records, [fresh], selections)
        points = [r for r in vertex_rows['decoded'] if r['feature_object_id'] == receiver]
        if len(points) != 1:
            raise ValueError('Scale reconstruction center native route unresolved')
        settings.update({k:v for k,v in points[0].items() if k != 'feature_object_id'})
    point = settings['point']
    point_entity = point['entity']
    backend_id = reference(body, 10)
    _, backend = typed(backend_id, '69EE2FA7-BCC7-449E-9CA9-976CEFDFED44')
    if (len(backend) != 178 or backend[:23] != bytes(23)
            or struct.unpack_from('<I',backend,75)[0] != 1 or reference(backend,167) != receiver):
        raise ValueError('Scale reconstruction center backend framing/owner differs')
    method = struct.unpack_from('<I',backend,47)[0]
    descriptor_id = reference(backend,79)
    center = numbers(backend,23,3)
    settings['reconstruction_center_cm'] = center
    # Native mapping fields are revalidated against their bytes. Prior ordinal
    # guesses and later display annotations are deliberately not source evidence.
    binding_input = dict(decoded=[dict(
        mapping_record_object_id=m['mapping_record_object_id'],owner_object_id=m['owner_object_id'],
        history_blob_member=m['history_blob_member'],body_count=m['body_count'],
        bindings=[dict(stored_handle=b['stored_handle'],native_body_object_id=b['native_body_object_id'])
            for b in m['bindings']]) for m in body_blob_bindings.get('decoded',[])])
    mapping = decode_body_asm_identifiers(data, records, member, members, binding_input)
    correspondences = decode_profile_cache_correspondence(data, records, private, member, members, mapping)
    source_groups, body_proofs, owner_ids = [], [], [receiver]
    component_ids = set()

    def body_component(identity):
        typed(identity, BODY)
        rows = [b for b in properties['bodies'] if b['object_id'] == identity]
        if len(rows) != 1 or 'collection_object_id' not in rows[0] or 'component_object_id' not in rows[0]:
            raise ValueError('Scale reconstruction BODY reciprocal component owner unresolved')
        prop = rows[0]
        collections = [c for c in properties['collections'] if c['object_id'] == prop['collection_object_id']]
        if len(collections) != 1 or identity not in collections[0]['body_object_ids']:
            raise ValueError('Scale reconstruction BODY/repeated collection membership differs')
        _, collection = typed(prop['collection_object_id'], COLLECTION)
        _, native = typed(identity, BODY)
        component = prop['component_object_id']
        typed(component, COMPONENT)
        if reference(native,len(native)-11) != prop['collection_object_id'] or reference(collection,len(collection)-11) != component:
            raise ValueError('Scale reconstruction BODY/collection/component backlinks differ')
        component_ids.add(component)
        body_proofs.append(dict(native_body_object_id=identity,body_properties=prop,collection=collections[0]))
        return component

    def sketch_frame(sketch):
        identity = sketch['sketch_object_id']
        typed(identity, SKETCH)
        bases = [r for r in records if not r.is_primary and r.object_id == identity and r.class_guid == SKETCH_BASE_GUID]
        if len(bases) != 1:
            raise ValueError('Scale reconstruction Sketch base ambiguous')
        base = bases[0]
        payload = data[base.body:base.end]
        transform_id = reference(payload,0)
        transform, matrix_payload = typed(transform_id,'F47A46FB-DA27-4AFA-8A72-1B38FA596E23')
        matrix = rigid_matrix(sketch.get('placement',{}).get('sketch_to_component_matrix',[]))
        # All current source/center sketches have independently stored implicit
        # identity frames. General placed extrusion direction semantics stay out.
        if (len(matrix_payload) != 15 or matrix_payload[:4] != bytes.fromhex('00000100')
                or matrix != IDENTITY or sketch['placement'].get('transform_object_id') != transform_id
                or sketch['placement'].get('record_offset') != transform.start):
            raise ValueError('Scale reconstruction requires observed identity native Sketch frame')
        component = reference(matrix_payload,len(matrix_payload)-11)
        typed(component, COMPONENT)
        if sketch.get('component_object_id') != component:
            raise ValueError('Scale reconstruction Sketch collection/transform component disagrees')
        component_ids.add(component)
        return dict(component_object_id=component,sketch_base_record_offset=base.start,
            sketch_base_payload_hex=payload.hex(),transform=raw(transform_id),
            canonical_placement=copy.deepcopy(sketch['placement']),
            collection_component_association=sketch['component_association'])

    def point_native(identity, sketch_id):
        _, payload = typed(identity, POINT)
        props, cursor = attributes(payload,2)
        if payload[:2] != b'\0\1' or len(payload)-cursor != 99 or 'pt_tag' not in props or reference(payload,len(payload)-11) != sketch_id:
            raise ValueError('Scale reconstruction native Sketch POINT framing/owner differs')
        return dict(point_object_id=identity,entity_tag=props['pt_tag'],position_cm=numbers(payload,cursor+19,3),
            native_record=raw(identity,POINT))

    for item in settings['input_selections']:
        owner, native, anchor_id = item['source_owner_object_id'],item['native_body_object_id'],item['body_anchor_object_id']
        typed(item['descriptor_object_id'],'9716F783-676D-42E0-93F9-EBF273E7C035')
        typed(owner, EXTRUDE)
        parameters_equal(owner)
        anchor_rows = [a for a in selections['body_anchors'] if a['source_owner_object_id'] == owner]
        if (len(anchor_rows) != 1 or anchor_rows[0]['object_id'] != anchor_id
                or anchor_rows[0]['native_body_object_id'] != native):
            raise ValueError('Scale reconstruction source Extrude does not own one unique selected BODY anchor')
        _, anchor = typed(anchor_id,ANCHOR)
        if len(anchor) != 102 or reference(anchor,80) != native or reference(anchor,91) != owner:
            raise ValueError('Scale reconstruction source anchor/BODY/owner native references differ')
        source_rows = [f for f in private if f['object_id'] == owner]
        if len(source_rows) != 1:
            raise ValueError('Scale reconstruction fresh native Extrude feature label missing or ambiguous')
        source = source_rows[0]
        _, source_body = typed(owner,EXTRUDE)
        controls, reasons = decode_extrude(source_body,source,allow_surface=True)
        side = controls['extent']['side_one']
        if (reasons or controls['operation']['kind'] != 'NewBody' or controls['is_solid'] is not True
                or controls['extent']['mode'] != 'OneSided' or controls['start']['kind'] != 'ProfilePlane'
                or side['condition'] != 'Distance' or controls['stored_second_extent_enabled'] != 0
                or side.get('taper_angle_radians') != 0 or side['uninterpreted_flags'] != 0
                or not math.isfinite(side['distance_cm']) or side['distance_cm'] <= 0
                or controls['extent']['stored_direction_vector'] != [0.,0.,1.]):
            raise ValueError('Scale reconstruction requires solid NewBody untapered one-sided positive +Z Distance Extrude')
        rows = [r for r in correspondences['decoded'] if r['source_feature_object_id'] == owner]
        if len(rows) != 1 or rows[0]['native_body_object_id'] != native or rows[0]['body_anchor_object_id'] != anchor_id:
            raise ValueError('Scale reconstruction complete owned profile/cache correspondence unresolved')
        correspondence = rows[0]
        loops = correspondence['profile_loops']
        if len(loops) != 1 or loops[0]['is_outer'] is not True or len(loops[0]['curve_references']) != 4:
            raise ValueError('Scale reconstruction requires one complete four-Line outer profile')
        sketches = [f for f in private if f['kind'] == 'Sketch' and f['sketch_object_id'] == correspondence['native_sketch_object_id']]
        if len(sketches) != 1:
            raise ValueError('Scale reconstruction native source Sketch ambiguous')
        sketch = sketches[0]
        frame = sketch_frame(sketch)
        body_component(native)
        native_lines, native_points = [], {}
        for curve in correspondence['source_curves']:
            identity = curve['native_entity_object_id']
            _, payload = typed(identity,LINE)
            props, cursor = attributes(payload,2)
            geometry = [g for g in sketch['geometry'] if g['object_id'] == identity and g['kind'] == 'Line']
            if (len(geometry) != 1 or payload[:2] != b'\0\1' or len(payload)-cursor != 171
                    or props.get('crv_primary_id') != curve['native_entity_tag'] or props.get('crv_secondary_id') != 0
                    or reference(payload,len(payload)-11) != sketch['sketch_object_id']):
                raise ValueError('Scale reconstruction native profile Line tag/extent/owner differs')
            geometry = geometry[0]
            if reference(payload,cursor+107) != geometry['start_point_id'] or reference(payload,cursor+96) != geometry['end_point_id']:
                raise ValueError('Scale reconstruction native profile Line endpoint identities differ')
            for key in ('start_point_id','end_point_id'):
                point_id = geometry[key]
                native_points[point_id] = point_native(point_id,sketch['sketch_object_id'])
            native_lines.append(dict(line_object_id=identity,start_point_id=geometry['start_point_id'],
                end_point_id=geometry['end_point_id'],entity_tag=curve['native_entity_tag'],native_record=raw(identity,LINE)))
        degree = {identity:sum(identity in (line['start_point_id'],line['end_point_id']) for line in native_lines)
            for identity in native_points}
        reachable = {next(iter(native_points))} if native_points else set()
        for _ in range(4):
            reachable.update(p for line in native_lines
                if {line['start_point_id'],line['end_point_id']} & reachable
                for p in (line['start_point_id'],line['end_point_id']))
        if (len(native_lines) != 4 or len(native_points) != 4 or len({line['line_object_id'] for line in native_lines}) != 4
                or reachable != set(native_points)
                or any(value != 2 for value in degree.values())
                or any(line['start_point_id'] == line['end_point_id'] for line in native_lines)
                or any(p['position_cm'][2] != 0 for p in native_points.values())):
            raise ValueError('Scale reconstruction native four-Line profile POINT incidence/plane incomplete')
        matches = [(m,b) for m in mapping['decoded'] for b in m['bindings'] if b['native_body_object_id'] == native]
        if len(matches) != 1 or matches[0][1]['asm_body_index'] != correspondence['asm_body_index']:
            raise ValueError('Scale reconstruction native BODY/profile same-asset mapping differs')
        mapped, binding = matches[0]
        source_groups.append(dict(source_feature_object_id=owner,native_body_object_id=native,
            body_anchor_object_id=anchor_id,source_anchor=anchor_rows[0],input_descriptor=item,
            binding=binding,mapping_record_object_id=mapped['mapping_record_object_id'],
            history_blob_member=mapped['history_blob_member'],asm_body_index=binding['asm_body_index'],
            profile_cache_correspondence=correspondence,source_sketch=sketch,source_sketch_frame_provenance=frame,
            native_profile_lines=native_lines,native_profile_points=list(native_points.values()),
            extrude_controls=controls,extrude_direction_component=[0.,0.,1.],
            direction_scope='Observed native +Z vector and identity Sketch frame only',
            source_native_records=[raw(owner),raw(anchor_id),raw(native),raw(item['descriptor_object_id'])]))
        owner_ids += [owner,sketch['object_id']]
    if len({g['native_body_object_id'] for g in source_groups}) != len(source_groups):
        raise ValueError('Scale reconstruction selected BODY identities overlap')
    result_anchors = [a for a in selections['body_anchors'] if a['source_owner_object_id'] == receiver]
    if result_anchors:
        raise ValueError('Scale reconstruction observed same-BODY family cannot admit a Scale-owned result anchor')

    point_proof = dict(selection=copy.deepcopy(point),backend=raw(backend_id),stored_method_code=method,
        center_position_cm=center,coordinate_scope='Stored native backend in the independently qualified parent component; no occurrence transform')
    if point_entity['kind'] in ('ConstructionPoint','SketchPoint'):
        _, descriptor = typed(descriptor_id,'5A1BF548-241F-46FD-9FB5-E4B05126EB9D')
        if (len(descriptor) != 263 or reference(descriptor,252) != receiver
                or point['descriptor_object_id'] != descriptor_id):
            raise ValueError('Scale reconstruction center owned descriptor differs')
        leaf_id = reference(descriptor,2)
        point_proof['native_selection_records'] = [raw(descriptor_id),raw(leaf_id)]
        if point_entity['kind'] == 'SketchPoint':
            if method != 10:
                raise ValueError('Scale reconstruction SketchPoint center method differs')
            sketches = [f for f in private if f['kind'] == 'Sketch' and f['sketch_object_id'] == point_entity['sketch_object_id']]
            if len(sketches) != 1:
                raise ValueError('Scale reconstruction center Sketch ambiguous')
            point_proof['source_sketch_frame_provenance'] = sketch_frame(sketches[0])
            point_proof['native_point'] = point_native(point_entity['object_id'],point_entity['sketch_object_id'])
            owner_ids.append(sketches[0]['object_id'])
        else:
            if method != 9:
                raise ValueError('Scale reconstruction ConstructionPoint center method differs')
            identity = point_entity['object_id']
            _, native_point = typed(identity,'0E18EEF2-0D6F-480C-997E-5EBC7369AE5F')
            if 'origin_container_object_id' in point_entity:
                container_id = point_entity['origin_container_object_id']
                _, container = typed(container_id,'2972A3B8-3627-49BC-8C3D-18707605EC44')
                n = struct.unpack_from('<I',container,4)[0]
                if (container[:4] != bytes(4) or n != 7 or len(container) != 19+11*n
                        or [reference(container,8+11*i) for i in range(n)].count(identity) != 1
                        or reference(native_point,len(native_point)-11) != container_id):
                    raise ValueError('Scale reconstruction origin point/container membership differs')
                component_ids.add(reference(container,len(container)-11))
                point_proof['component_route'] = dict(kind='OriginContainer',container=raw(container_id),native_point=raw(identity))
            else:
                definition_rows = [d for d in definitions['definitions'] if d['feature_object_id'] == point_entity['feature_object_id']]
                if len(definition_rows) != 1 or definition_rows[0]['definition_kind'] != 'ByPoint':
                    raise ValueError('Scale reconstruction custom point explicit ByPoint definition unresolved')
                definition = definition_rows[0]
                collection_id = reference(native_point,len(native_point)-11)
                _, collection = typed(collection_id,'A8635B5F-1E2C-45FD-8BA9-0173B0FEB75E')
                count = struct.unpack_from('<I',collection,2)[0]
                repeat = len(collection)-15-11*count
                if (collection[:2] != bytes(2) or count != 1 or len(collection) != 51+22*count
                        or reference(collection,6) != identity or struct.unpack_from('<I',collection,repeat)[0] != count
                        or reference(collection,repeat+4) != identity):
                    raise ValueError('Scale reconstruction custom point repeated collection differs')
                component_ids.add(reference(collection,len(collection)-11))
                support = definition['support_inputs'][0]['entity']
                sketches = [f for f in private if f['kind'] == 'Sketch' and f['sketch_object_id'] == support['sketch_object_id']]
                if len(sketches) != 1:
                    raise ValueError('Scale reconstruction custom point support Sketch ambiguous')
                point_proof['source_sketch_frame_provenance'] = sketch_frame(sketches[0])
                point_proof['definition'] = definition
                point_proof['component_route'] = dict(kind='RepeatedConstructionPointCollection',
                    collection=raw(collection_id),native_point=raw(identity))
                owner_ids += [point_entity['feature_object_id'],sketches[0]['object_id']]
        if not same(center,point_entity['position_cm']):
            raise ValueError('Scale reconstruction explicit point/backend coordinates disagree')
    elif point_entity['kind'] == 'BRepVertexRecipe':
        if method != 1 or point['descriptor_object_id'] != descriptor_id:
            raise ValueError('Scale reconstruction vertex recipe method/descriptor differs')
        body_component(point_entity['native_body_object_id'])
        if point_entity['native_body_object_id'] not in {g['native_body_object_id'] for g in source_groups}:
            raise ValueError('Scale reconstruction vertex center anchored BODY is outside selected source group')
        point_proof['initial_cache_incidence'] = decode_selection_recipe_incidence(data,records,private,member,members,
            mapping,selections,descriptor_ids=[descriptor_id])
        point_proof['initial_cache_vertex_identity'] = None
        point_proof['coordinate_scope'] = ('Literal native backend/typed vertex-context coordinate caches agree; '
            'missing initial recipe-name correspondence is retained, no coordinate choice of a VERTEX')
    else:
        raise ValueError('Scale reconstruction point kind outside observed native routes')
    if len(component_ids) != 1:
        raise ValueError('Scale reconstruction source/point/component frames disagree')
    component = next(iter(component_ids))
    typed(component,COMPONENT)
    dependency_owners = [dict(object_id=i) for i in dict.fromkeys(owner_ids)]
    decode_dependencies(data,records,dependency_owners,assembly)
    if any(f.get('component_object_id') != component or 'component_scope_object_id' not in f for f in dependency_owners):
        raise ValueError('Scale reconstruction fresh receiver/source/point dependency component scopes disagree')
    return dict(feature_object_id=receiver,settings=settings,source_groups=source_groups,point_provenance=point_proof,
        component_provenance=dict(component_object_id=component,body_ownership=body_proofs,
            dependency_scopes=dependency_owners,assembly_scope=assembly['scope']),
        feature_native_record=raw(receiver),source_group_count=len(source_groups),
        scale_owned_result_anchors=[],cache_lifecycle_scope='Explicit selected source Extrude anchor remains mapped to initial stored BODY; no distinct Scale result or before/current state is assigned',
        API_handle_identity=None,persistent_identity=None,qualified_historical_state=None,scope=SCOPE)
