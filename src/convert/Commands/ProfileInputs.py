from collections.abc import Sequence

from convert.Commands.CheckKinds import CheckKinds
from convert.Commands.IsClosedProfile import IsClosedProfile
from interchange.geometry.Models.Sketch import Sketch


# generator history needs actual closed supported sketch geometry rather than unverified profile references
def ProfileInputs(Sketches: Sequence[Sketch]) -> set[str]:
    Profiles = set[str]()
    for SketchValue in Sketches:
        if SketchValue.suppressed or len(SketchValue.closed_profile_entity_ids) != 1:
            continue
        for Entity in SketchValue.entities:
            CheckKinds(Entity)
        Entities = {Entity.id: Entity for Entity in SketchValue.entities}
        if len(Entities) != len(SketchValue.entities):
            continue
        Group = SketchValue.closed_profile_entity_ids[0]
        if not 1 <= len(Group) <= 4 or len(set(Group)) != len(Group):
            continue
        if any(EntityId not in Entities for EntityId in Group):
            continue
        if IsClosedProfile(tuple(Entities[EntityId] for EntityId in Group)):
            Profiles.add(SketchValue.id)
    return Profiles
