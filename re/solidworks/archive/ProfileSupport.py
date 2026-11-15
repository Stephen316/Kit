"""Read the witnessed modern profile continuation up to the face support token."""

from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KObjectRefKind,
)
from convert.adapters.solidworks.resolved.ContourChain import ReadChain
from FaceOccurrence import read_surface_id
from SketchRoot import KGeneration, Require


# the cut profile reaches the same contour format through a different class kind
def read_chain(cursor, pointer_kind=KClassRefKind):
    return ReadChain(cursor, pointer_kind)


# the embedded kernel packet has its own length and independent object storage
def read_body_packet(cursor):
    Require(cursor.read("<iB"), (3, 0), "profile body and compact kernel selector")
    (length,) = cursor.read("<i")
    start = cursor.position
    Require(0 < length <= len(cursor.blob) - start, True, "bounded kernel packet")
    cursor.position += length
    return {"start": start, "end": cursor.position, "size": length}


# each saved profile edge records its specific cap and boundary in the shared archive map
def read_edge(cursor, pointer_kind):
    offset = cursor.position
    index = cursor.pointer(pointer_kind, "moEdgeRef_c")
    Require(cursor.read("<3Ii"), (1, 0, 4, 512), "guarded edge entity array")
    cursor.read("<I")
    cursor.vector(2)
    cursor.null()
    cap = read_surface_id(cursor, "moEndFaceSurfIdRep_c", cap=True)
    boundaries = [read_surface_id(cursor, "moFromSktEntSurfIdRep_c") for _ in range(3)]
    Require(cursor.read("<4I"), (0, 0, KGeneration, 0), "modern edge reference trailer")
    for boundary in boundaries:
        for field in ("feature_id", "time_word", "file_ref_object"):
            Require(boundary[field], cap[field], f"same edge source {field}")
    return {
        "offset": offset,
        "object_index": index,
        "end": cursor.position,
        "primary": cap,
        "boundary_occurrences": [boundary["occurrence"] for boundary in boundaries],
    }


# reaching the witnessed token through typed reads distinguishes the effective support from lookalikes
def read_profile_support(cursor):
    sketch = cursor.pointer(KObjectRefKind, "sgSketch")
    return read_profile_body(cursor, sketch)


# the sequential reader already resolved the sketch before entering the profile body
def read_profile_body(cursor, sketch):
    Require(cursor.read("<Ii"), (1, 1), "one modern profile chain")
    chain = read_chain(cursor)
    body = read_body_packet(cursor)
    Require(cursor.read("<i"), (0,), "empty profile pair map")
    Require(cursor.read("<H"), (4,), "four profile edge references")
    edges = [read_edge(cursor, KDefinitionKind)]
    edges.extend(read_edge(cursor, KClassRefKind) for _ in range(3))
    Require(cursor.read("<4I"), (4, 16, 1, 4), "observed profile edge index layout")
    edge_order = cursor.read("<4I")
    Require(cursor.read("<i"), (0,), "no secondary body packets")
    contour_flags, contour_count = cursor.read("<IH")
    Require(contour_count, 0, "empty contour object map")
    cursor.null()  # optional profile line handle
    return {
        "sketch_object": sketch,
        "chain": chain,
        "kernel_packet": body,
        "edge_references": edges,
        "edge_order": edge_order,
        "contour_flags": contour_flags,
        "support_offset": cursor.position,
        "next_map_index": cursor.next_index,
    }
