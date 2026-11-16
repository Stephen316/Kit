# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import dist as Distance, isclose as IsClose, pi as PiValue

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
from interchange.geometry.Models.Transform import KTransformIdentity
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch


# The existing neutral BRep decoder returns geometry in millimetres.
def PointMetres(Value):
    return (Value.x / 1000, Value.y / 1000, Value.z / 1000)


# A cylinder and its cap circles may express the same axis with opposite orientation.
def CheckParallel(Value, Axis):
    Unit = (Value.x, Value.y, Value.z)
    RequireArch(
        min(
            Distance(Unit, Axis),
            Distance(Unit, tuple(-Component for Component in Axis)),
        )
        <= KPlaneTolerance,
        True,
        "active circular surface or curve does not align with the boss axis",
    )


# The decoded body and raw face roster must identify the very same native shell atom.
def ReadPartitionAtom(DataValue, Model):
    Header = ParaHeaderData(DataValue)
    RequireArch(Header is not None, True, "unreadable active circular partition header")
    Inner = DataValue[Header.body_offset :]
    Tables = ScanPartRecords(Inner)
    RequireArch(Tables is not None, True, "unreadable active circular partition table")
    ShellIds = {Face.references[3] for Face in Tables.bridges.values()}
    RequireArch(len(ShellIds) == 1, True, "expected one raw circular partition shell")
    (Shell,) = ShellIds
    Owner, Region, Faces = ReadShellOwner(Inner, Tables.bridges, Shell)
    RequireArch(
        {NativeId("face", Face) for Face in Faces} == {Face.id for Face in Model.faces},
        True,
        "raw circular shell faces disagree with the decoded solid",
    )
    return {
        "native_shell": Shell,
        "native_owner": Owner,
        "native_region": Region,
        "body_atom_id": ReadOwnerAtoms(Inner, frozenset({Owner}))[Owner],
    }


# Associate every circular edge with its planar cap and the same cylindrical side.
def ReadBoundaryUses(Model, CylinderId):
    Coedges = {Use.id: Use.edge_id for Use in Model.coedges}
    Loops = {
        Loop.id: tuple(Coedges[Use] for Use in Loop.coedge_ids) for Loop in Model.loops
    }
    Boundaries = {
        Face.surface_id: [Edge for Loop in Face.loop_ids for Edge in Loops[Loop]]
        for Face in Model.faces
    }
    Expected = {Edge.id for Edge in Model.edges}
    Side = Boundaries.pop(CylinderId)
    RequireArch(
        len(Side) == 2
        and set(Side) == Expected
        and all(len(Cap) == 1 for Cap in Boundaries.values())
        and {Cap[0] for Cap in Boundaries.values()} == Expected,
        True,
        "active cap loops do not share their two closed curves with the cylindrical side",
    )
    return {SurfaceId: Cap[0] for SurfaceId, Cap in Boundaries.items()}


# Check that the measured active cylinder axis and cap edges remain on the reached design axis.
def AxisOffset(Anchor, Origin, Axis):
    Offset = PointOffset(Anchor, Origin, Axis)
    Projected = tuple(
        Value + Offset * Base for Value, Base in zip(Origin, Axis, strict=True)
    )
    RequireArch(
        Distance(Anchor, Projected) <= KPlaneTolerance,
        True,
        "active circular axis departs from the saved sketch",
    )
    return Offset


