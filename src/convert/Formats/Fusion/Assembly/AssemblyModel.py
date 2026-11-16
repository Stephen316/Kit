from dataclasses import dataclass as Dataclass

from convert.Formats.Fusion.Assembly.NativeComponent import NativeComponent
from convert.Formats.Fusion.Assembly.NativeOccurrence import NativeOccur


# the root placement stays available separately from local child occurrences
@Dataclass(frozen=True, slots=True)
class NativeAssembly:
    RootComponentId: int
    RootTransform: tuple[float, ...]
    Components: tuple[NativeComponent, ...]
    Occurrences: tuple[NativeOccur, ...]
