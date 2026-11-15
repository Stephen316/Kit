from typing import Protocol


# nested records need their owner to preserve tracing and the shared allocation map
class PointerReader(Protocol):

    # nullable children and class declarations use the same validated pointer path
    def __call__(
        self,
        KindValue: str,
        NameValue: str | None = None,
        SchemaValue: int = 1,
    ) -> int: ...
