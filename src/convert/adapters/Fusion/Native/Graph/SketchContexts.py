from typing import TypeAlias

from convert.adapters.Fusion.Native.Graph.SketchContext import SketchContext
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext

KSketchContexts: TypeAlias = (  # lgtm[py/unused-global-variable]
    SketchContext | ExtrudeContext
)
