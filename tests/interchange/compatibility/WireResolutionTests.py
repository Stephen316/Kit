from dataclasses import make_dataclass as MakeRecord
from typing import cast as CastValue

from interchange.serialization.RecordType import DataRecord
from interchange.serialization.Wire import ResolveField


# matching aliases must still honor base slot priority and normalized legacy names
def CheckSlotOrder() -> None:
    Parent = MakeRecord("WireParent", [("EntityId", str)], slots=True)
    Record = CastValue(
        type[DataRecord],
        MakeRecord("WireRecord", [("id", str)], bases=(Parent,), slots=True),
    )
    assert ResolveField(Record, "id") == "EntityId"
    assert ResolveField(Record, "EntityId") == "id"
    assert ResolveField(Record, "Id") == "id"
    WireKey = CastValue(type[str], type("WireKey", (str,), {"__hash__": None}))
    assert ResolveField(Record, WireKey("id")) == "EntityId"


# classes without canonical slots can still provide historical dataclass field names
def CheckReflection() -> None:
    Record = CastValue(
        type[DataRecord], MakeRecord("WireRecord", [("reflected_name", str)])
    )
    assert ResolveField(Record, "reflected_name") == "reflected_name"
    assert ResolveField(Record, "unknown_name") == "UnknownName"


# extension classes may expose a different schema after the first field lookup
def CheckSlotChange() -> None:
    Record = CastValue(
        type[DataRecord], MakeRecord("WireRecord", [("old_name", str)], slots=True)
    )
    assert ResolveField(Record, "new_name") == "NewName"
    setattr(Record, "__slots__", ("new_name",))
    assert ResolveField(Record, "new_name") == "new_name"
