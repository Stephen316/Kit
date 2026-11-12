# document validation needs a distinct public failure type for callers
class DocumentError(ValueError):
    __slots__ = ()
