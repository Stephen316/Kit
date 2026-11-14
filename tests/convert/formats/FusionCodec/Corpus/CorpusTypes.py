from typing import TypedDict


class ArchiveSchema(TypedDict):
    MetadataHash: str


class CorpusSchema(TypedDict):
    Profiles: dict[str, ArchiveSchema]
