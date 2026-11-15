from convert.formats.Fusion.DocumentCodec.Auxiliary.Mesh.CheckMeshMaps import (
    CheckMeshMaps,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Mesh.CheckMeshRefs import (
    CheckMeshRefs,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel


# invalid doc meshes input must fail here so supporting records retain their owning document relationships
def CheckDocMeshes(Value: DocumentModel) -> None:
    Records = tuple(
        Record
        for Segment in Value.Segments
        if Segment.Metadata.Header.SegmentId == 0
        for Record in Segment.Records
    )
    CheckMeshMaps(Records)
    CheckMeshRefs(Records, Value.Meshes)
