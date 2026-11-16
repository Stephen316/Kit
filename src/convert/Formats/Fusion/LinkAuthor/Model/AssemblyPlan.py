from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.LinkAuthor.Model.ActionKeys import ActionKeys
from convert.Formats.Fusion.LinkAuthor.Model.LinkKeys import LinkKeys
from convert.Formats.Fusion.LinkAuthor.Model.PlaceKeys import PlaceKeys


# assembly plan needs an explicit state contract so cross document references retain their intended ownership
@MakeDataClass(frozen=True, slots=True)
class AssemblyPlan:
    XRefId: int
    Places: tuple[PlaceKeys, ...]
    Pins: tuple[ActionKeys | None, ...]
    Joint: ActionKeys | None
    Links: tuple[LinkKeys, ...]
    DesignNext: int
    ActNext: int
    BrowserNext: int
    FeatureNext: int
    InstanceNext: int
