from collections.abc import Mapping

from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KNullKind,
    KObjectRefKind,
    ArchiveError,
    TagAction,
)


# configuration and resolved records need one source of truth for typed archive references
def ResolveMapType(
    TagValue: TagAction,
    ClassMap: Mapping[int, str],
    ObjectMap: Mapping[int, str],
    SchemaValue: int = 1,
) -> str | None:
    if TagValue.kind == KNullKind:
        return None
    if TagValue.kind == KDefinitionKind:
        if TagValue.schema != SchemaValue:
            raise ArchiveError(
                f"archive schema {TagValue.schema} differs from {SchemaValue}"
            )
        return TagValue.class_name
    if TagValue.index and TagValue.kind in (KClassRefKind, KObjectRefKind):
        OwnerMap = ClassMap if TagValue.kind == KClassRefKind else ObjectMap
        NameValue = OwnerMap.get(TagValue.index)
        if NameValue is not None:
            return NameValue
    raise ArchiveError(f"unallocated archive {TagValue.kind} {TagValue.index}")


# one checked reservation preserves ownership when a definition requires two slots
def BindMapTagMut(
    TagValue: TagAction,
    Counter: int,
    ClassMap: dict[int, str],
    ObjectMap: dict[int, str],
    NameValue: str | None,
) -> tuple[int, int]:
    if TagValue.kind not in (KDefinitionKind, KClassRefKind):
        return TagValue.index, Counter
    ObjectIndex = Counter + int(TagValue.kind == KDefinitionKind)
    if NameValue is None or any(
        Index in ClassMap or Index in ObjectMap
        for Index in range(Counter, ObjectIndex + 1)
    ):
        raise ArchiveError(
            f"expected unused map slots at {Counter} through {ObjectIndex}"
        )
    if TagValue.kind == KDefinitionKind:
        ClassMap[Counter] = NameValue
    ObjectMap[ObjectIndex] = NameValue
    return ObjectIndex, ObjectIndex + 1
