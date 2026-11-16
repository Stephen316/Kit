from convert.Formats.Fusion.Profiles.Trimmed.CirclePortions import ReadCircleTrim
from convert.Formats.Fusion.Profiles.Trimmed.LinePortions import ReadLineTrim
from convert.Formats.Fusion.Profiles.Trimmed.MixedPortions import ReadMixedTrim
from convert.Formats.Fusion.Profiles.Trimmed.TrimPortion import TrimPortion
from convert.Formats.Fusion.Profiles.Trimmed.TrimRing import CheckTrimRing
from convert.Formats.Fusion.Profiles.Trimmed.TrimSelectors import ReadTrimMembers
from convert.Formats.Fusion.Profiles.Trimmed.TrimSources import ReadTrimSource
from interchange.geometry.Models.GeometryCurves import CircleGeometry, LineGeometry
from interchange.geometry.Models.Sketch import Sketch


# only observed source families can turn exact native selectors into bounded portions
def ReadTrimProfile(
    BodyValue: bytes, DescriptorId: int, SketchValue: Sketch
) -> tuple[TrimPortion, ...]:
    Sources = ReadTrimSource(SketchValue)
    Members = ReadTrimMembers(BodyValue, DescriptorId, Sources)
    Circles = {
        TagValue: Entity.geometry
        for TagValue, Entity in Sources.items()
        if isinstance(Entity.geometry, CircleGeometry)
    }
    Lines = tuple(
        Entity
        for Entity in Sources.values()
        if isinstance(Entity.geometry, LineGeometry)
    )
    if not Lines and 2 <= len(Circles) <= 3:
        Portions = ReadCircleTrim(Circles, Members)
    elif not Circles and len(Lines) == 8:
        Portions = ReadLineTrim(Lines, Members)
    elif len(Circles) == len(Lines) == 1:
        Portions = ReadMixedTrim(next(iter(Circles.values())), Lines[0], Members)
    else:
        raise ValueError("Unsupported Fusion trimmed profile source family")
    CheckTrimRing(Sources, Portions)
    return Portions
