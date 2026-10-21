"""Bounded native four-node triangular mesh assets and typed ownership routes.

The six-buffer UDPMESH v2 layout is observed in three owned tetra captures.
Normals, auxiliary streams, material fields and mesh lifecycle stay unresolved.
No BRep conversion, procedural mesh rebuilding or general mesh writer is offered.
"""
import hashlib
import lzma
import math
import re
import struct

from decode_parameters import read_string
from decode_sketch import reference
from decode_placement import IDENTITY, transform_point

MESH = 'EA90DA22-556C-4C61-89BB-20C2681B7A9D'
ASSET = 'A8338A26-5436-433C-8BAC-C3CF024AD595'
ASSET_FILE = 'A1BAA3F6-4B67-4A0D-BACC-75F38A2230F3'
COLLECTION = '443807AD-8025-41A3-8A50-5157579C3D78'
COLLECTION_BASE = 'A7AEA631-985B-4DD1-8CE2-DE2C-14B54081'
OWNER_BASE = 'CB844AB6-240D-4fc9-9C9F-3679DC896D6F'
COMPONENT_BASE = '42054630-20A0-40E1-B969-CFE9E742F5C9'
MESH_FEATURE = '99F6967E-ED35-4222-B906-5CCF0AC70B53'
NAME_HELPER = '702b9cd2-537c-429e-8cc4-22beeeb98c37'
NAME_PROPERTY = 'E5B3F49A-D8D0-4EEF-BC2B-FCDDAEF9745E'
SIGNATURE = bytes.fromhex('895544504d4553480d0a1a0a')
DICTIONARY = bytes.fromhex('86a2723004a372306905a2723106a2723207a17403a17602')
DESCRIPTORS = ['82a14403a15403', '82a15401a16401', '83a14403a15403a155c3',
               '82a15401a16401', '82a15401a16401', '82a15401a16401']
UUID_PATTERN = re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}')
SCOPE = ('Observed UDPMESH v2 six-buffer closed four-node/four-triangle assets, typed native mesh/collection/component '
         'ownership and reciprocal asset UUID/filename links. Native mesh matrices recover component centimetres; '
         'triangle indices use stored signed forward differences and a final absolute anchor. Normals/auxiliary '
         'buffers, material semantics, BaseFeature ownership, Plane Cut, lifecycle, BRep conversion and regeneration remain unresolved.')


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _protobuf(data):
    """Frame only varint/length-delimited metadata fields; retain literal bytes."""
    cursor, fields = 0, []
    def varint():
        nonlocal cursor
        value = 0
        for i in range(10):
            _require(cursor < len(data), 'Truncated mesh metadata varint')
            byte = data[cursor]; cursor += 1
            value |= (byte & 127) << (7*i)
            if byte < 128:
                _require(i == 0 or byte != 0, 'Noncanonical mesh metadata varint')
                return value
        raise ValueError('Mesh metadata varint exceeds bound')
    while cursor < len(data):
        start = cursor
        key = varint(); number, wire = key >> 3, key & 7
        _require(number > 0 and wire in (0, 2), 'Unobserved mesh metadata wire type')
        if wire == 0:
            value = varint()
        else:
            n = varint()
            _require(n <= 4096 and cursor+n <= len(data), 'Mesh metadata field exceeds bounded extent')
            value = data[cursor:cursor+n]; cursor += n
        fields.append((number, wire, value, start, cursor))
        _require(len(fields) <= 64, 'Too many mesh metadata fields')
    return fields


def _backward_differences(values):
    result = list(values)
    for i in range(len(result)-2, -1, -1):
        result[i] = result[i+1]-result[i]
    return result


