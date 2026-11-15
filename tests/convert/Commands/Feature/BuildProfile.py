from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.models.DocumentModel import CadDocument
from tests.convert.Commands.Feature.ProfileEntities import ProfileEntities


# declared closed profile groups must be challenged by actual invalid contour geometry
def BuildProfile(RecordKind: str) -> CadDocument:
    Document = MakeFusionDoc(
        DocumentSpec("Profile closure", "height", 20.0, ProfileKind="cuboid")
    )
    Entities = ProfileEntities(RecordKind)
    Groups: tuple[tuple[str, ...], ...] = (tuple(Entity.id for Entity in Entities),)
    if RecordKind == "DuplicateMember":
        Groups = ((*Groups[0][:-1], Groups[0][0]),)
    elif RecordKind == "MultipleLoops":
        Groups = tuple((Entity.id,) for Entity in Entities)
    return ReplaceData(
        Document,
        metadata={},
        sketches=(
            ReplaceData(
                Document.sketches[0],
                entities=Entities,
                closed_profile_entity_ids=Groups,
            ),
        ),
    )
