from dataclasses import dataclass as Dataclass

from BossConfigPrefs import DisplayProfile, UnitPreset
from ConfigAnnotations import SavedAnnotationFonts
from ConfigDatums import SavedDatumFonts
from ConfigDetailComposition import ConfigDetail
from ConfigDetailEnd import DetailDescriptions, SavedDetailEnd
from ConfigDetailOpening import (
    DetailOpening,
    PlainCharFormat,
    PointCharFormat,
    UnsetCharFormat,
)
from ConfigDetailStart import DetailDimSettings, DetailNames
from ConfigDimensionStyles import SavedStyleSettings
from ConfigFinishNote import SavedHelperFonts
from ConfigLabels import SavedLabelFonts
from ConfigTables import SavedTableFonts
from ConfigTolerance import SavedToleranceFonts
from ConfigWeld import SavedWeldFonts, WeldFinishFonts
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch


# the ordinary drafting profile uses these five format roles across its existing codecs
@Dataclass(frozen=True, slots=True, kw_only=True)
class DetailFonts:
    Standard: PlainCharFormat
    Plain: PlainCharFormat
    WeldRoot: PlainCharFormat
    Unset: UnsetCharFormat
    PointLabel: PointCharFormat


# each caller selects its drafting text and options while the codec owns the supported defaults
def BuildDetailPrefs(
    *,
    Opening: DetailOpening,
    Names: DetailNames,
    Dimensions: DetailDimSettings,
    Descriptions: DetailDescriptions,
    Fonts: DetailFonts,
    DisplayUnits: UnitPreset,
    PreviousLinear: float,
) -> ConfigDetail:
    Units = DisplayProfile(DisplayUnits)
    RequireArch(PreviousLinear in (0.0, 20.0), True, "known prior linear style value")
    Standard, Plain, Unset = Fonts.Standard, Fonts.Plain, Fonts.Unset
    Finish = WeldFinishFonts(Surface=Unset, Annotation=Unset)
    return ConfigDetail(
        Opening=Opening,
        Names=Names,
        OpeningFont=Standard,
        Dimensions=Dimensions,
        Styles=SavedStyleSettings(
            LengthUnit=Units.Length, LinearPrevious=PreviousLinear, Font=Standard
        ),
        Annotations=SavedAnnotationFonts(
            Standard=Standard, WeldRoot=Fonts.WeldRoot, RevisionCloud=Plain
        ),
        Tables=SavedTableFonts(Member=Plain, Shared=Plain),
        Labels=SavedLabelFonts(
            Label=Standard,
            Auxiliary=Plain,
            Orthographic=Plain,
            Component=Plain,
            Shared=Plain,
        ),
        FinishNote=SavedHelperFonts(
            Finish=Unset, FinishAnnotation=Unset, Note=Unset, NoteAnnotation=Unset
        ),
        Weld=SavedWeldFonts(
            Main=Unset,
            FirstSide=Unset,
            SecondSide=Unset,
            FirstFinish=Finish,
            SecondFinish=Finish,
        ),
        Tolerance=SavedToleranceFonts(Main=Unset, Annotation=Unset),
        End=SavedDetailEnd(
            Datums=SavedDatumFonts(CenterMark=Unset, Feature=Unset, Target=Unset),
            BorderFont=Fonts.PointLabel,
            ZoneFont=Fonts.PointLabel,
            Descriptions=Descriptions,
        ),
    )
