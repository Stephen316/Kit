from dataclasses import replace

from BossInput import ProjectBoss
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import LineGeometry, PointGeometry
from interchange.geometry.Models.Sketch import (
    ConstraintRef,
    Sketch,
    SketchEntity,
    SketchRelation,
)
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Expression, Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource


# construct a fresh neutral example using independent authored dimensions and arbitrary IDs
def authored_case(right: bool, width: float, height: float, depth: float) -> CadDocument:
    x, y = (-height, width) if right else (width, height)
    origin, bottom, far, left = (
        PlaneVector(0.0, 0.0),
        PlaneVector(x, 0.0),
        PlaneVector(x, y),
        PlaneVector(0.0, y),
    )
    lines = (
        SketchEntity("pine", "line", LineGeometry(origin, bottom)),
        SketchEntity("elm", "line", LineGeometry(far, bottom)),
        SketchEntity("oak", "line", LineGeometry(left, far)),
        SketchEntity("ash", "line", LineGeometry(origin, left)),
        SketchEntity(
            "datum-point", "point", PointGeometry(origin), construction=True, fixed=True
        ),
    )
    axes = tuple(
        SketchRelation(f"axis-{identity}", kind, (ConstraintRef(identity),))
        for identity, kind in (
            ("pine", "horizontal"),
            ("elm", "vertical"),
            ("oak", "horizontal"),
            ("ash", "vertical"),
        )
    )
    coincident = tuple(
        SketchRelation(
            f"join-{slot}",
            "coincident",
            tuple(ConstraintRef(*operand) for operand in pair),
        )
        for slot, pair in enumerate(
            (
                (("pine", "start"), ("ash", "start")),
                (("pine", "end"), ("elm", "end")),
                (("elm", "start"), ("oak", "end")),
                (("oak", "start"), ("ash", "end")),
                (("datum-point", ""), ("pine", "start")),
            )
        )
    )
    width_edge, height_edge = ("ash", "pine") if right else ("pine", "ash")
    dims = (
        SketchRelation(
            "size-width",
            "distance_y" if right else "distance_x",
            (ConstraintRef(width_edge, "end"), ConstraintRef(width_edge, "start")),
            "W",
        ),
        SketchRelation(
            "size-height",
            "distance",
            (ConstraintRef(height_edge, "start"), ConstraintRef(height_edge, "end")),
            "H",
        ),
    )
    frame = (
        Transform(
            SpaceVector(0, 0, 0),
            SpaceVector(0, 0, -1),
            SpaceVector(0, 1, 0),
            SpaceVector(1, 0, 0),
        )
        if right
        else Transform()
    )
    return CadDocument(
        source=CadSource("kit.neutral", "", ""),
        configurations=(Configuration("main", "Default", active=True),),
        parameters=(
            Parameter(
                "W",
                "width_mm",
                ParameterValue(width, ValueKind.LENGTH, "mm"),
                owner_id="profile",
            ),
            Parameter(
                "H",
                "height_mm",
                ParameterValue(height, ValueKind.LENGTH, "mm"),
                owner_id="profile",
            ),
            Parameter(
                "D",
                "depth_mm",
                ParameterValue(depth / 10.0, ValueKind.LENGTH, "cm"),
                owner_id="form",
            ),
        ),
        support_planes=(SupportPlane("datum", "Base datum", frame),),
        sketches=(
            Sketch(
                "drawing",
                "Construction outline",
                "datum",
                lines,
                (*coincident, *axes, *dims),
                ("W", "H"),
                (("pine", "elm", "oak", "ash"),),
            ),
        ),
        selections=(),
        feature_timeline=(
            FeatureStep(
                "profile",
                "Construction outline",
                "reference",
                0,
                sketch_id="drawing",
                parameter_ids=("W", "H"),
            ),
            FeatureStep(
                "form",
                "Pad",
                "extrusion",
                1,
                ("profile",),
                "drawing",
                ("D",),
                "create",
                DistanceExtrude("D", frame.z_axis),
            ),
        ),
        bodies=(DesignBody("solid-body", "Original volume", "form"),),
    )


def rules_case(document: CadDocument, rules: tuple[SketchRelation, ...]) -> CadDocument:
    (sketch,) = document.sketches
    return replace(document, sketches=(replace(sketch, constraints=rules),))


def expect_refused(document: CadDocument, reason: str) -> None:
    try:
        ProjectBoss(document)
    except ValueError as error:
        RequireArch(reason in str(error), True, f"unexpected refusal for {reason}")
    else:
        raise ValueError(f"unsupported neutral graph accepted for {reason}")


# hosted checks preserve edit ownership and distinguish equality of geometry from shared nodes
def hosted_cases() -> list[tuple[int, float, float, float]]:
    results = []
    for right, width, height, depth in (
        (False, 37.5, 18.25, 13.5),
        (True, 42.25, 17.5, -8.75),
    ):
        graph = ProjectBoss(authored_case(right, width, height, depth))
        RequireArch(
            graph.Profile.AxisCode == (1 if right else 3)
            and graph.Profile.EdgeSlots == {1: (0, 3), 2: (0, 2), 3: (2, 1), 4: (3, 1)}
            and tuple(edge.SourceId for edge in graph.Profile.Edges)
            == ("pine", "ash", "oak", "elm")
            and graph.Profile.Edges[3].SourceSlots == (1, 3)
            and tuple(corner.RelationCount for corner in graph.Corners) == (3, 0, 1, 1)
            and graph.Width.PointSlots == ((0, 2) if right else (0, 3))
            and graph.Height.PointSlots == ((0, 3) if right else (0, 2))
            and (
                graph.Width.Length.ParameterId,
                graph.Width.Length.FeatureId,
                graph.Height.Length.ParameterId,
                graph.Height.Length.FeatureId,
                graph.Depth.ParameterId,
                graph.Depth.FeatureId,
                graph.Depth.Millimetres,
            )
            == ("W", "profile", "H", "profile", "D", "form", depth)
            and graph.MagnitudeMm == abs(depth)
            and graph.Reversed == (depth < 0),
            True,
            "canonical allocated topology, dimension owners and signed extent",
        )
        RequireArch(
            graph.AxialBoundsMm,
            (min(0, depth), max(0, depth)),
            "one-sided axial bounds",
        )
        results.append((graph.Profile.AxisCode, width, height, graph.Depth.Millimetres))
    seed = authored_case(False, 37.5, 18.25, 13.5)
    (sketch,) = seed.sketches
    missing = rules_case(seed, sketch.constraints[1:])
    wrong_width = replace(
        sketch.constraints[-2],
        references=(ConstraintRef("ash", "start"), ConstraintRef("ash", "end")),
    )
    wrong_side = rules_case(
        seed, (*sketch.constraints[:-2], wrong_width, sketch.constraints[-1])
    )
    bad_depth = replace(seed.parameters[2], expression=Expression("width_mm", ("W",)))
    driven = replace(seed, parameters=(*seed.parameters[:2], bad_depth))
    for case, reason in (
        (missing, "four endpoint coincidences"),
        (wrong_side, "actual anchored side"),
        (driven, "independent owner-bound length"),
        (authored_case(False, 19.0, 19.0, 8.0), "distinct supported side lengths"),
    ):
        expect_refused(case, reason)
    return results
