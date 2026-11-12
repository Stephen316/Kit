from collections.abc import Callable
from dataclasses import replace as Replace

from convert.formats.Fusion.BodyInputs.InputContext import InputContext
from convert.formats.Fusion.Revolves.JoinRevModels import JoinRevModels
from convert.formats.Fusion.Scales.ScaleInputsPlan import ReadScalePicks
from convert.formats.Fusion.Scales.ScaleSeed import ReadScaleSeed
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable, ReadAsmTable
from convert.formats.Fusion.Topology.AsmEdge.PrismCache import ReadPrismCache
from convert.formats.Fusion.Topology.BodyAsmMap import ReadBodyAsmRef
from convert.formats.Fusion.Topology.NativeBody import NativeBody
from convert.formats.Fusion.Topology.SolidBodyRecord import MakeSolidRecord
from convert.geometry.Scale.ScalePrism import BuildScalePrism
from interchange.brep.topology.BrepModel import BrepModel
from interchange.core.Common import FreezeMapping
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.VectorSpace import SpaceVector


# complete body proofs compare derived geometry against its explicitly mapped saved cache
def ReadScaleBodies(
    Document: CadDocument,
    BulkData: bytes,
    Context: InputContext,
    Feature: FeatureStep,
    FeatureId: int,
    Members: tuple[NativeBody, ...],
    Factors: SpaceVector,
    Center: SpaceVector,
    LoadBlob: Callable[[str], bytes],
) -> tuple[tuple[DesignBody, ...], BrepModel]:
    Inputs = ReadScalePicks(Document, BulkData, Context, Feature, FeatureId, Members)
    Tables: dict[str, AsmTable] = {}
    Bodies: list[DesignBody] = []
    Models: list[BrepModel] = []
    for Source, Member, AnchorId in Inputs:
        SeedValue = ReadScaleSeed(Document, Source, Member.ComponentId)
        BodyId = f"fusion-derived-body-{Source.id}"
        Geometry = BuildScalePrism(
            BodyId, SeedValue.Profile, SeedValue.Frame, SeedValue.Depth, Factors, Center
        )
        Mapping = ReadBodyAsmRef(
            BulkData, Context.Owners, Member.ObjectId, Member.ComponentId
        )
        Table = Tables.get(Mapping.FileName)
        if Table is None:
            Table = ReadAsmTable(LoadBlob(Mapping.FileName))
            Tables[Mapping.FileName] = Table
        Ordinal = ReadPrismCache(
            Table, Mapping.Handle, Mapping.Handles, Geometry[0], SeedValue.CurveTags
        )
        BodyValue, Model = MakeSolidRecord(
            BodyId,
            "Scale result",
            Feature,
            Geometry,
            Context.Owners,
            (Member.ObjectId, AnchorId),
            Member.CollectionId,
            "source_profile_scale",
        )
        Bodies.append(
            Replace(
                BodyValue,
                name=Member.Name or Source.name or BodyValue.name,
                attributes=FreezeMapping(
                    {
                        **BodyValue.attributes,
                        "fusion.scale_source_feature_id": Source.id,
                        "fusion.asm_body_ordinal": Ordinal,
                        "fusion.asm_body_handle": Mapping.Handle,
                        "fusion.asm_history_member": Mapping.FileName,
                    }
                ),
            )
        )
        Models.append(Model)
    return tuple(Bodies), JoinRevModels(tuple(Models))
