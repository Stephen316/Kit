from __future__ import annotations

from typing import TYPE_CHECKING as TypeChecking, Sequence

if TypeChecking:
    from convert.adapters.solidworks.core.Native import NativeMarker


def ProfileHeader(
    Edges: Sequence[NativeMarker],
    Markers: Sequence[NativeMarker],
    Component: set[int],
    Vertices: set[int],
    HeaderLocus: str,
) -> int | None:
    OwnedEdges = {Edges[Index].offset for Index in Component}
    FirstIndex = next(
        Index for Index, Marker in enumerate(Markers) if Marker.offset in OwnedEdges
    )
    if FirstIndex == 0:
        return None
    Header = Markers[FirstIndex - 1]
    EdgeRun = Markers[FirstIndex : FirstIndex + len(Component)]
    Endpoints = frozenset(Header.endpoint_indices or ())
    EdgeEndpoints = {frozenset(Marker.endpoint_indices or ()) for Marker in EdgeRun}
    if (
        {Marker.offset for Marker in EdgeRun} == OwnedEdges
        and Header.prefix == EdgeRun[0].prefix
        and Header.locus == HeaderLocus
        and Header.semantic == "native"
        and Header.profile_role == 1
        and Header.native_kind == 0
        and Header.object_index is None
        and Header.coordinates_mm is None
        and Header.length == 92
        and len(Endpoints) == 2
        and Endpoints <= Vertices
        and Endpoints not in EdgeEndpoints
    ):
        return Header.offset
    return None
