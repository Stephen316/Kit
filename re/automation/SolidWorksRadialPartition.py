# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Check the active cylindrical solid against the resolved boss and licensed measurements."""

from math import dist, isclose, pi, sqrt

from PairedCaptureIntake import require
from convert.adapters.solidworks.Config.OrdinaryMap import ReadOrdinaryMap
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Parasolid import DecodeBrep, DecodePartition
from convert.adapters.solidworks.Core.Partition.PartAtomOwner import ReadOwnerAtoms
from convert.adapters.solidworks.Core.Partition.PartShellOwner import ReadShellOwner
from convert.adapters.solidworks.Resolved.Scope.Distance import (
    KPlaneTolerance,
    PointOffset,
)
from convert.Geometry.Parasolid import NativeId, ParaHeaderData, ScanPartRecords
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface


# The existing neutral BRep decoder returns geometry in millimetres.
def point_metres(value):
    return (value.x / 1000, value.y / 1000, value.z / 1000)


# A cylinder and its cap circles may express the same axis with opposite orientation.
def check_parallel(value, axis):
    unit = (value.x, value.y, value.z)
    require(
        min(dist(unit, axis), dist(unit, tuple(-component for component in axis)))
        <= KPlaneTolerance,
        "active circular surface or curve does not align with the boss axis",
    )


# The decoded body and raw face roster must identify the very same native shell atom.
def read_partition_atom(data, model):
    header = ParaHeaderData(data)
    require(header is not None, "unreadable active circular partition header")
    inner = data[header.body_offset :]
    tables = ScanPartRecords(inner)
    require(tables is not None, "unreadable active circular partition table")
    shell_ids = {face.references[3] for face in tables.bridges.values()}
    require(len(shell_ids) == 1, "expected one raw circular partition shell")
    (shell,) = shell_ids
    owner, region, faces = ReadShellOwner(inner, tables.bridges, shell)
    require(
        {NativeId("face", face) for face in faces} == {face.id for face in model.faces},
        "raw circular shell faces disagree with the decoded solid",
    )
    return {
        "native_shell": shell,
        "native_owner": owner,
        "native_region": region,
        "body_atom_id": ReadOwnerAtoms(inner, frozenset({owner}))[owner],
    }


# Associate every circular edge with its planar cap and the same cylindrical side.
def read_boundary_uses(model, cylinder_id):
    coedges = {use.id: use.edge_id for use in model.coedges}
    loops = {
        loop.id: tuple(coedges[use] for use in loop.coedge_ids) for loop in model.loops
    }
    boundaries = {
        face.surface_id: [edge for loop in face.loop_ids for edge in loops[loop]]
        for face in model.faces
    }
    expected = {edge.id for edge in model.edges}
    side = boundaries.pop(cylinder_id)
    require(
        len(side) == 2
        and set(side) == expected
        and all(len(cap) == 1 for cap in boundaries.values())
        and {cap[0] for cap in boundaries.values()} == expected,
        "active cap loops do not share their two closed curves with the cylindrical side",
    )
    return {surface_id: cap[0] for surface_id, cap in boundaries.items()}


# Check that the measured active cylinder axis and cap edges remain on the reached design axis.
def axis_offset(anchor, origin, axis):
    offset = PointOffset(anchor, origin, axis)
    projected = tuple(
        value + offset * base for value, base in zip(origin, axis, strict=True)
    )
    require(
        dist(anchor, projected) <= KPlaneTolerance,
        "active circular axis departs from the saved sketch",
    )
    return offset


