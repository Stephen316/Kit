"""Native generation-19000 document properties for a fresh ordinary part."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from re import compile as Compile
from xml.etree.ElementTree import fromstring

from PartFraming import VersionStorage
from PartOpc import (
    APP_PROPERTIES,
    CORE_PROPERTIES,
    CUSTOM_PROPERTIES_XML,
    PACKAGE_NS,
)
from PartSectionProperties import KConfigXml, EncodeSectionProps
from PartSimpleProperties import (
    AppProperties,
    CoreProperties as XmlCoreProperties,
    EncodeAppProps,
    EncodeCoreProps,
)

CORE_NS = f"{PACKAGE_NS}/metadata/core-properties"
ELEMENTS_NS = "http://purl.org/dc/elements/1.1/"
TERMS_NS = "http://purl.org/dc/terms/"
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
INVALID_NAME_TEXT = Compile(r"[\x00-\x1f\ud800-\udfff\ufffe\uffff]")


@dataclass(frozen=True)
class CoreProperties:
    LastModifiedBy: str
    CreatedTime: int
    ModifiedTime: int


@dataclass(frozen=True)
class CustomSummary:
    HasHyperlinks: bool
    AdditionalPropertyCount: int


# The native fresh extended-properties DOM owns these presentation defaults.
DEFAULT_APP = AppProperties(
    "Normal.dotm",
    1526,
    "SOLIDWORKS",
    0,
    "Dassault Systèmes SolidWorks Corporation",
    False,
    False,
    False,
    "23.0000",
)


# The OLE summary clock is formatted as UTC whole seconds.
def SummaryTime(Seconds: int) -> datetime:
    if type(Seconds) is not int or not 0 <= Seconds <= 0xFFFFFFFF:
        raise ValueError(
            "core property time must fit the part's unsigned seconds range"
        )
    return EPOCH + timedelta(seconds=Seconds)


def EncodeDocumentProperties(
    Generation: int, Core: CoreProperties, Custom: CustomSummary
) -> dict[str, bytes]:
    VersionStorage(Generation)
    Author = Core.LastModifiedBy
    if (
        not issubclass(type(Author), str)
        or not Author
        or INVALID_NAME_TEXT.search(Author)
    ):
        raise ValueError("core property last modifier must be valid XML identity text")
    Count = Custom.AdditionalPropertyCount
    if Custom.HasHyperlinks is not False or type(Count) is not int or Count != 0:
        raise ValueError("custom properties support the empty unlinked summary")
    return {
        APP_PROPERTIES: EncodeAppProps(DEFAULT_APP),
        CORE_PROPERTIES: EncodeCoreProps(
            XmlCoreProperties(
                Author, SummaryTime(Core.CreatedTime), SummaryTime(Core.ModifiedTime)
            )
        ),
        CUSTOM_PROPERTIES_XML: EncodeSectionProps(False)[CUSTOM_PROPERTIES_XML],
    }


# The configured user section acquires UTF-8 independently of the office section.
def EncodeConfigurationProperties(
    Generation: int, StorageIndex: int, AdditionalPropertyCount: int
) -> dict[str, bytes]:
    VersionStorage(Generation)
    if (
        type(StorageIndex) is not int
        or StorageIndex != 0
        or type(AdditionalPropertyCount) is not int
        or AdditionalPropertyCount != 0
    ):
        raise ValueError("only the first empty configuration property set is supported")
    return {KConfigXml: EncodeSectionProps(False)[KConfigXml]}


def ReadCoreProperties(Generation: int, Data: bytes) -> CoreProperties:
    VersionStorage(Generation)
    Root = fromstring(Data)
    Names = (
        f"{{{ELEMENTS_NS}}}lastModifiedBy",
        f"{{{TERMS_NS}}}created",
        f"{{{TERMS_NS}}}modified",
    )
    if (
        Root.tag != f"{{{CORE_NS}}}coreProperties"
        or tuple(Child.tag for Child in Root) != Names
    ):
        raise ValueError("unsupported native core property layout")
    Author, Created, Modified = (Child.text for Child in Root)
    if not Author or Created is None or Modified is None:
        raise ValueError("incomplete native core property fields")
    Times = []
    for Time in (Created, Modified):
        Date = datetime.fromisoformat(Time)
        Seconds = (Date - EPOCH) // timedelta(seconds=1) if Date.tzinfo else -1
        if (
            SummaryTime(Seconds).isoformat(timespec="seconds").replace("+00:00", "Z")
            != Time
        ):
            raise ValueError("unsupported core property date format")
        Times.append(Seconds)
    return CoreProperties(Author, *Times)
