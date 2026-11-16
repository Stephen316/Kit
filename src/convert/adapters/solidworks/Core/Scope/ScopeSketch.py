from dataclasses import replace as Replace

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Core.Cut.FaceProjection import KFaceSupportSource
from convert.adapters.solidworks.Core.Cut.LinkedRectangle import SeedLinkedRect
from convert.adapters.solidworks.Core.OrdinaryRead import KArchiveSupport
from convert.adapters.solidworks.Core.RectBindings import BindRectangle
from convert.adapters.solidworks.Core.RectProjection import BuildRect
from convert.adapters.solidworks.Core.RectRelations import ProjectAxes
from convert.adapters.solidworks.Core.RectSource import RectSource
from convert.adapters.solidworks.Resolved.ProfileSketch import ProfileSketch
from convert.adapters.solidworks.Resolved.RectanglePart import RectanglePart
from convert.adapters.solidworks.Resolved.Scope.Profile import ScopeProfile
from convert.adapters.solidworks.Sketch.GeometryTypes import Coincidence, PointReference
from convert.adapters.solidworks.Sketch.MemberSpans import MemberSpan
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


# scoped rectangles retain the actual inline geometry and its owned relation records
def BuildScopeRect(
    Template: Sketch,
    Profile: ProfileSketch,
    PlaneValue: SupportPlane,
    StreamName: str,
    Anchor: RectanglePart | None = None,
) -> Sketch:
    RequireArch(
        (Template.name, Template.attributes.get("native_object_id")),
        (Profile.NameValue, Profile.FeatureId),
        "scoped sketch owner",
    )
    RequireArch(
        Profile.Geometry["length_dimensions"], [], "scoped profile has no lengths"
    )
    Seeded = SeedLinkedRect(
        Replace(Template, entities=(), constraints=(), closed_profile_entity_ids=()),
        Profile,
        StreamName,
    )
    if Anchor is not None:
        Bound = BuildRect(Seeded, Anchor, StreamName, ())
    else:
        EmptyRelations: tuple[list[PointReference], list[Coincidence]] = ([], [])
        RequireArch(
            (Profile.Geometry["external_point_references"], Profile.Coincidences),
            EmptyRelations,
            "scoped rectangle has no other saved relations",
        )
        Binding = BindRectangle(Seeded, Profile, StreamName)
        Bound = Replace(
            Seeded,
            constraints=ProjectAxes(Seeded, Profile.Geometry, Binding, StreamName),
        )
    return Replace(
        Bound,
        support_plane_id=PlaneValue.id,
        attributes=FreezeMapping(
            {
                **Bound.attributes,
                "native_geometry_source": "typed-resolved-sketch",
                "support_plane_source": (
                    KArchiveSupport
                    if PlaneValue.support_selection_id is None
                    else KFaceSupportSource
                ),
                "support_plane_native_id": PlaneValue.attributes.get(
                    "native_object_id"
                ),
                "unframed_support_plane_native_id": None,
            }
        ),
    )


# the saved principal frame supplies the neutral sketch axes and origin
def ScopeDatum(
    Template: SupportPlane, Profile: ScopeProfile, StreamName: str
) -> SupportPlane:
    Datum = Profile.Datum
    RequireArch(
        (Template.id, Template.name),
        (f"sldprt:plane:{Datum.FeatureId}", Datum.NameValue),
        "resolved principal datum owner",
    )
    First, Second, Normal = (
        SpaceVector(*AxisValue) for AxisValue in Profile.Directions
    )
    Point = SpaceVector(*(Value * 1000 for Value in Datum.Geometry.PointMetres))
    return Replace(
        Template,
        transform=Transform(Point, First, Second, Normal),
        provenance=RectSource(
            str(Datum.FeatureId),
            StreamName,
            MemberSpan(Datum.Offset, Datum.EndOffset),
            "scoped-principal-support",
        ),
    )
