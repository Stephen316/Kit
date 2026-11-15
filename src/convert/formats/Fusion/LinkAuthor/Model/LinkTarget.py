from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel


# link target needs an explicit state contract so cross document references retain their intended ownership
@MakeDataClass(frozen=True, slots=True)
class LinkTarget:
    DisplayName: str
    LineageUrn: str
    VersionUrn: str
    Target: DocumentModel
