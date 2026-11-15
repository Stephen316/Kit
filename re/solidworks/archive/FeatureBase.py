"""Read the common modern SOLIDWORKS feature base."""

from functools import partial

from convert.adapters.solidworks.config.FeatureBase import ReadFeatBase
from convert.adapters.solidworks.container.Archive import ReadString
from SketchRoot import Require


# empty labels keep the replay on the witnessed ordinary feature layout
def read_empty_label(cursor):
    name, width = ReadString(cursor.blob, cursor.position)
    Require(name, "", "empty feature label")
    cursor.position += width
    return name


# both embedded planes and named nodes need the same modern feature base framing
def read_feature_base(cursor):
    ReadFeatBase(cursor.read, cursor.vector, cursor.null, partial(read_empty_label, cursor))
