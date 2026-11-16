from collections.abc import Callable
from dataclasses import replace as Replace

from convert.Formats.Fusion.BodyInputs.InputContext import InputContext
from convert.Formats.Fusion.Revolves.JoinRevModels import JoinRevModels
from convert.Formats.Fusion.Scales.ScaleInputsPlan import ReadScalePicks
from convert.Formats.Fusion.Scales.ScaleSeed import ReadScaleSeed
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable, ReadAsmTable
from convert.Formats.Fusion.Topology.AsmEdge.PrismCache import ReadPrismCache
from convert.Formats.Fusion.Topology.BodyAsmMap import ReadBodyAsmRef
from convert.Formats.Fusion.Topology.NativeBody import NativeBody
from convert.Formats.Fusion.Topology.SolidBodyRecord import MakeSolidRecord
from convert.Geometry.Scale.ScalePrism import BuildScalePrism
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.VectorSpace import SpaceVector


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
