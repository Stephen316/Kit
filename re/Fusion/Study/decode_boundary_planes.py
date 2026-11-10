"""Observed Boundary Fill plane proxy variant with explicit native-plane links."""

import struct
import uuid

from decode_parameters import read_string
from decode_selection import native_proxy_references
from decode_sketch import reference


def resolve_boundary_plane_selection(data, records, selection_id, known_entities, owner_id):
    """Resolve the observed 252-byte descriptor; raise for unobserved layouts.

    This follows explicit proxy/descriptor/terminal references into independently
    decoded construction geometry. Descriptor metadata after the UUID strings is
    retained as opaque bytes and does not establish occurrence transforms or the
    side of a selected Boundary Fill cell.
    """
    def primary(identity, guid):
        candidates = [r for r in records if r.is_primary and r.object_id == identity and r.class_guid == guid]
        if len(candidates) != 1:
            raise ValueError("Boundary Fill plane typed reference unresolved: "+guid)
        record = candidates[0]
        return record, data[record.body:record.end]

    proxy, payload = primary(selection_id, "2CA5A1CD-C99B-4C9B-91AF-57989148E841")
    if reference(payload, len(payload)-11) != owner_id:
        raise ValueError("Boundary Fill plane proxy owner disagrees")
    descriptor_ids, props = native_proxy_references(data, proxy)
    if len(descriptor_ids) != 1 or props:
        raise ValueError("Unsupported Boundary Fill plane proxy list/attributes")
    _, descriptor = primary(descriptor_ids[0], "5A1BF548-241F-46FD-9FB5-E4B05126EB9D")
    if (len(descriptor) != 252 or descriptor[:2] != b"\0\0"
            or struct.unpack_from("<I", descriptor, 13)[0] != 1
            or reference(descriptor, len(descriptor)-11) != owner_id):
        raise ValueError("Unsupported Boundary Fill plane descriptor layout/owner")
    namespace, cursor = read_string(descriptor, 17)
    entity_guid, cursor = read_string(descriptor, cursor)
    if len(namespace) != 36 or len(entity_guid) != 36:
        raise ValueError("Unsupported Boundary Fill plane descriptor UUIDs")
    uuid.UUID(namespace)
    uuid.UUID(entity_guid)
    if cursor != 169 or descriptor[cursor:cursor+30] != bytes.fromhex(
            "020000000000000000000000000000000400000000000000000000000000"):
        raise ValueError("Unobserved Boundary Fill plane descriptor metadata prefix")
    terminal_id = reference(descriptor, 2)
    _, terminal = primary(terminal_id, "90055C05-546C-4EE7-B3C9-3DD922AD0C9C")
    if len(terminal) != 10 or terminal[:2] != b"\0\0":
        raise ValueError("Unsupported Boundary Fill plane native terminal")
    entity_id = struct.unpack_from("<Q", terminal, 2)[0]
    plane = known_entities.get(entity_id)
    if plane is None or plane.get("kind") != "ConstructionPlane":
        raise ValueError("Boundary Fill plane terminal does not resolve to known native plane geometry")
    primary(entity_id, "8D424E29-DE23-4B1F-A3AD-84C52A497D1A")
    return {"entity": plane, "selection_object_id": selection_id,
            "descriptor_object_id": descriptor_ids[0], "terminal_object_id": terminal_id,
            "namespace_text": namespace, "entity_guid_text": entity_guid,
            "association": "Explicit owned proxy -> plane descriptor -> typed native-plane terminal reference chain",
            "descriptor_metadata_hex": descriptor[cursor:len(descriptor)-11].hex(),
            "descriptor_metadata_scope": "Stored metadata retained; flags/context semantics are unresolved",
            "coordinate_scope": "Native component geometry; occurrence transforms are not inferred",
            "cell_side_scope": "Plane selection resolved; selected-cell side semantics remain unresolved"}
