"""Explicit Hole support-plane/face/sketch and extent input relationships.

Placement point identities remain with decode_hole_point_sources. This reader
keeps cached coordinates, native recipes and exact persistent topology distinct.
"""
import struct
import uuid

from decode_body_selections import ANCHOR, CONTEXT, HELPER, SUPPORT, decode_body_selections
from decode_brep_recipes import RECIPE_GUID
from decode_extrude import optional_reference
from decode_holes import decode_hole
from decode_parameters import read_string
from decode_recipe_components import decode_counted_recipe
from decode_selection import known_construction_entities, native_proxy_references
from decode_sketch import attributes, reference

HOLE = '1C037A07-4A15-43F6-ABFC-BBF61B9038D4'
AXIS = 'F2A7590D-6654-4674-B393-A2AEF4FEC48A'
POINT = '69EE2FA7-BCC7-449E-9CA9-976CEFDFED44'
TOPOLOGY = '5662F619-2281-4AD9-93DC-1FCFDA1062E7'
NATIVE_DESCRIPTOR = '5A1BF548-241F-46FD-9FB5-E4B05126EB9D'
IDENTITY_LEAF = '90055C05-546C-4EE7-B3C9-3DD922AD0C9C'
PROXY = '2CA5A1CD-C99B-4C9B-91AF-57989148E841'
CORE = '3CDCCC70-F7AD-47C4-9112-38A52DD802D8'
SCOPE = 'Owned Hole support face/origin-plane/sketch identities, distinct AtCenter edge recipe, native extent face/body inputs and reciprocal dependencies; exact persistent topology and geometry evaluation unresolved'


