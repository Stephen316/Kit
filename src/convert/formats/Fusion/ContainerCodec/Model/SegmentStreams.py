from dataclasses import dataclass as MakeDataClass


# segment streams needs an explicit state contract so archive members retain their native ownership and reference relationships
@MakeDataClass(frozen=True, slots=True)
class SegmentStreams:
    SegmentId: int
    Metadata: bytes
    BulkData: bytes
