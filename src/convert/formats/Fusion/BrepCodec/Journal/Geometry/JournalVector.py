from typing import TypeAlias

# the journal vector shape must stay shared so journal reconstruction uses one contract for compatible values
KJournalVector: TypeAlias = tuple[float, float, float]
