"""Read bounded sketch geometry with the native object map preserved."""

import math as Math
import struct as Struct

from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KNullKind,
    KObjectRefKind,
    ReadString,
    ReadTag,
)
from SketchRoot import KGeneration, Require

# only these value dimension subclasses share the observed distance serializer
KDistanceTypes = ("sgPntPntDist", "sgPntPntHorDist", "sgPntPntVertDist")


# inline members and their nested objects must share the restored archive map
class SketchCursor:

    # each sketch begins with the strictly allocated map from its enclosing part archive
    def __init__(SelfData, BlobValue, Start, ReadSketchObject):
        SelfData.BlobValue = BlobValue
        SelfData.Offset = Start.offset + ReadTag(BlobValue, Start.offset).size
        SelfData.Classes = Start.Classes
        SelfData.Objects = Start.Objects
        SelfData.Objects[0] = None
        SelfData.NextIndex = Start.Counter
        SelfData.NodeNames = {}
        SelfData.Scalars = {}
        SelfData.Dimensions = []
        SelfData.Handles = {}
        SelfData.ReadSketchObject = ReadSketchObject

    # all fields must advance the shared cursor before their children are considered
    def ReadValue(SelfData, Format):
        Value = Struct.unpack_from(Format, SelfData.BlobValue, SelfData.Offset)
        SelfData.Offset += Struct.calcsize(Format)
        return Value

    # opaque presentation runs still need bounded lengths before the next pointer
    def AdvanceBytes(SelfData, Width):
        Require(
            0 <= Width <= len(SelfData.BlobValue) - SelfData.Offset,
            True,
            "bounded presentation run",
        )
        SelfData.Offset += Width

    # untrusted counts must fit before an array traversal starts
    def ReadCount(SelfData):
        (Count,) = SelfData.ReadValue("<i")
        if Count < 0 or Count > (len(SelfData.BlobValue) - SelfData.Offset) // 2:
            raise ValueError(f"Invalid count {Count} before {SelfData.Offset}")
        return Count

    # parameter names use the same string framing as the ordinary archive reader
    def ReadText(SelfData):
        Value, Width = ReadString(SelfData.BlobValue, SelfData.Offset)
        SelfData.Offset += Width
        return Value

    # nonfinite geometry must never qualify as measured research evidence
    def ReadPoint(SelfData, Dimension):
        Coords = SelfData.ReadValue("<" + "d" * Dimension)
        if not all(map(Math.isfinite, Coords)):
            raise ValueError(f"Nonfinite point coordinate before {SelfData.Offset}")
        return Coords

    # independent type checks prevent ambiguous archive ownership from yielding geometry
    def ReadObject(SelfData, *Expected):
        TagValue, NameValue, ObjectIndex = SelfData.TakePointer(Expected)
        if TagValue.kind in (KDefinitionKind, KClassRefKind):
            SelfData.ReadPayload(NameValue, ObjectIndex)
        return ObjectIndex

    # display evidence and geometry must use one allocation rule for the same archive
    def TakePointer(SelfData, Expected, KindValue=None):
        Offset = SelfData.Offset
        TagValue = ReadTag(SelfData.BlobValue, Offset)
        if KindValue is not None:
            Require(TagValue.kind, KindValue, f"archive tag kind at {Offset}")
        NameValue = SelfData.FindType(TagValue)
        Require(
            NameValue in Expected,
            True,
            f"typed archive pointer at {Offset} ({NameValue})",
        )
        SelfData.Offset += TagValue.size
        ObjectIndex = TagValue.index
        if TagValue.kind == KDefinitionKind:
            SelfData.Classes[SelfData.NextIndex] = NameValue
            SelfData.NextIndex += 1
        if TagValue.kind in (KDefinitionKind, KClassRefKind):
            ObjectIndex = SelfData.NextIndex
            SelfData.Objects[ObjectIndex] = NameValue
            SelfData.NextIndex += 1
        return TagValue, NameValue, ObjectIndex

    # reference tokens must resolve the correct kind before a caller can use them
    def FindType(SelfData, TagValue):
        if TagValue.kind == KDefinitionKind:
            Require(TagValue.schema, 1, f"archive schema at {SelfData.Offset}")
            return TagValue.class_name
        if TagValue.kind == KClassRefKind and TagValue.index in SelfData.Classes:
            return SelfData.Classes[TagValue.index]
        if (
            TagValue.kind == KObjectRefKind
            and TagValue.index in SelfData.Objects
            and TagValue.index != 0
        ):
            return SelfData.Objects[TagValue.index]
        if TagValue.kind == KNullKind:
            return None
        raise ValueError(
            f"Unallocated {TagValue.kind} {TagValue.index} at {SelfData.Offset}"
        )

    # typed geometry children need their own guarded layout before cursor advancement
    def ReadPayload(SelfData, NameValue, ObjectIndex):
        if NameValue in ("sgPointHandle", "sgLineHandle"):
            (Index,) = SelfData.ReadValue("<H")
            Require(Index < 0x777F, True, "short sketch handle index width")
            SelfData.Handles[ObjectIndex] = Index, *SelfData.ReadValue("<2i")
        elif NameValue == "sgExtEnt_c":
            SelfData.ReadObject("moSketchExtRef_w")
            for _ in range(3):
                SelfData.ReadObject(None)
            SelfData.ReadText()
        elif NameValue == "moSketchExtRef_w":
            SelfData.ReadObject("moCompSketchEntHandle_c")
            SelfData.ReadRefTail()
            (Flags,) = SelfData.ReadValue("<h")
            Require(-2 <= Flags <= 0, True, "valid external reference mode")
            SelfData.ReadObject(None, "moPointBackedUpData_c")
        elif NameValue == "moCompSketchEntHandle_c":
            SelfData.ReadComponent()
            _, TimeWord = SelfData.ReadValue("<iI")
            Require(TimeWord < 0xFFFFFFFF, True, "compact feature reference time")
            SelfData.ReadObject("sgPointHandle", "sgLineHandle")
            SelfData.ReadValue("<I")
        elif NameValue == "moUnitComponent_c":
            SelfData.ReadObject("moPart_c")
            Require(
                SelfData.ReadValue("<B"), (0,), "absent unit component external owner"
            )
        elif NameValue == "moPointBackedUpData_c":
            SelfData.ReadPoint(3)
        elif NameValue == "moNodeName_c":
            SelfData.NodeNames[ObjectIndex] = SelfData.ReadText()
        elif NameValue == "moLengthParameter_c":
            NameIndex = SelfData.ReadObject("moNodeName_c")
            SelfData.ReadValue("<4i")
            SelfData.ReadText()
            SelfData.ReadObject(None)
            (Value,) = SelfData.ReadPoint(1)
            Require(SelfData.ReadValue("<B"), (0,), "absent native length override")
            SelfData.Scalars[ObjectIndex] = SelfData.NodeNames[NameIndex], Value
        elif NameValue in KDistanceTypes:
            SelfData.ReadDistance(NameValue)
        else:
            SelfData.ReadRelation(NameValue, ObjectIndex)

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

    # both native handles reconstruct the same local part ownership before binding geometry
    def ReadComponent(SelfData):
        SelfData.ReadObject("moUnitComponent_c")
        Words = SelfData.ReadValue("<20I")
        Require(Words[-1], KGeneration, "native component-reference generation")
        Require(
            tuple(Words[Index] for Index in (6, 14, 15, 16, 17, 18)),
            (0,) * 6,
            "absent native component extras",
        )

    # the next sketch allocation lives inside the active local dimension handle
    def ReadDimHandle(SelfData):
        SelfData.ReadComponent()
        Require(SelfData.ReadValue("<H"), (0,), "absent dimension transform")
        for _ in range(4):
            SelfData.ReadObject(None)
        SelfData.ReadValue("<B")
        SelfData.ReadObject(None)
        SelfData.ReadObject(None)
        SelfData.ReadValue("<i")
        Require(SelfData.ReadValue("<H"), (0,), "absent second dimension transform")
        SelfData.ReadValue("<i")
        SelfData.ReadObject("sgSketch")
        SelfData.ReadValue("<i")

    # the same wrapper branch surrounds both sketch dimension and entity handles
    def ReadRefTail(SelfData):
        SelfData.ReadValue("<H")
        SelfData.ReadObject(None)
        SelfData.ReadValue("<2i")
        Require(SelfData.ReadValue("<2H"), (0, 0), "absent reference transforms")
        SelfData.ReadValue("<11i")

    # distance evidence needs the scalar and both point handles from one owner
    def ReadDistance(SelfData, NameValue):
        DimId, ValueId = SelfData.ReadDimBase("moLengthParameter_c")
        Require(SelfData.ReadValue("<H"), (0,), "absent sgValGDim transform")
        First = SelfData.ReadObject("sgPointHandle")
        Second = SelfData.ReadObject("sgPointHandle")
        SelfData.ReadValue("<4H")
        SelfData.ReadObject(None)  # 3D plane
        SelfData.ReadPoint(3)
        Label, Value = SelfData.Scalars[ValueId]
        SelfData.Dimensions.append((NameValue, DimId, Label, Value, First, Second))

    # logical and value dimension layouts share one base parameter reference
    def ReadDimBase(SelfData, ExpectedParam):
        SelfData.ReadValue("<i")
        ValueId = SelfData.ReadObject(ExpectedParam)
        SelfData.ReadObject(None)  # tolerance
        DimId, _, _, _ = SelfData.ReadValue("<4i")
        SelfData.ReadObject(None)
        SelfData.ReadValue("<H")
        Require(SelfData.ReadValue("<B"), (0,), "absent dimension alternate name")
        SelfData.ReadValue("<i3H")  # sgDim scalar fields
        return DimId, ValueId
