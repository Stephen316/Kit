"""Open-time metadata for a new or once opened ordinary standalone part."""

from dataclasses import dataclass
from xml.etree.ElementTree import Element, SubElement, fromstring

from PartFraming import VersionStorage
from PartOpc import OFFICE_NS, EncodePackageXml

OPEN_TIME_STREAM = "docProps/OpenTime.xml"
OPEN_TIME_NS = f"{OFFICE_NS}/SolidworksOpenTime"
VARIANT_TYPE_NS = f"{OFFICE_NS}/docPropsVTypes"
TIMING_FIELDS = ("count", "TotalFileOpenTime", "LWcount", "LWTotalFileOpenTime")
DISPLAY_TIME = "FileOpenTime"


@dataclass(frozen=True)
class OpenTiming:
    Count: int
    TotalSeconds: int | None


@dataclass(frozen=True)
class PartOpenTime:
    Resolved: OpenTiming
    Lightweight: OpenTiming
    ShowResolvedAverage: bool = False


# The fresh sentinel and a single saved open have different clock meanings.
def TimingFields(Timing: OpenTiming) -> tuple[int, int]:
    Count, Total = Timing.Count, Timing.TotalSeconds
    if type(Count) is int:
        if Count == 0 and Total is None:
            return Count, -1
        if Count == 1 and type(Total) is int and 0 <= Total <= 0xFFFFFFFE:
            return Count, Total
    raise ValueError("only fresh and once-open timing histories are supported")


def AverageText(Resolved: tuple[int, int], Show: bool) -> str | None:
    if type(Show) is not bool:
        raise ValueError("the formatted open average selection must be boolean")
    if not Show:
        return None
    Count, Total = Resolved
    if Count != 1 or Total <= 0:
        raise ValueError("open average needs a positive measured duration")
    Minutes, Seconds = divmod(Total, 60)
    return f"{Minutes}:{Seconds:02}"


def EncodePartOpenTime(Generation: int, State: PartOpenTime) -> bytes:
    VersionStorage(Generation)
    Resolved = TimingFields(State.Resolved)
    Lightweight = TimingFields(State.Lightweight)
    if Lightweight[1] > 0:
        raise ValueError("the ordinary timing codec omits a lightweight open average")
    Average = AverageText(Resolved, State.ShowResolvedAverage)
    Root = Element("Properties", {"xmlns": OPEN_TIME_NS, "xmlns:vt": VARIANT_TYPE_NS})
    # Each child explicitly resets the default namespace in the native DOM.
    for Name, Value in zip(TIMING_FIELDS, (*Resolved, *Lightweight), strict=True):
        SubElement(Root, Name, xmlns="").text = str(Value)
    if Average is not None:
        SubElement(Root, DISPLAY_TIME, xmlns="").text = Average
    return EncodePackageXml(Root, Standalone=True)


def ReadPartOpenTime(Generation: int, Data: bytes) -> PartOpenTime:
    VersionStorage(Generation)
    Root = fromstring(Data)
    Names = tuple(Child.tag for Child in Root)
    if Root.tag != f"{{{OPEN_TIME_NS}}}Properties" or Names not in (
        TIMING_FIELDS,
        (*TIMING_FIELDS, DISPLAY_TIME),
    ):
        raise ValueError("unsupported native open timing element layout")
    Text = tuple(Child.text for Child in Root)
    if None in Text or any(Child.attrib or len(Child) for Child in Root):
        raise ValueError("invalid native open timing scalar element")
    Count, Total, LWCount, LWTotal = (
        int(Value) for Value in Text[:4] if Value is not None
    )
    Show = len(Names) == 5
    State = PartOpenTime(
        OpenTiming(Count, None if Total == -1 else Total),
        OpenTiming(LWCount, None if LWTotal == -1 else LWTotal),
        Show,
    )
    Average = AverageText(TimingFields(State.Resolved), Show)
    if TimingFields(State.Lightweight)[1] > 0 or (Show and Text[-1] != Average):
        raise ValueError("unsupported native formatted open duration")
    return State
