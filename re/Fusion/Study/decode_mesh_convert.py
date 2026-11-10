"""Observed Faceted parametric MeshConvert source/result graph, not a converter."""
import struct
import lzma
import uuid

from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_selections import decode_body_selections
from decode_mesh_contents import MESH, _require
from decode_retained_mesh_sources import decode_retained_mesh_source
from decode_mesh_selections import decode_mesh_selection
from decode_parameters import read_string
from decode_sketch import reference

CONVERT = '62B85DC3-27B5-47BA-9F13-B2527B72EE49'
SOURCE_LIST = 'D6FB6F05-98CD-4BFF-BF90-594F77725DC1'
STATE = 'B7F34D7B-DAC4-41A5-B67D-D672537C3BFA'
CONTROLLER = 'ABA79BE7-D8D2-4C17-B59B-C2035E111F77'
BODY = 'D3937028-C20C-4E65-B010-94AD418A5C20'
COLLECTION = 'CD57BC48-50EC-47DC-975A-FB6DEA72F4DA'
MAPPING = '74CA4562-59F8-4C97-8AD1-F8297C21F9AA'
SCOPE = ('Observed successful Faceted parametric MeshConvert layout with typed mesh input proxy/list, '
         'explicit result BRep BODY anchor and owned UUID controller/state, native collection/history blob '
         'mapping and independently stored ASM BODY identifier. Method/operation alternatives are not '
         'generalized from unvaried codes; current mesh diagnostics, failed Prismatic conversion, inactive '
         'Organic controls, topology regeneration and lifecycle remain separately scoped.')


