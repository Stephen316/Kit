# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from collections.abc import Mapping as MappingBase
from typing import cast as CastValue
from typing import Protocol as TypeProtocol
from typing import runtime_checkable as RuntimeCheck


# reflection consumers need only the stable public surface shared by dataclass fields
@RuntimeCheck
class DataField(TypeProtocol):
    name: str
    type: object
    kw_only: bool


# compatibility renames runtime classes so wire identity needs the preserved source name
def CanonName(ClassType: type[object]) -> str:
    CanonicalValue: object = vars(ClassType).get("__canonical_name__")
    return CanonicalValue if isinstance(CanonicalValue, str) else ClassType.__name__


# dynamic dataclass metadata must be validated before reflection code relies on its shape
def GetFieldMap(SourceValue: object) -> dict[str, DataField]:
    ClassType = SourceValue if isinstance(SourceValue, type) else type(SourceValue)
    RawFields: object = vars(ClassType).get("__dataclass_fields__")
    if not isinstance(RawFields, MappingBase):
        raise TypeError(f"{ClassType.__name__} is not a dataclass type")
    FieldItems = CastValue(MappingBase[object, object], RawFields)
    ResultValue: dict[str, DataField] = {}
    for FieldName, FieldValue in FieldItems.items():
        if not isinstance(FieldName, str) or not isinstance(FieldValue, DataField):
            raise TypeError(f"{ClassType.__name__} has invalid dataclass metadata")
        ResultValue[FieldName] = FieldValue
    return ResultValue


# ordered field access keeps reflection deterministic without depending on private typing contracts
def GetDataFields(SourceValue: object) -> tuple[DataField, ...]:
    return tuple(GetFieldMap(SourceValue).values())
