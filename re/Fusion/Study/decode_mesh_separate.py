"""Observed MeshSeparate methods and explicit result/source provenance.

Current counted result meshes and retained selected source are distinct. Geometry
errors never invalidate proven controls or become silent prefix truncation.
"""
import lzma
import struct
import uuid

from decode_mesh_contents import MESH, MESH_FEATURE, _require, decode_mesh_contents
from decode_mesh_geometry_variants import decode_mesh_asset, decode_mesh_contents_variants, native_layout
from decode_mesh_selections import decode_mesh_selection
from decode_parameters import read_string
from decode_timeline import feature_state
from decode_sketch import reference

SEPARATE = '6B6FDE2E-D9B9-4866-9D07-3123C919B0D2'
METHODS = {0: 'Shell', 1: 'FaceGroup'}
SCOPE = ('Observed MeshBody MeshSeparate Shell/FaceGroup definitions, explicit result lists, reciprocal current '
         'mesh/collection/feature ownership and retained selected source. Keep-body and inactive multiple-body '
         'flags, face-group partitions, unsupported compressed geometry, lifecycle and regeneration unresolved.')


def _typed(data, records, identity, guid, *, primary=True):
    rows = [r for r in records if r.is_primary == primary and r.object_id == identity and r.class_guid == guid]
    all_rows = [r for r in records if r.is_primary and r.object_id == identity] if primary else rows
    _require(len(rows) == len(all_rows) == 1, 'MeshSeparate typed reference missing, ambiguous or wrong class')
    return rows[0], data[rows[0].body:rows[0].end]


