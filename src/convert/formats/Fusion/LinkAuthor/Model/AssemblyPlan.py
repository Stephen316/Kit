from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.LinkAuthor.Model.ActionKeys import ActionKeys
from convert.formats.Fusion.LinkAuthor.Model.LinkKeys import LinkKeys
from convert.formats.Fusion.LinkAuthor.Model.PlaceKeys import PlaceKeys


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
