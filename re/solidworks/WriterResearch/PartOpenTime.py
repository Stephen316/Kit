"""Open-time metadata for a new or once opened ordinary standalone part."""

from dataclasses import dataclass
from xml.etree.ElementTree import Element, SubElement, fromstring

from PartFraming import VersionStorage
from PartOpc import OFFICE_NS, EncodePackageXml


OPEN_TIME_STREAM = "docProps/OpenTime.xml"
OPEN_TIME_NS = f"{OFFICE_NS}/SolidworksOpenTime"
VARIANT_TYPE_NS = f"{OFFICE_NS}/docPropsVTypes"
TIMING_FIELDS = ("count", "TotalFileOpenTime", "LWcount", "LWTotalFileOpenTime")


@dataclass(frozen=True)
class OpenTiming:
    Count: int
    TotalSeconds: int | None


@dataclass(frozen=True)
class PartOpenTime:
    Resolved: OpenTiming
    Lightweight: OpenTiming


# These saved timing pairs have no formatted average elements.
def TimingFields(Timing: OpenTiming) -> tuple[int, int]:
    Count, Total = Timing.Count, Timing.TotalSeconds
    if type(Count) is int:
        if Count == 0 and Total is None:
            return Count, -1
        if Count == 1 and type(Total) is int and Total == 0:
            return Count, Total
    raise ValueError("only fresh and once-open timing histories are supported")


def EncodePartOpenTime(Generation: int, State: PartOpenTime) -> bytes:
    VersionStorage(Generation)
    Resolved = TimingFields(State.Resolved)
    Lightweight = TimingFields(State.Lightweight)
    Root = Element("Properties", {"xmlns": OPEN_TIME_NS, "xmlns:vt": VARIANT_TYPE_NS})
    # Each child explicitly resets the default namespace in the native DOM.
    for Name, Value in zip(TIMING_FIELDS, (*Resolved, *Lightweight), strict=True):
        SubElement(Root, Name, xmlns="").text = str(Value)
    return EncodePackageXml(Root, Standalone=True)


def ReadPartOpenTime(Generation: int, Data: bytes) -> PartOpenTime:
    VersionStorage(Generation)
    Root = fromstring(Data)
    if Root.tag != f"{{{OPEN_TIME_NS}}}Properties" or tuple(Child.tag for Child in Root) != TIMING_FIELDS:
        raise ValueError("unsupported native open timing element layout")
    Text = tuple(Child.text for Child in Root)
    if None in Text or any(Child.attrib or len(Child) for Child in Root):
        raise ValueError("invalid native open timing scalar element")
    Count, Total, LWCount, LWTotal = (int(Value) for Value in Text if Value is not None)
    State = PartOpenTime(
        OpenTiming(Count, None if Total == -1 else Total),
        OpenTiming(LWCount, None if LWTotal == -1 else LWTotal),
    )
    _ = TimingFields(State.Resolved)
    _ = TimingFields(State.Lightweight)
    return State
