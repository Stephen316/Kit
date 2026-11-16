from dataclasses import replace as Replace

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Core.Cut.CutLoop import BuildCutLoop
from convert.adapters.solidworks.Core.RectBindings import ReadMmPoints
from convert.adapters.solidworks.Core.RectSource import RectSource
from convert.adapters.solidworks.Resolved.ProfileSketch import ProfileSketch
from convert.adapters.solidworks.Sketch.InlineSketch import InlineRead
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import PointGeometry
from interchange.geometry.Models.Sketch import ConstraintRef, Sketch, SketchEntity, SketchRelation
from interchange.geometry.Models.VectorPlane import PlaneVector


# initially empty linked sketches need a point entity for each actual saved member
def LinkedRectPts(
    Profile: ProfileSketch, SketchId: str, StreamName: str
) -> tuple[SketchEntity, ...]:
    Report = Profile.Geometry
    return tuple(
        SketchEntity(
            f"{SketchId}:native-point:{PointValue['id'][1]}", GeometryKind.KPoint,
            PointGeometry(PlaneVector(*Position)),
            provenance=RectSource(
                str(PointValue["id"][1]), StreamName, Source, "sketch-point",
            ),
        )
        for PointValue, Position, Source in zip(
            Report["point_relation_tallies"], ReadMmPoints(Profile), Profile.Members.Points,
            strict=True,
        )
    )


# saved axis targets are required before the normal rectangle relation projection
def LinkedRectAxes(
    Profile: ProfileSketch, Lines: tuple[SketchEntity, ...]
) -> tuple[SketchRelation, ...]:
    ByIdentity = {Value.attributes["native_segment_id"]: Value.id for Value in Lines}
    return tuple(
        SketchRelation(
            f"sldprt:constraint:{Profile.FeatureId}:native-axis:{Relation['start']}",
            Relation["kind"],
            (ConstraintRef(ByIdentity[Relation["segment_native_id"]]),),
        )
        for Relation in Profile.Geometry["member_relations"]
    )


# configuration owned members seed the same checked projection used by ordinary rectangles
def SeedLinkedRect(SketchValue: Sketch, Profile: ProfileSketch, StreamName: str) -> Sketch:
    RequireArch(
        (SketchValue.entities, SketchValue.closed_profile_entity_ids), ((), ()),
        "empty linked rectangle before materialization",
    )
    RequireArch(
        all(Value.kind not in ("horizontal", "vertical") for Value in SketchValue.constraints),
        True, "only saved axis identities can seed the empty perimeter",
    )
    DataValue = InlineRead(Profile.Geometry, Profile.Coincidences, Profile.Members)
    Lines = BuildCutLoop(DataValue, SketchValue.id, StreamName)
    Points = LinkedRectPts(Profile, SketchValue.id, StreamName)
    RequireArch(
        len({Value.id for Value in Points}), len(Points), "unique linked rectangle point identities"
    )
    return Replace(
        SketchValue, entities=(*Lines, *Points),
        closed_profile_entity_ids=(tuple(Value.id for Value in Lines),),
        constraints=(*SketchValue.constraints, *LinkedRectAxes(Profile, Lines)),
        attributes=FreezeMapping({
            **SketchValue.attributes,
            "native_geometry_source": "typed-config-rectangle",
            "native_profile_count": 1,
            "native_sketch_object_id": Profile.SketchIndex,
        }),
    )
