"""Fresh native Shell selections and source Sketch/Extrude operand proofs.

This reader does not assign a removed FACE by coordinates, construct a hollow
solid, or label a literal cache view as a chronological modeling state.
"""
import copy
import math
import struct

from decode_assembly import decode_assembly, SKETCH_BASE_GUID
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_properties import BODY, COLLECTION, decode_body_properties
from decode_body_selections import ANCHOR, HELPER, SUPPORT, decode_body_selections
from decode_body_tool_selections import decode_body_tool_selections
from decode_body_tools import decode_body_tool
from decode_dependencies import decode_dependencies
from decode_extrude import decode_extrude
from decode_one_face_edge_sources import _replay_recipe
from decode_parameters import decode_stream
from decode_placement import IDENTITY, decode_placement, rigid_matrix
from decode_profile_cache_correspondence import decode_profile_cache_correspondence
from decode_recipe_components import decode_counted_recipe
from decode_selection import known_construction_entities
from decode_selection_context_recipes import TOPOLOGY, decode_selection_context_recipes
from decode_sketch import attributes, decode_sketches, numbers, reference

SHELL = 'E8063467-BC05-4688-8196-AECB90F0EFEE'
EXTRUDE = 'DD405BC2-D673-44F0-8833-5CB2A1C186C7'
LINE = 'DCA267ED-D615-4934-B64F-AD805E8003E2'
POINT = 'C2CEDAE7-1716-47C1-B7B1-07B70081D0FB'
COMPONENT = 'E03784ED-5E19-4E14-B9F2-3B07017018CD'
SCOPE = ('Observed Shell scalar controls and owned Body/Face operands, historical source '
    'anchors, complete counted removed-FACE recipe bytes and independent four-Line '
    'Sketch/NewBody Extrude/component provenance. Removed-face cache incidence and hollow '
    'geometry are qualified separately; no API/current/persistent identity or chronology.')


