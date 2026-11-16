from convert.Formats.Fusion.DocumentCodec.Defaults.BaseDefaults import BaseDefaults
from convert.Formats.Fusion.DocumentCodec.Defaults.ExtrudeDefaults import (
    ExtrudeDefaults,
)
from convert.Formats.Fusion.DocumentCodec.Defaults.SketchDefaults import SketchDefaults
from convert.Formats.Fusion.DocumentCodec.Form.AddFormMut import AddFormMut
from convert.Formats.Fusion.DocumentCodec.Form.CheckFormSpec import CheckFormSpec
from convert.Formats.Fusion.DocumentCodec.Form.FormDefaults import FormDefaults
from convert.Formats.Fusion.DocumentCodec.Form.FormParts import FormParts
from convert.Formats.Fusion.DocumentCodec.Form.FormSpec import FormSpec
from convert.Formats.Fusion.DocumentCodec.Form.LinkDynamicMut import LinkDynamicMut
from convert.Formats.Fusion.DocumentCodec.Form.LinkFormBodyMut import (
    LinkFormBodyMut,
    LinkNodeMatMut,
)
from convert.Formats.Fusion.DocumentCodec.Form.LinkFormMut import LinkFormMut
from convert.Formats.Fusion.DocumentCodec.Form.LinkFormTagsMut import LinkFormTagsMut
from convert.Formats.Fusion.DocumentCodec.Form.LinkFrameMut import LinkFrameMut
from convert.Formats.Fusion.DocumentCodec.Foundation.AddCollectMut import AddCollectMut
from convert.Formats.Fusion.DocumentCodec.Foundation.AddComputeMut import AddComputeMut
from convert.Formats.Fusion.DocumentCodec.Foundation.AddGeometryMut import (
    AddGeometryMut,
)
from convert.Formats.Fusion.DocumentCodec.Foundation.AddRootsMut import AddRootsMut
from convert.Formats.Fusion.DocumentCodec.Foundation.AddUnitsMut import AddUnitsMut
from convert.Formats.Fusion.DocumentCodec.Foundation.LinkCompMut import LinkCompMut
from convert.Formats.Fusion.DocumentCodec.Foundation.LinkRootsMut import LinkRootsMut
from convert.Formats.Fusion.DocumentCodec.Materials.LinkMaterialMut import (
    LinkMaterialMut,
)
from convert.Formats.Fusion.DocumentCodec.Model.CreateAuthor import CreateAuthor
from convert.Formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.DocumentCodec.Records.EmitDesign import EmitDesign
from convert.Formats.Fusion.SegmentCodec.Features.Binary.CheckUuid import CheckUuid


# the form design operation needs a consistent construction rule so editable control cages retain their document relationships
def BuildFormDesign(
    SpecValue: FormSpec, AssetId: str, Parts: FormParts, UnixMicros: int
) -> DesignResult:
    CheckFormSpec(SpecValue)
    CheckUuid(AssetId)
    if type(UnixMicros) is not int or UnixMicros < 2:
        raise ValueError("Form document time must be a positive microsecond count")
    Document = DocumentSpec(
        SpecValue.Title,
        "form",
        1.0,
        "form",
        BodyName=SpecValue.BodyName,
        Material=SpecValue.Material,
    )
    Author = CreateAuthor(Document, AssetId)
    Author.BrepPart = Parts.History
    for Defaults in (
        BaseDefaults(),
        SketchDefaults(),
        ExtrudeDefaults(),
        FormDefaults(),
    ):
        Author.Defaults.update(Defaults)
    for Builder in (
        AddRootsMut,
        AddCollectMut,
        AddComputeMut,
        AddGeometryMut,
        AddUnitsMut,
        LinkCompMut,
        LinkRootsMut,
    ):
        Builder(Author)
    AddFormMut(Author, SpecValue)
    LinkFormMut(Author, SpecValue)
    LinkFrameMut(Author, SpecValue, Parts)
    LinkFormTagsMut(Author, SpecValue)
    LinkFormBodyMut(Author, SpecValue, Parts)
    LinkMaterialMut(Author)
    LinkNodeMatMut(Author)
    LinkDynamicMut(Author, UnixMicros)
    return EmitDesign(Author)
