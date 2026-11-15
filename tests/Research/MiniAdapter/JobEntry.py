from dataclasses import dataclass as DataClass


# the fixture must persist submission identity lease state and terminal outcomes across process calls
@DataClass
class JobEntry:
    RawSpec: dict[str, object]
    KindName: str
    Inputs: dict[str, str]
    Depends: list[str]
    Resources: list[str]
    MaxAttempts: int
    LeaseSeconds: int
    TimeoutSeconds: int
    JobState: str = "queued"
    Attempts: int = 0
    Generation: int = 0
    PrintHash: str = ""
    ClaimHash: str = ""
    TokenHash: str = ""
    LeaseUntil: float = 0.0
    Deadline: float = 0.0
    ResultHash: str = ""
    Reason: str = ""
    Order: int = 0
