"""Opt-in observed mesh operation layouts; old successful outputs exact."""
import lzma
import math
import re
import struct

from decode_mesh_contents import (
    ASSET, ASSET_FILE, MESH, UUID_PATTERN, _backward_differences, _require,
    _triangle_properties, decode_mesh_contents, decode_paramesh_geometry, decode_paramesh_header)
from decode_parameters import read_string
from decode_sketch import reference

PLANE_CUT = 'E3EB3760-4362-48D6-ABF3-698B0C12C5A9'
SEPARATE = '6B6FDE2E-D9B9-4866-9D07-3123C919B0D2'
SCOPE = ('Observed size-delimited UDPMESH v2 six-buffer triangle layouts (4 nodes/3 or4 faces,6 nodes/8 faces), '
         'typed mesh collection/component ownership and same-asset UUID/filename links. Only observed uniform '
         'native matrices are applied. Open-mesh signed tetra sums are not enclosed volumes; normal/auxiliary '
         'buffers, arbitrary topology, procedural regeneration and lifecycle remain unresolved.')
SHAPES = {(48, 36, 72, 20, 24, 12), (48, 48, 96, 32, 48, 16),
          (72, 96, 176, 64, 72, 32), (72, 96, 192, 72, 96, 32)}
REMESH_SHAPES = {(108, 168, 248, 88, 88, 56), (192, 336, 432, 152, 120, 112)}
COMBINE_SHAPES = {(792, 1536, 1440, 456, 400, 512), (492, 936, 992, 332, 232, 312)}
CUT_SHAPE = (312, 576, 744, 268, 208, 192)
SHELL_OPEN_SHAPES = {(32940, 65772, 22056, 48, 184, 21924), (18672, 37236, 12536, 44, 168, 12412)}
SHELL_CLOSED_SHAPES = {(32940, 65784, 22080, 60, 208, 21928)}
SHELL_SHAPES = SHELL_OPEN_SHAPES | SHELL_CLOSED_SHAPES
SEPARATE_COMPOUND_SHAPE = (96, 96, 192, 64, 96, 32)
ZERO_SUFFIX_SHAPES = {CUT_SHAPE, SEPARATE_COMPOUND_SHAPE}
OPERATION_SHAPES = REMESH_SHAPES | COMBINE_SHAPES | ZERO_SUFFIX_SHAPES | SHELL_SHAPES
OPERATION_SCOPE = ('Observed size-delimited UDPMESH v2 triangle layouts including9/14,16/28,66/128 and41/78 nodes/faces; '
                'typed native mesh/component/asset routes and positive uniform matrices. Counts derive from exact '
                'coordinate/index buffer extents. Normal/auxiliary buffers, arbitrary layouts, lifecycle and regeneration remain unresolved.')
CUT_SCOPE = ('Observed26-node/48-triangle Cut layout with exact declared-size index payload and separately retained '
             'single emitted zero suffix. Typed native ownership/asset links and strict index replay qualify geometry; '
             'surplus-byte meaning, auxiliary buffers, lifecycle and regeneration remain unresolved.')
SHELL_SCOPE = ('Observed Shell cache layouts with2745 nodes/5481-or5482 triangles and1556/3103, bounded buffers '
               'through65784 bytes, typed native ownership/asset routes and positive uniform matrices. Open cases '
               'retain three boundary edges and no enclosed volume; auxiliary semantics, lifecycle and regeneration unresolved.')
SEPARATE_SCOPE = ('Observed Separate direct output-list ownership and typed current component/mesh/asset routes, '
                  'including two disjoint tetrahedra in one8-node/8-triangle asset with separately retained zero index suffix. '
                  'Stored source retention, auxiliary bytes, arbitrary partitions and regeneration remain unqualified.')


def triangle_properties(points, indices):
    props = _triangle_properties(points, indices)
    directed = {}
    for start in range(0, len(indices), 3):
        tri = indices[start:start+3]
        for i in range(3):
            key = tri[i], tri[(i+1)%3]
            directed[key] = directed.get(key, 0)+1
    closed = bool(directed) and all(n == 1 and directed.get((b, a)) == 1 for (a, b), n in directed.items())
    props['derived_closed_oriented_edge_incidence'] = closed
    props['derived_boundary_edge_count'] = sum(n for (a, b), n in directed.items() if (b, a) not in directed)
    props['volume_applicability'] = ('Closed oriented stored triangular mesh; signed tetrahedral sum is a derived enclosed volume'
                                    if closed else 'Open mesh: signed tetrahedral sum is not an enclosed physical volume')
    if not closed:
        props['raw_signed_tetrahedral_sum_cm3'] = props.pop('derived_signed_volume_cm3')
        props.pop('derived_absolute_volume_cm3')
        props['derived_enclosed_volume_cm3'] = None
    return props


