from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class SegmentStreams:
    SegmentId: int
    Metadata: bytes
    BulkData: bytes
