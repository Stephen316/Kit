from convert.formats.Fusion.DocumentCodec.Defaults.BaseDefaults import BaseDefaults
from convert.formats.Fusion.DocumentCodec.Defaults.ExtrudeDefaults import (
    ExtrudeDefaults,
)
from convert.formats.Fusion.DocumentCodec.Defaults.SketchDefaults import SketchDefaults
from convert.formats.Fusion.DocumentCodec.Form.AddFormMut import AddFormMut
from convert.formats.Fusion.DocumentCodec.Form.CheckFormSpec import CheckFormSpec
from convert.formats.Fusion.DocumentCodec.Form.FormDefaults import FormDefaults
from convert.formats.Fusion.DocumentCodec.Form.FormParts import FormParts
from convert.formats.Fusion.DocumentCodec.Form.FormSpec import FormSpec
from convert.formats.Fusion.DocumentCodec.Form.LinkDynamicMut import LinkDynamicMut
from convert.formats.Fusion.DocumentCodec.Form.LinkFormBodyMut import (
    LinkFormBodyMut,
    LinkNodeMatMut,
)
from convert.formats.Fusion.DocumentCodec.Form.LinkFormMut import LinkFormMut
from convert.formats.Fusion.DocumentCodec.Form.LinkFormTagsMut import LinkFormTagsMut
from convert.formats.Fusion.DocumentCodec.Form.LinkFrameMut import LinkFrameMut
from convert.formats.Fusion.DocumentCodec.Foundation.AddCollectMut import AddCollectMut
from convert.formats.Fusion.DocumentCodec.Foundation.AddComputeMut import AddComputeMut
from convert.formats.Fusion.DocumentCodec.Foundation.AddGeometryMut import (
    AddGeometryMut,
)
from convert.formats.Fusion.DocumentCodec.Foundation.AddRootsMut import AddRootsMut
from convert.formats.Fusion.DocumentCodec.Foundation.AddUnitsMut import AddUnitsMut
from convert.formats.Fusion.DocumentCodec.Foundation.LinkCompMut import LinkCompMut
from convert.formats.Fusion.DocumentCodec.Foundation.LinkRootsMut import LinkRootsMut
from convert.formats.Fusion.DocumentCodec.Materials.LinkMaterialMut import (
    LinkMaterialMut,
)
from convert.formats.Fusion.DocumentCodec.Model.CreateAuthor import CreateAuthor
from convert.formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.Records.EmitDesign import EmitDesign
from convert.formats.Fusion.SegmentCodec.Features.Binary.CheckUuid import CheckUuid


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
