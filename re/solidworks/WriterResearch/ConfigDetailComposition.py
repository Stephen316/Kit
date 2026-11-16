from dataclasses import dataclass

from ConfigAnnotations import SavedAnnotationFonts, WriteSavedAnnotations
from ConfigDetailEnd import SavedDetailEnd, WriteSavedDetailEnd
from ConfigDetailOpening import DetailOpening, PlainCharFormat
from ConfigDetailStart import DetailDimSettings, DetailNames, WriteDetailStart
from ConfigDimensionStyles import SavedStyleSettings, WriteSavedDimensionStyles
from ConfigFinishNote import SavedHelperFonts, WriteSavedFinishNote
from ConfigLabels import SavedLabelFonts, WriteSavedLabels
from ConfigTables import SavedTableFonts, WriteSavedTables
from ConfigTolerance import SavedToleranceFonts, WriteSavedTolerance
from ConfigUnits import KLengthClass
from ConfigWeld import SavedWeldFonts, WriteSavedWeld
from PartArchive import PartArchiveWriter
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch


@dataclass(frozen=True, slots=True, kw_only=True)
class ConfigDetail:
    Opening: DetailOpening
    Names: DetailNames
    OpeningFont: PlainCharFormat
    Dimensions: DetailDimSettings
    Styles: SavedStyleSettings
    Annotations: SavedAnnotationFonts
    Tables: SavedTableFonts
    Labels: SavedLabelFonts
    FinishNote: SavedHelperFonts
    Weld: SavedWeldFonts
    Tolerance: SavedToleranceFonts
    End: SavedDetailEnd


def WriteConfigDetail(Writer: PartArchiveWriter, Generation: int, State: ConfigDetail) -> None:
    RequireArch((type(Generation), Generation), (int, KConfigGen), "saved detail generation")
    Before = Writer.Snapshot()
    RequireArch(
        Writer.objects.get(Before.NextIndex - 1),
        "moRelMgr_c",
        "saved detail follows the relation manager",
    )
    RequireArch(KLengthClass in Writer.classes, True, "filed length unit class")

    # all stages append to the enclosing archive and use its actual object slots
    FirstChunk = len(Writer.chunks)
    try:
        WriteDetailStart(
            Writer,
            Generation,
            State.Opening,
            State.Names,
            State.OpeningFont,
            State.Dimensions,
        )
        WriteSavedDimensionStyles(Writer, Generation, State.Styles)
        WriteSavedAnnotations(Writer, Generation, State.Annotations)
        WriteSavedTables(Writer, Generation, State.Tables)
        WriteSavedLabels(Writer, Generation, State.Labels)
        WriteSavedFinishNote(Writer, Generation, State.FinishNote)
        WriteSavedWeld(Writer, Generation, State.Weld)
        WriteSavedTolerance(Writer, Generation, State.Tolerance)
        WriteSavedDetailEnd(Writer, Generation, State.End)
    except Exception:
        del Writer.chunks[FirstChunk:]
        Writer.classes.clear()
        Writer.classes.update((Name, Index) for Index, Name in Before.Classes)
        Writer.objects.clear()
        Writer.objects.update(Before.Objects)
        Writer.SetNextIndex(Before.NextIndex)
        raise
