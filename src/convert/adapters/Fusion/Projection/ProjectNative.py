from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.adapters.Fusion.Native.Projection.ProjectVendor import ProjectVendor
from convert.adapters.Fusion.Projection.CompareNative import CompareNative
from convert.adapters.Fusion.Projection.NativeIndex import MakeIndex
from convert.adapters.Fusion.Projection.NativeProfile import NativeProfile
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange.document.models.DocumentModel import CadDocument
from interchange.records.RecordSource import CadSource


def ProjectNative(ModelValue: DocumentModel, Source: CadSource) -> CadDocument:
    if ModelValue.Meshes:
        raise ValueError("Strict Fusion projection does not yet support mesh bodies")
    if (
        ModelValue.Configurations
        or ModelValue.Snapshots
        or ModelValue.Graphics is not None
    ):
        return ProjectVendor(ModelValue, Source)
    SpecValue = NativeProfile(MakeIndex(ModelValue), ModelValue)
    Expected = ReadDocument(EmitDocument(SpecValue))
    CompareNative(ModelValue, Expected)
    Document = MakeFusionDoc(SpecValue)
    Contract = {"version": 1, "model": EncodeState(ModelValue)}
    return ReplaceData(
        Document, source=Source, metadata={"fusion.native_state": Contract}
    )