# Check analytic surfaces and full circular boundaries before deriving cylinder metrics.
def check_cylinder(model, boss, radius):
    require(
        model is not None
        and len(model.bodies) == len(model.regions) == len(model.shells) == 1
        and model.regions[0].solid
        and model.shells[0].closed
        and len(model.faces) == len(model.surfaces) == 3
        and len(model.edges) == len(model.curves) == 2
        and len(model.vertices) == len(model.edges)
        and not model.wires
        and not model.validate(frozenset()),
        "active circular partition is not a single closed analytic solid",
    )
    require(
        set(face.surface_id for face in model.faces)
        == set(surface.id for surface in model.surfaces)
        and all(isinstance(curve, CircleCurve) for curve in model.curves),
        "active circular faces or closed edge curves do not cover the solid",
    )
    cylinders = [
        surface for surface in model.surfaces if isinstance(surface, CylinderSurface)
    ]
    planes = [
        surface for surface in model.surfaces if isinstance(surface, PlaneSurface)
    ]
    require(
        len(cylinders) == 1 and len(planes) == 2,
        "expected one cylinder and two planar caps",
    )
    require(
        all(
            edge.start_vertex_id == edge.end_vertex_id
            and isclose(
                edge.end_parameter - edge.start_parameter,
                2 * pi,
                rel_tol=0,
                abs_tol=KPlaneTolerance,
            )
            for edge in model.edges
        )
        and {edge.curve_id for edge in model.edges}
        == {curve.id for curve in model.curves}
        and {edge.start_vertex_id for edge in model.edges}
        == {vertex.id for vertex in model.vertices},
        "active circular boundaries do not cover a full revolution",
    )
    (cylinder,) = cylinders
    origin, axis, depth = boss["start_center_m"], boss["axis"], boss["signed_depth_m"]
    check_parallel(cylinder.axis, axis)
    require(
        isclose(cylinder.radius / 1000, radius, rel_tol=0, abs_tol=KPlaneTolerance),
        "active cylinder radius differs from the owned sketch",
    )
    axis_offset(point_metres(cylinder.origin), origin, axis)
    boundaries = read_boundary_uses(model, cylinder.id)
    curves_by_id = {curve.id: curve for curve in model.curves}
    curves_by_edge = {edge.id: curves_by_id[edge.curve_id] for edge in model.edges}
    offsets = []
    for plane in planes:
        check_parallel(plane.normal, axis)
        offset = PointOffset(point_metres(plane.origin), origin, axis)
        offsets.append(offset)
        curve = curves_by_edge[boundaries[plane.id]]
        check_parallel(curve.axis, axis)
        require(
            isclose(curve.radius / 1000, radius, rel_tol=0, abs_tol=KPlaneTolerance)
            and isclose(
                axis_offset(point_metres(curve.center), origin, axis),
                offset,
                rel_tol=0,
                abs_tol=KPlaneTolerance,
            ),
            "active circular edge disagrees with the radius or cap plane",
        )
    require(
        dist(sorted(offsets), (0, depth)) <= KPlaneTolerance,
        "active cap planes disagree with the boss extent",
    )
    return {
        "face_count": len(model.faces),
        "edge_count": len(model.edges),
        "closed_edge_representative_vertices": len(model.vertices),
        "radius_m": radius,
        "analytic_volume_m3": pi * radius**2 * depth,
        "cap_offsets_m": sorted(offsets),
    }


# Join the active payload, the configuration region and the resolved atom occurrence.
def read_boss_partition(archive, config_stream, boss, circle):
    config, walk = ReadOrdinaryMap(archive.require(config_stream), KConfigGen)
    atoms = [index for index, kind in config.Objects.items() if kind == "moAtom_c"]
    regions = [row for group in walk["regions"] for row in group]
    require(
        atoms == [boss["transfer_object"]]
        and len(regions) == 1
        and regions[0][0] == boss["saved_body_id"],
        "circular boss transfer or saved body does not match the active configuration",
    )
    stream = f"{config_stream}-Partition"
    sources = [
        value
        for value in DecodePartition(archive.require(stream), stream)
        if value.kind == "partition"
    ]
    require(len(sources) == 1, "expected one active circular partition payload")
    (payload,) = sources
    model = DecodeBrep(payload.data)
    geometry = check_cylinder(model, boss, circle["radial_metres"])
    identity = read_partition_atom(payload.data, model)
    require(
        identity["body_atom_id"] == regions[0][0],
        "active cylindrical shell atom disagrees with the configuration",
    )
    return {
        **identity,
        **geometry,
        "config_region": regions[0],
        "stream": stream,
        "payload_sha256": payload.sha256,
        "schema": payload.schema,
    }


# Compare analytic cylinder metrics with the independent licensed native body measurements.
def check_licensed_body(archive_body, boss, native):
    radius, depth = archive_body["radius_m"], boss["signed_depth_m"]
    origin, axis = boss["start_center_m"], boss["axis"]
    extents = tuple(radius * sqrt(max(0.0, 1 - direction**2)) for direction in axis)
    tip = tuple(
        value + depth * direction for value, direction in zip(origin, axis, strict=True)
    )
    lower = tuple(
        min(start, end) - extent
        for start, end, extent in zip(origin, tip, extents, strict=True)
    )
    upper = tuple(
        max(start, end) + extent
        for start, end, extent in zip(origin, tip, extents, strict=True)
    )
    require(
        native["solid_body_count"] == 1
        and all(
            native[key] == archive_body[key] for key in ("face_count", "edge_count")
        )
        and native["vertex_count"] == 0
        and dist(native["bounds_min_m"], lower) <= KPlaneTolerance
        and dist(native["bounds_max_m"], upper) <= KPlaneTolerance
        and dist(native["center_of_mass_m"], boss["centroid_m"]) <= KPlaneTolerance
        and isclose(
            native["volume_m3"], archive_body["analytic_volume_m3"], rel_tol=1e-8
        ),
        "licensed cylinder measures disagree with the owned active partition",
    )