def decode_mesh_separate_definition(data, records, feature_id):
    """Pure typed definition/owner proof; no asset decoding or shared-reader call."""
    record, body = _typed(data, records, feature_id, SEPARATE)
    _require(body[:2] == bytes(2), 'MeshSeparate prefix differs')
    count = struct.unpack_from('<I', body, 2)[0]
    _require(count in (1, 2), 'Unobserved MeshSeparate result count')
    outputs = [reference(body, 6+11*i) for i in range(count)]
    end_list = 6+11*count
    _require(len(set(outputs)) == count and body[end_list:end_list+2] == bytes(2)
             and body[end_list+6:end_list+12] == bytes(6), 'MeshSeparate result list/opaque control framing differs')
    method = struct.unpack_from('<I', body, end_list+2)[0]
    _require(method in METHODS and (method, count) in ((0, 1), (0, 2), (1, 1)), 'Unobserved MeshSeparate method/count family')
    selection = decode_mesh_selection(data, records, reference(body, end_list+12), feature_id)
    _require(selection['mesh_object_id'] not in outputs and body[end_list+23] == 0, 'MeshSeparate source aliases result or separator differs')
    nil, cursor = read_string(body, end_list+24)
    _require(nil == str(uuid.UUID(int=0)) and body[cursor:cursor+3] == bytes(3)
             and struct.unpack_from('<I', body, cursor+3)[0] == 2, 'MeshSeparate dependency framing differs')
    repeated_offset = cursor+7
    repeated = [reference(body, repeated_offset+11*i) for i in range(2)]
    _require(repeated == [selection['proxy_object_id'], selection['descriptor_object_id']], 'MeshSeparate dependency table differs from owned source')
    cursor = repeated_offset+22
    _require(body[cursor:cursor+4] == b'\xff'*4, 'MeshSeparate feature marker differs')
    label, cursor = read_string(body, cursor+4)
    index = struct.unpack_from('<Q', body, cursor)[0]
    name, tail = read_string(body, cursor+8)
    _require(label == 'MeshSeparate' and len(body)-tail == 66, 'MeshSeparate label/shared footer extent differs')
    state = feature_state(body)
    _, state_body = _typed(data, records, reference(body, tail+7), 'B7F34D7B-DAC4-41A5-B67D-D672537C3BFA')
    _require(state_body == bytes.fromhex('0000000000000100000000000000'), 'Unobserved MeshSeparate stored state payload')
    collections = []
    for mesh_id in outputs:
        _, payload = _typed(data, records, mesh_id, MESH)
        _require(len(payload) == 831 and payload[:2] == bytes(2)
                 and struct.unpack_from('<Q', payload, 2)[0] in (2, 3)
                 and payload[10:22] == bytes.fromhex('000101010000000000000000')
                 and reference(payload, 489) == feature_id, 'MeshSeparate result native prefix/feature owner differs')
        _, inherited = _typed(data, records, mesh_id, 'CB844AB6-240D-4fc9-9C9F-3679DC896D6F', primary=False)
        _require(len(inherited) == 11, 'MeshSeparate result owner fragment extent differs')
        collections.append(reference(inherited, 0))
    _require(len(set(collections)) == 1, 'MeshSeparate output collections differ')
    collection_id = collections[0]
    _typed(data, records, collection_id, '443807AD-8025-41A3-8A50-5157579C3D78')
    _, collection = _typed(data, records, collection_id, 'A7AEA631-985B-4DD1-8CE2-DE2C-14B54081', primary=False)
    _require(collection[:1] == b'\0' and len(collection) == 16+11*count
             and struct.unpack_from('<I', collection, 1)[0] == count
             and [reference(collection, 5+11*i) for i in range(count)] == outputs,
             'MeshSeparate result list does not equal reciprocal current counted collection')
    component_id = reference(collection, len(collection)-11)
    _typed(data, records, component_id, 'E03784ED-5E19-4E14-B9F2-3B07017018CD')
    source_id = selection['mesh_object_id']
    _, source = _typed(data, records, source_id, MESH)
    _require(source[:22] == bytes.fromhex('00000100000000000000000100010000000000000000'), 'Unobserved MeshSeparate retained source prefix')
    _, owner = _typed(data, records, source_id, 'CB844AB6-240D-4fc9-9C9F-3679DC896D6F', primary=False)
    _require(len(owner) == 11 and reference(owner, 0) == collection_id, 'MeshSeparate source retained owner differs from result collection')
    base_id = reference(source, 489)
    _, base = _typed(data, records, base_id, MESH_FEATURE)
    _require(base[:6] == bytes(2)+struct.pack('<I', 1) and reference(base, 6) == source_id, 'MeshSeparate source/BaseMesh membership is not reciprocal')
    native_ids = {r.object_id for r in records if r.is_primary and r.class_guid == MESH}
    _require(native_ids == set(outputs+[source_id]), 'MeshSeparate outside observed source/result native mesh family')
    def ref(identity):
        return b'\1'+struct.pack('<Q', identity)+bytes(2)
    def text(value):
        return struct.pack('<I', len(value))+value.encode('utf-16le')
    replay = (bytes(2)+struct.pack('<I', count)+b''.join(ref(i) for i in outputs)+bytes(2)
        +struct.pack('<I', method)+bytes(6)+ref(selection['proxy_object_id'])+bytes(1)+text(nil)
        +bytes(3)+struct.pack('<I', 2)+b''.join(ref(i) for i in repeated)+b'\xff'*4+text(label)
        +struct.pack('<Q', index)+text(name)+body[tail:])
    _require(replay == body, 'MeshSeparate full feature payload replay disagrees')
    return dict(feature_object_id=feature_id, class_guid=SEPARATE, name=name, stored_index=index,
        method=METHODS[method], stored_method_code=method, method_field_body_relative_offset=end_list+2,
        output_mesh_object_ids=outputs, source_selection=selection, source_base_mesh_feature_object_id=base_id,
        mesh_collection_object_id=collection_id, component_object_id=component_id,
        stored_uninterpreted_control_prefix_hex=body[end_list:end_list+2].hex(),
        stored_uninterpreted_control_suffix_hex=body[end_list+6:end_list+12].hex(),
        repeated_dependency_object_ids=repeated,
        layout=dict(feature_body_offset=record.body, feature_body_end_offset=record.end,
            feature_body_hex=body.hex(), repeated_dependency_body_relative_offset=repeated_offset,
            shared_footer_hex=body[tail:].hex(), shared_feature_state=state, exact_full_payload_replay=True))