def decode_geometry_layout(framing, raw_buffers):
    shape = tuple(map(len, raw_buffers))
    _require(shape in SHAPES | OPERATION_SHAPES, 'Unobserved opt-in mesh buffer dimensions')
    suffix = framing['buffers'][1].get('emitted_suffix_hex')
    _require((shape in ZERO_SUFFIX_SHAPES and suffix == '00') or (shape not in ZERO_SUFFIX_SHAPES and suffix is None),
             'Index surplus evidence outside captured Cut layout')
    node_count, face_count = shape[0]//12, shape[1]//12
    coordinates = list(struct.unpack('<'+'f'*(node_count*3), raw_buffers[0]))
    _require(all(math.isfinite(v) for v in coordinates), 'Nonfinite stored mesh coordinates')
    differences = list(struct.unpack('<'+'i'*(face_count*3), raw_buffers[1]))
    indices = _backward_differences(differences)
    _require(all(0 <= i < node_count for i in indices), 'Decoded mesh triangle index outside node array')
    _require([indices[i+1]-indices[i] for i in range(len(indices)-1)]+[indices[-1]] == differences,
             'Opt-in mesh signed-difference inverse replay failed')
    points = [coordinates[i:i+3] for i in range(0, len(coordinates), 3)]
    props = triangle_properties(points, indices)
    expected_open = face_count == 3 or shape in SHELL_OPEN_SHAPES
    _require(props['derived_closed_oriented_edge_incidence'] == (not expected_open), 'Mesh incidence outside captured open/closed layout')
    if shape in SHELL_OPEN_SHAPES:
        _require(props['derived_boundary_edge_count'] == 3, 'Shell boundary incidence outside captured layout')
    return {'format': 'ObservedUDPMESHv2SixBufferTriangleVariants', **framing,
            'stored_node_coordinates_float32': points, 'triangle_node_indices': indices,
            'triangle_index_encoding': 'SignedInt32 forward differences followed by final absolute index; integrated backward',
            'node_count': node_count, 'triangle_count': face_count,
            'count_evidence': {'stored_coordinate_buffer_bytes': shape[0], 'coordinate_descriptor': 'D=3,T=3 observed Float32 triples',
                'stored_triangle_buffer_bytes': shape[1], 'triangle_descriptor': 'T=1,d=1 observed Int32 forward-difference triples',
                'node_count_derivation': 'Stored uncompressed coordinate byte count divided by12',
                'triangle_count_derivation': 'Stored uncompressed triangle-index byte count divided by12',
                'metadata_count_scope': 'No independent vertex/triangle scalar count identified; repeated buffer kind4 remains4 for6-node/8-triangle captures and is not a vertex/face count'},
            'unresolved_buffers': [2, 3, 4, 5],
            'normal_scope': 'Stored descriptor/buffer bytes retained; normal/auxiliary transformations unresolved'}


def native_layout(stage, payload, context):
    if stage == 'MeshPrefix':
        _require(len(payload) == 22 and payload[:2] == bytes(2) and payload[10:] == bytes.fromhex('000101010000000000000000'), 'Unobserved opt-in native mesh prefix')
        index = struct.unpack_from('<Q', payload, 2)[0]
        _require(index in (1, 2, 3), 'Unobserved native mesh stored index')
        return {'stored_mesh_index': index, 'stored_prefix_11_22_hex': payload[11:].hex(),
                'prefix_scope': ('Captured stored index3 in Separate output; packed prefix retained literally without flag meanings'
                    if index == 3 else 'Stored index1/2 observed; remaining packed prefix retained literally, never treated as coincident native object257 reference')}
    if stage == 'AssetPrefix':
        _require(len(payload) == 13 and payload[:2] == bytes(2) and payload[10] in (0, 1) and payload[11:] == b'\1\0', 'Unobserved mesh asset prefix')
        scalar = struct.unpack_from('<d', payload, 2)[0]
        _require(math.isfinite(scalar), 'Invalid mesh asset header scalar')
        return {'stored_asset_header_scalar': scalar, 'stored_asset_header_flag': payload[10], 'asset_header_scalar_scope': 'Literal finite native header value; semantic meaning unresolved'}
    if stage == 'ComponentProperties':
        return triangle_properties(payload, context['indices'])
    if stage == 'MeshFeatureOwner':
        from decode_mesh_selections import decode_mesh_selection
        data, records = context['data'], context['records']
        matches = [r for r in records if r.is_primary and r.object_id == context['feature_object_id']]
        if len(matches) == 1 and matches[0].class_guid == SEPARATE:
            from decode_mesh_separate import decode_mesh_separate_definition
            definition = decode_mesh_separate_definition(data, records, context['feature_object_id'])
            _require(definition['feature_object_id'] == context['feature_object_id'] and
                     definition['output_mesh_object_ids'].count(context['mesh_object_id']) == 1,
                     'Separate native output membership does not reciprocate mesh feature owner')
            return {'native_feature_owner_output_membership': {
                'feature_object_id': context['feature_object_id'], 'feature_class_guid': SEPARATE,
                'ordered_output_mesh_object_ids': definition['output_mesh_object_ids'],
                'current_mesh_object_id': context['mesh_object_id'],
                'association': 'Explicit typed Separate output list and native mesh owner backlinks; current collection membership independently checked'}}
        _require(len(matches) == 1 and matches[0].class_guid == PLANE_CUT, 'Unobserved mesh feature owner variant')
        body = data[matches[0].body:matches[0].end]
        _require(body[:2] == bytes(2) and struct.unpack_from('<I', body, 2)[0] == 1 and struct.unpack_from('<I', body, 6)[0] == 16,
                 'Only captured SplitBody mesh owner variant is supported')
        selection = decode_mesh_selection(data, records, reference(body, 154), context['feature_object_id'])
        _require(selection['mesh_object_id'] == context['mesh_object_id'], 'PlaneCut result descriptor does not reciprocate native mesh feature owner')
        return {'native_feature_owner_selection': selection}
    raise ValueError('Unknown opt-in mesh layout stage')


