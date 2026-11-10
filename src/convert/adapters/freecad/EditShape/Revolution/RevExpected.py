# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from dataclasses import dataclass as MakeDataClass

from convert.adapters.freecad.EditShape.Revolution.RevCarriers import (
    KRevCurve,
    KRevSurface,
)
from convert.geometry.Opencascade import DecodeFailure
from interchange.brep.curves.BrepCurves import CircleCurve, LineCurve
from interchange.brep.surfaces.BrepSurfaces import (
    ConeSurface,
    CylinderSurface,
    PlaneSurface,
)
from interchange.brep.topology.BrepModel import BrepModel
from interchange.brep.topology.BrepTopology import BrepEdge
from interchange.geometry.models.VectorSpace import SpaceVector

# oriented edge keys preserve model winding after arbitrary native identifier assignment
KFaceLoop = tuple[tuple[str, int], ...]


# reconstructed analytic boundaries provide immutable geometry and topology witnesses
@MakeDataClass(frozen=True, slots=True)
class RevFace:
    Surface: KRevSurface
    Sense: int
    Loops: tuple[KFaceLoop, ...]


# native topology is compared against one independently reconstructed solid
@MakeDataClass(frozen=True, slots=True)
class RevExpected:
    Points: dict[str, SpaceVector]
    Edges: dict[str, BrepEdge]
    Curves: dict[str, KRevCurve]
    Faces: tuple[RevFace, ...]
    IsFull: bool


# a native wire can start at any edge without changing its directed boundary
def LoopKey(LoopValue: KFaceLoop) -> KFaceLoop:
    Start = LoopValue.index(min(LoopValue))
    return LoopValue[Start:] + LoopValue[:Start]


# native and neutral faces must have the same effective oriented boundary rings
def ReadWantFaces(
    Expected: BrepModel, FaceSenses: dict[str, int]
) -> tuple[RevFace, ...]:
    Surfaces = {Value.id: Value for Value in Expected.surfaces}
    Loops = {Value.id: Value for Value in Expected.loops}
    Coedges = {Value.id: Value for Value in Expected.coedges}
    Faces: list[RevFace] = []
    for FaceValue in Expected.faces:
        Surface = Surfaces[FaceValue.surface_id]
        if not isinstance(Surface, (PlaneSurface, CylinderSurface, ConeSurface)):
            raise DecodeFailure("unsupported expected Revolution surface")
        UseSense = FaceSenses[FaceValue.id]
        Sense = UseSense if FaceValue.same_sense else -UseSense
        Rings: list[KFaceLoop] = []
        for LoopId in FaceValue.loop_ids:
            UsesValue = tuple(Coedges[Index] for Index in Loops[LoopId].coedge_ids)
            RingValue = tuple(
                (Value.edge_id, -1 if Value.reversed else 1) for Value in UsesValue
            )
            if UseSense < 0:
                RingValue = tuple(
                    (Index, -SenseValue) for Index, SenseValue in reversed(RingValue)
                )
            Rings.append(LoopKey(RingValue))
        Faces.append(RevFace(Surface, Sense, tuple(sorted(Rings))))
    return tuple(Faces)


# the model witness is confined to one simple bounded positive radius sweep
def ReadRevExpected(Expected: BrepModel) -> RevExpected:
    if (
        len(Expected.bodies) != 1
        or len(Expected.regions) != 1
        or len(Expected.shells) != 1
        or len(Expected.shell_uses) != 1
        or not Expected.regions[0].solid
        or not Expected.shells[0].closed
        or Expected.wires
        or not 3 <= len(Expected.faces) <= 66
        or not 3 <= len(Expected.edges) <= 192
        or any(Value.degenerate for Value in Expected.edges)
    ):
        raise DecodeFailure("unsupported expected Revolution solid")
    Edges = {Value.id: Value for Value in Expected.edges}
    Curves = {
        Value.id: Value
        for Value in Expected.curves
        if isinstance(Value, (CircleCurve, LineCurve))
    }
    if len(Curves) != len(Expected.curves):
        raise DecodeFailure("unsupported expected Revolution curve")
    IsFull = all(
        isinstance(Curves[Value.curve_id], CircleCurve) for Value in Edges.values()
    )
    ShellSense = -1 if Expected.shell_uses[0].reversed else 1
    FaceSenses = {
        Value.face_id: -ShellSense if Value.reversed else ShellSense
        for Value in Expected.face_uses
    }
    return RevExpected(
        {Value.id: Value.point for Value in Expected.vertices},
        Edges,
        Curves,
        ReadWantFaces(Expected, FaceSenses),
        IsFull,
    )
