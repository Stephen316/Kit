from convert.Formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Graphics.EmitSceneParts import (
    EmitSceneParts,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Configuration.CheckDocConfig import (
    CheckDocConfig,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Images.CheckDocImages import (
    CheckDocImages,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Links.CheckDocLinks import (
    CheckDocLinks,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Configuration.EmitConfigPart import (
    EmitConfigPart,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Snapshots.EmitSnapPart import (
    EmitSnapPart,
)
from convert.Formats.Fusion.ContainerCodec.Model.FusionContainer import FusionContainer
from convert.Formats.Fusion.DocumentCodec.EmitBodyPart import EmitBodyPart
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Form.EmitFormPart import (
    EmitFormPart,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Form.CheckDocForms import (
    CheckDocForms,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Mesh.CheckDocMeshes import (
    CheckDocMeshes,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Mesh.EmitMeshPart import (
    EmitMeshPart,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Graphics.CheckDocScene import (
    CheckDocScene,
)
from convert.Formats.Fusion.DocumentCodec.Reading.EmitMatPart import EmitMatPart
from convert.Formats.Fusion.DocumentCodec.Reading.Materials.CheckDocMats import (
    CheckDocMats,
)
from convert.Formats.Fusion.DocumentCodec.Records.EmitDocSegment import EmitDocSegment


# the parsed operation needs a consistent construction rule so model state retains its native feature and ownership relationships
def EmitParsed(Value: DocumentModel) -> bytes:
    CheckDocMats(Value)
    CheckDocConfig(Value)
    CheckDocLinks(Value)
    CheckDocScene(Value)
    CheckDocMeshes(Value)
    CheckDocForms(Value)
    CheckDocImages(Value)
    Streams = tuple(EmitDocSegment(Segment) for Segment in Value.Segments)
    Parts = (
        tuple(EmitBodyPart(BodyValue) for BodyValue in Value.Bodies)
        + tuple(EmitMatPart(Material) for Material in Value.Materials)
        + tuple(EmitSnapPart(Snapshot) for Snapshot in Value.Snapshots)
        + tuple(EmitConfigPart(Configuration) for Configuration in Value.Configurations)
        + EmitSceneParts(Value.Graphics)
        + tuple(EmitMeshPart(MeshValue) for MeshValue in Value.Meshes)
        + tuple(EmitFormPart(FormValue) for FormValue in Value.Forms)
        + Value.Images
    )
    Container = FusionContainer(
        Value.Document,
        Value.Asset,
        Streams,
        Value.Previews,
        Parts,
        Value.EmptyFolders,
        Value.Properties,
        Value.Redirects,
    )
    return EmitContainer(Container)
