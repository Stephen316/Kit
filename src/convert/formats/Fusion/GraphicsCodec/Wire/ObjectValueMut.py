from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef
from re import fullmatch as FullMatch
from convert.formats.Fusion.GraphicsCodec.Wire.XferObjectMut import XferObjectMut

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def ObjectValueMut(
    State: SceneCodec, ClassName: str, Value: ObjectRef | None
) -> ObjectRef:
    ObjectId = State.TextValue(Value.ObjectId if Value else None)
    if FullMatch(r"0x[0-9a-fA-F]{1,16}|[0-9A-F]{16}", ObjectId) is None or int(ObjectId, 16) == 0:
        raise ValueError(f"Invalid graphics object identity for {ClassName}: {ObjectId[:64]!r}")
    Result = ObjectRef(ClassName, ObjectId)
    State.CheckResult(Value, Result)
    Existing = State.ObjectKinds.get(ObjectId)
    if Existing is not None:
        if Existing != ClassName:
            raise ValueError("Graphics object identity has conflicting classes")
        return Result
    if State.Depth >= 128 or len(State.ObjectKinds) >= 1000000:
        raise ValueError("Graphics object graph exceeds qualified limits")
    Current = State.InputObjects.get(Result)
    if not State.IsReading and Current is None:
        raise ValueError("Undefined graphics object reference")
    State.ObjectKinds[ObjectId] = ClassName
    Previous = State.ActiveNode
    State.ActiveNode = ObjectId
    State.Depth += 1
    Parsed = XferObjectMut(State, ClassName, Current)
    State.Depth -= 1
    State.ActiveNode = Previous
    State.CheckResult(Current, Parsed)
    State.ObjectValues[Result] = Parsed
    return Result
