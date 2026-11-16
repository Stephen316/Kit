from uuid import uuid4 as MakeUuid

from convert.Formats.Fusion.DocumentCodec.BuildBodyPart import BuildBodyPart
from convert.Formats.Fusion.DocumentCodec.BuildDesign import BuildDesign
from convert.Formats.Fusion.DocumentCodec.Materials.BuildMatPart import BuildMatPart
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.DocumentCodec.PackDocument import PackDocument


# the document operation needs a consistent construction rule so model state retains its native feature and ownership relationships
def EmitDocument(SpecValue: DocumentSpec) -> bytes:
    Design = BuildDesign(SpecValue, str(MakeUuid()))
    return PackDocument(
        Design,
        SpecValue.Title,
        BuildBodyPart(SpecValue, Design) + BuildMatPart(Design),
    )
