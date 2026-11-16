from typing import cast as CastValue

from interchange.assembly.AssemblyEnums import ComponentKind, MateEntityKind, MateKind
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateEntity import MateEntity
from interchange.Enums.EnumGeometry import ConstraintKind, GeometryKind
from interchange.geometry.Models.Sketch import SketchEntity, SketchRelation

# portable conversion needs explicit supported kind sets for open typed records
KRecordKinds: dict[type[object], frozenset[str]] = {
    Record: frozenset(
        KindValue.value for KindValue in Kinds if KindValue.value != "native"
    )
    for Record, Kinds in (
        (ComponentDef, ComponentKind),
        (MateConstraint, MateKind),
        (MateEntity, MateEntityKind),
        (SketchEntity, GeometryKind),
        (SketchRelation, ConstraintKind),
    )
}


# open record kind strings must not imply supported semantics merely because links validate
def CheckKinds(Record: object) -> None:
    for RecordType, AllowedKinds in KRecordKinds.items():
        if (
            isinstance(Record, RecordType)
            and CastValue(str, getattr(Record, "kind")) not in AllowedKinds
        ):
            raise ValueError(
                "NativeRecord records are not conversion-ready; use kit decode or kit research for inspection"
            )
