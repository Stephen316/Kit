from collections.abc import Mapping

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import (
    DwgField,
    DwgRecord,
    KDwgValue,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Objects.LookupSpec import LookupSpec
from convert.formats.Fusion.DrawingCodec.Dwg.Records.SpecOp import SpecOp
from convert.formats.Fusion.DrawingCodec.Dwg.Records.SpecScope import (
    KBranchKinds,
    KScopes,
    IsBranchTrue,
)

KNoSpares: frozenset[str] = frozenset()


def ShapeOpsMut(
    SpecOps: tuple[SpecOp, ...],
    Values: Mapping[str, KDwgValue],
    Written: list[DwgField],
    Scopes: KScopes,
    VersionText: str,
) -> None:
    Inner = (Written, *Scopes)
    for Operation in SpecOps:
        if Operation.OpKind in KBranchKinds:
            IsTaken = IsBranchTrue(Operation, Inner, VersionText)
            Chosen = Operation.BodyOps if IsTaken else Operation.ElseOps
            ShapeOpsMut(Chosen, Values, Written, Scopes, VersionText)
            continue
        if Operation.OpName not in Values:
            raise ValueError(f"Authored DWG record lacks field {Operation.OpName!r}")
        Written.append(DwgField(Operation.OpName, Values[Operation.OpName]))


def ShapeRecord(
    SpecKey: str,
    Values: Mapping[str, KDwgValue],
    VersionText: str,
    SpareFields: frozenset[str] = KNoSpares,
) -> DwgRecord:
    Written: list[DwgField] = []
    ShapeOpsMut(LookupSpec(SpecKey), Values, Written, (), VersionText)
    Unused = set(Values) - {Entry.FieldName for Entry in Written} - SpareFields
    if Unused:
        raise ValueError(f"Authored DWG record has unused fields {sorted(Unused)}")
    return DwgRecord(tuple(Written))
