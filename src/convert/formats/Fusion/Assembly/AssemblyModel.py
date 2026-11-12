from dataclasses import dataclass as Dataclass

from convert.formats.Fusion.Assembly.NativeComponent import NativeComponent
from convert.formats.Fusion.Assembly.NativeOccurrence import NativeOccur


# the root placement stays available separately from local child occurrences
@Dataclass(frozen=True, slots=True)
class NativeAssembly:
    RootComponentId: int
    RootTransform: tuple[float, ...]
    Components: tuple[NativeComponent, ...]
    Occurrences: tuple[NativeOccur, ...]
