from dataclasses import dataclass as MakeDataClass


# bundle file needs an explicit state contract so linked archive members retain their document relationships
@MakeDataClass(frozen=True, slots=True)
class BundleFile:
    FileName: str
    DataValue: bytes
