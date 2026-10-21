"""Fresh native solid NewBody Extrude profiles, extents and component frames.

This source proof does not choose cached cap/side entities, interpret a literal
journal view as a modeling state, or reconstruct ToEntity/ThroughAll/thin/boolean
features. Geometry reconstruction is a separate consumer of these native inputs.
"""
import copy
import math
import struct
import uuid

from decode_assembly import decode_assembly, SKETCH_BASE_GUID
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_properties import BODY, COLLECTION, decode_body_properties
from decode_body_selections import ANCHOR, decode_body_selections
from decode_dependencies import decode_dependencies
from decode_extrude import decode_extrude
from decode_parameters import decode_stream, read_string
from decode_placement import decode_placement, rigid_matrix, transform_vector
from decode_profile_cache_correspondence import decode_profile_cache_correspondence
from decode_profiles import PROFILE_DESCRIPTOR_GUID, PROFILE_LOOP_GUID, read_loops
from decode_sketch import attributes, decode_sketches, numbers, reference

EXTRUDE = 'DD405BC2-D673-44F0-8833-5CB2A1C186C7'
LINE = 'DCA267ED-D615-4934-B64F-AD805E8003E2'
CIRCLE = 'F0130424-8B7E-4092-93C9-1CA807482534'
POINT = 'C2CEDAE7-1716-47C1-B7B1-07B70081D0FB'
SKETCH = '44A64366-4BD3-4B24-881A-F94C206E8F2D'
COMPONENT = 'E03784ED-5E19-4E14-B9F2-3B07017018CD'
SCOPE = ('Observed solid NewBody Extrude, complete Circle or four-Line profile, native POINT/curve '
    'incidence and rigid Sketch/component frame; one/two-sided/symmetric Distance, ProfilePlane/Offset '
    'start and signed taper operands retained. Creator-owned BODY and same-asset stored-ID mapping '
    'qualify the reconstruction input only; cache lifecycle, cap identity, persistent/API identity '
    'and general feature regeneration remain unresolved.')


