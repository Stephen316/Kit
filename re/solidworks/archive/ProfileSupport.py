"""Keep positional evidence reports on the packaged cut profile reader."""

from convert.adapters.solidworks.container.Archive import KObjectRefKind
from convert.adapters.solidworks.resolved.ContourChain import ReadChain as read_chain
from convert.adapters.solidworks.resolved.cut.CutProfileBody import ReadCutBody as read_profile_body


def read_profile_support(cursor):
    _, _, sketch = cursor.TakePointer(("sgSketch",), KObjectRefKind, CompactOnly=True)
    return read_profile_body(cursor, sketch)
