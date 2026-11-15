from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias, Union

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef


# drawing field needs an explicit state contract so section boundaries and object references remain consistent
@MakeDataClass(frozen=True, slots=True)
class DwgField:
    FieldName: str
    FieldValue: "KDwgValue"


# drawing record needs an explicit state contract so section boundaries and object references remain consistent
@MakeDataClass(frozen=True, slots=True)
class DwgRecord:
    RecordFields: tuple[DwgField, ...]


# the drawing value shape must stay shared so native drawing reconstruction uses one contract for compatible values
KDwgValue: TypeAlias = Union[
    int,
    float,
    str,
    bytes,
    DwgHandleRef,
    DwgRecord,
    tuple[float, ...],
    tuple[DwgHandleRef, ...],
    tuple[DwgRecord, ...],
]