def qualify_extrusion_source_operands(data, records, features, member, members,
                                     body_blob_bindings, feature, *, allow_plane_limits=False):
    """Return a fresh creator/source row, None outside Extrude, or ValueError."""
    if feature.get('class_guid') != EXTRUDE:
        return None
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    if any(len(rows) != 1 for rows in grouped.values()):
        raise ValueError('Extrusion source duplicate primary namespace')

    def typed(identity, guid=None):
        rows = grouped.get(identity, [])
        if len(rows) != 1 or guid is not None and rows[0].class_guid != guid:
            raise ValueError('Extrusion source typed identity missing, ambiguous or wrong class')
        return rows[0],data[rows[0].body:rows[0].end]

    def raw(identity, guid=None):
        record,payload = typed(identity,guid)
        return dict(object_id=identity,class_guid=record.class_guid,record_offset=record.start,
            body_offset=record.body,end_offset=record.end,payload_hex=payload.hex())

    receiver = feature['object_id']
    record,body = typed(receiver,EXTRUDE)
    supplied = [f for f in features if f['object_id'] == receiver]
    if (len(supplied) != 1 or feature.get('record_offset') != record.start
            or supplied[0].get('class_guid') != EXTRUDE):
        raise ValueError('Extrusion source receiver metadata inconsistent')
    if member not in members or members[member] != data or not member.endswith('/FusionDesignSegmentType1/BulkStream.dat'):
        raise ValueError('Extrusion source exact native member/bytes scope differs')
    from decode_basics import named_features, attach_parameters
    private = named_features(data,records)
    parameters,_ = decode_stream(data,records)
    attach_parameters(data,records,private,parameters)
    decode_sketches(data,records,private)
    decode_placement(data,records,private)
    assembly = decode_assembly(data,records,private)
    properties = decode_body_properties(data,records,assembly)
    fresh_rows = [f for f in private if f['object_id'] == receiver]
    if len(fresh_rows) != 1:
        raise ValueError('Extrusion source fresh receiver label missing or ambiguous')
    fresh = fresh_rows[0]
    keys = ('binding_object_id','parameter_object_id','role','raw_float64','display_units')
    if ([{k:p.get(k) for k in keys} for p in supplied[0].get('parameters',[])] !=
            [{k:p.get(k) for k in keys} for p in fresh['parameters']]):
        raise ValueError('Extrusion source supplied parameters disagree with fresh reciprocal bindings')
    settings,reasons = decode_extrude(body,fresh,allow_surface=True)
    extent,start = settings['extent'],settings['start']
    plane_limit_provenance = None
    if allow_plane_limits and (start['kind'] == 'FromEntity' or extent['side_one']['condition'] == 'ToEntity'):
        from decode_extrusion_plane_limits import qualify_extrusion_plane_limits
        plane_limit_provenance = qualify_extrusion_plane_limits(data,records,private,fresh,settings)
    if ((reasons and plane_limit_provenance is None) or settings['operation']['kind'] != 'NewBody' or settings['is_solid'] is not True
            or extent['mode'] not in ('OneSided','TwoSided','Symmetric')
            or start['kind'] not in ('ProfilePlane','Offset') and plane_limit_provenance is None):
        raise ValueError('Extrusion reconstruction requires solid NewBody Distance with ProfilePlane/Offset start')
    sides = [extent['side_one']] + ([extent['side_two']] if extent['mode'] == 'TwoSided' else [])
    if (any((s['condition'] != 'Distance' or s['uninterpreted_flags'] != 0) and plane_limit_provenance is None
            or 'distance_cm' in s and (not math.isfinite(s['distance_cm']) or s['distance_cm'] == 0)
            or not math.isfinite(s.get('taper_angle_radians',0.)) for s in sides)
            or start['kind'] == 'Offset' and not math.isfinite(start['offset_cm'])
            or settings['stored_second_extent_enabled'] != (0 if extent['mode'] == 'OneSided' else 1)
            or extent['mode'] == 'Symmetric' and extent.get('distance_convention') not in ('FullLength','HalfLength')
            or any(not math.isfinite(v) for v in extent['stored_direction_vector'])):
        raise ValueError('Extrusion source active distance/taper/start operands outside finite observed family')
    selections = decode_body_selections(data,records)
    anchors = [a for a in selections['body_anchors'] if a['source_owner_object_id'] == receiver]
    if len(anchors) != 1:
        raise ValueError('Extrusion source requires one unique creator-owned BODY anchor')
    anchor = anchors[0]
    native,anchor_id = anchor['native_body_object_id'],anchor['object_id']
    typed(native,BODY)
    _,anchor_body = typed(anchor_id,ANCHOR)
    if len(anchor_body) != 102 or reference(anchor_body,80) != native or reference(anchor_body,91) != receiver:
        raise ValueError('Extrusion source creator/anchor/BODY reciprocity differs')
    descriptors = []
    for r in grouped.values():
        r = r[0]
        if r.class_guid == PROFILE_DESCRIPTOR_GUID:
            payload = data[r.body:r.end]
            if len(payload) >= 17 and reference(payload,len(payload)-11) == receiver:
                descriptors.append((r,payload))
    if len(descriptors) != 1:
        raise ValueError('Extrusion source requires one explicitly owned profile descriptor')
    descriptor,db = descriptors[0]
    if db[:2] != bytes(2) or struct.unpack_from('<I',db,13)[0] != 1:
        raise ValueError('Extrusion source profile descriptor prefix/count differs')
    namespace,cursor = read_string(db,17)
    sketch_text,cursor = read_string(db,cursor)
    if len(namespace) != 36 or not sketch_text.isascii() or not sketch_text.isdecimal():
        raise ValueError('Extrusion source explicit profile Sketch namespace differs')
    uuid.UUID(namespace)
    sketch_id = int(sketch_text)
    typed(sketch_id,SKETCH)
    sketches = [s for s in private if s['kind'] == 'Sketch' and s['sketch_object_id'] == sketch_id]
    if len(sketches) != 1:
        raise ValueError('Extrusion source native Sketch metadata missing or ambiguous')
    sketch = sketches[0]
    definition_id = reference(db,2)
    _,definition = typed(definition_id,PROFILE_LOOP_GUID)
    loops = read_loops(definition,descriptor.object_id,sketch)
    if len(loops) != 1 or loops[0]['is_outer'] is not True:
        raise ValueError('Extrusion source requires one complete outer profile loop')
    refs = loops[0]['curve_references']
    kinds = [r['entity_kind'] for r in refs]
    profile_kind = 'Circle' if kinds == ['Circle'] else 'FourLine' if kinds == ['Line']*4 else None
    if profile_kind is None:
        raise ValueError('Extrusion source profile outside complete Circle/four-Line family')
    bases = [r for r in records if not r.is_primary and r.object_id == sketch_id and r.class_guid == SKETCH_BASE_GUID]
    if len(bases) != 1:
        raise ValueError('Extrusion source Sketch base missing or ambiguous')
    base = bases[0]
    raw_base = data[base.body:base.end]
    transform_id = reference(raw_base,0)
    transform,matrix_payload = typed(transform_id,'F47A46FB-DA27-4AFA-8A72-1B38FA596E23')
    matrix = rigid_matrix(sketch.get('placement',{}).get('sketch_to_component_matrix',[]))
    if (len(matrix_payload) not in (15,143) or matrix_payload[:2] != bytes(2) or matrix_payload[-12] != 0
            or len(matrix_payload) == 15 and matrix_payload[:4] != bytes.fromhex('00000100')
            or len(matrix_payload) == 143 and (matrix_payload[2] != 0 or numbers(matrix_payload,3,16) != matrix)
            or sketch['placement'].get('transform_object_id') != transform_id
            or sketch['placement'].get('record_offset') != transform.start):
        raise ValueError('Extrusion source native rigid Sketch frame differs')
    component = reference(matrix_payload,len(matrix_payload)-11)
    typed(component,COMPONENT)
    if sketch.get('component_object_id') != component:
        raise ValueError('Extrusion source Sketch collection/transform component differs')
    lines,circles,points = [],[],{}
    for ref in refs:
        identity = ref['entity_id']
        _,payload = typed(identity,LINE if profile_kind == 'FourLine' else CIRCLE)
        props,cursor = attributes(payload,2)
        matches = [g for g in sketch['geometry'] if g['object_id'] == identity and g['kind'] == ref['entity_kind']]
        expected_length = 171 if profile_kind == 'FourLine' else 162
        if (len(matches) != 1 or payload[:2] != b'\0\1' or len(payload)-cursor != expected_length
                or props.get('crv_primary_id') != ref['entity_tag'] or props.get('crv_secondary_id') != 0
                or reference(payload,len(payload)-11) != sketch_id):
            raise ValueError('Extrusion source native curve tag/frame/owner differs')
        geometry = matches[0]
        values = numbers(payload,cursor,12)
        if not all(math.isfinite(v) for v in values):
            raise ValueError('Extrusion source curve has nonfinite coefficients')
        if profile_kind == 'FourLine':
            if reference(payload,cursor+107) != geometry['start_point_id'] or reference(payload,cursor+96) != geometry['end_point_id']:
                raise ValueError('Extrusion source Line endpoint identities differ')
            ids = [geometry['start_point_id'],geometry['end_point_id']]
            lines.append(dict(line_object_id=identity,start_point_id=ids[0],end_point_id=ids[1],
                entity_tag=ref['entity_tag'],geometry=geometry,native_record=raw(identity)))
        else:
            ids = [geometry['center_point_id']]
            if reference(payload,cursor+96) != ids[0] or not math.isfinite(geometry['radius_cm']) or geometry['radius_cm'] <= 0:
                raise ValueError('Extrusion source Circle centre/radius differs')
            normal,axis = geometry['normal'],geometry['reference_axis']
            if (not math.isclose(math.hypot(*normal),1.,abs_tol=1e-10)
                    or not math.isclose(math.hypot(*axis),1.,abs_tol=1e-10)
                    or abs(sum(a*b for a,b in zip(normal,axis))) > 1e-10
                    or geometry['center_cm'][2] != 0 or abs(abs(normal[2])-1.) > 1e-10):
                raise ValueError('Extrusion source Circle native profile plane/frame differs')
            circles.append(dict(circle_object_id=identity,center_point_id=ids[0],entity_tag=ref['entity_tag'],
                radius_cm=geometry['radius_cm'],center_cm=geometry['center_cm'],normal=normal,
                reference_axis=axis,geometry=geometry,native_record=raw(identity)))
        for point_id in ids:
            _,point_payload = typed(point_id,POINT)
            pp,pc = attributes(point_payload,2)
            position = numbers(point_payload,pc+19,3)
            if (point_payload[:2] != b'\0\1' or len(point_payload)-pc != 99 or 'pt_tag' not in pp
                    or reference(point_payload,len(point_payload)-11) != sketch_id
                    or any(not math.isfinite(v) for v in position) or position[2] != 0):
                raise ValueError('Extrusion source typed native POINT owner/plane differs')
            points[point_id] = dict(point_object_id=point_id,entity_tag=pp['pt_tag'],position_cm=position,native_record=raw(point_id))
    if profile_kind == 'FourLine':
        degree = {i:sum(i in (line['start_point_id'],line['end_point_id']) for line in lines) for i in points}
        reachable = {next(iter(points))} if points else set()
        for _ in range(4):
            reachable.update(i for line in lines if {line['start_point_id'],line['end_point_id']} & reachable
                for i in (line['start_point_id'],line['end_point_id']))
        if (len(points) != 4 or len({r['line_object_id'] for r in lines}) != 4 or set(degree.values()) != {2}
                or reachable != set(points) or any(r['start_point_id'] == r['end_point_id'] for r in lines)):
            raise ValueError('Extrusion source native four-Line POINT incidence cycle incomplete')
    binding_input = dict(decoded=[dict(mapping_record_object_id=m['mapping_record_object_id'],owner_object_id=m['owner_object_id'],
        history_blob_member=m['history_blob_member'],body_count=m['body_count'],bindings=[dict(stored_handle=b['stored_handle'],
        native_body_object_id=b['native_body_object_id']) for b in m['bindings']]) for m in body_blob_bindings.get('decoded',[])])
    mappings = decode_body_asm_identifiers(data,records,member,members,binding_input)
    mapped = [(m,b) for m in mappings['decoded'] for b in m['bindings'] if b['native_body_object_id'] == native]
    if len(mapped) != 1:
        raise ValueError('Extrusion source BODY lacks unique same-asset stored-ID mapping')
    mapping,binding = mapped[0]
    profiles = decode_profile_cache_correspondence(data,records,private,member,members,mappings)
    matches = [r for r in profiles['decoded'] if r['source_feature_object_id'] == receiver]
    if len(matches) > 1:
        raise ValueError('Extrusion source profile-cache correspondence ambiguous')
    profile_cache = matches[0] if matches else None
    diagnostics = [r for r in profiles['unresolved'] if r['source_feature_object_id'] == receiver]
    props = [b for b in properties['bodies'] if b['object_id'] == native]
    if len(props) != 1 or 'collection_object_id' not in props[0] or props[0].get('component_object_id') != component:
        raise ValueError('Extrusion source native BODY/Sketch component differs')
    prop = props[0]
    collection_id = prop['collection_object_id']
    collections = [c for c in properties['collections'] if c['object_id'] == collection_id]
    _,collection = typed(collection_id,COLLECTION)
    _,native_body = typed(native,BODY)
    if (len(collections) != 1 or native not in collections[0]['body_object_ids']
            or reference(native_body,len(native_body)-11) != collection_id or reference(collection,len(collection)-11) != component):
        raise ValueError('Extrusion source BODY/repeated collection/component backlinks differ')
    dependencies = [dict(object_id=i) for i in dict.fromkeys((receiver,sketch['object_id']))]
    decode_dependencies(data,records,dependencies,assembly)
    if any(f.get('component_object_id') != component or 'component_scope_object_id' not in f for f in dependencies):
        raise ValueError('Extrusion source fresh dependency component proof differs')
    group = dict(source_feature_object_id=receiver,native_body_object_id=native,body_anchor_object_id=anchor_id,
        source_anchor=anchor,binding=binding,mapping_record_object_id=mapping['mapping_record_object_id'],
        history_blob_member=mapping['history_blob_member'],asm_body_index=binding['asm_body_index'],
        native_profile_kind=profile_kind,native_profile_selection=dict(profile_descriptor_object_id=descriptor.object_id,
            profile_loop_definition_object_id=definition_id,native_sketch_object_id=sketch_id,namespace_text=namespace,
            profile_loops=loops,descriptor_native_record=raw(descriptor.object_id),loop_native_record=raw(definition_id)),
        native_profile_lines=lines,native_profile_circles=circles,native_profile_points=list(points.values()),
        source_sketch=sketch,source_sketch_frame_provenance=dict(component_object_id=component,
            sketch_base_record_offset=base.start,sketch_base_payload_hex=raw_base.hex(),transform=raw(transform_id),
            canonical_placement=copy.deepcopy(sketch['placement']),collection_component_association=sketch['component_association']),
        extrude_controls=settings,stored_direction_vector=extent['stored_direction_vector'],
        sketch_normal_component=transform_vector(matrix,[0.,0.,1.]),
        direction_scope='Stored Extrude vector and independent native Sketch-to-component frame; consumer must qualify their relation',
        profile_cache_correspondence=profile_cache,profile_cache_diagnostics=diagnostics,
        source_native_records=[raw(receiver),raw(anchor_id),raw(native)])
    result = dict(feature_object_id=receiver,settings=settings,source_groups=[group],source_group_count=1,
        component_provenance=dict(component_object_id=component,body_ownership=[dict(native_body_object_id=native,
            body_properties=prop,collection=collections[0])],dependency_scopes=dependencies,assembly_scope=assembly['scope']),
        feature_native_record=raw(receiver),API_handle_identity=None,persistent_identity=None,qualified_historical_state=None,
        cache_lifecycle_scope='Creator-owned native BODY and initial stored-ID association only; later mutations or literal-view slots are not assigned chronological state',scope=SCOPE)
    if plane_limit_provenance is not None:
        group['plane_limit_provenance'] = plane_limit_provenance
        result['plane_limit_provenance'] = plane_limit_provenance
        result['scope'] = SCOPE+' '+plane_limit_provenance['scope']
    return result