def decode_mesh_convert(data, records, features, member, members):
    result = {'decoded': [], 'unresolved': [], 'scope': SCOPE}
    candidates = [r for r in records if r.is_primary and r.class_guid == CONVERT]
    if not candidates:
        return result
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    def typed(identity, guid):
        rows = grouped.get(identity, [])
        _require(len(rows) == 1 and rows[0].class_guid == guid, 'Convert typed reference missing, ambiguous or wrong class')
        return rows[0], data[rows[0].body:rows[0].end]
    features_by_id = {f['object_id']: f for f in features}
    selections = decode_body_selections(data, records)
    for record in candidates:
        try:
            typed(record.object_id, CONVERT)
            feature = features_by_id.get(record.object_id)
            _require(feature is not None and feature.get('class_guid') == CONVERT and feature.get('native_kind_label') == 'Convert Mesh' and feature.get('record_offset') == record.start, 'Convert feature discovery identity/label unresolved')
            body = data[record.body:record.end]
            _require(body[:14] == bytes.fromhex('0001000000000300000001000000') and body[25:39] == bytes.fromhex('ffffffff00000000000001000000'), 'Only captured Faceted parametric Convert header supported')
            source_list_id = reference(body, 14)
            _, source_list = typed(source_list_id, SOURCE_LIST)
            _require(len(source_list) == 20 and source_list[:3] == bytes(3) and source_list[14:] == bytes.fromhex('010100000000'), 'Unobserved singleton mesh Convert source-list layout')
            source_proxy_id = reference(source_list, 3)
            source_selection = decode_mesh_selection(data, records, source_proxy_id, record.object_id)
            _require(reference(body, 141) == source_proxy_id and reference(body, 152) == source_selection['descriptor_object_id'], 'Convert repeated source proxy/descriptor list disagrees')
            namespace, cursor = read_string(body, 58)
            _require(namespace == str(uuid.UUID(int=0)) and cursor == 134 and body[134:141] == bytes(3)+struct.pack('<I', 2) and struct.unpack_from('<I', body, 163)[0] == 4, 'Unobserved Convert native dependency table')
            label, cursor = read_string(body, 167)
            _require(label == 'Convert Mesh', 'Convert stored label disagrees')
            stored_index = struct.unpack_from('<Q', body, cursor)[0]
            name, name_end = read_string(body, cursor+8)
            _require(name == feature.get('name') and stored_index == feature.get('stored_index') and body[50:58] == bytes(8), 'Convert native name/index framing disagrees with discovery')
            anchor_id = reference(body, 39)
            anchors = [a for a in selections['body_anchors'] if a['object_id'] == anchor_id and a['source_owner_object_id'] == record.object_id]
            _require(len(anchors) == 1, 'Convert result body anchor not uniquely owned')
            anchor = anchors[0]
            result_body_id = anchor['native_body_object_id']
            _, result_body = typed(result_body_id, BODY)
            _require(len(body) == name_end+66 and body[name_end:name_end+7] == bytes(7), 'Unobserved Convert shared state footer')
            state_id = reference(body, name_end+7)
            _, state = typed(state_id, STATE)
            _require(len(state) == 33 and state[:6] == bytes(2)+struct.pack('<I', 1) and state[17:] == struct.pack('<QQ', 1, 2), 'Unobserved Convert singleton state/controller framing')
            controller_id = reference(state, 6)
            _, controller = typed(controller_id, CONTROLLER)
            _require(controller[:3] == bytes(3), 'Unobserved Convert ASM controller prefix')
            controller_uuid, c = read_string(controller, 3)
            _require(controller_uuid == anchor['native_uuid_text'] and c == 79 and controller[c:c+8] == struct.pack('<II', 0, 1), 'Convert controller/result-anchor UUID or framing disagrees')
            label_count = struct.unpack_from('<I', controller, 87)[0]
            _require(label_count in (3, 4), 'Unobserved Convert controller literal-label count')
            labels = controller[91:91+label_count].decode('ascii')
            c = 91+label_count
            table_count = struct.unpack_from('<I', controller, c)[0]; c += 4
            _require(labels == ('123' if label_count == 3 else '1234') and table_count == label_count+1 and c+4*table_count+15 == len(controller), 'Unobserved Convert controller counted literal table')
            table = list(struct.unpack_from('<'+'I'*table_count, controller, c)); c += 4*table_count
            _require(table == list(range(table_count)) and controller[c+8:] == bytes.fromhex('00010000000000'), 'Unobserved Convert controller table/trailer')
            source_mesh_id = source_selection['mesh_object_id']
            source_mesh = decode_retained_mesh_source(data, records, source_mesh_id, source_selection, member, members)
            collection_id = reference(result_body, len(result_body)-11)
            _, collection = typed(collection_id, COLLECTION)
            count = struct.unpack_from('<I', collection, 7)[0]
            _require(count == 1 and reference(collection, 11) == result_body_id, 'Only captured singleton Convert BRep result collection supported')
            repeated = len(collection)-26
            _require(struct.unpack_from('<I', collection, repeated)[0] == 1 and reference(collection, repeated+4) == result_body_id and reference(collection, len(collection)-11) == source_mesh['component_object_id'], 'Convert BRep result repeated collection/component ownership disagrees')
            mappings = []
            for mapping in records:
                if not mapping.is_primary or mapping.class_guid != MAPPING:
                    continue
                payload = data[mapping.body:mapping.end]
                if payload[:6] != bytes(2)+struct.pack('<I', 1):
                    continue
                handle, native_body_id = struct.unpack_from('<QQ', payload, 6)
                if native_body_id != result_body_id:
                    continue
                _require(reference(payload, 22) == collection_id and payload[33] == 0, 'Convert native body/history mapping owner disagrees')
                filename, end = read_string(payload, 34)
                _require(end == len(payload) and filename.startswith('BREP.') and filename.endswith('.smbh') and '/' not in filename and '\\' not in filename, 'Unobserved Convert native history filename')
                path = member.split('/FusionDesignSegmentType1/')[0]+'/Breps.BlobParts/'+filename
                _require(path in members, 'Convert native history blob missing from same asset')
                mappings.append({'mapping_record_object_id': mapping.object_id, 'owner_object_id': collection_id,
                    'history_blob_member': path, 'body_count': 1,
                    'bindings': [{'stored_handle': handle, 'native_body_object_id': result_body_id}]})
            _require(len(mappings) == 1, 'Convert BRep result/history mapping not unique')
            identifiers = decode_body_asm_identifiers(data, records, member, members, {'decoded': mappings})
            _require(len(identifiers['decoded']) == 1 and not identifiers['unresolved'], 'Convert typed stored ASM BODY identifier association unresolved')
            settings = {'mesh_convert_method': 'Faceted',
                'method_decode_scope': 'Only successful captured Faceted layout accepted; no independently varied method enum field or Prismatic schema claimed',
                'mesh_convert_operation': 'ObservedParametricFeature',
                'operation_decode_scope': 'Explicit stored Convert feature with owned input/result/history graph; operation enum alternatives unobserved',
                'stored_uninterpreted_header_uint32': list(struct.unpack_from('<III', body, 2)),
                'source_list_object_id': source_list_id, 'source_mesh_selection': source_selection,
                'qualified_source_mesh': source_mesh,
                'source_mesh_scope': 'Explicit Convert input selection and separately qualified mesh asset; old general mesh_contents diagnostic is unchanged',
                'result_body_anchor': anchor, 'result_native_body_object_id': result_body_id,
                'result_body_collection_object_id': collection_id,
                'result_body_component_object_id': source_mesh['component_object_id'],
                'native_history_mapping': mappings[0], 'stored_asm_body_identifier': identifiers['decoded'][0],
                'state_object_id': state_id, 'history_controller_object_id': controller_id,
                'history_controller_uuid': controller_uuid, 'controller_literal_labels': labels,
                'controller_stored_table': table, 'controller_uninterpreted_uint64': struct.unpack_from('<Q', controller, c)[0],
                'controller_scope': 'Owned state/controller UUID agrees with result anchor; table labels are literal and not interpreted as face/edge identifiers or replay commands',
                'inactive_controls_scope': 'Organic resolution/accuracy/numberOfFaces/preprocess not decoded as active controls',
                'geometry_scope': 'Typed native BRep BODY/history root distinct from source mesh asset; no geometry-based identity, conversion replay or persistent lifecycle inference'}
            result['decoded'].append({'feature_object_id': record.object_id, 'kind': 'MeshConvert',
                'name': name, 'class_guid': CONVERT, 'settings': settings})
        except (ValueError, IndexError, UnicodeError, struct.error, KeyError, lzma.LZMAError) as error:
            result['unresolved'].append({'feature_object_id': record.object_id, 'reason': str(error)})
    return result