def decode_hole_supports(data, records, features, body_selections=None):
    """Additional decoded/unresolved/scope; no feature mutation or point duplication."""
    if not any(feature['kind'] == 'Hole' for feature in features):
        return {'decoded': [], 'unresolved': [], 'scope': SCOPE}
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: items[0] for identity, items in grouped.items() if len(items) == 1}
    bodies = body_selections if body_selections is not None else decode_body_selections(data, records)
    anchors = {a['object_id']: a for a in bodies['body_anchors']}
    body_descriptors = {d['object_id']: d for d in bodies['body_descriptors']}
    body_proxies = {p['selection_record_object_id']: p for p in bodies['selection_proxies']}
    known = known_construction_entities(data, records, features)

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Hole support typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    def text_uuid(payload, cursor):
        text, end = read_string(payload, cursor)
        if len(text) != 36:
            raise ValueError('Unobserved Hole support UUID length')
        uuid.UUID(text)
        return text, end

    def support(identity, owner, expected_sources=None):
        _, payload = typed(identity, SUPPORT)
        if len(payload) < 39 or payload[:6] != bytes(6):
            raise ValueError('Unobserved Hole reciprocal support prefix')
        count = struct.unpack_from('<I', payload, 8)[0]
        if (count > 64 or len(payload) != 39+19*count or payload[-8:] != bytes(8)
                or payload[6:8] != (b'\1\1' if count else bytes(2))):
            raise ValueError('Unobserved Hole reciprocal support count/extent')
        sources = [reference(payload, 12+19*i) for i in range(count)]
        if (reference(payload, 12+19*count) != owner or any(source not in primary for source in sources)
                or (expected_sources is not None and sources != expected_sources)):
            raise ValueError('Hole support source/owner correspondence is not reciprocal')
        return {'support_object_id': identity, 'source_record_object_ids': sources,
                'stored_payload_hex': payload.hex(), 'scope': 'Explicit counted source references and reciprocal owner;8-byte cache fields uninterpreted'}

    def helper(identity):
        _, payload = typed(identity, HELPER)
        if payload != bytes.fromhex('0001000000000000000000000000'):
            raise ValueError('Unobserved Hole input helper framing')

    def topology(identity, owner, allowed_kinds):
        _, payload = typed(identity, TOPOLOGY)
        if (len(payload) != 276 or payload[:3] != bytes(3) or payload[3] not in (0, 1)
                or struct.unpack_from('<I', payload, 15)[0] != 1 or reference(payload, 265) != owner):
            raise ValueError('Unobserved Hole topology descriptor count/owner')
        namespace, cursor = text_uuid(payload, 19)
        entity, cursor = text_uuid(payload, cursor)
        if cursor != 171 or payload[171:183] != struct.pack('<QI', 2, 1) or struct.unpack_from('<I', payload, 194)[0] != 1:
            raise ValueError('Unobserved Hole topology context/anchor count')
        recipe_id = reference(payload, 4)
        recipe_record, _ = typed(recipe_id, RECIPE_GUID)
        recipe = decode_counted_recipe(data, recipe_record)
        if recipe['payload_kind'] not in allowed_kinds:
            raise ValueError('Hole selected topology recipe kind disagrees with input role')
        anchor_id = reference(payload, 198)
        typed(anchor_id, ANCHOR)
        anchor = anchors.get(anchor_id)
        if anchor is None:
            raise ValueError('Hole topology historical body anchor unresolved')
        context_id = reference(payload, 183)
        if recipe['payload_kind'] == 'edge_recipe_data':
            _, context = typed(context_id, 'B0B3FA59-C374-444F-B424-24AA5DE41645')
            if len(context) != 103 or context[:2] != bytes(2) or context[-5:] != bytes.fromhex('0000000100'):
                raise ValueError('Unobserved AtCenter edge context framing')
            context_scope = 'Typed B0B103 context bytes retained; natural curve family and edge evaluator unresolved'
        else:
            _, context = typed(context_id, CONTEXT)
            if len(context) != 171 or context[:2] != bytes(2) or context[6:10] != bytes(4):
                raise ValueError('Unobserved Hole face namespace context')
            context_namespace, end = text_uuid(context, 10)
            context_entity, end = text_uuid(context, end)
            if (context_namespace != namespace or context_entity != entity or end != 162
                    or context[162:] != struct.pack('<QB', 2, 0)):
                raise ValueError('Hole topology descriptor/context namespaces disagree')
            context_scope = 'Explicit namespace/entity correspondence only; no plane equation or persistent face identity inferred'
        helper_id = reference(payload, 239)
        helper(helper_id)
        source_support = support(reference(payload, 253), identity, [anchor['source_owner_object_id']])
        return {'kind': 'BRepEdgeRecipe' if recipe['payload_kind'] == 'edge_recipe_data' else 'BRepFaceRecipe',
                'descriptor_object_id': identity, 'recipe': recipe,
                'namespace_text': namespace, 'entity_guid_text': entity,
                'body_anchor_object_id': anchor_id, 'native_body_object_id': anchor['native_body_object_id'],
                'source_owner_object_id': anchor['source_owner_object_id'],
                'context_object_id': context_id, 'context_payload_hex': context.hex(), 'context_scope': context_scope,
                'helper_object_id': helper_id, 'reciprocal_support': source_support,
                'geometry_status': 'Owned typed recipe and historical body provenance; exact selected geometry and persistent BRep/ASM identity unresolved'}

    def native_source(identity, owner, expected_kind):
        _, payload = typed(identity, NATIVE_DESCRIPTOR)
        if (len(payload) != 263 or payload[:2] != bytes(2)
                or struct.unpack_from('<I', payload, 13)[0] != 1 or reference(payload, 252) != owner):
            raise ValueError('Unobserved Hole native source descriptor/owner')
        namespace, cursor = text_uuid(payload, 17)
        entity, cursor = text_uuid(payload, cursor)
        if cursor != 169 or payload[169:181] != struct.pack('<QI', 2, 1) or payload[192:196] != bytes(4):
            raise ValueError('Unobserved Hole native source context/anchor count')
        leaf_id = reference(payload, 2)
        _, leaf = typed(leaf_id, IDENTITY_LEAF)
        if len(leaf) != 10 or leaf[:2] != bytes(2):
            raise ValueError('Unobserved Hole native identity leaf')
        native_id = struct.unpack_from('<Q', leaf, 2)[0]
        context_id = reference(payload, 181)
        _, context = typed(context_id, 'CC54ECAD-6DE8-4DE1-803D-BBE0E751975B')
        if context[:2] != bytes(2):
            raise ValueError('Unobserved Hole native plane context prefix')
        if expected_kind == 'ConstructionPlane':
            entity_source = known.get(native_id)
            if (entity_source is None or entity_source['kind'] != 'ConstructionPlane' or len(context) != 87
                    or 'origin_container_object_id' not in entity_source):
                raise ValueError('Only captured explicit native origin-plane support admitted')
            expected_sources = [identity]
            source = {'kind': 'ConstructionPlane', 'entity': entity_source}
        else:
            typed(native_id, '44A64366-4BD3-4B24-881A-F94C206E8F2D')
            sketches = [f for f in features if f['kind'] == 'Sketch' and f.get('sketch_object_id') == native_id]
            if len(sketches) != 1 or len(context) != 77:
                raise ValueError('Hole sketch-plane source is unresolved or ambiguous')
            sketch = sketches[0]
            expected_sources = [sketch['object_id'], identity]
            source = {'kind': 'SketchPlane', 'sketch_object_id': native_id,
                      'sketch_feature_object_id': sketch['object_id'], 'sketch_name': sketch.get('name'),
                      'underlying_support_status': 'Native source sketch identity explicit; its support definition is retained on the sketch, not inferred from Hole caches'}
        helper_id = reference(payload, 226)
        helper(helper_id)
        source.update(descriptor_object_id=identity, terminal_object_id=leaf_id,
                      namespace_text=namespace, entity_guid_text=entity,
                      context_object_id=context_id, context_payload_hex=context.hex(),
                      context_status='Typed source context retained; matrix/transform semantics unresolved',
                      helper_object_id=helper_id, reciprocal_support=support(reference(payload, 240), identity, expected_sources))
        return source

    def backend(identity, owner, is_axis, methods):
        _, payload = typed(identity, AXIS if is_axis else POINT)
        length, method_offset, count_offset, descriptor_offset, helper_offset, support_offset = (
            (202, 70, 99, 103, 165, 179) if is_axis else (178, 47, 75, 79, 141, 155))
        if (len(payload) != length or payload[:2] != bytes(2)
                or (is_axis and payload[:6] != bytes.fromhex('000008000000'))
                or struct.unpack_from('<I', payload, count_offset)[0] != 1
                or reference(payload, length-11) != owner):
            raise ValueError('Unobserved Hole input backend count/owner')
        method = struct.unpack_from('<I', payload, method_offset)[0]
        if method not in methods:
            raise ValueError('Unobserved Hole backend method for source role')
        descriptor_id = reference(payload, descriptor_offset)
        helper(reference(payload, helper_offset))
        reciprocal = support(reference(payload, support_offset), identity, [] if method == 6 else [descriptor_id])
        return {'backend_object_id': identity, 'stored_method_code': method,
                'descriptor_object_id': descriptor_id, 'reciprocal_support': reciprocal}

    def body_proxy(identity, owner):
        proxy = body_proxies.get(identity)
        if proxy is None or proxy['owner_object_id'] != owner or len(proxy['descriptor_object_ids']) != 1:
            raise ValueError('Hole native body input proxy unresolved')
        descriptor = body_descriptors.get(proxy['descriptor_object_ids'][0])
        if descriptor is None or descriptor['owner_object_id'] != owner:
            raise ValueError('Hole native body descriptor owner unresolved')
        return {'kind': 'NativeBodyRecipe', 'selection_record_object_id': identity,
                'descriptor_object_id': descriptor['object_id'], 'recipe_record_object_id': descriptor['recipe_record_object_id'],
                'native_body_object_id': descriptor['native_body_object_id'],
                'body_anchor_object_id': descriptor['body_anchor_object_id'],
                'source_owner_object_id': descriptor['source_owner_object_id'],
                'scope': 'Owned native body recipe and historical body anchor; current/final body identity not inferred'}

    def tail(body, settings):
        cursor = attributes(body, 2)[1] if body[1] else 6
        cursor += (8 if body[1] else 4)+33+19*len(settings['point_association_records'])
        for _ in range(4):
            _, cursor = optional_reference(body, cursor)
        count = struct.unpack_from('<I', body, cursor)[0]
        if count != settings['position_count']:
            raise ValueError('Hole tail position count disagrees with settings')
        cursor += 4+11*count
        for _ in range(5):
            _, cursor = optional_reference(body, cursor)
        if body[cursor:cursor+4] != bytes(4):
            raise ValueError('Hole tail tip separator disagrees')
        _, cursor = optional_reference(body, cursor+4)
        if reference(body, cursor) != settings['input_record_object_ids']['TipAngle']:
            raise ValueError('Hole tail TipAngle binding disagrees')
        cursor += 11
        count = struct.unpack_from('<I', body, cursor)[0]
        if count != (0 if settings['extent']['condition'] == 'Distance' else 1):
            raise ValueError('Hole native extent selection count disagrees with active extent')
        extent_ids = [reference(body, cursor+4+11*i) for i in range(count)]
        cursor += 4+11*count
        if body[cursor:cursor+20] != bytes(20) or struct.unpack_from('<I', body, cursor+20)[0] != 1:
            raise ValueError('Unobserved Hole native extent/body input separator')
        body_id = reference(body, cursor+24)
        namespace, cursor = text_uuid(body, cursor+35)
        if body[cursor:cursor+3] != bytes(3):
            raise ValueError('Unobserved Hole input dependency namespace')
        count = struct.unpack_from('<I', body, cursor+3)[0]
        if not 1 <= count <= 64 or cursor+7+11*count > len(body):
            raise ValueError('Unobserved Hole dependency table extent')
        dependencies = [reference(body, cursor+7+11*i) for i in range(count)]
        required = {body_id, *extent_ids, *settings['input_record_object_ids']['positions'],
                    settings['input_record_object_ids']['axis'], settings['input_record_object_ids']['opaque_core_input']}
        if not required.issubset(dependencies) or any(identity not in primary for identity in dependencies):
            raise ValueError('Hole direct input/dependency table correspondence disagrees')
        return extent_ids, body_id, dependencies, namespace

    decoded, unresolved = [], []
    for feature in features:
        if feature['kind'] != 'Hole':
            continue
        owner = feature['object_id']
        try:
            _, body = typed(owner, HOLE)
            settings = decode_hole(data, records, body, feature)
            inputs = settings['input_record_object_ids']
            axis_source = backend(inputs['axis'], owner, True, (13, 14, 19))
            method = axis_source['stored_method_code']
            if method == 19:
                selected = topology(axis_source['descriptor_object_id'], owner, ('bounded_face_recipe_data',))
            else:
                selected = native_source(axis_source['descriptor_object_id'], owner, 'ConstructionPlane' if method == 14 else 'SketchPlane')
            axis_source['source'] = selected
            positions = []
            for index, identity in enumerate(inputs['positions']):
                position = backend(identity, owner, False, (6, 10, 12, 17))
                position_method = position['stored_method_code']
                if position_method in (6, 17):
                    position['source'] = topology(position['descriptor_object_id'], owner,
                        ('face_recipe_data',) if position_method == 6 else ('bounded_face_recipe_data',))
                    if method != 19 or position['source']['body_anchor_object_id'] != selected['body_anchor_object_id']:
                        raise ValueError('Hole position/direction historical support body disagrees')
                elif position_method == 12:
                    position['source'] = native_source(position['descriptor_object_id'], owner, 'ConstructionPlane')
                    if method != 14 or position['source']['entity']['object_id'] != selected['entity']['object_id']:
                        raise ValueError('Hole point/direction origin-plane identities disagree')
                else:
                    if settings['position_definition'] not in ('SketchPoint', 'SketchPoints') or method != 13:
                        raise ValueError('Hole sketch-point provider mode disagrees with support sketch')
                    position['source'] = {'kind': 'SketchPointProvider', 'identity_status': 'Detailed source sketch point/tag association belongs to decode_hole_point_sources; not duplicated here'}
                position['position_ordinal'] = index
                positions.append(position)
            center = None
            if settings['position_definition'] == 'AtCenter':
                center = backend(inputs['center'], owner, False, (5,))
                center['source'] = topology(center['descriptor_object_id'], owner, ('edge_recipe_data',))
                if center['source']['body_anchor_object_id'] != selected['body_anchor_object_id']:
                    raise ValueError('AtCenter edge/direction historical body disagrees')
            extent_ids, body_id, dependencies, native_namespace = tail(body, settings)
            native_body_input = body_proxy(body_id, owner)
            extent = {'condition': settings['extent']['condition'], 'native_selection_record_object_ids': extent_ids}
            if extent_ids:
                target_id = extent_ids[0]
                if extent['condition'] == 'ToEntity':
                    proxy_record, proxy_payload = typed(target_id, PROXY)
                    descriptors, props = native_proxy_references(data, proxy_record)
                    if props or len(descriptors) != 1 or reference(proxy_payload, len(proxy_payload)-11) != owner:
                        raise ValueError('Hole ToEntity target proxy descriptor count/owner disagrees')
                    target = topology(descriptors[0], owner, ('face_recipe_data',))
                    support(reference(proxy_payload, 82), target_id, descriptors)
                    extent.update(target={'selection_record_object_id': target_id, **target},
                                  selection_status='Explicit owned ToEntity face recipe and historical body; exact persistent target face/geometry unresolved')
                else:
                    extent.update(native_body_extent_input=body_proxy(target_id, owner),
                                  selection_status='Native ThroughAll body input decoded; API setAllExtent supplies no user-selected target entity argument')
            _, core = typed(inputs['opaque_core_input'], CORE)
            core_count = struct.unpack_from('<I', core, 13)[0]
            if (core_count not in (1, 3) or core_count != settings['position_count']
                    or len(core) != 70+11*core_count or core[:2] != bytes(2) or reference(core, 2) != owner
                    or reference(core, len(core)-11) != owner):
                raise ValueError('Hole core input owner/count disagrees')
            core_contexts = []
            for index in range(core_count):
                core_context_id = reference(core, 17+11*index)
                _, core_context = typed(core_context_id, CONTEXT)
                if len(core_context) != 171 or core_context[:2] != bytes(2):
                    raise ValueError('Unobserved Hole core context framing')
                core_contexts.append({'object_id': core_context_id, 'payload_hex': core_context.hex()})
            core_cursor = 17+11*core_count
            helper(reference(core, core_cursor+16))
            core_support = support(reference(core, core_cursor+30), inputs['opaque_core_input'])
            if not {inputs['axis'], *inputs['positions'], *extent_ids}.issubset(core_support['source_record_object_ids']):
                raise ValueError('Hole core dependencies omit direct position/direction/extent inputs')
            decoded.append({'feature_object_id': owner, 'position_definition': settings['position_definition'],
                'support': axis_source, 'position_support_inputs': positions, 'center_edge_input': center,
                'extent_inputs': extent, 'native_body_input': native_body_input,
                'core_input': {'object_id': inputs['opaque_core_input'], 'stored_context_count': core_count,
                               'contexts': core_contexts, 'reciprocal_dependencies': core_support,
                               'status': 'Owned core namespace/dependency route; not interpreted as the selected extent target'},
                'native_dependency_record_object_ids': dependencies,
                'native_metadata_namespace_text': native_namespace,
                'support_selection_status': 'Explicit owned support face, native origin-plane or sketch-plane identity decoded; persistent face geometry/topology remains unresolved',
                'scope': SCOPE})
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            unresolved.append({'feature_object_id': owner, 'reason': str(error)})
    return {'decoded': decoded, 'unresolved': unresolved, 'scope': SCOPE}


