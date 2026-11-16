# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import dist as Distance, isclose as IsClose, pi as PiValue
from typing import TypedDict

from convert.adapters.solidworks.Config.OrdinaryMap import ReadOrdinaryMap
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Config.Regions import KRegionRow
from convert.adapters.solidworks.Container.Archive import ArchiveError
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.PlaneBasis import KSavedVector
from convert.adapters.solidworks.Resolved.Circular.Records import CircularBoss
from convert.adapters.solidworks.Sketch.CircularRecords import CircularMember
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
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.geometry.Models.Transform import KTransformIdentity
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch


# the raw shell retains the native owner and named body atom
class CircularAtom(TypedDict):
    native_shell: int
    native_owner: int
    native_region: int
    body_atom_id: int


# the bounded analytic geometry derives from the isolated closed cylinder
class CylinderData(TypedDict):
    face_count: int
    edge_count: int
    closed_edge_representative_vertices: int
    radius_m: float
    analytic_volume_m3: float
    cap_offsets_m: list[float]


# the checked body combines the raw shell and active stream provenance
class CircularShape(CircularAtom, CylinderData):
    config_region: KRegionRow
    stream: str
    payload_sha256: str
    schema: str


# the existing neutral brep decoder returns geometry in millimetres
def PointMetres(Value: SpaceVector) -> KSavedVector:
    return (Value.x / 1000, Value.y / 1000, Value.z / 1000)


# a cylinder and its cap circles may express the same axis with opposite orientation
def CheckParallel(Value: SpaceVector, AxisValue: KSavedVector) -> None:
    UnitVector = (Value.x, Value.y, Value.z)
    RequireArch(
        min(
            Distance(UnitVector, AxisValue),
            Distance(UnitVector, tuple(-Component for Component in AxisValue)),
        )
        <= KPlaneTolerance,
        True,
        "active circular surface or curve does not align with the boss axis",
    )


# the decoded body and raw face roster must identify the very same native shell atom
def ReadShellAtom(DataValue: bytes, Model: BrepModel) -> CircularAtom:
    Header = ParaHeaderData(DataValue)
    if Header is None:
        raise ArchiveError("unreadable active circular partition header")
    Inner = DataValue[Header.body_offset :]
    Tables = ScanPartRecords(Inner)
    if Tables is None:
        raise ArchiveError("unreadable active circular partition table")
    ShellIds = {FaceValue.references[3] for FaceValue in Tables.bridges.values()}
    RequireArch(len(ShellIds) == 1, True, "expected one raw circular partition shell")
    (Shell,) = ShellIds
    Owner, Region, Faces = ReadShellOwner(Inner, Tables.bridges, Shell)
    RequireArch(
        {NativeId("face", FaceValue) for FaceValue in Faces}
        == {FaceValue.id for FaceValue in Model.faces},
        True,
        "raw circular shell faces disagree with the decoded solid",
    )
    return {
        "native_shell": Shell,
        "native_owner": Owner,
        "native_region": Region,
        "body_atom_id": ReadOwnerAtoms(Inner, frozenset({Owner}))[Owner],
    }


# associate every circular edge with its planar cap and the same cylindrical side
def ReadLoopEdges(Model: BrepModel, CylinderId: str) -> dict[str, str]:
    Coedges = {UseValue.id: UseValue.edge_id for UseValue in Model.coedges}
    Loops = {
        LoopValue.id: tuple(Coedges[UseValue] for UseValue in LoopValue.coedge_ids)
        for LoopValue in Model.loops
    }
    Boundaries = {
        FaceValue.surface_id: [
            EdgeValue
            for LoopValue in FaceValue.loop_ids
            for EdgeValue in Loops[LoopValue]
        ]
        for FaceValue in Model.faces
    }
    Expected = {EdgeValue.id for EdgeValue in Model.edges}
    SideValue = Boundaries.pop(CylinderId)
    RequireArch(
        len(SideValue) == 2
        and set(SideValue) == Expected
        and all(len(CapValue) == 1 for CapValue in Boundaries.values())
        and {CapValue[0] for CapValue in Boundaries.values()} == Expected,
        True,
        "active cap loops do not share their two closed curves with the cylindrical side",
    )
    return {SurfaceId: CapValue[0] for SurfaceId, CapValue in Boundaries.items()}


