from convert.formats.Fusion.TSplineCodec.Model.SymmetryMap import SymmetryMap
from convert.formats.Fusion.TSplineCodec.Validation.CheckIndices import CheckIndices


def CheckSymMap(Mapping: SymmetryMap, Limit: int) -> None:
    for Pairs in (Mapping.Forward, Mapping.Reverse):
        CheckIndices(
            tuple(Value.SourceIndex for Value in Pairs), Limit, "symmetry source"
        )
        CheckIndices(
            tuple(Value.TargetIndex for Value in Pairs), Limit, "symmetry target"
        )
    Forward = {Value.SourceIndex: Value.TargetIndex for Value in Mapping.Forward}
    Reverse = {Value.SourceIndex: Value.TargetIndex for Value in Mapping.Reverse}
    if set(Forward) & set(Reverse) or set(Forward) | set(Reverse) != set(range(Limit)):
        raise ValueError("Unsupported TSM symmetry partition")
    if any(Reverse.get(Target) != Source for Source, Target in Forward.items()):
        raise ValueError("Nonreciprocal TSM forward symmetry")
    if any(
        Source != Target and Forward.get(Target) != Source
        for Source, Target in Reverse.items()
    ):
        raise ValueError("Nonreciprocal TSM reverse symmetry")