def qualify_shell_source_operands(data, records, features, member, members,
                                   body_blob_bindings, feature):
    """Return a fresh source row, None outside Shell, or scoped ValueError."""
    if feature.get('class_guid') != SHELL:
        return None
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    if any(len(rows) != 1 for rows in grouped.values()):
        raise ValueError('Shell source duplicate primary namespace')

    def typed(identity, guid=None):
        rows = grouped.get(identity, [])
        if len(rows) != 1 or guid is not None and rows[0].class_guid != guid:
            raise ValueError('Shell source native identity missing, ambiguous or wrong class')
        record = rows[0]
        return record, data[record.body:record.end]

    def raw(identity, guid=None):
        record, payload = typed(identity, guid)
        return dict(object_id=identity,class_guid=record.class_guid,record_offset=record.start,
            body_offset=record.body,end_offset=record.end,payload_hex=payload.hex())

    receiver = feature['object_id']
    record, body = typed(receiver,SHELL)
    supplied = [f for f in features if f['object_id'] == receiver]
    if (len(supplied) != 1 or feature.get('record_offset') != record.start
            or supplied[0].get('record_offset') != record.start or supplied[0].get('kind') != 'Shell'):
        raise ValueError('Shell source receiving metadata inconsistent')
    if member not in members or members[member] != data or not member.endswith('/FusionDesignSegmentType1/BulkStream.dat'):
        raise ValueError('Shell source exact native member/bytes scope differs')
    from decode_basics import named_features, attach_parameters
    private = named_features(data,records)
    parameters, _ = decode_stream(data,records)
    attach_parameters(data,records,private,parameters)
    decode_sketches(data,records,private)
    decode_placement(data,records,private)
    assembly = decode_assembly(data,records,private)
    properties = decode_body_properties(data,records,assembly)
    rows = [f for f in private if f['object_id'] == receiver]
    if len(rows) != 1:
        raise ValueError('Shell source fresh receiving feature label missing or ambiguous')
    fresh = rows[0]

    def parameters_equal(identity):
        old = [f for f in features if f['object_id'] == identity]
        new = [f for f in private if f['object_id'] == identity]
        keys = ('binding_object_id','parameter_object_id','role','raw_float64','display_units')
        if (len(old) != 1 or len(new) != 1 or
                [{k:p.get(k) for k in keys} for p in old[0].get('parameters',[])] !=
                [{k:p.get(k) for k in keys} for p in new[0]['parameters']]):
            raise ValueError('Shell source supplied parameters disagree with fresh reciprocal bindings')

    parameters_equal(receiver)
    settings = decode_body_tool(data,records,body,fresh,known_construction_entities(data,records,private))
    thicknesses = [settings[k] for k in ('inside_thickness_cm','outside_thickness_cm') if settings[k] is not None]
    if not thicknesses or any(not math.isfinite(value) or value <= 0 for value in thicknesses):
        raise ValueError('Shell source requires finite positive active thicknesses')
    fresh['tool_settings'] = settings
    selections = decode_body_selections(data,records)
    inputs = decode_body_tool_selections(data,records,[fresh],selections)
    rows = [r for r in inputs['decoded'] if r['feature_object_id'] == receiver]
    if len(rows) != 1:
        raise ValueError('Shell source explicit Body/Face input selection unresolved')
    settings.update(rows[0]['settings'])
    if not 1 <= settings['input_count'] <= 2:
        raise ValueError('Shell source requires one or two captured Body/Face operands')
    contexts = decode_selection_context_recipes(data,records,selections)
    selected_inputs = []
    for ordinal,item in enumerate(settings['input_selections']):
        native = copy.deepcopy(item)
        native['operand_index'] = ordinal
        did = item['descriptor_object_id']
        _, descriptor = typed(did,TOPOLOGY if item['kind'] == 'Face' else '9716F783-676D-42E0-93F9-EBF273E7C035')
        native['native_descriptor'] = raw(did)
        if item['kind'] == 'Face':
            if (len(descriptor) != 276 or descriptor[:4] != bytes(4)
                    or descriptor[209:223] != struct.pack('<I',16)+bytes(10)
                    or descriptor[223:227] != b'\1\1\0\0' or descriptor[227:235] != bytes(8)
                    or descriptor[235:239] != b'\1\1\0\0' or descriptor[250:253] != b'\1\0\0'
                    or descriptor[264] != 0 or reference(descriptor,265) != receiver):
                raise ValueError('Shell source Face descriptor complete trailer/owner framing differs')
            ctx = [r for r in contexts['contexts'] if r['descriptor_object_id'] == did and r['owner_object_id'] == receiver]
            if (len(ctx) != 1 or ctx[0]['descriptor_recipe'] != item['recipe']
                    or ctx[0]['native_body_object_id'] != item['native_body_object_id']
                    or ctx[0]['source_owner_object_id'] != item['source_owner_object_id']):
                raise ValueError('Shell source Face recipe/context namespace or anchor differs')
            helper_id, support_id = reference(descriptor,239),reference(descriptor,253)
            _, helper = typed(helper_id,HELPER)
            _, support = typed(support_id,SUPPORT)
            if (helper != bytes.fromhex('0001000000000000000000000000') or len(support) != 58
                    or support[:12] != bytes(6)+b'\1\1'+struct.pack('<I',1)
                    or reference(support,12) != item['source_owner_object_id']
                    or reference(support,31) != did or support[-8:] != bytes(8)):
                raise ValueError('Shell source Face source-support/helper reciprocity differs')
            recipe_record,_ = typed(item['recipe']['object_id'],'7ACC2A03-0261-4879-A14A-A93D661A5BDC')
            recipe = decode_counted_recipe(data,recipe_record)
            if (recipe['payload_kind'] != 'bounded_face_recipe_data' or recipe['payload_length'] != 476
                    or _replay_recipe(recipe) != data[recipe_record.body:recipe_record.end]):
                raise ValueError('Shell source complete counted 476-byte removed-FACE recipe replay differs')
            native.update(counted_recipe=recipe,exact_counted_recipe_payload_replay=True,
                typed_context=ctx[0],descriptor_support=raw(support_id),descriptor_helper=raw(helper_id),
                recipe_native_record=raw(recipe_record.object_id),removed_face_cache_identity=None)
        elif item['kind'] != 'Body':
            raise ValueError('Shell source selected kind outside observed Body/Face operands')
        selected_inputs.append(native)
    binding_input = dict(decoded=[dict(mapping_record_object_id=m['mapping_record_object_id'],
        owner_object_id=m['owner_object_id'],history_blob_member=m['history_blob_member'],body_count=m['body_count'],
        bindings=[dict(stored_handle=b['stored_handle'],native_body_object_id=b['native_body_object_id'])
            for b in m['bindings']]) for m in body_blob_bindings.get('decoded',[])])
    mappings = decode_body_asm_identifiers(data,records,member,members,binding_input)
    profiles = decode_profile_cache_correspondence(data,records,private,member,members,mappings)
    groups, component_ids, body_ownership, owner_ids = [],set(),[],[receiver]
    # Group only by explicit native BODY/anchor/source-owner identities. Selection
    # order stays in selected_inputs and is never a source/result pairing rule.
    keys = list(dict.fromkeys((s['native_body_object_id'],s['body_anchor_object_id'],s['source_owner_object_id'])
        for s in selected_inputs))
    for native,anchor_id,owner in keys:
        typed(owner,EXTRUDE)
        parameters_equal(owner)
        source_rows = [f for f in private if f['object_id'] == owner]
        if len(source_rows) != 1:
            raise ValueError('Shell source fresh Extrude metadata missing or ambiguous')
        source = source_rows[0]
        source_anchors = [a for a in selections['body_anchors'] if a['source_owner_object_id'] == owner]
        _, anchor = typed(anchor_id,ANCHOR)
        if (len(source_anchors) != 1 or source_anchors[0]['object_id'] != anchor_id
                or source_anchors[0]['native_body_object_id'] != native or len(anchor) != 102
                or reference(anchor,80) != native or reference(anchor,91) != owner):
            raise ValueError('Shell source Extrude/anchor/BODY identities differ')
        _, source_body = typed(owner,EXTRUDE)
        controls,reasons = decode_extrude(source_body,source,allow_surface=True)
        side = controls['extent']['side_one']
        if (reasons or controls['operation']['kind'] != 'NewBody' or controls['is_solid'] is not True
                or controls['extent']['mode'] != 'OneSided' or controls['start']['kind'] != 'ProfilePlane'
                or controls['stored_second_extent_enabled'] != 0 or side['condition'] != 'Distance'
                or side.get('taper_angle_radians') != 0 or side['uninterpreted_flags'] != 0
                or not math.isfinite(side['distance_cm']) or side['distance_cm'] <= 0
                or controls['extent']['stored_direction_vector'] != [0.,0.,1.]):
            raise ValueError('Shell source requires solid untapered positive +Z one-sided NewBody Extrude')
        rows = [r for r in profiles['decoded'] if r['source_feature_object_id'] == owner]
        if len(rows) != 1 or rows[0]['native_body_object_id'] != native or rows[0]['body_anchor_object_id'] != anchor_id:
            raise ValueError('Shell source complete native profile/cache correspondence unresolved')
        profile = rows[0]
        loops = profile['profile_loops']
        if len(loops) != 1 or loops[0]['is_outer'] is not True or len(loops[0]['curve_references']) != 4:
            raise ValueError('Shell source requires one complete four-Line outer profile')
        sketches = [f for f in private if f['kind'] == 'Sketch' and f['sketch_object_id'] == profile['native_sketch_object_id']]
        if len(sketches) != 1:
            raise ValueError('Shell source native Sketch ambiguous')
        sketch = sketches[0]
        bases = [r for r in records if not r.is_primary and r.object_id == sketch['sketch_object_id']
            and r.class_guid == SKETCH_BASE_GUID]
        if len(bases) != 1:
            raise ValueError('Shell source Sketch base ambiguous')
        base = bases[0]
        raw_base = data[base.body:base.end]
        transform_id = reference(raw_base,0)
        transform, matrix_payload = typed(transform_id,'F47A46FB-DA27-4AFA-8A72-1B38FA596E23')
        matrix = rigid_matrix(sketch.get('placement',{}).get('sketch_to_component_matrix',[]))
        if (len(matrix_payload) != 15 or matrix_payload[:4] != bytes.fromhex('00000100') or matrix != IDENTITY
                or sketch['placement'].get('transform_object_id') != transform_id
                or sketch['placement'].get('record_offset') != transform.start):
            raise ValueError('Shell source requires observed identity native Sketch frame')
        component = reference(matrix_payload,len(matrix_payload)-11)
        typed(component,COMPONENT)
        if sketch.get('component_object_id') != component:
            raise ValueError('Shell source Sketch collection/transform component differs')
        component_ids.add(component)
        lines, points = [],{}
        for curve in profile['source_curves']:
            identity = curve['native_entity_object_id']
            _, payload = typed(identity,LINE)
            props,cursor = attributes(payload,2)
            geometry = [g for g in sketch['geometry'] if g['object_id'] == identity and g['kind'] == 'Line']
            if (len(geometry) != 1 or payload[:2] != b'\0\1' or len(payload)-cursor != 171
                    or props.get('crv_primary_id') != curve['native_entity_tag'] or props.get('crv_secondary_id') != 0
                    or reference(payload,len(payload)-11) != sketch['sketch_object_id']):
                raise ValueError('Shell source typed native profile Line tag/frame/owner differs')
            geometry = geometry[0]
            if reference(payload,cursor+107) != geometry['start_point_id'] or reference(payload,cursor+96) != geometry['end_point_id']:
                raise ValueError('Shell source native Line endpoint references differ')
            for point_id in (geometry['start_point_id'],geometry['end_point_id']):
                _, point_payload = typed(point_id,POINT)
                pp,pc = attributes(point_payload,2)
                if (point_payload[:2] != b'\0\1' or len(point_payload)-pc != 99 or 'pt_tag' not in pp
                        or reference(point_payload,len(point_payload)-11) != sketch['sketch_object_id']):
                    raise ValueError('Shell source typed native profile POINT frame/owner differs')
                points[point_id] = dict(point_object_id=point_id,entity_tag=pp['pt_tag'],
                    position_cm=numbers(point_payload,pc+19,3),native_record=raw(point_id))
            lines.append(dict(line_object_id=identity,start_point_id=geometry['start_point_id'],
                end_point_id=geometry['end_point_id'],entity_tag=curve['native_entity_tag'],native_record=raw(identity)))
        degree = {i:sum(i in (line['start_point_id'],line['end_point_id']) for line in lines) for i in points}
        reachable = {next(iter(points))} if points else set()
        for _ in range(4):
            reachable.update(i for line in lines if {line['start_point_id'],line['end_point_id']} & reachable
                for i in (line['start_point_id'],line['end_point_id']))
        if (len(lines) != 4 or len(points) != 4 or len({line['line_object_id'] for line in lines}) != 4
                or set(degree.values()) != {2} or reachable != set(points)
                or any(line['start_point_id'] == line['end_point_id'] for line in lines)
                or any(p['position_cm'][2] != 0 for p in points.values())):
            raise ValueError('Shell source native four-Line profile POINT incidence/plane incomplete')
        mapped = [(m,b) for m in mappings['decoded'] for b in m['bindings'] if b['native_body_object_id'] == native]
        if len(mapped) != 1 or mapped[0][1]['asm_body_index'] != profile['asm_body_index']:
            raise ValueError('Shell source profile and fresh same-asset BODY mapping differ')
        mapping,binding = mapped[0]
        typed(native,BODY)
        props = [b for b in properties['bodies'] if b['object_id'] == native]
        if len(props) != 1 or 'collection_object_id' not in props[0] or props[0].get('component_object_id') != component:
            raise ValueError('Shell source native BODY/Sketch component ownership differs')
        body_property = props[0]
        collections = [c for c in properties['collections'] if c['object_id'] == body_property['collection_object_id']]
        _, collection = typed(body_property['collection_object_id'],COLLECTION)
        _, native_body = typed(native,BODY)
        if (len(collections) != 1 or native not in collections[0]['body_object_ids']
                or reference(native_body,len(native_body)-11) != body_property['collection_object_id']
                or reference(collection,len(collection)-11) != component):
            raise ValueError('Shell source BODY/repeated collection/component backlinks differ')
        body_ownership.append(dict(native_body_object_id=native,body_properties=body_property,collection=collections[0]))
        groups.append(dict(source_feature_object_id=owner,native_body_object_id=native,body_anchor_object_id=anchor_id,
            source_anchor=source_anchors[0],selected_input_indices=[s['operand_index'] for s in selected_inputs
                if (s['native_body_object_id'],s['body_anchor_object_id'],s['source_owner_object_id']) == (native,anchor_id,owner)],
            binding=binding,mapping_record_object_id=mapping['mapping_record_object_id'],
            history_blob_member=mapping['history_blob_member'],asm_body_index=binding['asm_body_index'],
            profile_cache_correspondence=profile,source_sketch=sketch,
            source_sketch_frame_provenance=dict(component_object_id=component,sketch_base_record_offset=base.start,
                sketch_base_payload_hex=raw_base.hex(),transform=raw(transform_id),
                canonical_placement=copy.deepcopy(sketch['placement']),collection_component_association=sketch['component_association']),
            native_profile_lines=lines,native_profile_points=list(points.values()),extrude_controls=controls,
            extrude_direction_component=[0.,0.,1.],direction_scope='Observed +Z stored vector and identity Sketch frame only',
            source_native_records=[raw(owner),raw(anchor_id),raw(native)]))
        owner_ids += [owner,sketch['object_id']]
    if len(component_ids) != 1:
        raise ValueError('Shell source selected BODY/Sketch components differ')
    component = next(iter(component_ids))
    dependency_owners = [dict(object_id=i) for i in dict.fromkeys(owner_ids)]
    decode_dependencies(data,records,dependency_owners,assembly)
    if any(f.get('component_object_id') != component or 'component_scope_object_id' not in f for f in dependency_owners):
        raise ValueError('Shell source receiving/source/Sketch fresh dependency components differ')
    if any(a['source_owner_object_id'] == receiver for a in selections['body_anchors']):
        raise ValueError('Shell source observed same-BODY family cannot admit Shell-owned result anchors')
    return dict(feature_object_id=receiver,settings=settings,selected_inputs=selected_inputs,source_groups=groups,
        component_provenance=dict(component_object_id=component,body_ownership=body_ownership,
            dependency_scopes=dependency_owners,assembly_scope=assembly['scope']),feature_native_record=raw(receiver),
        shell_owned_result_anchors=[],source_group_count=len(groups),
        source_to_result_pairing=None,API_handle_identity=None,persistent_identity=None,qualified_historical_state=None,
        cache_lifecycle_scope='Selected source Extrude anchors remain mapped to initial BODY caches; no separate Shell result or before/current state inferred',scope=SCOPE)
