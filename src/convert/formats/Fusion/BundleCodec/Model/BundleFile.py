from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class BundleFile:
    FileName: str
    DataValue: bytes
