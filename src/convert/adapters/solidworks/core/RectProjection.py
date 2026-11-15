from dataclasses import replace as Replace

from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.core.RectBindings import BindRectangle
from convert.adapters.solidworks.core.RectEntities import ProjectRectEdge, ProjectRectPt
from convert.adapters.solidworks.core.RectOrigin import BindRectOrigin
from convert.adapters.solidworks.core.RectRelations import ProjectAxes, ProjectOrigin
from convert.adapters.solidworks.resolved.RectanglePart import RectanglePart
from interchange.geometry.models.Sketch import Sketch, SketchEntity


# an ordinary sketch only adopts typed geometry when its existing public identities corroborate
def ProjectRect(
    Neutral: Sketch, Parsed: RectanglePart | None, StreamName: str
) -> Sketch:
    if Parsed is None:
        return Neutral
    try:
        return BuildRect(Neutral, Parsed, StreamName)
    except (KeyError, IndexError, ValueError):
        return Neutral


# committing one replacement keeps geometry and solver references consistent as a group
def BuildRect(Neutral: Sketch, Parsed: RectanglePart, StreamName: str) -> Sketch:
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
