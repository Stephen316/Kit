"""Retain the original sketch report while using packaged equation traversal."""

from ArchiveVersion import KApplicationBuild
from SketchRoot import KGeneration, Require
from convert.adapters.solidworks.Config.CutConfig import ReadCutRel
from convert.adapters.solidworks.Sketch.Geometry import KAxisRelations


def ReadSketchConfiguration(BlobValue, BuildName, IncludeCoincidence=False):
    Require(BuildName, KApplicationBuild, "witnessed sketch presentation build")
    Cursor, _, Sketches, _ = ReadCutRel(BlobValue, KGeneration)
    Results = []
    for Sketch in Sketches.values():
        Report = dict(Sketch.SketchData.Geometry)
        if IncludeCoincidence:
            Report["point_coincidences"] = Sketch.SketchData.Coincidences
        Report["body_end"] = Sketch.EndOffset
        Report["map_index_after_body"] = Sketch.NextIndex
        Results.append(Report)
    return Results, Cursor


def ReadSketches(BlobValue, BuildName, IncludeCoincidence=False):
    Sketches, Cursor = ReadSketchConfiguration(BlobValue, BuildName, IncludeCoincidence)
    return Sketches, {"end": Cursor.Offset, "next_map_index": Cursor.NextIndex}
