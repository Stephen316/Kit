from typing import TypedDict


# the archive schema boundary needs grouped coverage so repository automation cannot silently change its observable contract
class ArchiveSchema(TypedDict):
    MetadataHash: str


# the corpus schema boundary needs grouped coverage so repository automation cannot silently change its observable contract
class CorpusSchema(TypedDict):
    Profiles: dict[str, ArchiveSchema]
