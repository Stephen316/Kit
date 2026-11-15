"""Read bounded sketch geometry with the native object map preserved."""

from types import SimpleNamespace

from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KObjectRefKind,
    ReadTag,
)
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from SketchRoot import KGeneration, Require

# only these value dimension subclasses share the observed distance serializer
KDistanceTypes = ("sgPntPntDist", "sgPntPntHorDist", "sgPntPntVertDist")

# local display handles share a serialized empty component with feature dimension handles
KEmptyDimensionComponent = (0,) * 10 + (-1,) * 4 + (0,) * 5 + (KGeneration,)


# inline members and their nested objects must share the restored archive map
class SketchCursor(ArchiveCursor):

    # only a just-allocated inline sketch may take over the enclosing archive map
    @classmethod
    def FromEnclosing(ClassValue, Parent, Offset, ObjectIndex):
        TagValue = ReadTag(Parent.blob, Offset)
        Require(
            TagValue.kind in (KDefinitionKind, KClassRefKind),
            True,
            "inline sketch allocation",
        )
        Require(Parent.position, Offset + TagValue.size, "inline sketch payload start")
        Require(ObjectIndex, Parent.next_index - 1, "latest inline sketch allocation")
        Require(Parent.objects.get(ObjectIndex), "sgSketch", "inline sketch object type")
        return ClassValue(
            Parent.blob,
            SimpleNamespace(
                offset=Offset,
                Counter=Parent.next_index,
                Classes=Parent.classes,
                Objects=Parent.objects,
            ),
            None,
        )

    # each sketch begins with the strictly allocated map from its enclosing part archive
    def __init__(SelfData, BlobValue, Start, ReadSketchObject):
        super().__init__(
            BlobValue,
            Start.offset + ReadTag(BlobValue, Start.offset).size,
            Start.Counter,
            Start.Classes,
            Start.Objects,
        )
        SelfData.NodeNames = {}
        SelfData.Scalars = {}
        SelfData.Dimensions = []
        SelfData.Handles = {}
        SelfData.SketchReferences = {}
        SelfData.PointReferences = {}
        SelfData.ReadSketchObject = ReadSketchObject

    # opaque presentation runs still need bounded lengths before the next pointer
    def AdvanceBytes(SelfData, Width):
        Require(
            0 <= Width <= len(SelfData.BlobValue) - SelfData.Offset,
            True,
            "bounded presentation run",
        )
        SelfData.Offset += Width

    # independent type checks prevent ambiguous archive ownership from yielding geometry
    def ReadObject(SelfData, *Expected):
        TagValue, NameValue, ObjectIndex = SelfData.TakePointer(Expected)
        if TagValue.kind in (KDefinitionKind, KClassRefKind):
            SelfData.ReadPayload(NameValue, ObjectIndex)
        return ObjectIndex

    # typed geometry children need their own guarded layout before cursor advancement
    def ReadPayload(SelfData, NameValue, ObjectIndex):
        if NameValue in ("sgPointHandle", "sgLineHandle"):
            (Index,) = SelfData.ReadValue("<H")
            Require(Index < 0x777F, True, "short sketch handle index width")
            SelfData.Handles[ObjectIndex] = Index, *SelfData.ReadValue("<2i")
        elif NameValue == "sgExtEnt_c":
            Wrapper = SelfData.ReadObject("moSketchExtRef_w")
            SelfData.SketchReferences[ObjectIndex] = SelfData.SketchReferences[Wrapper]
            for _ in range(3):
                SelfData.ReadObject(None)
            SelfData.ReadText()
        elif NameValue == "moSketchExtRef_w":
            Component = SelfData.ReadObject("moCompSketchEntHandle_c")
            SelfData.SketchReferences[ObjectIndex] = SelfData.SketchReferences[
                Component
            ]
            SelfData.ReadRefTail()
            (Flags,) = SelfData.ReadValue("<h")
            Require(-2 <= Flags <= 0, True, "valid external reference mode")
            SelfData.ReadObject(None, "moPointBackedUpData_c")
        elif NameValue == "moCompSketchEntHandle_c":
            SelfData.ReadComponent()
            FeatureId, TimeWord = SelfData.ReadValue("<iI")
            Require(TimeWord < 0xFFFFFFFF, True, "compact feature reference time")
            Entity = SelfData.ReadObject("sgPointHandle", "sgLineHandle")
            SelfData.SketchReferences[ObjectIndex] = {
                "feature_id": FeatureId,
                "feature_time": TimeWord,
                "handle_class": SelfData.Objects[Entity],
                "handle_fields": SelfData.Handles[Entity],
            }
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
    def ReadDimHandle(SelfData, SketchObject=None):
        if SketchObject is None:
            SelfData.ReadComponent()
        else:
            SelfData.ReadObject(None)
            Require(
                SelfData.ReadValue("<20i"),
                KEmptyDimensionComponent,
                "empty display handle component",
            )
        Require(SelfData.ReadValue("<H"), (0,), "absent dimension transform")
        for _ in range(4):
            SelfData.ReadObject(None)
        (Selector,) = SelfData.ReadValue("<B")
        SelfData.ReadObject(None)
        SelfData.ReadObject(None)
        (State,) = SelfData.ReadValue("<i")
        Require(SelfData.ReadValue("<H"), (0,), "absent second dimension transform")
        (Flags,) = SelfData.ReadValue("<i")
        if SketchObject is None:
            SelfData.ReadObject("sgSketch")
        else:
            Require((Selector, State, Flags), (0, -1, 0), "local display handle state")
            _, _, Owner = SelfData.TakePointer(("sgSketch",), KObjectRefKind)
            Require(Owner, SketchObject, "display handle owns its sketch")
        (DimensionSlot,) = SelfData.ReadValue("<i")
        return DimensionSlot

    # the same wrapper branch surrounds both sketch dimension and entity handles
    def ReadRefTail(SelfData):
        SelfData.ReadValue("<H")
        SelfData.ReadObject(None)
        SelfData.ReadValue("<2i")
        Require(SelfData.ReadValue("<2H"), (0, 0), "absent reference transforms")
        SelfData.ReadValue("<11i")

    # distance evidence needs the scalar and both point handles from one owner
    def ReadDistance(SelfData, NameValue):
        DimId, ValueId, _ = SelfData.ReadDimBase("moLengthParameter_c")
        Require(SelfData.ReadValue("<H"), (0,), "absent sgValGDim transform")
        First = SelfData.ReadObject("sgPointHandle")
        Second = SelfData.ReadObject("sgPointHandle")
        SelfData.ReadValue("<4H")
        SelfData.ReadObject(None)  # 3D plane
        SelfData.ReadPoint(3)
        Label, Value = SelfData.Scalars[ValueId]
        SelfData.Dimensions.append((NameValue, DimId, Label, Value, First, Second))

    # the stored flag precedes the alternate name in feature and sketch dimensions
    def ReadDimBaseFields(SelfData, ExpectedParam):
        SelfData.ReadValue("<i")
        ValueId = SelfData.ReadObject(ExpectedParam)
        SelfData.ReadObject(None)  # tolerance
        DimId, _, _, _ = SelfData.ReadValue("<4i")
        SelfData.ReadObject(None)
        (State,) = SelfData.ReadValue("<H")
        Require(SelfData.ReadValue("<B"), (0,), "absent dimension alternate name")
        return DimId, ValueId, State

    # scalar callers need only the common dimension identity and parameter reference
    def ReadDimBasePrefix(SelfData, ExpectedParam):
        DimId, ValueId, _ = SelfData.ReadDimBaseFields(ExpectedParam)
        return DimId, ValueId

    # sketch dimensions append their scalar type after the shared parameter fields
    def ReadDimBase(SelfData, ExpectedParam):
        DimId, ValueId = SelfData.ReadDimBasePrefix(ExpectedParam)
        TypeValue, *_ = SelfData.ReadValue("<i3H")  # sgDim type and scalar fields
        return DimId, ValueId, TypeValue
