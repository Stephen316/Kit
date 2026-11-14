from uuid import uuid4 as MakeUuid

from convert.formats.Fusion.DocumentCodec.BuildBodyPart import BuildBodyPart
from convert.formats.Fusion.DocumentCodec.BuildDesign import BuildDesign
from convert.formats.Fusion.DocumentCodec.Materials.BuildMatPart import BuildMatPart
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.PackDocument import PackDocument


def EmitDocument(SpecValue: DocumentSpec) -> bytes:
    Design = BuildDesign(SpecValue, str(MakeUuid()))
    return PackDocument(
        Design,
        SpecValue.Title,
        BuildBodyPart(SpecValue, Design) + BuildMatPart(Design),
    )
