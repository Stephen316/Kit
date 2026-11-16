from dataclasses import replace as Replace

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Core.Cut.LinkedRectangle import SeedLinkedRect
from convert.adapters.solidworks.Core.Native import NativeDimension
from convert.adapters.solidworks.Core.RectBindings import BindRectangle
from convert.adapters.solidworks.Core.RectDistances import ProjectDists
from convert.adapters.solidworks.Core.RectEntities import ProjectRectEdge, ProjectRectPt
from convert.adapters.solidworks.Core.RectOrigin import BindRectOrigin
from convert.adapters.solidworks.Core.RectRelations import ProjectAxes, ProjectOrigin
from convert.adapters.solidworks.Resolved.RectanglePart import RectanglePart
from interchange.geometry.Models.Sketch import Sketch, SketchEntity


# an ordinary sketch only adopts typed geometry when its existing public identities corroborate
def ProjectRect(
    Neutral: Sketch,
    Parsed: RectanglePart | None,
    StreamName: str,
    Entries: tuple[tuple[NativeDimension, str], ...] = (),
    *,
    SeedEmpty: bool = False,
) -> Sketch:
    if Parsed is None:
        return Neutral
    try:
        Source = SeedLinkedRect(Neutral, Parsed.Profile, StreamName) if SeedEmpty else Neutral
        return BuildRect(Source, Parsed, StreamName, Entries)
    except (KeyError, IndexError, ValueError):
        return Neutral


# committing one replacement keeps geometry and solver references consistent as a group
def BuildRect(
    Neutral: Sketch,
    Parsed: RectanglePart,
    StreamName: str,
    Entries: tuple[tuple[NativeDimension, str], ...],
) -> Sketch:
    Profile = Parsed.Profile
    RequireArch(Neutral.name, Profile.NameValue, "typed native and public sketch name")
    RequireArch(
        Neutral.attributes.get("native_object_id"),
        Profile.FeatureId,
        "typed native and public sketch identity",
    )
    Binding = BindRectangle(Neutral, Profile, StreamName)
    Origin = BindRectOrigin(Parsed, Binding)
    Entities: dict[str, SketchEntity] = {}
    for Bound in Binding.Edges:
        Entities[Bound.Entity.id] = ProjectRectEdge(
            Bound, Binding, Profile.FeatureId, StreamName
        )
    for SlotValue, Entity in enumerate(Binding.PointEntities):
        Entities[Entity.id] = ProjectRectPt(
            Profile, Binding, Origin, SlotValue, StreamName
        )
    RequireArch(
        len(Entities),
        len(Neutral.entities),
        "typed members cover the existing rectangle entities",
    )
    Rules = ProjectAxes(Neutral, Profile.Geometry, Binding, StreamName)
    Rules = ProjectDists(Rules, Profile, Binding, StreamName, Entries)
    Coincidence = ProjectOrigin(Binding, Origin, Profile.FeatureId, StreamName)
    RequireArch(
        Coincidence.id not in {RuleValue.id for RuleValue in Rules},
        True,
        "unique saved coincidence identity",
    )
    return Replace(
        Neutral,
        entities=tuple(Entities[Entity.id] for Entity in Neutral.entities),
        constraints=(*Rules, Coincidence),
    )
