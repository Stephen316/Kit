from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel


@MakeDataClass(frozen=True, slots=True)
class LinkTarget:
    DisplayName: str
    LineageUrn: str
    VersionUrn: str
    Target: DocumentModel