def _triangle_properties(points, indices):
    area, volume, directed = 0.0, 0.0, {}
    for i in range(0, len(indices), 3):
        triangle = indices[i:i+3]
        _require(len(set(triangle)) == 3, 'Degenerate mesh triangle indices')
        a, b, c = [points[j] for j in triangle]
        u, v = [b[j]-a[j] for j in range(3)], [c[j]-a[j] for j in range(3)]
        cross = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
        triangle_area = math.sqrt(sum(x*x for x in cross))/2
        _require(triangle_area > 0 and math.isfinite(triangle_area), 'Degenerate mesh triangle geometry')
        area += triangle_area
        volume += sum(a[j]*(b[(j+1)%3]*c[(j+2)%3]-b[(j+2)%3]*c[(j+1)%3]) for j in range(3))/6
        for j in range(3):
            edge = triangle[j], triangle[(j+1)%3]
            directed[edge] = directed.get(edge, 0)+1
    closed_oriented = len(directed) == 12 and all(count == 1 and directed.get((b, a)) == 1 for (a, b), count in directed.items())
    return {'triangle_count': len(indices)//3, 'derived_area_cm2': area,
            'derived_signed_volume_cm3': volume, 'derived_absolute_volume_cm3': abs(volume),
            'derived_closed_oriented_edge_incidence': closed_oriented,
            'derived_undirected_edge_count': len({tuple(sorted(e)) for e in directed}),
            'derived_component_bounds_cm': {'min': [min(p[j] for p in points) for j in range(3)],
                                            'max': [max(p[j] for p in points) for j in range(3)]}}


def decode_paramesh_geometry(blob):
    """Strict observed container, bounded LZMA buffers and literal triangle data."""
    _require(len(blob) <= 1024*1024 and blob[:12] == SIGNATURE, 'Unsupported mesh asset signature/size')
    _require(blob[12:48] == struct.pack('<I', 2)+bytes(32), 'Unobserved mesh asset version/header')
    metadata_length, metadata_kind = struct.unpack_from('<QI', blob, 48)
    _require(metadata_kind == 1 and 0 < metadata_length <= 4096 and 60+metadata_length <= len(blob), 'Unobserved mesh metadata framing')
    metadata = blob[60:60+metadata_length]
    fields = _protobuf(metadata)
    _require([(n, w) for n, w, _, _, _ in fields] == [(4, 2), (5, 2), (7, 2), (8, 2), (9, 0), (12, 2), (21, 2), (22, 2)], 'Unobserved mesh metadata field sequence')
    naming = _protobuf(fields[3][2])
    _require([(n, w) for n, w, _, _, _ in naming] == [(1, 2), (3, 2)] and naming[0][2] == b'fusion_uuid', 'Mesh fusion_uuid metadata framing missing')
    fusion_uuid = naming[1][2].decode('ascii')
    _require(UUID_PATTERN.fullmatch(fusion_uuid) is not None, 'Invalid mesh asset fusion_uuid')
    _require(fields[4][2] == 1 and fields[6][2] == b'v' and fields[7][2] == b't', 'Unobserved mesh metadata literal controls')
    cursor = 60+metadata_length
    dictionary_length, dictionary_kind = struct.unpack_from('<QI', blob, cursor)
    _require(dictionary_length == len(DICTIONARY) and dictionary_kind == 3 and blob[cursor+12:cursor+12+dictionary_length] == DICTIONARY, 'Unobserved mesh buffer dictionary')
    dictionary_end = cursor+12+dictionary_length
    cursor = dictionary_end
    blocks, raw_buffers = [], []
    for ordinal, descriptor in enumerate(DESCRIPTORS):
        _require(cursor+14 <= len(blob), 'Truncated mesh buffer header')
        length, kind, descriptor_length = struct.unpack_from('<QIH', blob, cursor)
        end = cursor+12+length
        _require(kind == 4 and 6+descriptor_length < length <= 65536 and end <= len(blob), 'Unobserved mesh buffer framing/size')
        descriptor_start = cursor+14
        actual_descriptor = blob[descriptor_start:descriptor_start+descriptor_length]
        _require(actual_descriptor.hex() == descriptor, 'Unobserved mesh buffer descriptor')
        size_offset = descriptor_start+descriptor_length
        uncompressed_size = struct.unpack_from('<I', blob, size_offset)[0]
        compressed = blob[size_offset+4:end]
        _require(0 < uncompressed_size <= 65536 and compressed[:2] == b'\x5d\x14', 'Unobserved mesh LZMA properties/size')
        decoder = lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=[{
            'id': lzma.FILTER_LZMA1, 'dict_size': 1 << 20, 'lc': 3, 'lp': 0, 'pb': 2}])
        raw = decoder.decompress(compressed[2:], max_length=uncompressed_size+1)
        _require(len(raw) == uncompressed_size and not decoder.eof and decoder.needs_input and not decoder.unused_data, 'Mesh LZMA decoded extent/end-marker disagrees')
        blocks.append({'buffer_ordinal': ordinal, 'asset_offset': cursor, 'stored_length': length,
                       'stored_kind': kind, 'descriptor_hex': descriptor, 'uncompressed_size': uncompressed_size,
                       'compressed_properties_hex': compressed[:2].hex(), 'compressed_payload_hex': compressed[2:].hex(),
                       'uncompressed_payload_hex': raw.hex(), 'stored_frame_hex': blob[cursor:end].hex()})
        raw_buffers.append(raw); cursor = end
    _require(cursor == len(blob), 'Unexpected trailing mesh asset bytes')
    _require([len(r) for r in raw_buffers] == [48, 48, 96, 32, 48, 16], 'Only observed four-node/four-triangle buffer dimensions are supported')
    coordinates = list(struct.unpack('<12f', raw_buffers[0]))
    _require(all(math.isfinite(v) for v in coordinates), 'Nonfinite stored mesh coordinates')
    differences = list(struct.unpack('<12i', raw_buffers[1]))
    indices = _backward_differences(differences)
    _require(all(0 <= index < 4 for index in indices), 'Decoded mesh triangle index outside node array')
    _require([indices[i+1]-indices[i] for i in range(11)]+[indices[-1]] == differences, 'Mesh signed-difference inverse replay failed')
    points = [coordinates[i:i+3] for i in range(0, len(coordinates), 3)]
    _require(_triangle_properties(points, indices)['derived_closed_oriented_edge_incidence'], 'Mesh topology is outside observed closed oriented tetra layout')
    return {'format': 'ObservedUDPMESHv2SixBufferTetra', 'asset_size_bytes': len(blob),
            'asset_sha256': hashlib.sha256(blob).hexdigest(), 'fusion_uuid': fusion_uuid,
            'stored_header_metadata_dictionary_hex': blob[:dictionary_end].hex(),
            'stored_metadata_hex': metadata.hex(), 'buffers': blocks,
            'stored_node_coordinates_float32': points, 'triangle_node_indices': indices,
            'triangle_index_encoding': 'SignedInt32 forward differences followed by final absolute index; integrated backward',
            'unresolved_buffers': [2, 3, 4, 5],
            'normal_scope': 'Stored descriptor/buffer bytes retained; no normals decoding or semantics for auxiliary buffers'}


