from typing import TypeVar

# member value must remain consistent across callers so entity identifiers retain their schema and reference meaning
KMemberValue = TypeVar("KMemberValue", covariant=True)
