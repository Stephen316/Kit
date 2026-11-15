from dataclasses import dataclass as MakeDataClass


# original wire coordinates keep a journal revision addressable inside its source member
@MakeDataClass(frozen=True, slots=True)
class AsmLocation:
    StartOffset: int
    EndOffset: int
