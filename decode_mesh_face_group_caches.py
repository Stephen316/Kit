"""Ordered temporary triangle group labels in qualified UDPMESH buffer5.

Consumes the existing native current-mesh summary. Neither geometry-based
identity selection nor historical/retained-source asset promotion is done here.
"""
import struct

from decode_mesh_contents import _backward_differences, _require

DESCRIPTOR = '82a15401a16401'
OBSERVED_DIMENSIONS = {(4,3),(4,4),(6,8),(8,8),(9,14),(16,28),(26,48),(41,78),(66,128),
                       (1556,3103),(2745,5481),(2745,5482)}
SCOPE = ('Observed complete UDPMESH buffer5 signedInt32 forward differences and final absolute anchor, '
         'yielding one temporary group label per stored triangle in qualified current native mesh/asset '
         'layouts. Ordered API group arrays corroborate the observed layouts; temporary labels are not '
         'persistent native face/group IDs. Retained sources, lifecycle, other auxiliary buffers and '
         'regeneration remain unresolved.')


def decode_mesh_face_group_cache(mesh):
    geometry = mesh['geometry']
    _require(mesh['mesh_object_id'] in mesh['collection_mesh_object_ids'],
             'Face-group source is not a counted current native mesh')
    _require(geometry['format'] in ('ObservedUDPMESHv2SixBufferTetra','ObservedUDPMESHv2SixBufferTriangleVariants'),
             'Face-group cache source geometry not qualified')
    _require(mesh['asset_fusion_uuid'] == geometry['fusion_uuid'] and mesh['asset_member'].endswith('.paramesh'),
             'Face-group cache source asset identity disagrees')
    nodes, indices = geometry['stored_node_coordinates_float32'], geometry['triangle_node_indices']
    _require(len(indices)%3 == 0 and (len(nodes),len(indices)//3) in OBSERVED_DIMENSIONS
             and all(isinstance(i,int) and 0 <= i < len(nodes) for i in indices),
             'Face-group cache geometry dimensions/index bounds outside observed layouts')
    count = len(indices)//3
    buffers = geometry['buffers']
    _require(len(buffers) == 6 and buffers[5]['buffer_ordinal'] == 5,
             'Face-group cache requires six buffers and ordinal5')
    block = buffers[5]
    _require(block['descriptor_hex'] == DESCRIPTOR and 'decompression_scope' not in block,
             'Face-group cache requires complete observed signed-difference descriptor')
    raw = bytes.fromhex(block['uncompressed_payload_hex'])
    _require(len(raw) == block['uncompressed_size'] == count*4,
             'Face-group cache requires one complete Int32 per stored triangle')
    differences = list(struct.unpack('<'+'i'*count,raw))
    labels = _backward_differences(differences)
    _require(all(0 <= value <= 0x7fffffff for value in labels),
             'Face-group temporary label outside observed nonnegative Int32 domain')
    replay = [labels[i+1]-labels[i] for i in range(count-1)]+[labels[-1]]
    _require(replay == differences and struct.pack('<'+'i'*count,*replay) == raw,
             'Face-group forward-difference byte replay disagrees')
    return dict(mesh_object_id=mesh['mesh_object_id'],component_object_id=mesh['component_object_id'],
        asset_object_id=mesh['asset_object_id'],asset_member=mesh['asset_member'],asset_fusion_uuid=mesh['asset_fusion_uuid'],
        asset_sha256=geometry['asset_sha256'],buffer_ordinal=5,buffer_asset_offset=block['asset_offset'],
        stored_descriptor_hex=DESCRIPTOR,stored_payload_hex=raw.hex(),stored_int32_forward_differences=differences,
        decoded_triangle_face_group_temporary_ids=labels,triangle_label_count=count,
        distinct_temporary_label_count=len(set(labels)),
        triangle_order='Consecutive triples of qualified geometry.triangle_node_indices; no coordinate-based reordering',
        encoding='SignedInt32 forward differences followed by final absolute label, integrated backward',
        zero_label_scope='Literal zero retained; no semantic assignment to unlabeled/source/default groups',
        identity_scope='Temporary cache labels only; no persistent native face/group identity',scope=SCOPE)


def decode_mesh_face_group_caches(mesh_contents):
    """Return decoded/unresolved/scope without mutating the current-mesh summary."""
    result = dict(decoded=[],unresolved=[],scope=SCOPE)
    meshes = mesh_contents['decoded']
    ids = [mesh['mesh_object_id'] for mesh in meshes]
    for mesh in meshes:
        try:
            _require(ids.count(mesh['mesh_object_id']) == 1, 'Face-group native mesh identity ambiguous')
            result['decoded'].append(decode_mesh_face_group_cache(mesh))
        except (ValueError,KeyError,IndexError,struct.error,TypeError) as error:
            result['unresolved'].append(dict(mesh_object_id=mesh['mesh_object_id'],reason=str(error)))
    return result
