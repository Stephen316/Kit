from enum import StrEnum


# the json style contract needs a dedicated boundary so drawing members retain their sheet and model associations
class JsonStyle(StrEnum):
    KCompact = "Compact"
    KSpaced = "Spaced"
