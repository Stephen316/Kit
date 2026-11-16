from dataclasses import dataclass as Dataclass
from math import isclose as IsClose, isfinite as IsFinite

from BossProfile import KSlots, LocalProfile
from RectangleDims import KDrivingNames
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.DistanceParam import KLengthFactors
from interchange.geometry.Models.Sketch import Sketch, SketchRelation
from interchange.Records.RecordParameter import Parameter

KEndpoint = tuple[str, str]
KDirections = ("horizontal", "vertical")
KDistances = ("distance", "distance_x", "distance_y")


# preserve the portable value and identity before a target dimension ID is allocated
@Dataclass(frozen=True, slots=True)
class DrivingLength:
    ParameterId: str
    Name: str
    FeatureId: str
    Millimetres: float


# the target uses anchor-first slots while retaining the actual dimension relation ID
@Dataclass(frozen=True, slots=True)
class BoundSize:
    Length: DrivingLength
    RelationId: str
    PointSlots: KSlots


def ReadDrivingLength(ParameterValue: Parameter, FeatureId: str) -> DrivingLength:
    Value = ParameterValue.value
    RequireArch(
        ParameterValue.role == ParameterRole.KDriving
        and ParameterValue.owner_id == FeatureId
        and ParameterValue.expression is None
        and bool(ParameterValue.name)
        and "\0" not in ParameterValue.name
        and Value.kind == ValueKind.KLength
        and Value.unit in ("mm", "cm")
        and type(Value.value) in (int, float),
        True,
        f"{ParameterValue.id} must be an independent owner-bound length",
    )
    Millimetres = float(Value.value) * KLengthFactors[Value.unit]
    RequireArch(
        IsFinite(Millimetres), True, f"{ParameterValue.id} finite system length"
    )
    return DrivingLength(ParameterValue.id, ParameterValue.name, FeatureId, Millimetres)


def Endpoints(Relation: SketchRelation) -> tuple[KEndpoint, ...]:
    return tuple((Ref.entity_id, Ref.point) for Ref in Relation.references)


# explicit endpoint coincidences can become shared target corner slots
def CheckCoincidences(
    Rows: list[SketchRelation], Profile: LocalProfile, Source: dict[KEndpoint, int]
) -> None:
    Corners = {
        frozenset(Ref for Ref, Index in Source.items() if Index == Slot)
        for Slot in range(4)
    }
    Seen = set()
    Anchors = 0
    for Relation in Rows:
        Ends = Endpoints(Relation)
        RequireArch(len(Ends), 2, f"{Relation.id} has two coincidence operands")
        RequireArch(Relation.parameter_id, None, f"{Relation.id} has no value binding")
        if any(Name == Profile.OriginId for Name, _ in Ends):
            Fixed = [Ref for Ref in Ends if Ref[0] == Profile.OriginId]
            Perimeter = [Ref for Ref in Ends if Ref[0] != Profile.OriginId]
            RequireArch(
                len(Fixed) == len(Perimeter) == 1
                and Fixed[0][1] in ("", "start")
                and Source.get(Perimeter[0]) == 0,
                True,
                f"{Relation.id} connects the corner to the distinct fixed origin",
            )
            Anchors += 1
        else:
            Seen.add(frozenset(Ends))
    RequireArch(
        len(Rows) == 5 and Anchors == 1 and Seen == Corners,
        True,
        "four endpoint coincidences and one distinct origin anchor",
    )


# use the actual selected sides and dimension operands, never the parameter value alone
def ReadSize(
    Relation: SketchRelation,
    Profile: LocalProfile,
    Source: dict[KEndpoint, int],
    Parameters: dict[str, Parameter],
    Owner: str,
) -> BoundSize:
    ParameterValue = Parameters.get(Relation.parameter_id or "")
    if ParameterValue is None:
        raise ValueError(f"{Relation.id} has no owned size parameter")
    Length = ReadDrivingLength(ParameterValue, Owner)
    RequireArch(Length.Name in KDrivingNames, True, f"{Relation.id} size role")
    IsX = (Length.Name == KDrivingNames[0]) == (Profile.AxisCode == 3)
    Slots = (0, 3) if IsX else (0, 2)
    Actual = tuple(Source.get(End) for End in Endpoints(Relation))
    RequireArch(
        len(Actual) == 2
        and set(Actual) == set(Slots)
        and Relation.kind in ("distance", "distance_x" if IsX else "distance_y"),
        True,
        f"{Relation.id} must measure its actual anchored side",
    )
    Extent = abs(Profile.CornersMm[Slots[1]][0 if IsX else 1])
    RequireArch(
        Length.Millimetres > 0
        and IsClose(Length.Millimetres, Extent, rel_tol=0, abs_tol=1e-12),
        True,
        f"{Relation.id} value differs from its measured local side",
    )
    return BoundSize(Length, Relation.id, Slots)


# the ordinal target axes are checked against the independent explicit source relations
def ReadRectRules(
    SketchValue: Sketch,
    Profile: LocalProfile,
    Parameters: dict[str, Parameter],
    Owner: str,
) -> tuple[BoundSize, BoundSize]:
    Source = {
        (Edge.SourceId, Side): Slot
        for Edge in Profile.Edges
        for Side, Slot in zip(("start", "end"), Edge.SourceSlots, strict=True)
    }
    Rows: dict[str, list[SketchRelation]] = {}
    Ids: set[str] = set()
    for Relation in SketchValue.constraints:
        RequireArch(
            not Relation.suppressed
            and Relation.driving
            and Relation.id not in Ids
            and Relation.kind in (*KDirections, *KDistances, "coincident"),
            True,
            f"{Relation.id} is outside the solved rectangle rules",
        )
        Ids.add(Relation.id)
        Rows.setdefault(Relation.kind, []).append(Relation)
    AxisRows = [Row for Kind in KDirections for Row in Rows.get(Kind, ())]
    Expected = {
        ((Edge.SourceId, ""),): "horizontal" if Edge.Identity in (1, 3) else "vertical"
        for Edge in Profile.Edges
    }
    RequireArch(
        len(AxisRows) == 4
        and {Endpoints(Row): Row.kind for Row in AxisRows} == Expected
        and all(Row.parameter_id is None for Row in AxisRows),
        True,
        "one correct axis rule for every perimeter line",
    )
    CheckCoincidences(Rows.get("coincident", []), Profile, Source)
    Dims = [
        ReadSize(Row, Profile, Source, Parameters, Owner)
        for Kind in KDistances
        for Row in Rows.get(Kind, ())
    ]
    RequireArch(len(Dims), 2, "both independent rectangle size relations")
    ByRole = {Dim.Length.Name: Dim for Dim in Dims}
    RequireArch(set(ByRole), set(KDrivingNames), "unique width and height roles")
    Width, Height = (ByRole[Name] for Name in KDrivingNames)
    RequireArch(
        not IsClose(
            Width.Length.Millimetres,
            Height.Length.Millimetres,
            rel_tol=0,
            abs_tol=1e-12,
        )
        and len(SketchValue.parameter_ids) == 2
        and set(SketchValue.parameter_ids)
        == {Width.Length.ParameterId, Height.Length.ParameterId},
        True,
        "distinct supported side lengths and exclusively owned sketch parameters",
    )
    return Width, Height
