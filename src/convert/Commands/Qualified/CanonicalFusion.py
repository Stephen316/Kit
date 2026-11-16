from dataclasses import replace as ReplaceData

from interchange.document.Models.DocumentModel import CadDocument


# geometry qualification needs a fresh authoritative sdk projection independent of supplied neutral geometry
def CanonicalFusion(Document: CadDocument, ContractName: str) -> CadDocument:
    from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
    from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
    from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec

    Contract = Document.metadata[ContractName]
    if ContractName == "fusion.authoring":
        SpecValue = CheckContract(Contract, "spec")
        if not isinstance(SpecValue, DocumentSpec):
            raise ValueError(
                "Qualified geometry requires an authoring document specification"
            )
        return MakeFusionDoc(SpecValue)
    from convert.adapters.Fusion.Bridge.NativeVersion import NativeVersion
    from convert.adapters.Fusion.Native.Projection.ProjectVendor import ProjectVendor
    from convert.adapters.Fusion.Projection.ProjectNative import ProjectNative
    from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel

    Version = NativeVersion(Contract)
    ModelValue = CheckContract(Contract, "model", Version)
    if not isinstance(ModelValue, DocumentModel):
        raise ValueError("Qualified geometry requires a native document model")
    Projector = ProjectVendor if Version == 2 else ProjectNative
    return ReplaceData(
        Projector(ModelValue, Document.source), metadata={ContractName: Contract}
    )