# Check analytic surfaces and full circular boundaries before deriving cylinder metrics.
def CheckCylinder(Model, Boss, Radius):
    RequireArch(
        Model is not None
        and len(Model.bodies) == len(Model.regions) == len(Model.shells) == 1
        and Model.regions[0].solid
        and Model.shells[0].closed
        and len(Model.faces) == len(Model.surfaces) == 3
        and len(Model.edges) == len(Model.curves) == 2
        and len(Model.vertices) == len(Model.edges)
        and not Model.wires
        and not Model.validate(frozenset()),
        True,
        "active circular partition is not a single closed analytic solid",
    )
    (Carrier,) = Model.bodies
    (Region,) = Model.regions
    RequireArch(
        (Carrier.region_ids, Carrier.transform, Carrier.wire_ids, Carrier.vertex_ids),
        ((Region.id,), KTransformIdentity, (), ()),
        "active circular carrier owns exactly the saved solid",
    )
    RequireArch(
        set(Face.surface_id for Face in Model.faces)
        == set(Surface.id for Surface in Model.surfaces)
        and all(isinstance(Curve, CircleCurve) for Curve in Model.curves),
        True,
        "active circular faces or closed edge curves do not cover the solid",
    )
    Cylinders = [
        Surface for Surface in Model.surfaces if isinstance(Surface, CylinderSurface)
    ]
    Planes = [
        Surface for Surface in Model.surfaces if isinstance(Surface, PlaneSurface)
    ]
    RequireArch(
        len(Cylinders) == 1 and len(Planes) == 2,
        True,
        "expected one cylinder and two planar caps",
    )
    RequireArch(
        all(
            Edge.start_vertex_id == Edge.end_vertex_id
            and IsClose(
                Edge.end_parameter - Edge.start_parameter,
                2 * PiValue,
                rel_tol=0,
                abs_tol=KPlaneTolerance,
            )
            for Edge in Model.edges
        )
        and {Edge.curve_id for Edge in Model.edges}
        == {Curve.id for Curve in Model.curves}
        and {Edge.start_vertex_id for Edge in Model.edges}
        == {Vertex.id for Vertex in Model.vertices},
        True,
        "active circular boundaries do not cover a full revolution",
    )
    (Cylinder,) = Cylinders
    Origin, Axis, Depth = Boss["start_center_m"], Boss["axis"], Boss["signed_depth_m"]
    CheckParallel(Cylinder.axis, Axis)
    RequireArch(
        IsClose(Cylinder.radius / 1000, Radius, rel_tol=0, abs_tol=KPlaneTolerance),
        True,
        "active cylinder radius differs from the owned sketch",
    )
    AxisOffset(PointMetres(Cylinder.origin), Origin, Axis)
    Boundaries = ReadBoundaryUses(Model, Cylinder.id)
    CurvesById = {Curve.id: Curve for Curve in Model.curves}
    CurvesByEdge = {Edge.id: CurvesById[Edge.curve_id] for Edge in Model.edges}
    Offsets = []
    for Plane in Planes:
        CheckParallel(Plane.normal, Axis)
        Offset = PointOffset(PointMetres(Plane.origin), Origin, Axis)
        Offsets.append(Offset)
        Curve = CurvesByEdge[Boundaries[Plane.id]]
        CheckParallel(Curve.axis, Axis)
        RequireArch(
            IsClose(Curve.radius / 1000, Radius, rel_tol=0, abs_tol=KPlaneTolerance)
            and IsClose(
                AxisOffset(PointMetres(Curve.center), Origin, Axis),
                Offset,
                rel_tol=0,
                abs_tol=KPlaneTolerance,
            ),
            True,
            "active circular edge disagrees with the radius or cap plane",
        )
    RequireArch(
        Distance(sorted(Offsets), (0, Depth)) <= KPlaneTolerance,
        True,
        "active cap planes disagree with the boss extent",
    )
    return {
        "face_count": len(Model.faces),
        "edge_count": len(Model.edges),
        "closed_edge_representative_vertices": len(Model.vertices),
        "radius_m": Radius,
        "analytic_volume_m3": PiValue * Radius**2 * Depth,
        "cap_offsets_m": sorted(Offsets),
    }


# Join the active payload, the configuration region and the resolved atom occurrence.
def ReadCircularPartition(Archive, ConfigStream, Boss, Circle):
    Config, Walk = ReadOrdinaryMap(Archive.Require(ConfigStream), KConfigGen)
    Atoms = [Index for Index, Kind in Config.Objects.items() if Kind == "moAtom_c"]
    Regions = [Row for Group in Walk["regions"] for Row in Group]
    RequireArch(
        Atoms == [Boss["transfer_object"]]
        and len(Regions) == 1
        and Regions[0][0] == Boss["saved_body_id"],
        True,
        "circular boss transfer or saved body does not match the active configuration",
    )
    Stream = f"{ConfigStream}-Partition"
    Sources = [
        Value
        for Value in DecodePartition(Archive.Require(Stream), Stream)
        if Value.kind == "partition"
    ]
    RequireArch(
        len(Sources) == 1, True, "expected one active circular partition payload"
    )
    (Payload,) = Sources
    Model = DecodeBrep(Payload.data)
    Geometry = CheckCylinder(Model, Boss, Circle["radial_metres"])
    Identity = ReadPartitionAtom(Payload.data, Model)
    RequireArch(
        Identity["body_atom_id"] == Regions[0][0],
        True,
        "active cylindrical shell atom disagrees with the configuration",
    )
    return Model, {
        **Identity,
        **Geometry,
        "config_region": Regions[0],
        "stream": Stream,
        "payload_sha256": Payload.sha256,
        "schema": Payload.schema,
    }
