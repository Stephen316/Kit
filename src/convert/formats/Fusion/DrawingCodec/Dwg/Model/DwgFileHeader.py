from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class DwgFileHeader:
    VersionText: str
    PaddingBytes: bytes
    MaintenanceVersion: int
    HeaderMarker: int
    PreviewAddress: int
    AppVersion: int
    AppMaintenance: int
    CodePage: int
    ReservedTriple: bytes
    SecurityFlags: int
    ReservedAddress: int
    SummaryAddress: int
    VbaAddress: int
    CryptAddress: int
    AppInfoAddress: int
    AppHistoryAddress: int
    TrailingWords: tuple[int, ...]
