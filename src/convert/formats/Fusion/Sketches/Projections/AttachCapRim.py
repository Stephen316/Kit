from dataclasses import replace as Replace

from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.Sketches.FaceSupport.FaceRecipePick import FaceRecipePick
from convert.formats.Fusion.Sketches.FaceSupport.SavedFaceProof import SavedFaceProof
from convert.formats.Fusion.Sketches.Projections.CapSource import IndexCapNames
from convert.formats.Fusion.Sketches.Projections.CheckCapLine import CheckCapLine
from convert.formats.Fusion.Sketches.Projections.ReadCapRim import ReadCapRim
from convert.formats.Fusion.Sketches.Projections.RetainCapLine import RetainCapLine
from convert.formats.Fusion.Sketches.SketchRuleScope import (
    IndexRuleEnts,
    ReadSketchRoot,
)
from convert.formats.Fusion.Topology.RecipeRead import KRecipeGuid
from interchange.geometry.models.Sketch import Sketch, SketchEntity
from interchange.geometry.models.Transform import Transform


# every saved cap edge must map to one line in a closed cache cycle before any links publish
def AttachCapRim(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    SketchValue: Sketch,
    Recipe: FaceRecipePick,
    Proof: SavedFaceProof,
    Frame: Transform,
) -> Sketch:
    RootSpan = ReadSketchRoot(SketchValue, Owners)
    ControllerId, EntryId, Outputs = ReadCapRim(
        BulkData, Owners, RootSpan.ObjectId, Recipe
    )
    Sources = IndexCapNames(BulkData, Owners, Recipe)
    Entities = IndexRuleEnts(BulkData, Owners, SketchValue, RootSpan.ObjectId)
    Revised: dict[str, SketchEntity] = {}
    Starts: list[int] = []
    Finishes: list[int] = []
    for Value in Outputs:
        RecipeBytes = SelectCursor(
            BulkData, Owners, Value.RecipeId, KRecipeGuid
        ).DataValue
        Context = Sources.pop(RecipeBytes, None)
        Entity = Entities.get(Value.EntityId)
        if Context is None or Entity is None:
            raise ValueError(
                "Fusion cap projection output lacks one unique named source"
            )
        Match = Proof.FaceEvidence.Edges[Context.Operands]
        First, Second = Match[1]
        Start, Finish = CheckCapLine(
            Entity,
            Frame,
            (Proof.FaceEvidence.Points[First], Proof.FaceEvidence.Points[Second]),
        )
        Records = (
            ControllerId,
            EntryId,
            Context.ContextId,
            Context.RecipeId,
            Value.NameId,
            Value.RecipeId,
        )
        DesignSpans = tuple(
            ParamOrigin(Owners[Identity]).spans[0] for Identity in Records
        )
        Revised[Entity.id] = RetainCapLine(
            Entity, Proof, Match, Context, ControllerId, DesignSpans
        )
        Starts.append(Start)
        Finishes.append(Finish)
    if Sources or len(set(Starts)) != 4 or Finishes != Starts[1:] + Starts[:1]:
        raise ValueError(
            "Fusion cap projection inventory or directed cache cycle disagrees"
        )
    return Replace(
        SketchValue,
        entities=tuple(Revised.get(Value.id, Value) for Value in SketchValue.entities),
    )
