"""Adapt the packaged support decoder to the established research report."""

from convert.adapters.solidworks.Resolved.PlaneAtom import ReadAtomMaps as read_partition_tail
from convert.adapters.solidworks.Resolved.Support.SupportPlane import ReadFaceSupport
from FeatureBase import read_feature_base
from SketchRoot import KGeneration


# the existing reports keep their previous prefix structure
def read_reference_plane(cursor, context):
    result = ReadFaceSupport(cursor, KGeneration, context)
    result.pop("offset")
    return result
