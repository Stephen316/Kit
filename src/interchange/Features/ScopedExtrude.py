from dataclasses import dataclass as MakeDataClass
from typing import Literal, cast as CastValue

from interchange.Features.FeatureContract import FeatureDef
from interchange.Features.FeatureExtrude import ExtrudeFeature


# scoped features preserve authored selection independently of the result at this rebuild
@MakeDataClass(frozen=True, slots=True)
class ScopedExtrude(FeatureDef):
    Extrusion: ExtrudeFeature
    ScopeMode: Literal["all_applicable", "explicit"]
    SelectedBodyIds: tuple[str, ...]
    AffectedBodyIds: tuple[str, ...]

    # malformed scope records must fail before a writer can mistake them for an ordinary extrusion
    def __post_init__(self) -> None:
        if not isinstance(CastValue(object, self.Extrusion), ExtrudeFeature):
            raise ValueError("scoped extrusion requires an extrusion definition")
        for BodyIds in (self.SelectedBodyIds, self.AffectedBodyIds):
            if not isinstance(CastValue(object, BodyIds), tuple) or not all(
                isinstance(CastValue(object, Identity), str) and Identity.strip()
                for Identity in BodyIds
            ):
                raise ValueError("scope body IDs must be a tuple of nonempty text")
            if len(set(BodyIds)) != len(BodyIds):
                raise ValueError("scope body IDs must be distinct within each list")
        ScopeMode = CastValue(object, self.ScopeMode)
        if ScopeMode == "all_applicable":
            if self.SelectedBodyIds:
                raise ValueError("all-applicable scope cannot carry explicit body IDs")
        elif ScopeMode != "explicit" or not self.SelectedBodyIds:
            raise ValueError("explicit scope requires selected body IDs")
        elif not set(self.AffectedBodyIds) <= set(self.SelectedBodyIds):
            raise ValueError("explicit scope affected bodies must be selected")