def validate_fixtures(root, zstd_library=None):
    """Fourteen saved Hole captures; existing getter evidence and bounded guards."""
    import json
    from pathlib import Path
    from decode_basics import decode_basics
    from decode_hole_point_sources import decode_hole_point_sources
    from decode_sketch import same
    from fusion_archive import read_members
    from fusion_metadata import design_records

    root = Path(root)
    report = {'scope': SCOPE, 'integration': {
        'reader': 'decode_hole_supports(data,records,features,body_selections=None)',
        'merge': 'Attach decoded support/center/extent provenance to corresponding Hole tool_settings or retain separate hole_supports summary. ToEntity extent target gains typed face-recipe provenance; preserve exact target geometry/topology unresolved. Existing detailed sketch point sources stay with decode_hole_point_sources.',
        'expected_outputs': 'samples[].expected_summary contains full per-file additional output.',
        'validator': 'decode_hole_supports.validate_fixtures(root,zstd_library=None)'},
        'schema': {
            'direction': 'Owned F2A202: method19 -> bounded-face topology; method14 ->90055 explicit native origin-plane identity; method13 ->90055 explicit source-sketch identity. Descriptor103, owner191, reciprocal support179.',
            'position_support': 'Owned69EE178: method17 selects bounded-face recipe; method6 selects face recipe; method12 selects explicit origin-plane identity; method10 source-point identities are delegated to existing point reader. Descriptor79, owner167, support155.',
            'AtCenter': 'Distinct method5 center provider selects an edge recipe, while its position method6 selects a face. The axis method19 independently selects a bounded-face recipe. Same historical body anchor is checked; no coordinates choose topology identities.',
            'extent': 'Sequential cursor follows optional input fields through TipAngle; u32 native extent-selection count0 for Distance,1 for ToEntity/ThroughAll, explicit proxy references,20zero bytes, body-input count1 and body proxy. ToEntity proxy selects face_recipe_data; ThroughAll selects body_recipe_data via existing body decoder.',
            'core': 'Owned3CDCCC has u32 context count1/3 and that many C46D namespace contexts, reciprocal support entries referencing active native inputs. Count agrees with saved placement count; no context-to-position identity assignment inferred. Core is not the selected target.',
            'metadata': 'Valid stored metadata UUID retained. Ordinary captured holes use nil UUID; tapped holes have a nonzero UUID, whose meaning remains unresolved.'},
        'evidence_limits': [
            'Original API truth captures Hole position, direction, extent class and numeric settings, not post-creation face/plane/target selection entity getters. Role interpretation uses controlled saved generator calls plus typed native framing and reciprocal references.',
            'GenerateHoleSamples.setPositionByPoint(seed.endFaces.item(0),...) and setOneSideToExtent(seed.startFaces.item(0),False) establish support/target roles. No source recipe is identified as an exact geometric end/start face in production.',
            'GenerateHolePlacements uses the explicit XY plane for reversed cases, a face-supported HoleLocations sketch for sketch-point cases and setPositionAtCenter(top,top.edges.item(0)) for AtCenter.',
            'GenerateTappedHoles calls setPositionByPoint on an extrusion end face. Position backend normalizes to method6 rather than the method17 stored by earlier ordinary holes.',
            'ThroughAll has an internal native body extent input. The API setAllExtent call has no user-selected target argument, so this body is not presented as an explicit user selection.',
            'B0B103 center-edge context is retained opaque. It does not establish a circle equation, selected BRep edge identity or regeneration.'],
        'samples': [], 'comparisons': [], 'malformed_guards': []}
    loaded = {}
    kind_counts = {}

    def check(label, actual, expected):
        assert actual == expected, (label, actual, expected)
        report['comparisons'].append({'label': label, 'actual': actual, 'expected': expected, 'passed': True})

    for folder in ('holes-926347c1eaa8', 'holeplacements-04adf73afe93', 'tappedholes-409e96788503'):
        truth = json.loads((root/folder/'ground_truth.json').read_text())
        assert not truth['errors']
        for actual in truth['samples']:
            filename = folder+'/'+actual['file']
            model = decode_basics(root/filename, zstd_library)['streams'][0]
            members = read_members(root/filename, zstd_library)
            data = members[model['member']]
            records, _ = design_records(data, members[model['member'].replace('BulkStream.dat', 'MetaStream.dat')])
            features = model['features']
            prior_points = decode_hole_point_sources(data, records, features)
            parsed = decode_hole_supports(data, records, features, model['body_selections'])
            check(filename+' exactly one supported Hole', len(parsed['decoded']), 1)
            check(filename+' no new unresolved', parsed['unresolved'], [])
            item = parsed['decoded'][0]
            support_kind = item['support']['source']['kind']
            expected_kind = ('ConstructionPlane' if actual['file'].startswith('reversed_') else
                             'SketchPlane' if actual['file'] in ('sketch_point.f3d', 'sketch_points.f3d') else 'BRepFaceRecipe')
            check(filename+' native support kind matches controlled generator role', support_kind, expected_kind)
            kind_counts[support_kind] = kind_counts.get(support_kind, 0)+1
            if expected_kind == 'ConstructionPlane':
                check(filename+' explicit native origin-plane name', item['support']['source']['entity']['name'], 'XY')
            elif expected_kind == 'SketchPlane':
                check(filename+' explicit source sketch name', item['support']['source']['sketch_name'], 'HoleLocations')
            feature = next(f for f in features if f['kind'] == 'Hole' and f['object_id'] == item['feature_object_id'])
            record = next(r for r in records if r.is_primary and r.object_id == item['feature_object_id'])
            settings = decode_hole(data, records, data[record.body:record.end], feature)
            api = actual.get('settings', {}) if folder.startswith('tappedholes-') else actual
            if api.get('position_cm') is not None:
                check(filename+' existing cached Hole position matches saved actual getter', same(settings['position_cm'], api['position_cm']), True)
            if 'direction' in api:
                check(filename+' existing Hole direction matches saved actual getter', same(settings['direction'], api['direction']), True)
            if 'extent_kind' in api:
                check(filename+' saved actual extent class', item['extent_inputs']['condition'],
                      {'DistanceExtentDefinition': 'Distance', 'AllExtentDefinition': 'ThroughAll',
                       'ToEntityExtentDefinition': 'ToEntity', 'OneSideToExtentDefinition': 'ToEntity'}[api['extent_kind']])
            if item['extent_inputs']['condition'] == 'ToEntity':
                check(filename+' target is an owned face recipe', item['extent_inputs']['target']['recipe']['payload_kind'], 'face_recipe_data')
                check(filename+' target record distinct from core input', item['extent_inputs']['target']['selection_record_object_id'] != item['core_input']['object_id'], True)
            if item['center_edge_input'] is not None:
                check(filename+' center source distinct from position provider', item['center_edge_input']['backend_object_id'] != item['position_support_inputs'][0]['backend_object_id'], True)
                check(filename+' center source typed edge recipe', item['center_edge_input']['source']['recipe']['payload_kind'], 'edge_recipe_data')
            check(filename+' detailed point associations unchanged', decode_hole_point_sources(data, records, features) == prior_points, True)
            report['samples'].append({'file': filename, 'expected_summary': parsed,
                                      'saved_API_context': actual,
                                      'support_entity_API_getter_status': 'Not captured; controlled generator role plus explicit native provenance only'})
            loaded[filename] = data, records, features, parsed

    guards = [
        ('Hole axis owner disagreement', 'holes-926347c1eaa8/simple.f3d', 298, 192, struct.pack('<Q', 999999)),
        ('Face context UUID disagreement', 'holes-926347c1eaa8/simple.f3d', 341, 14, b'f\0'),
        ('Direction supporting-plane identity disagrees with position plane', 'holeplacements-04adf73afe93/reversed_distance.f3d', 303, 2, struct.pack('<Q', 43)),
        ('AtCenter edge provider wrong method', 'holeplacements-04adf73afe93/center_edge.f3d', 300, 47, struct.pack('<I', 6)),
        ('ToEntity target proxy owner disagreement', 'holes-926347c1eaa8/to_bottom.f3d', 312, 95, struct.pack('<Q', 243)),
        ('ToEntity body descriptor cannot masquerade as face target', 'holes-926347c1eaa8/to_bottom.f3d', 312, 7, struct.pack('<Q', 286))]
    for label, filename, identity, offset, replacement in guards:
        data, records, features, _ = loaded[filename]
        record = next(r for r in records if r.is_primary and r.object_id == identity)
        changed = bytearray(data)
        changed[record.body+offset:record.body+offset+len(replacement)] = replacement
        rejected = decode_hole_supports(bytes(changed), records, features)
        assert not rejected['decoded'] and len(rejected['unresolved']) == 1, label
        report['malformed_guards'].append({'label': label, 'rejected': True, 'reason': rejected['unresolved'][0]['reason']})
    report['validation'] = {'saved_files': len(report['samples']), 'decoded_supports_by_kind': kind_counts,
                            'AtCenter_edge_sources': 1, 'ToEntity_face_targets': 1, 'ThroughAll_native_body_extent_inputs': 2,
                            'comparisons_passed': len(report['comparisons']), 'malformed_guards_passed': len(report['malformed_guards']),
                            'actual_API_support_entity_getter_comparisons': 0, 'new_API_calls': 0}
    return report
