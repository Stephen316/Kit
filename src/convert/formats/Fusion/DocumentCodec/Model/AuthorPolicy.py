from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class AuthorPolicy:
    FirstDesignId: int = 1000
    DesignSegmentId: int = 0
    ActSegmentId: int = 1
    ParamBirthday: int = 6
    TimeStamp: int = 0
    SketchGeneration: int = 2
    FirstSketchTag: int = 100
    FirstOperationId: int = 300
    BodyKey: int = 0
    HistoryCurrentId: int = 4
    HistoryInitialId: int = 2
    HistoryCurrentStateId: int = 4
    HistoryNextEntityTag: int = 1
    HistoryBoardStatus: int = 2
    SideFaceLabel: str = "3"
    TopFaceLabel: str = "2"
    BottomFaceLabel: str = "1"
    TopEdgeLabel: str = "-1"
    BodyOccurrenceCount: int = 1
    CurveProgenitorTag: int = 3
    BodyProgenitorTag: int = 4
    HistoryMaxStateId: int | None = None
