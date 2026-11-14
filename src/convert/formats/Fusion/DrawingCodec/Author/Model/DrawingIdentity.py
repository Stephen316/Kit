from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class DrawingIdentity:
    DocumentId: str
    VersionId: str
    AssetId: str
    RevisionId: str
    LinkRole: str
    ComponentGuid: str
    ComponentRevision: str
    InstanceGuid: str
    DrawingToken: str
    DesignToken: str
    DrawingFile: str
    DesignFile: str
