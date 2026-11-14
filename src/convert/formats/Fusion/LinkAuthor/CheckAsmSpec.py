from dataclasses import replace as Replace
from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.LinkAuthor.Building.LinkTables import UrnVersion
from convert.formats.Fusion.LinkAuthor.MatrixMath import CheckMatrix
from convert.formats.Fusion.LinkAuthor.Model.AssemblySpec import AssemblySpec
from convert.formats.Fusion.LinkAuthor.Model.LinkTarget import LinkTarget
from convert.formats.Fusion.LinkAuthor.Model.PlacedPart import PlacedPart
from convert.formats.Fusion.LinkAuthor.Model.RigidJoint import RigidJoint
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaCtx import CheckCtxUrn

KMaxTargets = 64

KMaxNameText = 200

KMaxPathText = 1024

KBadNameText = frozenset('/\\:*?"<>|')


def IsPlainName(TextValue: object, Limit: int) -> bool:
    return (
        type(TextValue) is str
        and 0 < len(TextValue) <= Limit
        and TextValue.isprintable()
        and TextValue == TextValue.strip()
        and not KBadNameText.intersection(TextValue)
    )


def CheckTarget(Value: object) -> LinkTarget:
    if not isinstance(Value, LinkTarget):
        raise ValueError("Fusion assembly target must be a link target")
    Target = Value
    if not IsPlainName(Target.DisplayName, KMaxNameText) or not isinstance(
        CastValue(object, Target.Target), DocumentModel
    ):
        raise ValueError("Fusion assembly target needs a plain name and a document")
    _ = CheckCtxUrn(Target.LineageUrn)
    _ = UrnVersion(CheckCtxUrn(Target.VersionUrn))
    return Target


def CheckPlacement(Value: object, Targets: int) -> PlacedPart:
    if not isinstance(Value, PlacedPart):
        raise ValueError("Fusion assembly placement must be a placed part")
    Placement = Value
    if (
        type(Placement.TargetIndex) is not int
        or not 0 <= Placement.TargetIndex < Targets
        or type(Placement.Grounded) is not bool
    ):
        raise ValueError(
            "Fusion assembly placement has an invalid target or ground flag"
        )
    return Replace(Placement, Matrix=CheckMatrix(Placement.Matrix))


def CheckJoint(Value: object, Placements: int) -> RigidJoint | None:
    if Value is None:
        return None
    if not isinstance(Value, RigidJoint):
        raise ValueError("Fusion assembly joint must be a rigid joint")
    Joint = Value
    Indices = (Joint.FirstIndex, Joint.SecondIndex)
    if any(
        type(Index) is not int or not 0 <= Index < Placements for Index in Indices
    ) or (Joint.FirstIndex == Joint.SecondIndex):
        raise ValueError("Fusion assembly joint needs two distinct placements")
    return Joint


def CheckAsmSpec(Value: object) -> AssemblySpec:
    if not isinstance(Value, AssemblySpec):
        raise ValueError("Fusion assembly authoring needs an assembly spec")
    Request = Value
    if (
        not isinstance(CastValue(object, Request.Base), DocumentSpec)
        or Request.Base.ProfileKind != "parameter"
        or type(Request.SourcePath) is not str
        or not IsPlainName(Request.SourcePath.replace("/", "_"), KMaxPathText)
    ):
        raise ValueError("Fusion assembly base must be a parameter document")
    if (
        type(Request.Targets) is not tuple
        or not 0 < len(Request.Targets) <= KMaxTargets
    ):
        raise ValueError("Fusion assembly needs between one and 64 targets")
    Targets = tuple(CheckTarget(Target) for Target in Request.Targets)
    if len({Target.Target.Asset.AssetId for Target in Targets}) != len(Targets):
        raise ValueError("Fusion assembly targets must be distinct documents")
    if type(Request.Placements) is not tuple:
        raise ValueError("Fusion assembly placements must be a tuple")
    Placements = tuple(
        CheckPlacement(Entry, len(Targets)) for Entry in Request.Placements
    )
    if sorted(Entry.TargetIndex for Entry in Placements) != list(range(len(Targets))):
        raise ValueError("Fusion assembly must place each target exactly once")
    return Replace(
        Request,
        Targets=Targets,
        Placements=Placements,
        Joint=CheckJoint(Request.Joint, len(Placements)),
    )
