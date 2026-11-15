from convert.adapters.Fusion.Authoring.MakeParams import MakeLength
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.OffsetSpec import (
    OffsetSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import PlaneSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.BodyGridSpec import (
    BodyGridSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LoftSpec import LoftSpec
from interchange.records.RecordParameter import Parameter


# the driving length contract needs a shared interpretation so public document claims remain grounded in native records
def DrivingLength(Feature: KPartFeature) -> tuple[str, float] | None:
    if isinstance(Feature, FilletSpec):
        return "Radius", Feature.RadiusMm
    if isinstance(Feature, ChamferSpec):
        Label = "Distance 1" if Feature.SecondMm > 0 else "Distance"
        return Label, Feature.DistanceMm
    if isinstance(Feature, ShellSpec):
        return "innerThickness", Feature.ThicknessMm
    if isinstance(Feature, ExtrudeSpec):
        return "AlongDistance", Feature.DistanceMm
    if isinstance(Feature, HoleSpec):
        return "HoleDiameter", Feature.DiameterMm
    if isinstance(Feature, (PatternSpec, BodyGridSpec)):
        return "uSpaceDistance", Feature.SpacingUMm
    if isinstance(Feature, PlaneSpec):
        return "AlongDistance", Feature.OffsetMm
    if isinstance(Feature, OffsetSpec):
        return "distance", Feature.DistanceMm
    if isinstance(Feature, LoftSpec):
        return "AlongDistance", Feature.HeightMm
    return None


# the part parameters operation needs a consistent construction rule so public document claims remain grounded in native records
def MakePartParams(SpecValue: DocumentSpec) -> tuple[Parameter, ...]:
    Values: list[Parameter] = []
    for Index, Feature in enumerate(SpecValue.Features):
        Identity = "feature" + str(Index + 1)
        Driving = DrivingLength(Feature)
        if Driving is not None:
            NameValue, Amount = Driving
            Values.append(MakeLength(Identity + "-amount", NameValue, Amount, Identity))
    return tuple(Values)
