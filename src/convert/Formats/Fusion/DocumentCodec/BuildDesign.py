from convert.Formats.Fusion.DocumentCodec.CheckDocSpec import CheckDocSpec
from convert.Formats.Fusion.DocumentCodec.Materials.LinkMaterialMut import (
    LinkMaterialMut,
)
from convert.Formats.Fusion.DocumentCodec.Defaults.BaseDefaults import BaseDefaults
from convert.Formats.Fusion.DocumentCodec.Defaults.ExtrudeDefaults import (
    ExtrudeDefaults,
)
from convert.Formats.Fusion.DocumentCodec.Defaults.SketchDefaults import SketchDefaults
from convert.Formats.Fusion.DocumentCodec.Extrusion.AddExtrudeMut import AddExtrudeMut
from convert.Formats.Fusion.DocumentCodec.Extrusion.BindParamsMut import BindParamsMut
from convert.Formats.Fusion.DocumentCodec.Extrusion.LinkBodyMut import LinkBodyMut
from convert.Formats.Fusion.DocumentCodec.Extrusion.LinkExtrudeMut import LinkExtrudeMut
from convert.Formats.Fusion.DocumentCodec.Extrusion.LinkProfileMut import LinkProfileMut
from convert.Formats.Fusion.DocumentCodec.Foundation.AddCollectMut import AddCollectMut
from convert.Formats.Fusion.DocumentCodec.Foundation.AddComputeMut import AddComputeMut
from convert.Formats.Fusion.DocumentCodec.Foundation.AddGeometryMut import (
    AddGeometryMut,
)
from convert.Formats.Fusion.DocumentCodec.Foundation.AddRootsMut import AddRootsMut
from convert.Formats.Fusion.DocumentCodec.Foundation.AddUnitsMut import AddUnitsMut
from convert.Formats.Fusion.DocumentCodec.Foundation.LinkCompMut import LinkCompMut
from convert.Formats.Fusion.DocumentCodec.Foundation.LinkRootsMut import LinkRootsMut
from convert.Formats.Fusion.DocumentCodec.Model.CreateAuthor import CreateAuthor
from convert.Formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.DocumentCodec.Records.EmitDesign import EmitDesign
from convert.Formats.Fusion.DocumentCodec.Sketch.AddCircleMut import AddCircleMut
from convert.Formats.Fusion.DocumentCodec.Sketch.LinkCircleMut import LinkCircleMut
from convert.Formats.Fusion.DocumentCodec.Rectangle.AddRectangle import AddRectangle
from convert.Formats.Fusion.DocumentCodec.Rectangle.LinkRectangle import LinkRectangle
from convert.Formats.Fusion.DocumentCodec.Rectangle.Dimensions.ConstrainMut import (
    ConstrainMut,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Design.AddPartMut import (
    AddPartMut,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Vocabulary.FeatureDefaults import (
    FeatureDefaults,
)
from convert.Formats.Fusion.SegmentCodec.Features.Binary.CheckUuid import CheckUuid


# the design operation needs a consistent construction rule so model state retains its native feature and ownership relationships
def BuildDesign(SpecValue: DocumentSpec, AssetId: str) -> DesignResult:
    CheckDocSpec(SpecValue)
    CheckUuid(AssetId)
    Author = CreateAuthor(SpecValue, AssetId)
    Author.Defaults.update(BaseDefaults())
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
    if SpecValue.ProfileKind in ("circle", "extrusion", "frustum"):
        Author.Defaults.update(SketchDefaults())
        AddCircleMut(Author)
        LinkCircleMut(Author)
    if SpecValue.ProfileKind in ("rectangle", "cuboid"):
        Author.Defaults.update(SketchDefaults())
        AddRectangle(Author)
        LinkRectangle(Author)
    if SpecValue.ProfileKind in ("extrusion", "cuboid", "frustum"):
        Author.Defaults.update(ExtrudeDefaults())
        for Builder in (
            AddExtrudeMut,
            BindParamsMut,
            LinkProfileMut,
            LinkExtrudeMut,
            LinkBodyMut,
            LinkMaterialMut,
        ):
            Builder(Author)
    if SpecValue.ConstrainRectangle:
        ConstrainMut(Author)
    if SpecValue.ProfileKind == "part":
        Author.Defaults.update(SketchDefaults())
        Author.Defaults.update(ExtrudeDefaults())
    if SpecValue.Features:
        Author.Defaults.update(FeatureDefaults())
        AddPartMut(Author)
    return EmitDesign(Author)
