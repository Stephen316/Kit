from dataclasses import replace as Replace

from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.core.cut.CutLoop import BuildCutLoop
from convert.adapters.solidworks.core.cut.CutOwners import FindCutOwner
from convert.adapters.solidworks.sketch.InlineSketch import InlineRead
from interchange.core.Common import FreezeMapping
from interchange.document.models.DocumentModel import CadDocument

# face attachment depends on this sketch having a proved configuration perimeter
KCutLoopSource = "typed-config-sketch"


# materialization fills an empty cut profile only after its actual configuration loop closes
def ProjectCutLoop(
    Document: CadDocument, DataValue: InlineRead, ProfileId: int, StreamName: str
) -> CadDocument:
    try:
        SketchValue, _ = FindCutOwner(Document, ProfileId)
        RequireArch(
            (SketchValue.entities, SketchValue.closed_profile_entity_ids),
            ((), ()),
            "empty neutral cut profile for materialization",
        )
        Entities = BuildCutLoop(DataValue, SketchValue.id, StreamName)
    except (KeyError, IndexError, ValueError):
        return Document
    Bound = Replace(
        SketchValue,
        entities=Entities,
        closed_profile_entity_ids=(tuple(Value.id for Value in Entities),),
        attributes=FreezeMapping(
            {
                **SketchValue.attributes,
                "native_geometry_source": KCutLoopSource,
                "native_profile_count": 1,
                "native_sketch_object_id": DataValue.Geometry["object_index"],
            }
        ),
    )
    return Replace(
        Document,
        sketches=tuple(
            Bound if Value is SketchValue else Value for Value in Document.sketches
        ),
    )
