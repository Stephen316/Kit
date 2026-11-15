"""Read the common modern SOLIDWORKS feature base."""

from convert.adapters.solidworks.container.Archive import ReadString
from SketchRoot import Require


# empty labels keep the replay on the witnessed ordinary feature layout
def read_empty_label(cursor):
    name, width = ReadString(cursor.blob, cursor.position)
    Require(name, "", "empty feature label")
    cursor.position += width


# both embedded planes and named nodes need the same modern feature base framing
def read_feature_base(cursor):
    mode, _, _ = cursor.read("<2iI")
    Require(mode, 0, "ordinary feature mode")
    Require(cursor.read("<B"), (0,), "absent alternate feature label")
    cursor.read("<4i")
    cursor.vector(1)
    cursor.read("<i")
    cursor.null()  # moFolder_c
    read_empty_label(cursor)
    Require(cursor.read("<B"), (0,), "observed editable state")
    cursor.read("<HHBIHhf")  # entity display, style and line width
    cursor.read("<2i")
    cursor.null()  # moFeatComment_c
    cursor.read("<IBB")
    cursor.read("<5iH2i")  # includes the modern feature field at sldmodu+0x9d1bc4
