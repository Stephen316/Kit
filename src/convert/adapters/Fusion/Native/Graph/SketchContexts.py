from typing import TypeAlias

from convert.adapters.Fusion.Native.Graph.SketchContext import SketchContext
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext

# the sketch contexts variants need one shared contract so native adapter translation cannot omit a supported value shape
KSketchContexts: TypeAlias = (  # lgtm[py/unused-global-variable]
    SketchContext | ExtrudeContext
)
