from dataclasses import replace as Replace
from typing import Literal
from uuid import UUID

from BossOwners import ConfigPrefs
from CmgrVisualPrefix import CmgrVisualFields, RequireVisualFields
from ConfigDetailComposition import ConfigDetail
from ConfigEnvironment import ConfigEnvironment
from ConfigMaterial import RequireDensity
from ConfigModelOptions import ConfigModelOptions
from ConfigModelView import ConfigModelView, RequireView
from ConfigScene.ModelLists import PartMarker
from ConfigSectionHatch import RequireHatch, SectionHatch
from ConfigUnitFields import (
    KDisplayProfiles,
    ConfigUnitState,
    RequireUnitState,
    UnitDisplay,
)
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import ArchiveError
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

UnitPreset = Literal["metric", "inch"]

# each witnessed display profile supplies its coupled length and system selectors
KDisplayPresets = dict(zip(("metric", "inch"), KDisplayProfiles, strict=True))

# the model constructor initializes length scale and tolerance independently of display units
KModelScale = 1000.0
KLengthTolerance = 1e-8


# this lookup also serves the independently owned drafting length format
def DisplayProfile(Preset: UnitPreset) -> UnitDisplay:
    Display = KDisplayPresets.get(Preset)
    if Display is None:
        raise ArchiveError(
            "ordinary boss supports the known metric and inch display profiles"
        )
    return Display


# the initial formatter state is separate from the document display choice
def PartUnits(Preset: UnitPreset, PreviousLength: float) -> ConfigUnitState:
    Units = ConfigUnitState(DisplayProfile(Preset), PreviousLength)
    RequireUnitState(KConfigGen, Units)
    return Units


# drafting and environment provider preferences remain explicit while shared length units follow one choice
def BuildConfigPrefs(
    *,
    Title: str,
    DisplayUnits: UnitPreset,
    PreviousLength: float,
    ShowMissingReferences: bool,
    Visual: CmgrVisualFields,
    View: ConfigModelView,
    Hatch: SectionHatch,
    DensityKgM3: float,
    Detail: ConfigDetail,
    Environment: ConfigEnvironment,
    BlockIdentity: UUID,
    Marker: PartMarker,
) -> ConfigPrefs:
    Units = PartUnits(DisplayUnits, PreviousLength)
    RequireArch(
        type(ShowMissingReferences), bool, "explicit missing-reference preference"
    )
    RequireVisualFields(KConfigGen, Visual)
    RequireView(View)
    RequireHatch(Hatch)
    RequireDensity(DensityKgM3)
    return ConfigPrefs(
        Title=Title,
        Visual=Visual,
        Units=Units,
        View=View,
        Options=ConfigModelOptions(
            KModelScale, KLengthTolerance, int(ShowMissingReferences)
        ),
        Hatch=Hatch,
        DensityKgM3=DensityKgM3,
        Detail=Replace(
            Detail, Styles=Replace(Detail.Styles, LengthUnit=Units.Display.Length)
        ),
        Environment=Environment,
        BlockIdentity=BlockIdentity,
        Marker=Marker,
    )