def replay_paramesh_geometry(asset):
    """Replay literal framed bytes, not a mesh authoring API."""
    return bytes.fromhex(asset['stored_header_metadata_dictionary_hex'])+b''.join(bytes.fromhex(b['stored_frame_hex']) for b in asset['buffers'])


def decode_mesh_contents(data, records, member, members):
    """Read native mesh rows without changing features, source bytes or records."""
    result = {'decoded': [], 'unresolved': [], 'scope': SCOPE}
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    def typed(identity, guid):
        rows = grouped.get(identity, [])
        _require(len(rows) == 1 and rows[0].class_guid == guid, 'Mesh typed reference missing, ambiguous or wrong class: '+guid)
        return rows[0], data[rows[0].body:rows[0].end]
    def inherited(identity, guid):
        rows = [r for r in records if not r.is_primary and r.object_id == identity and r.class_guid == guid]
        _require(len(rows) == 1, 'Mesh inherited typed record missing or ambiguous: '+guid)
        return rows[0], data[rows[0].body:rows[0].end]
    for record in records:
        if not record.is_primary or record.class_guid != MESH:
            continue
        try:
            typed(record.object_id, MESH)
            body = data[record.body:record.end]
            _require(body[:22] == bytes.fromhex('00000100000000000000000101010000000000000000'), 'Unobserved native mesh prefix')
            cursor, matrices, matrix_encoding = 22, [], []
            for _ in range(2):
                _require(cursor < len(body) and body[cursor] in (0, 1), 'Unknown native mesh matrix encoding')
                implicit = body[cursor] == 1; cursor += 1
                matrix = list(IDENTITY) if implicit else list(struct.unpack_from('<16d', body, cursor))
                if not implicit:
                    cursor += 128
                _require(all(math.isfinite(x) for x in matrix) and matrix[0] > 0 and
                         matrix == [matrix[0], 0., 0., 0., 0., matrix[0], 0., 0., 0., 0., matrix[0], 0., 0., 0., 0., 1.],
                         'Only observed origin-preserving uniform native mesh matrices are supported')
                matrices.append(matrix); matrix_encoding.append('ImplicitIdentity' if implicit else 'ExplicitFloat64Matrix')
            _require(matrices[0] == matrices[1], 'Stored native mesh matrix copies disagree')
            matrix_end = cursor
            _, owner_body = inherited(record.object_id, OWNER_BASE)
            _require(len(owner_body) == 11, 'Unobserved mesh collection owner fragment')
            collection_id = reference(owner_body, 0)
            collection_record, _ = typed(collection_id, COLLECTION)
            collection_base, collection_body = inherited(collection_id, COLLECTION_BASE)
            _require(collection_body[:1] == b'\0', 'Unobserved mesh collection prefix')
            count = struct.unpack_from('<I', collection_body, 1)[0]
            _require(1 <= count <= 10000 and len(collection_body) == 16+11*count, 'Unobserved mesh collection extent')
            mesh_ids = [reference(collection_body, 5+11*i) for i in range(count)]
            _require(len(set(mesh_ids)) == count and mesh_ids.count(record.object_id) == 1, 'Mesh collection membership missing or repeated')
            for identity in mesh_ids:
                typed(identity, MESH)
                _, backlink = inherited(identity, OWNER_BASE)
                _require(len(backlink) == 11 and reference(backlink, 0) == collection_id, 'Mesh collection membership does not reciprocate')
            component_id = reference(collection_body, len(collection_body)-11)
            component_rows = grouped.get(component_id, [])
            _require(len(component_rows) == 1, 'Native mesh component identity missing or ambiguous')
            inherited(component_id, COMPONENT_BASE)
            candidates = []
            for asset_record in records:
                if not asset_record.is_primary or asset_record.class_guid != ASSET:
                    continue
                _, asset_body = typed(asset_record.object_id, ASSET)
                if asset_body[:13] != bytes.fromhex('00000000000000001040010100'):
                    continue
                n = struct.unpack_from('<I', asset_body, 13)[0]
                _require(n == 36 and len(asset_body) == 17+n+15, 'Unobserved native mesh asset UUID extent')
                uuid = asset_body[17:17+n].decode('ascii')
                _require(UUID_PATTERN.fullmatch(uuid) is not None and asset_body[-4:] == bytes(4), 'Unobserved native mesh asset UUID/footer')
                file_id = reference(asset_body, 17+n)
                file_record, file_body = typed(file_id, ASSET_FILE)
                _require(file_body[:2] == bytes(2) and reference(file_body, 2) == asset_record.object_id, 'Native mesh asset/filename backlink disagrees')
                filename, end = read_string(file_body, 13)
                _require(end == len(file_body) and re.fullmatch(r'ParaMeshGeometry\.[0-9a-f-]{36}\.paramesh', filename) is not None, 'Unobserved native mesh asset filename')
                marker = b'\1'+struct.pack('<Q', asset_record.object_id)+bytes(2)
                offsets = [i for i in range(matrix_end, len(body)-10) if body[i:i+11] == marker]
                for asset_offset in offsets:
                    if asset_offset < 22 or body[asset_offset+11] != 0:
                        continue
                    property_id = reference(body, asset_offset-22)
                    _, property_body = typed(property_id, NAME_PROPERTY)
                    _require(len(property_body) == 21 and property_body[:2] == bytes(2) and reference(property_body, 2) == record.object_id and property_body[13:] == bytes(8), 'Native mesh name-property backlink disagrees')
                    render_collection_id = reference(body, asset_offset-11)
                    typed(render_collection_id, 'CD57BC48-50EC-47DC-975A-FB6DEA72F4DA')
                    helper_id = reference(body, asset_offset+12)
                    _, helper_body = typed(helper_id, NAME_HELPER)
                    _require(len(helper_body) == 114 and helper_body[:10] == bytes.fromhex('00000000000002000000'), 'Unobserved mesh name-helper layout')
                    name, name_end = read_string(body, asset_offset+23)
                    _require(body[name_end:name_end+18] == struct.pack('<4f', 0, 0, 0, 1)+b'\1\1', 'Unobserved mesh name/material separator')
                    owner_feature = None
                    if asset_offset >= 33 and body[asset_offset-33] == 1:
                        possible = reference(body, asset_offset-33)
                        _, feature_body = typed(possible, MESH_FEATURE)
                        _require(feature_body[:2] == bytes(2) and struct.unpack_from('<I', feature_body, 2)[0] == 1 and reference(feature_body, 6) == record.object_id, 'Native BaseMeshFeature membership does not reciprocate mesh reference')
                        owner_feature = possible
                    else:
                        _require(body[asset_offset-23:asset_offset-22] == b'\0', 'Unobserved nullable native mesh feature slot')
                    asset_member = member.split('/FusionDesignSegmentType1/')[0]+'/ParaMeshGeometry.BlobParts/'+filename
                    _require(asset_member in members, 'Native mesh filename does not resolve in same asset')
                    geometry = decode_paramesh_geometry(members[asset_member])
                    _require(geometry['fusion_uuid'] == uuid, 'Native mesh UUID disagrees with stored asset fusion_uuid')
                    component_points = [transform_point(matrices[0], p) for p in geometry['stored_node_coordinates_float32']]
                    geometry['component_node_coordinates_cm'] = component_points
                    geometry.update(_triangle_properties(component_points, geometry['triangle_node_indices']))
                    candidates.append({'mesh_object_id': record.object_id, 'mesh_class_guid': MESH,
                        'mesh_record_offset': record.start, 'feature_object_id': owner_feature,
                        'native_feature_class_guid': MESH_FEATURE if owner_feature is not None else None,
                        'feature_owner_scope': 'Explicit reciprocal native BaseMeshFeature membership' if owner_feature is not None else 'Native feature slot null; API BaseFeature association not inferred',
                        'component_object_id': component_id, 'component_primary_class_guid': component_rows[0].class_guid,
                        'mesh_collection_object_id': collection_id, 'mesh_collection_record_offset': collection_record.start,
                        'mesh_collection_base_record_offset': collection_base.start, 'collection_mesh_object_ids': mesh_ids,
                        'name': name, 'name_helper_object_id': helper_id, 'name_property_object_id': property_id,
                        'asset_object_id': asset_record.object_id, 'asset_record_offset': asset_record.start,
                        'asset_filename_object_id': file_id, 'asset_filename_record_offset': file_record.start,
                        'asset_member': asset_member, 'asset_fusion_uuid': uuid,
                        'asset_reference_field_offset': record.body+asset_offset,
                        'stored_matrix_encodings': matrix_encoding, 'stored_matrix_copies': matrices,
                        'asset_coordinates_to_component_matrix': matrices[0],
                        'matrix_scope': 'Observed equal uniform-scale matrices; transformed stored vertices agree with component MeshBody.mesh API coordinates in three captures. Assembly/world placement and arbitrary affine cases unsupported.',
                        'stored_native_prefix_material_hex': body[matrix_end:asset_offset-22].hex(),
                        'stored_native_material_tail_hex': body[name_end+18:].hex(),
                        'geometry': geometry,
                        'ownership_evidence': 'Unique typed mesh/collection reciprocal membership and inherited component owner; native asset UUID/filename backlinks plus same-asset filename and embedded fusion_uuid agreement',
                        'unresolved': ['Normal buffer semantics', 'Auxiliary buffers', 'Material/property fields', 'API baseOrFormFeature is not reconstructed', 'Timeline lifecycle and mesh regeneration']})
            _require(len(candidates) == 1, 'Native mesh asset/owner route missing or ambiguous')
            result['decoded'].append(candidates[0])
        except (ValueError, IndexError, UnicodeError, struct.error, lzma.LZMAError) as error:
            result['unresolved'].append({'mesh_object_id': record.object_id, 'reason': str(error)})
    return result
