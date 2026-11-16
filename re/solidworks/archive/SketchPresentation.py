"""Check the witnessed application build before the common presentation read."""

from ArchiveVersion import KApplicationBuild
from convert.adapters.solidworks.Sketch.SketchTail import ReadSketchTail
from SketchRoot import Require


def ReadPresentation(cursor, build_name, geometry):
    Require(build_name, KApplicationBuild, "witnessed sketch presentation build")
    return ReadSketchTail(cursor, geometry)
