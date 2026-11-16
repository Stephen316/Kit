"""Use the packaged ordinary configuration map for rectangular research reports."""

from ArchiveVersion import KApplicationBuild
from SketchRoot import Require
from convert.adapters.solidworks.Config.OrdinaryMap import ReadOrdinaryMap
from convert.adapters.solidworks.Config.RootLayout import KConfigGen


# independent capture evidence still requires the witnessed application build
def read_rectangle_configuration(blob, build):
    Require(build, KApplicationBuild, "witnessed rectangular model build")
    return ReadOrdinaryMap(blob, KConfigGen)
