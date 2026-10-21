"""Observed octahedral unit-vector pool in qualified UDPMESH buffer2.

Pool order is serialized order only. No vertex/corner/display-node association
is inferred from matching vectors; source/current mesh selection is upstream.
"""
import math
import struct

from decode_mesh_contents import _require

DESCRIPTOR = '83a14403a15403a155c3'
SCOPE = ('Observed Float32-pair octahedral unit-vector pool in typed UDPMESH buffer2, qualified through native '
         'mesh/asset provenance. Directions corroborate saved display-normal sets; vector order, corner/vertex '
         'assignment, unused entries, original PolygonMesh normals and normal regeneration remain unresolved. '
         'Component covectors are derived by the proved native inverse uniform scale, not serialized XYZ normals.')


def unfold_octahedral(x, y):
    _require(math.isfinite(x) and math.isfinite(y) and -1 <= x <= 1 and -1 <= y <= 1,
             'Octahedral pair outside finite observed unit square')
    z = 1-abs(x)-abs(y)
    if z < 0:
        x, y = (1-abs(y))*(1 if x >= 0 else -1), (1-abs(x))*(1 if y >= 0 else -1)
    vector = [x, y, z]
    length = math.sqrt(sum(value*value for value in vector))
    _require(length > 0 and math.isfinite(length), 'Degenerate octahedral normal vector')
    return [value/length for value in vector]


def decode_mesh_normal_pool(mesh):
    geometry = mesh['geometry']
    _require(geometry['format'] in ('ObservedUDPMESHv2SixBufferTetra', 'ObservedUDPMESHv2SixBufferTriangleVariants'), 'Mesh normal source geometry layout not qualified')
    _require(mesh['asset_fusion_uuid'] == geometry['fusion_uuid'] and mesh['asset_member'].endswith('.paramesh'), 'Mesh normal source asset identity disagrees')
    buffers = geometry['buffers']
    _require(len(buffers) == 6 and buffers[2]['buffer_ordinal'] == 2 and buffers[2]['descriptor_hex'] == DESCRIPTOR, 'Unobserved mesh unit-vector buffer descriptor')
    block = buffers[2]
    _require('decompression_scope' not in block, 'Normal pool requires strict complete declared buffer extent')
    raw = bytes.fromhex(block['uncompressed_payload_hex'])
    _require(len(raw) == block['uncompressed_size'] and len(raw) % 8 == 0, 'Invalid Float32-pair normal buffer extent')
    count = len(raw)//8
    nodes, triangles = len(geometry['stored_node_coordinates_float32']), len(geometry['triangle_node_indices'])//3
    _require((nodes, triangles, count) in ((4, 3, 9), (4, 4, 12), (6, 8, 22), (6, 8, 24)), 'Normal pool count outside captured mesh layouts')
    pairs = [list(struct.unpack_from('<2f', raw, i)) for i in range(0, len(raw), 8)]
    _require(b''.join(struct.pack('<2f', *pair) for pair in pairs) == raw, 'Stored Float32-pair replay failed')
    matrix = mesh['asset_coordinates_to_component_matrix']
    _require(len(matrix) == 16 and all(math.isfinite(v) for v in matrix) and matrix[0] > 0 and
             matrix == [matrix[0], 0., 0., 0., 0., matrix[0], 0., 0., 0., 0., matrix[0], 0., 0., 0., 0., 1.],
             'Normal covectors require captured positive native uniform scale')
    _require(mesh['stored_matrix_copies'] == [matrix, matrix], 'Normal source matrix copies disagree')
    vectors = [unfold_octahedral(*pair) for pair in pairs]
    return {'mesh_object_id': mesh['mesh_object_id'], 'component_object_id': mesh['component_object_id'],
            'asset_object_id': mesh['asset_object_id'], 'asset_member': mesh['asset_member'],
            'asset_fusion_uuid': mesh['asset_fusion_uuid'], 'asset_sha256': geometry['asset_sha256'],
            'buffer_ordinal': 2, 'buffer_asset_offset': block['asset_offset'],
            'stored_descriptor_hex': DESCRIPTOR, 'stored_payload_hex': raw.hex(),
            'stored_packed_pairs_float32': pairs, 'stored_unit_vector_count': count,
            'derived_asset_unit_vectors': vectors,
            'derived_component_covectors': [[value/matrix[0] for value in vector] for vector in vectors],
            'native_uniform_scale': matrix[0],
            'lower_hemisphere_pair_count': sum(abs(x)+abs(y) > 1 for x, y in pairs),
            'encoding': 'Octahedral unit vector: z=1-|x|-|y|; fold xy when z<0, retain z, normalize',
            'association_status': 'Serialized vector pool only; per-vertex/corner/display-node association unresolved',
            'original_polygon_mesh_normals_status': 'Not reconstructed by this stored display-direction pool',
            'scope': SCOPE}


def decode_mesh_normal_pools(mesh_contents):
    result = {'decoded': [], 'unresolved': [], 'scope': SCOPE}
    for mesh in mesh_contents['decoded']:
        try:
            result['decoded'].append(decode_mesh_normal_pool(mesh))
        except (ValueError, KeyError, IndexError, struct.error) as error:
            result['unresolved'].append({'mesh_object_id': mesh.get('mesh_object_id'), 'reason': str(error)})
    return result