def _source_provenance(data, records, definition, member, members):
    from decode_retained_mesh_sources import decode_retained_mesh_source
    source = decode_retained_mesh_source(data, records, definition['source_selection']['mesh_object_id'],
        definition['source_selection'], member, members)
    _require(source['retained_owner_collection_member_ids'] == definition['output_mesh_object_ids']
        and source['retained_mesh_collection_object_id'] == definition['mesh_collection_object_id']
        and source['component_object_id'] == definition['component_object_id']
        and source['base_mesh_feature_object_id'] == definition['source_base_mesh_feature_object_id']
        and source['retained_membership_status'] == 'NotInCountedMembers',
        'MeshSeparate source factory disagrees with independent definition/collection ownership')
    return source


def decode_mesh_separate(data, records, features, member, members, mesh_contents=None):
    """Return decoded/unresolved/scope; successful rows feature_object_id/kind/name/settings."""
    result = dict(decoded=[],unresolved=[],scope=SCOPE)
    candidates = [r for r in records if r.is_primary and r.class_guid == SEPARATE]
    if not candidates:
        return result
    features_by_id = {}
    for feature in features:
        features_by_id.setdefault(feature['object_id'],[]).append(feature)
    strict = mesh_contents if mesh_contents is not None else decode_mesh_contents_variants(data,records,member,members)
    metadata = decode_mesh_contents(data,records,member,members,native_layout_decoder=native_layout,metadata_only=True)
    for record in candidates:
        try:
            definition = decode_mesh_separate_definition(data,records,record.object_id)
            rows = features_by_id.get(record.object_id,[])
            _require(len(rows)==1 and rows[0]['class_guid']==SEPARATE and rows[0]['record_offset']==record.start
                and rows[0].get('native_kind_label')=='MeshSeparate' and rows[0]['name']==definition['name']
                and rows[0]['stored_index']==definition['stored_index'], 'MeshSeparate discovery metadata differs')
            source = _source_provenance(data,records,definition,member,members)
            outputs,errors = [],[]
            for identity in definition['output_mesh_object_ids']:
                matches = [row for row in metadata['decoded'] if row['mesh_object_id']==identity]
                _require(len(matches)==1 and matches[0]['feature_object_id']==record.object_id,
                    'MeshSeparate output lacks strict current metadata/feature-owner proof')
                row = matches[0]
                geometry = [r for r in strict['decoded'] if r['mesh_object_id']==identity]
                _require(len(geometry)<=1, 'MeshSeparate output geometry identity ambiguous')
                outputs.append(dict(metadata=row,qualified_geometry=geometry[0]['geometry'] if geometry else None))
                errors.extend(r for r in strict['unresolved'] if r['mesh_object_id']==identity)
            settings = dict(method=definition['method'],stored_method_code=definition['stored_method_code'],
                is_keep_body=None,is_multiple_bodies=None,
                control_scope='Only isKeepBody=False captured; invariant raw control bytes remain uninterpreted. isMultipleBodies inactive for captured MeshBody input and never queried.',
                source_selection=definition['source_selection'],retained_source=source,
                result_mesh_object_ids=definition['output_mesh_object_ids'],current_result_meshes=outputs,
                current_result_count=len(outputs),result_owner_class_guid=SEPARATE,
                result_scope='Explicit native direct result list equals reciprocal current counted collection. Shell/facegroup algorithms and persistent source/result lifecycle are not reconstructed.',
                geometry_unresolved=errors,
                stored_uninterpreted_control_prefix_hex=definition['stored_uninterpreted_control_prefix_hex'],
                stored_uninterpreted_control_suffix_hex=definition['stored_uninterpreted_control_suffix_hex'],
                method_field_body_relative_offset=definition['method_field_body_relative_offset'],
                repeated_dependency_object_ids=definition['repeated_dependency_object_ids'],layout=definition['layout'])
            result['decoded'].append(dict(feature_object_id=record.object_id,kind='MeshSeparate',name=definition['name'],settings=settings))
        except (ValueError,KeyError,IndexError,UnicodeError,struct.error,TypeError,lzma.LZMAError) as error:
            result['unresolved'].append(dict(feature_object_id=record.object_id,reason=str(error)))
    return result
