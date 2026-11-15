"""Add the witnessed equation records to the shared native sketch reader."""

from types import SimpleNamespace

from convert.adapters.solidworks.container.Archive import ReadTag
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.container.LocalFrame import ReadLocalPart
from convert.adapters.solidworks.sketch.Cursor import SketchArchive
from convert.adapters.solidworks.sketch.DimFields import ReadDimBase, ReadDimFields
from convert.adapters.solidworks.sketch.DimHandle import ReadDimRoute, ReadRefTail
from convert.adapters.solidworks.sketch.InlineSketch import CheckInline
from convert.adapters.solidworks.sketch.Objects import KSketchTypes
from SketchRoot import KGeneration, Require


# the active relation reader retains its nested sketch callback
class SketchCursor(SketchArchive):
    def __init__(self, blob, start, read_sketch_object):
        offset = start.offset + ReadTag(blob, start.offset).size
        super().__init__(ArchiveCursor(blob, offset, start.Counter, start.Classes, start.Objects))
        self.ReadSketchObject = read_sketch_object

    @classmethod
    def FromEnclosing(cls, parent, offset, object_index):
        CheckInline(parent, offset, object_index)
        start = SimpleNamespace(offset=offset, Counter=parent.NextIndex, Classes=parent.Classes, Objects=parent.Objects)
        return cls(parent.BlobValue, start, None)

    def ReadPayload(self, name, object_index):
        if name in KSketchTypes:
            super().ReadPayload(name, object_index)
        else:
            self.ReadRelation(name, object_index)

    ReadDimBase = ReadDimBase
    ReadRefTail = ReadRefTail

    def ReadDimBasePrefix(self, expected):
        dimension, parameter, _ = ReadDimFields(self, expected)
        return dimension, parameter

    # equation handles materialize the sketch after the common dimension route
    def ReadDimHandle(self):
        ReadLocalPart(self, KGeneration)
        ReadDimRoute(self)
        self.ReadObject("sgSketch")
        (slot,) = self.ReadInts("<i")
        return slot

    # equation side objects preserve parent references before the next sketch begins
    def ReadRelation(SelfData, NameValue, ObjectIndex):
        if NameValue == "moRelEquationSide_c":
            SelfData.ReadEqSide()
        elif NameValue in ("moRelOperator_c", "moRelValue_c"):
            SelfData.ReadText()
            SelfData.ReadValue("<4i")
        elif NameValue == "moRelation_c":
            SelfData.ReadText()
            SelfData.ReadValue("<Hi")
            for _ in range(2):
                SelfData.ReadObject("moRelEquationSide_c")
            SelfData.ReadRelationTail()
        elif NameValue == "moRelDimension_c":
            Require(SelfData.ReadValue("<H"), (0,), "empty dimension operand list")
            SelfData.ReadObject(None)
            SelfData.ReadObject("moDimRefWrapper_c")
            SelfData.ReadText()
            SelfData.ReadValue("<4i")
        elif NameValue == "moDimRefWrapper_c":
            SelfData.ReadPoint(1)
            SelfData.ReadObject("moSkDimHandleValG2_c")
            SelfData.ReadRefTail()
        elif NameValue == "moSkDimHandleValG2_c":
            SelfData.ReadDimHandle()
        elif NameValue == "sgSketch":
            SelfData.ReadSketchObject(SelfData, ObjectIndex)
        else:
            raise ValueError(
                f"Unsupported materialization of {NameValue} at {SelfData.Offset}"
            )

    # the ordinary equation side needs the live relation map for its back reference
    def ReadEqSide(SelfData):
        (OperandCount,) = SelfData.ReadValue("<H")
        Require(
            OperandCount <= (len(SelfData.BlobValue) - SelfData.Offset) // 2,
            True,
            "valid relation operand count",
        )
        for _ in range(OperandCount):
            SelfData.ReadObject("moRelOperator_c", "moRelDimension_c", "moRelValue_c")
        SelfData.ReadEqSideTail()

    # the first sketch returns inside an equation side opened by the root walker
    def ReadEqSideTail(SelfData):
        SelfData.ReadText()
        SelfData.ReadValue("<2i")
        SelfData.ReadObject("moRelation_c")

    # modern relations keep an independently framed name between their scalars
    def ReadRelationTail(SelfData):
        SelfData.ReadValue("<2i")
        SelfData.ReadText()
        SelfData.ReadValue("<3i")
