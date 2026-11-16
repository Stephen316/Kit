"""Native generation-19000 document properties for a fresh ordinary part."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from re import compile as Compile
from xml.etree.ElementTree import Element, SubElement, fromstring

from PartFraming import VersionStorage
from PartOpc import (
    APP_PROPERTIES,
    CORE_PROPERTIES,
    CUSTOM_PROPERTIES_XML,
    OFFICE_NS,
    PACKAGE_NS,
    EncodePackageXml,
)


APP_NS = f"{OFFICE_NS}/extended-properties"
CUSTOM_NS = f"{OFFICE_NS}/custom-properties"
VARIANT_NS = f"{OFFICE_NS}/docPropsVTypes"
CORE_NS = f"{PACKAGE_NS}/metadata/core-properties"
ELEMENTS_NS = "http://purl.org/dc/elements/1.1/"
TERMS_NS = "http://purl.org/dc/terms/"
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
INVALID_NAME_TEXT = Compile(r"[\x00-\x1f\ud800-\udfff\ufffe\uffff]")
SUMMARY_SECTION = ("DocumentSummaryInformation", "{D5CDD502-2E9C-101B-9397-08002B2CF9AE}")
USER_SECTION = ("UserDefinedProperties", "{D5CDD505-2E9C-101B-9397-08002B2CF9AE}")
UTF8_CODE_PAGE = 65001


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
def MakeAppProperties() -> Element:
    Root = Element("Properties", {"xmlns": APP_NS, "xmlns:vt": VARIANT_NS})
    Fields = (
        ("Template", "Normal.dotm"),
        ("TotalTime", "1526"),
        ("Application", "SOLIDWORKS"),
        ("DocSecurity", "0"),
        ("Company", "Dassault Systèmes SolidWorks Corporation"),
        ("LinksUpToDate", "false"),
        ("SharedDoc", "false"),
        ("HyperlinksChanged", "false"),
        ("AppVersion", "23.0000"),
    )
    for Name, Value in Fields:
        SubElement(Root, Name).text = Value
    return Root


# The OLE summary clock is formatted as UTC whole seconds.
def FormatSummaryTime(Seconds: int) -> str:
    if type(Seconds) is not int or not 0 <= Seconds <= 0xFFFFFFFF:
        raise ValueError("core property time must fit the part's unsigned seconds range")
    return (EPOCH + timedelta(seconds=Seconds)).isoformat(timespec="seconds").replace("+00:00", "Z")


def MakeCoreProperties(State: CoreProperties) -> Element:
    Author = State.LastModifiedBy
    if not isinstance(Author, str) or not Author or INVALID_NAME_TEXT.search(Author):
        raise ValueError("core property last modifier must be valid XML identity text")
    Root = Element(
        "cp:coreProperties",
        {
            "xmlns:cp": CORE_NS,
            "xmlns:dc": ELEMENTS_NS,
            "xmlns:dcterms": TERMS_NS,
            "xmlns:dcmitype": "http://purl.org/dc/dcmitype/",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        },
    )
    SubElement(Root, "dc:lastModifiedBy").text = Author
    SubElement(Root, "dcterms:created").text = FormatSummaryTime(State.CreatedTime)
    SubElement(Root, "dcterms:modified").text = FormatSummaryTime(State.ModifiedTime)
    return Root


# Each native OLE section owns its codepage and its empty dictionary.
def MakeCustomProperties(State: CustomSummary) -> Element:
    Count = State.AdditionalPropertyCount
    if State.HasHyperlinks is not False or type(Count) is not int or Count != 0:
        raise ValueError("custom properties support the empty unlinked summary")
    Root = Element("Properties", {"xmlns": CUSTOM_NS, "xmlns:vt": VARIANT_NS})
    for Name, FormatId in (SUMMARY_SECTION, USER_SECTION):
        Section = SubElement(Root, "propertySection", xmlns="", name=Name, fmtid=FormatId)
        CodePage = SubElement(Section, "property", name="", pid="1", TypeID="0")
        SubElement(CodePage, "vt:i2").text = str(UTF8_CODE_PAGE)
        if Name == SUMMARY_SECTION[0]:
            Link = SubElement(Section, "property", name="", pid="22", TypeID="0")
            SubElement(Link, "vt:bool").text = "No"
        _ = SubElement(Section, "propertyNameDictionaryElement", name="", pid="0")
    return Root


def EncodeDocumentProperties(Generation: int, Core: CoreProperties, Custom: CustomSummary) -> dict[str, bytes]:
    VersionStorage(Generation)
    return {
        APP_PROPERTIES: EncodePackageXml(MakeAppProperties(), Standalone=True),
        CORE_PROPERTIES: EncodePackageXml(MakeCoreProperties(Core), Standalone=True),
        CUSTOM_PROPERTIES_XML: EncodePackageXml(
            MakeCustomProperties(Custom), Standalone=True, ShortEmptyElements=False
        ),
    }


def ReadCoreProperties(Generation: int, Data: bytes) -> CoreProperties:
    VersionStorage(Generation)
    Root = fromstring(Data)
    Names = (
        f"{{{ELEMENTS_NS}}}lastModifiedBy",
        f"{{{TERMS_NS}}}created",
        f"{{{TERMS_NS}}}modified",
    )
    if Root.tag != f"{{{CORE_NS}}}coreProperties" or tuple(Child.tag for Child in Root) != Names:
        raise ValueError("unsupported native core property layout")
    Author, Created, Modified = (Child.text for Child in Root)
    if not Author or Created is None or Modified is None:
        raise ValueError("incomplete native core property fields")
    Times = []
    for Time in (Created, Modified):
        Date = datetime.fromisoformat(Time)
        Seconds = (Date - EPOCH) // timedelta(seconds=1) if Date.tzinfo else -1
        if FormatSummaryTime(Seconds) != Time:
            raise ValueError("unsupported core property date format")
        Times.append(Seconds)
    return CoreProperties(Author, *Times)