def decode_mesh_asset(data, records, asset_object_id, member, members, *, metadata_only=False):
    """Typed asset UUID/file/backlink route independent of current mesh selection."""
    def typed(identity, guid):
        rows = [r for r in records if r.is_primary and r.object_id == identity]
        _require(len(rows) == 1 and rows[0].class_guid == guid, 'Mesh asset typed identity missing/ambiguous/wrong class')
        return rows[0], data[rows[0].body:rows[0].end]
    record, body = typed(asset_object_id, ASSET)
    extra = native_layout('AssetPrefix', body[:13], {})
    n = struct.unpack_from('<I', body, 13)[0]
    _require(n == 36 and len(body) == 68 and body[-4:] == bytes(4), 'Unobserved mesh asset UUID extent/footer')
    uuid = body[17:53].decode('ascii')
    _require(UUID_PATTERN.fullmatch(uuid) is not None, 'Invalid native mesh asset UUID')
    filename_id = reference(body, 53)
    filename_record, filename_body = typed(filename_id, ASSET_FILE)
    _require(filename_body[:2] == bytes(2) and reference(filename_body, 2) == asset_object_id, 'Mesh asset filename backlink disagrees')
    filename, end = read_string(filename_body, 13)
    _require(end == len(filename_body) and re.fullmatch(r'ParaMeshGeometry\.[0-9a-f-]{36}\.paramesh', filename) is not None, 'Invalid native mesh asset filename')
    path = member.split('/FusionDesignSegmentType1/')[0]+'/ParaMeshGeometry.BlobParts/'+filename
    _require(path in members, 'Mesh asset file absent from same asset')
    route_extras = {}
    if metadata_only:
        header, _ = decode_paramesh_header(members[path])
        _require(header['fusion_uuid'] == uuid, 'Native mesh asset UUID does not match embedded fusion_uuid')
        geometry = None
        route_extras = {'asset_header': header,
            'geometry_status': 'Not decoded: explicit typed asset metadata-only route; compressed-buffer validity unqualified'}
    else:
        try:
            geometry = decode_paramesh_geometry(members[path], geometry_decoder=decode_geometry_layout,
                allow_index_zero_suffix=True, max_uncompressed_buffer_size=65784)
        except lzma.LZMAError as error:
            raise ValueError(str(error)) from error
        _require(geometry['fusion_uuid'] == uuid, 'Native mesh asset UUID does not match embedded fusion_uuid')
    return {'asset_object_id': asset_object_id, 'asset_record_offset': record.start,
            'asset_filename_object_id': filename_id, 'asset_filename_record_offset': filename_record.start,
            'asset_member': path, 'asset_fusion_uuid': uuid, **extra, 'geometry': geometry, **route_extras}


def decode_mesh_contents_variants(data, records, member, members):
    strict = decode_mesh_contents(data, records, member, members)
    if not strict['unresolved']:
        return strict
    result = decode_mesh_contents(data, records, member, members,
        geometry_decoder=decode_geometry_layout, native_layout_decoder=native_layout, allow_index_zero_suffix=True,
        max_uncompressed_buffer_size=65784)
    shapes = [tuple(b['uncompressed_size'] for b in row['geometry']['buffers']) for row in result['decoded']]
    result['scope'] = (SHELL_SCOPE if any(shape in SHELL_SHAPES for shape in shapes) else
                      SEPARATE_SCOPE if any('native_feature_owner_output_membership' in row for row in result['decoded']) else
                      CUT_SCOPE if CUT_SHAPE in shapes else OPERATION_SCOPE if any(shape in OPERATION_SHAPES
                                        for shape in shapes) else SCOPE)
    return result
