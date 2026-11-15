from dataclasses import replace as Replace
from struct import error as StructError

from convert.adapters.solidworks.config.CutConfig import CutConfig, ReadCutConfig
from convert.adapters.solidworks.config.CutEquation import CutEquation, EquationDim
from convert.adapters.solidworks.config.RootLayout import KConfigGen
from convert.adapters.solidworks.container.Archive import ArchiveError
from convert.adapters.solidworks.core.cut.CutOpProjection import AttachCutOp
from convert.adapters.solidworks.core.cut.CutSource import CutSource
from convert.adapters.solidworks.core.Native import NativeEquation, NativeFeature, NativeModel
from convert.adapters.solidworks.resolved.cut.CutLinks import KCutListCount, CutLinks, ReadCutLinks
from convert.adapters.solidworks.resolved.cut.CutProof import ReadCutProof
from convert.adapters.solidworks.resolved.cut.LinkedProfile import LinkedProfile


# equation provenance keeps the exact stored slot of each ordered term
def BuildCutEq(Equation: CutEquation, StreamName: str, ConfigId: int) -> NativeEquation:
    _, _, Expression = Equation.SourceText.partition(" = ")
    return NativeEquation(
        source=Equation.SourceText,
        lhs=Equation.Target.LabelValue[1:-1],
        rhs=Expression,
        references=(Equation.OuterTerm.LabelValue[1:-1], Equation.InnerTerm.LabelValue[1:-1]),
        native_offset=Equation.TextStart,
        native_length=Equation.TextEnd - Equation.TextStart,
        configuration_id=ConfigId,
        native_stream=StreamName,
        archive_spans=(
            (Equation.Target.SlotOffset, 4, "equation-target-slot"),
            (Equation.OuterTerm.SlotOffset, 4, "equation-outer-slot"),
            (Equation.InnerTerm.SlotOffset, 4, "equation-inner-slot"),
        ),
    )


# authored length values retain the established parameter ids through the native feature
def UpdateEqOwner(
    Features: tuple[NativeFeature, ...], Profile: LinkedProfile,
    Terms: tuple[EquationDim, ...],
) -> tuple[NativeFeature, NativeFeature] | None:
    Matches = tuple(
        Feature
        for Feature in Features
        if (Feature.object_id, Feature.name) == (Profile.FeatureId, Profile.NameValue)
    )
    if len(Matches) != 1:
        return None
    (Owner,) = Matches
    Values = {TermValue.ParamName: TermValue.Metres for TermValue in Terms}
    Dimensions = tuple(
        Dimension for Dimension in Owner.dimensions if Dimension.name in Values
    )
    if len(Dimensions) != len(Values) or {Value.name for Value in Dimensions} != Values.keys():
        return None
    if any(Dimension.kind != "length" for Dimension in Dimensions):
        return None
    Updated = Replace(
        Owner,
        dimensions=tuple(
            Replace(Dimension, value_mm=Values[Dimension.name] * 1000, native_value=Values[Dimension.name])
            if Dimension.name in Values else Dimension
            for Dimension in Owner.dimensions
        ),
    )
    return Owner, Updated


# the typed assignments must agree with the resolved feature and parameter identities
def AttachCutEqs(
    Model: NativeModel, Config: CutConfig, Links: CutLinks, StreamName: str
) -> NativeModel:
    First, Second = Config.Equations
    Outer = UpdateEqOwner(
        Model.features, Links.Rectangle, (First.OuterTerm, Second.OuterTerm)
    )
    Inner = UpdateEqOwner(
        Model.features, Links.CutProfile,
        (First.Target, First.InnerTerm, Second.Target, Second.InnerTerm),
    )
    if Outer is None or Inner is None or Model.active_configuration_id is None:
        return Model
    Owners = {Source.object_id: Updated for Source, Updated in (Outer, Inner)}
    Equations = tuple(
        BuildCutEq(Equation, StreamName, Model.active_configuration_id)
        for Equation in Config.Equations
    )
    return Replace(
        Model,
        features=tuple(Owners.get(Feature.object_id, Feature) for Feature in Model.features),
        equations=Equations,
    )


# other schema families keep their existing equation reader when this archive shape fails
def ReadCutArchive(
    Model: NativeModel, ConfigBlob: bytes, Resolved: bytes,
    Generation: int | None, StreamName: str, ResolvedStream: str,
) -> NativeModel:
    if Generation != KConfigGen or int.from_bytes(Resolved[4:6], "little") != KCutListCount:
        return Model
    try:
        Config = ReadCutConfig(ConfigBlob, Generation)
        Links = ReadCutLinks(Resolved, Config)
    except (ArchiveError, StructError):
        return Model
    Result = AttachCutEqs(Model, Config, Links, StreamName)
    try:
        Proof = ReadCutProof(Links, Config)
    except (ArchiveError, StructError):
        return Result
    Operation = AttachCutOp(Result, Proof)
    SketchValue = Config.Sketches.get(Links.CutProfile.SketchIndex)
    if Operation is Result or SketchValue is None:
        return Operation
    return Replace(
        Operation,
        cut_source=CutSource(
            Proof.Support, SketchValue.SketchData, Links.CutProfile.FeatureId,
            Links.BossValue["native_feature_id"], StreamName, ResolvedStream,
        ),
    )
