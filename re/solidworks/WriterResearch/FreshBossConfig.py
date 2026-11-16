from uuid import UUID

from BossConfigPrefs import BuildConfigPrefs, UnitPreset
from BossDetailPrefs import BuildDetailPrefs, DetailFonts
from BossOwners import ConfigPrefs
from CmgrInherited import ArchiveFeature
from CmgrVisualPrefix import CmgrVisualFields
from ConfigDetailComposition import ConfigDetail
from ConfigDetailEnd import DetailDescriptions
from ConfigDetailOpening import (
    DetailOpening,
    DetailPrecision,
    PlainCharFormat,
    PointCharFormat,
    UnsetCharFormat,
)
from ConfigDetailStart import DetailDimSettings, DetailNames
from ConfigEnvironment import ConfigEnvironment, SceneLight
from ConfigModelView import ConfigModelView, CurvatureView, PlaneView
from ConfigScene.ModelLists import PartMarker
from ConfigSectionHatch import SectionHatch
from convert.adapters.solidworks.Container.Cmgr import Stamp


# independent fixture choices keep the generated archive test separate from saved preferences
def FixtureDetail(Units: UnitPreset) -> ConfigDetail:
    Font = PlainCharFormat(Face="Arial", Height=0.0035, LineSpacing=0.0)
    return BuildDetailPrefs(
        Opening=DetailOpening(
            CenterMarkSize=0.003,
            CenterMarkUseLines=True,
            UseTableTemplateSettings=True,
            DisplayGraphicBodiesInDrawingViews=True,
            CenterLineUseCenterline=True,
            VirtualSharpType=2,
            CenterLineDistance=0.0025,
            AutoCenterMarkHoles=True,
            AutoInsertCenterLine=False,
            AutoUpdateBom=True,
            AutoDesignIntent=False,
            CenterMarkUseCenterLine=True,
            UseNewCThreadDisplay=False,
            Linear=DetailPrecision(Digits=(2, 3, 4), Tolerances=(1e-5, 2e-5, 1e-6)),
            Angular=DetailPrecision(Digits=(2, 3, 4), Tolerances=(2e-4, 1e-4, 5e-5)),
        ),
        Names=DetailNames(
            MicrometreSuffix="\u00b5m",
            StatusLabels=(
                "Description",
                "High Priority",
                "Low Priority",
                "Complete",
                "Reminder",
            ),
        ),
        Dimensions=DetailDimSettings(
            ArrowsOut=2, SmartArrows=True, AddParentheses=False
        ),
        Descriptions=DetailDescriptions(
            SolidBodies=("Plate,", "", "x", "x"),
            SheetMetal="Sheet",
            CutListTemplates=(
                "%Description%",
                "%MATERIAL%",
                "%Description%, %MATERIAL%",
            ),
        ),
        Fonts=DetailFonts(
            Standard=PlainCharFormat(
                Face=Font.Face, Height=Font.Height, LineSpacing=0.001
            ),
            Plain=Font,
            WeldRoot=PlainCharFormat(Face=Font.Face, Height=0.00212, LineSpacing=0),
            Unset=UnsetCharFormat(Face="Segoe UI"),
            PointLabel=PointCharFormat(Face=Font.Face, Points=12),
        ),
        DisplayUnits=Units,
        PreviousLinear=0.0,
    )


# the light provider values are explicit independent inputs for this fixture
def FixtureLights() -> ConfigEnvironment:
    Feature = ArchiveFeature(111, 19000, 2026225, Stamp(1, 2))
    Lights = (
        SceneLight(Feature, (0.25, 0.5, 0.75), None),
        SceneLight(Feature, (0.1, 0.2, 0.3), (1.0, 0.0, 0.0)),
        SceneLight(Feature, (0.1, 0.2, 0.3), (0.0, 1.0, 0.0)),
        SceneLight(Feature, (0.1, 0.2, 0.3), (0.0, 0.0, 1.0)),
    )
    return ConfigEnvironment(Feature, Lights)


# the hosted stream exercise selects preferences without opening any source archive
def FixtureCfgPrefs(Units: UnitPreset) -> ConfigPrefs:
    return BuildConfigPrefs(
        Title="Ordinary proof",
        DisplayUnits=Units,
        PreviousLength=0.0,
        ShowMissingReferences=True,
        Visual=CmgrVisualFields(
            SurfaceColor=0x305080,
            WireColor=0x404040,
            HiddenLineColor=0xA0A0A0,
            MaterialName="Steel",
            AppearanceId=99,
            MaterialColor=0x305080,
            NativeAssetPath=r"C:\Design\data\graphics\materials\color.p2m",
            MappingMode=3,
            BumpStrength=0.001,
            DisplacementDistance=0.001,
            UsesNormalMap=True,
            UsesDefaultAppearance=True,
        ),
        View=ConfigModelView(None, PlaneView(1, 1, 0x556677, 0x778899, 50, 0x334455)),
        Hatch=SectionHatch("ANSI31", 0.0, 1.0, 0, 0, 1, -1, -1, 0),
        DensityKgM3=1320.0,
        Detail=FixtureDetail(Units),
        Environment=FixtureLights(),
        BlockIdentity=UUID("a4ebaa62-fa1a-421b-ae43-456f550f5b12"),
        Marker=PartMarker(3, 1),
    )
