from collections.abc import Iterable, Mapping
from dataclasses import fields as DataFields
from dataclasses import is_dataclass as IsDataClass
from typing import cast as CastValue

from convert.Commands.CheckKinds import CheckKinds
from interchange.document.models.DocumentModel import CadDocument

# retained source data needs a distinct refusal that directs callers toward inspection
KMetadataError = (
    "RetainedMetadata records are not conversion-ready; "
    "use kit decode or kit research for inspection"
)


# retained native bytes must be refused wherever serialization preserves them in the document graph
def CheckRetained(Document: CadDocument) -> None:
    Pending: list[object] = [Document]
    VisitedIds = set[int]()
    while Pending:
        Value = Pending.pop()
        ValueId = id(Value)
        if ValueId in VisitedIds:
            continue
        if IsDataClass(Value) and not isinstance(Value, type):
            CheckKinds(Value)
            VisitedIds.add(ValueId)
            Pending.extend(
                CastValue(object, getattr(Value, Field.name))
                for Field in DataFields(Value)
            )
            continue
        if isinstance(Value, (bytes, bytearray, memoryview)) or (
            isinstance(Value, Mapping) and "solidworks_source_bytes" in Value
        ):
            raise ValueError(KMetadataError)
        if not isinstance(Value, (Mapping, list, tuple, set, frozenset)):
            continue
        VisitedIds.add(ValueId)
        Pending.extend(
            CastValue(Mapping[object, object], Value).values()
            if isinstance(Value, Mapping)
            else CastValue(Iterable[object], Value)
        )
