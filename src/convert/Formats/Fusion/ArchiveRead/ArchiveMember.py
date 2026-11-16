from dataclasses import dataclass as MakeDataClass


# detached member facts keep the archive ledger independent of mutable zip objects
@MakeDataClass(frozen=True, slots=True)
class ArchiveMember:
    Name: str
    HeaderOffset: int
    Size: int
    CompressedSize: int
    Method: int
    Crc: int
    Flags: int
    IsDirectory: bool
