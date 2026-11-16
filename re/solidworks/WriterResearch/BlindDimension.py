from dataclasses import dataclass as DataClass
from math import hypot as Hypot, isclose as IsClose, isfinite as IsFinite
from struct import pack as PackFields
from typing import TypeAlias

from BlindDepth import DepthClasses, DepthFields, WriteDepthMut
from DisplayHandle import KHandleClass, RequireScope
from convert.adapters.solidworks.Container.Archive import KMaxMapIndex, EncodeNull
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Definition import ArchiveWriter
from convert.adapters.solidworks.Container.PlaneBasis import KUnitRows
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector

# the feature handle owns the ordinary parallel plane distance subclass
KClassName = "ParallelPlaneDistanceDim_c"

# the first owned distance class uses the ordinary schema in the part archive
KClassSchema = 1

# the saved model reference count stays distinct from its archive map occurrences
KRetainCount = 2

# two child class references each allocate one object in the enclosing archive map
KDepthClasses = ("moLengthParameter_c", "moNodeName_c")

# the dimension serializer explicitly stores its reference points vectors and pose
KGeometryFormat = "<9dH6dHB13dBH"

# an absent third reference leaves the default point at the model origin
KOrigin = (0.0, 0.0, 0.0)

# dimension placement and direction each require exactly three coordinate values
KTriple: TypeAlias = tuple[float, float, float]


# the selected reference frame and extrusion direction come from separate inputs
@DataClass(frozen=True, slots=True)
class DimGeometry:
    Frame: Transform
    Normal: SpaceVector
    Tangent: SpaceVector
    Reverse: bool


# reading neutral vectors by name retains their coordinate order on the native wire
def Axes(Vector: SpaceVector) -> KTriple:
    return (float(Vector.x), float(Vector.y), float(Vector.z))


# the inverse placement projects the selected model anchor onto each frame axis
def DotProduct(First: KTriple, Second: KTriple) -> float:
    return sum(A * B for A, B in zip(First, Second, strict=True))


# a rigid frame can be inverted directly when its stored basis is right handed
def RequireFrame(Basis: tuple[KTriple, KTriple, KTriple]) -> None:
    First, Second, Third = Basis
    CrossValue = (
        First[1] * Second[2] - First[2] * Second[1],
        First[2] * Second[0] - First[0] * Second[2],
        First[0] * Second[1] - First[1] * Second[0],
    )
    RequireArch(
        all(IsClose(Hypot(*Axis), 1.0, abs_tol=1e-9, rel_tol=0.0) for Axis in Basis)
        and all(
            IsClose(A, B, abs_tol=1e-9, rel_tol=0.0)
            for A, B in zip(CrossValue, Third, strict=True)
        ),
        True,
        "rigid dimension reference frame",
    )


# the native reference uses the inverse frame and the signed distance between planes
def EmitGeometry(Geometry: DimGeometry, DepthMetres: float) -> bytes:
    Frame = Geometry.Frame
    Basis = Axes(Frame.x_axis), Axes(Frame.y_axis), Axes(Frame.z_axis)
    RequireFrame(Basis)
    # Native point application takes matrix columns for each output coordinate.
    SavedRows = tuple(Value for Row in zip(*Basis, strict=True) for Value in Row)
    RequireArch(SavedRows != KUnitRows, True, "explicit dimension pose matrix")
    RequireArch(type(Geometry.Reverse), bool, "explicit extrusion reversal")
    XValue, YValue, ZValue = Axes(Frame.origin)
    Anchor = XValue / 1000, YValue / 1000, ZValue / 1000
    Normal, Tangent = Axes(Geometry.Normal), Axes(Geometry.Tangent)
    RequireArch(
        IsClose(Hypot(*Normal), 1.0, abs_tol=1e-9, rel_tol=0.0)
        and IsClose(Hypot(*Tangent), 1.0, abs_tol=1e-9, rel_tol=0.0)
        and IsClose(DotProduct(Normal, Tangent), 0.0, abs_tol=1e-9, rel_tol=0.0),
        True,
        "orthogonal unit dimension reference vectors",
    )
    SignValue = -1.0 if Geometry.Reverse else 1.0
    Direction = tuple(SignValue * Value for Value in Normal)
    Endpoint = tuple(
        A + DepthMetres * B for A, B in zip(Anchor, Direction, strict=True)
    )
    Translation = tuple(-DotProduct(Axis, Anchor) + 0.0 for Axis in Basis)
    RequireArch(
        Endpoint != Anchor
        and all(IsFinite(Value) for Value in (*Anchor, *Endpoint, *Translation)),
        True,
        "finite distinct parallel plane reference points",
    )
    return PackFields(
        KGeometryFormat,
        *Anchor,
        *Endpoint,
        *KOrigin,
        1,
        *Direction,
        *Tangent,
        1,
        1,
        *SavedRows,
        *Translation,
        1.0,
        0,
        0,
    )


# one named driving length and an explicit model identity define the owned distance child
def WriteDistMut(
    Writer: ArchiveWriter,
    *,
    Generation: int,
    ConditionOne: bool,
    DimensionId: int,
    RetainCount: int,
    NameValue: str,
    DepthMm: float,
    Geometry: DimGeometry,
) -> int:
    NextIndex = Writer.next_index
    RequireScope(Generation, ConditionOne, NextIndex)
    RequireArch(
        (type(RetainCount), RetainCount),
        (int, KRetainCount),
        "witnessed dimension retain count",
    )
    RequireArch(
        type(DimensionId) is int and 0 <= DimensionId <= 0x7FFFFFFF,
        True,
        "allocated dimension identity",
    )
    RequireArch(KClassName in Writer.classes, False, "first parallel distance class")
    RequireArch(
        Writer.classes.get(KHandleClass), NextIndex - 2, "adjacent feature handle"
    )
    RequireArch(
        NextIndex + 3 <= KMaxMapIndex
        and all(
            0 < Writer.classes.get(ClassName, 0) < NextIndex - 2
            for ClassName in KDepthClasses
        ),
        True,
        "depth child archive allocations",
    )
    _ = DepthClasses(Writer.classes)
    NameBytes, ValueBytes = DepthFields(NameValue, DepthMm)
    NullValue = EncodeNull()
    BodyValue = (
        NullValue  # dimension tolerance
        + PackFields("<4i", DimensionId, 0, 0, 0)
        + NullValue  # attachment point
        + PackFields("<HB", 0, 0)  # driven state and alternate name presence
        + EmitGeometry(Geometry, DepthMm / 1000)
    )
    Writer.begin_object(KClassName, KClassSchema)
    Writer.i32(RetainCount)
    WriteDepthMut(Writer, NameBytes, ValueBytes)
    Writer.raw(BodyValue)
    return NextIndex + 1
