from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias, Union

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef


@MakeDataClass(frozen=True, slots=True)
class DwgField:
    FieldName: str
    FieldValue: "KDwgValue"


@MakeDataClass(frozen=True, slots=True)
class DwgRecord:
    RecordFields: tuple[DwgField, ...]


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