# check that the measured active cylinder axis and cap edges remain on the reached design axis
def AxisOffset(
    Anchor: KSavedVector, Origin: KSavedVector, AxisValue: KSavedVector
) -> float:
    Offset = PointOffset(Anchor, Origin, AxisValue)
    Projected = tuple(
        Value + Offset * BaseValue
        for Value, BaseValue in zip(Origin, AxisValue, strict=True)
    )
    RequireArch(
        Distance(Anchor, Projected) <= KPlaneTolerance,
        True,
        "active circular axis departs from the saved sketch",
    )
    return Offset


# check analytic surfaces and full circular boundaries before deriving cylinder metrics
def CheckCylinder(
    Model: BrepModel, BossValue: CircularBoss, Radius: float
) -> CylinderData:
    RequireArch(
        len(Model.bodies) == len(Model.regions) == len(Model.shells) == 1
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
        set(FaceValue.surface_id for FaceValue in Model.faces)
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
            EdgeValue.start_vertex_id == EdgeValue.end_vertex_id
            and IsClose(
                EdgeValue.end_parameter - EdgeValue.start_parameter,
                2 * PiValue,
                rel_tol=0,
                abs_tol=KPlaneTolerance,
            )
            for EdgeValue in Model.edges
        )
        and {EdgeValue.curve_id for EdgeValue in Model.edges}
        == {Curve.id for Curve in Model.curves}
        and {EdgeValue.start_vertex_id for EdgeValue in Model.edges}
        == {Vertex.id for Vertex in Model.vertices},
        True,
        "active circular boundaries do not cover a full revolution",
    )
    (Cylinder,) = Cylinders
    Origin, AxisValue, Depth = (
        BossValue["start_center_m"],
        BossValue["axis"],
        BossValue["signed_depth_m"],
    )
    CheckParallel(Cylinder.axis, AxisValue)
    RequireArch(
        IsClose(Cylinder.radius / 1000, Radius, rel_tol=0, abs_tol=KPlaneTolerance),
        True,
        "active cylinder radius differs from the owned sketch",
    )
    _ = AxisOffset(PointMetres(Cylinder.origin), Origin, AxisValue)
    Boundaries = ReadLoopEdges(Model, Cylinder.id)
    CurvesById = {
        Curve.id: Curve for Curve in Model.curves if isinstance(Curve, CircleCurve)
    }
    CurvesByEdge = {
        EdgeValue.id: CurvesById[EdgeValue.curve_id] for EdgeValue in Model.edges
    }
    Offsets: list[float] = []
    for Plane in Planes:
        CheckParallel(Plane.normal, AxisValue)
        Offset = PointOffset(PointMetres(Plane.origin), Origin, AxisValue)
        Offsets.append(Offset)
        Curve = CurvesByEdge[Boundaries[Plane.id]]
        CheckParallel(Curve.axis, AxisValue)
        RequireArch(
            IsClose(Curve.radius / 1000, Radius, rel_tol=0, abs_tol=KPlaneTolerance)
            and IsClose(
                AxisOffset(PointMetres(Curve.center), Origin, AxisValue),
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


# join the active payload the configuration region and the resolved atom occurrence
def ReadRoundPart(
    Archive: SldprtArchive,
    ConfigStream: str,
    BossValue: CircularBoss,
    Circle: CircularMember,
) -> tuple[BrepModel, CircularShape]:
    Config, ConfigWalk = ReadOrdinaryMap(Archive.Require(ConfigStream), KConfigGen)
    Atoms = [
        Index for Index, ClassName in Config.Objects.items() if ClassName == "moAtom_c"
    ]
    Regions = [Record for Group in ConfigWalk["regions"] for Record in Group]
    RequireArch(
        Atoms == [BossValue["transfer_object"]]
        and len(Regions) == 1
        and Regions[0][0] == BossValue["saved_body_id"],
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
    if Model is None:
        raise ArchiveError(
            "active circular partition is not a single closed analytic solid"
        )
    Geometry = CheckCylinder(Model, BossValue, Circle["radial_metres"])
    Identity = ReadShellAtom(Payload.data, Model)
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
